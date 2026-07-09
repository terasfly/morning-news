from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
COVER_IMAGE = ROOT / "rytinis-virselis.png"
DEFAULT_OUTPUT_DIR = ROOT / "public"
DEFAULT_TIMEZONE = "Europe/London"

PAGE_W, PAGE_H = A4
MARGIN_X = 17 * mm
MARGIN_TOP = 15 * mm
MARGIN_BOTTOM = 15 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X

INK = colors.HexColor("#14213D")
MUTED = colors.HexColor("#5F6570")
RULE = colors.HexColor("#C8B99A")
PAPER = colors.HexColor("#F7F1E6")
SOFT_BLUE = colors.HexColor("#E8EEF5")
SOFT_GREEN = colors.HexColor("#E7F0EA")
GOLD = colors.HexColor("#B7853B")


TOPICS = [
    {
        "name": "AI",
        "tag": "AI ir technologijos",
        "why": (
            "Kodėl tai svarbu: AI keičia darbą, produktus ir reguliavimą greičiau negu "
            "dauguma komandų spėja prisitaikyti, todėl verta sekti ne tik modelių naujienas, "
            "bet ir infrastruktūrą, politiką bei realius produktų pokyčius."
        ),
        "keywords": [
            "ai",
            "artificial intelligence",
            "machine learning",
            "openai",
            "anthropic",
            "google deepmind",
            "model",
            "robot",
            "chip",
            "nvidia",
        ],
        "feeds": [
            ("ScienceDaily AI", "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml"),
            ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
            ("MIT News AI", "https://news.mit.edu/rss/topic/artificial-intelligence2"),
            (
                "Google News AI",
                "https://news.google.com/rss/search?q=artificial%20intelligence%20OR%20AI%20when%3A2d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
        ],
    },
    {
        "name": "Smegenys",
        "tag": "Smegenų mokslas",
        "why": (
            "Kodėl tai svarbu: smegenų tyrimai lėtai keliasi iš laboratorinių atradimų į "
            "diagnostiką, terapijas ir kasdienius sveikatos sprendimus. Geras signalas čia "
            "yra atsargus, šaltiniais paremtas progresas."
        ),
        "keywords": [
            "brain",
            "neuroscience",
            "neuron",
            "cognitive",
            "memory",
            "alzheimer",
            "parkinson",
            "dementia",
            "sleep",
            "mri",
        ],
        "feeds": [
            ("ScienceDaily Neuroscience", "https://www.sciencedaily.com/rss/mind_brain/neuroscience.xml"),
            ("Neuroscience News", "https://neurosciencenews.com/feed/"),
            ("Nature Neuroscience", "https://www.nature.com/subjects/neuroscience.rss"),
            (
                "Google News Neuroscience",
                "https://news.google.com/rss/search?q=neuroscience%20OR%20brain%20science%20OR%20Alzheimer%20when%3A2d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
        ],
    },
    {
        "name": "Longevity",
        "tag": "Longevity ir healthspan",
        "why": (
            "Kodėl tai svarbu: ilgaamžiškumo temos lengvai virsta pažadais be pagrindo. "
            "Vertingiausios istorijos yra tos, kurios kalba apie healthspan, prevenciją, "
            "senėjimo biologiją ir žmonėms patikrinamus veiksmus."
        ),
        "keywords": [
            "longevity",
            "healthspan",
            "aging",
            "ageing",
            "older adults",
            "senescence",
            "frailty",
            "metabolism",
            "exercise",
            "nutrition",
        ],
        "feeds": [
            ("ScienceDaily Healthy Aging", "https://www.sciencedaily.com/rss/health_medicine/healthy_aging.xml"),
            ("ScienceDaily Dementia", "https://www.sciencedaily.com/rss/mind_brain/dementia.xml"),
            ("Nature Ageing", "https://www.nature.com/subjects/ageing.rss"),
            (
                "Google News Longevity",
                "https://news.google.com/rss/search?q=longevity%20OR%20healthspan%20OR%20aging%20research%20when%3A2d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
        ],
    },
]


@dataclass
class Article:
    topic: str
    tag: str
    title: str
    summary: str
    url: str
    source: str
    published: str
    score: int


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?is)<br\s*/?>", " ", value)
    value = re.sub(r"(?is)</p\s*>", " ", value)
    value = re.sub(r"(?is)<.*?>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def truncate_sentence(text: str, limit: int = 360) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:")
    return f"{cut}..."


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_text(element: ET.Element, name: str) -> str:
    for child in list(element):
        if local_name(child.tag) == name.lower():
            return clean_text(child.text)
    return ""


def atom_link(element: ET.Element) -> str:
    for child in list(element):
        if local_name(child.tag) == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return ""


def parse_datetime(value: str) -> datetime | None:
    value = clean_text(value)
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def fetch_feed(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RytoSignalas/1.0 (+https://github.com/)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def parse_feed(data: bytes, fallback_source: str, topic: dict) -> list[Article]:
    root = ET.fromstring(data)
    entries: list[Article] = []
    topic_text = " ".join(topic["keywords"]).lower()

    rss_items = [node for node in root.iter() if local_name(node.tag) == "item"]
    atom_items = [node for node in root.iter() if local_name(node.tag) == "entry"]

    for item in rss_items:
        title = child_text(item, "title")
        url = child_text(item, "link") or child_text(item, "guid")
        summary = child_text(item, "description") or child_text(item, "summary")
        source = child_text(item, "source") or fallback_source
        published_dt = parse_datetime(child_text(item, "pubDate") or child_text(item, "published") or child_text(item, "updated"))
        entries.append(make_article(topic, title, summary, url, source, published_dt, topic_text, fallback_source))

    for item in atom_items:
        title = child_text(item, "title")
        url = atom_link(item)
        summary = child_text(item, "summary") or child_text(item, "content")
        source = fallback_source
        published_dt = parse_datetime(child_text(item, "published") or child_text(item, "updated"))
        entries.append(make_article(topic, title, summary, url, source, published_dt, topic_text, fallback_source))

    return [entry for entry in entries if entry.title and entry.url]


def make_article(
    topic: dict,
    title: str,
    summary: str,
    url: str,
    source: str,
    published_dt: datetime | None,
    topic_text: str,
    feed_source: str,
) -> Article:
    combined = f"{title} {summary}".lower()
    keyword_hits = sum(1 for keyword in topic["keywords"] if keyword.lower() in combined)
    title_hits = sum(1 for keyword in topic["keywords"] if keyword.lower() in title.lower())
    recency = 0
    if published_dt:
        age_hours = max(0, (datetime.now(timezone.utc) - published_dt).total_seconds() / 3600)
        recency = max(0, int(24 - (age_hours / 3)))
    summary_bonus = 26 if summary_is_useful(title, summary) else 0
    score = keyword_hits * 6 + title_hits * 4 + summary_bonus + recency
    if "google news" in feed_source.lower():
        score -= 22
    if topic["name"].lower() in topic_text:
        score += 1
    published = published_dt.isoformat() if published_dt else ""
    return Article(
        topic=topic["name"],
        tag=topic["tag"],
        title=clean_text(title),
        summary=truncate_sentence(summary) or "Trumpa šaltinio santrauka nepateikta. Atidaryk nuorodą detalesniam kontekstui.",
        url=url.strip(),
        source=clean_text(source) or "RSS šaltinis",
        published=published,
        score=score,
    )


def summary_is_useful(title: str, summary: str) -> bool:
    summary_clean = clean_text(summary)
    if len(summary_clean) < 120:
        return False
    title_tokens = set(re.findall(r"[a-zA-Z0-9]{4,}", clean_text(title).lower()))
    summary_tokens = set(re.findall(r"[a-zA-Z0-9]{4,}", summary_clean.lower()))
    return len(summary_tokens - title_tokens) >= 8


def collect_articles(per_topic: int) -> tuple[list[Article], list[str]]:
    selected: list[Article] = []
    errors: list[str] = []
    seen: set[str] = set()

    for topic in TOPICS:
        candidates: list[Article] = []
        for source, url in topic["feeds"]:
            try:
                feed = fetch_feed(url)
                candidates.extend(parse_feed(feed, source, topic))
            except (urllib.error.URLError, TimeoutError, ET.ParseError, ValueError) as exc:
                errors.append(f"{source}: {exc}")

        ranked = sorted(candidates, key=lambda article: (article.score, article.published), reverse=True)
        picked = 0
        for article in ranked:
            identity = article.url.split("?", 1)[0].rstrip("/") or article.title.lower()
            title_key = re.sub(r"\W+", "", article.title.lower())[:80]
            if identity in seen or title_key in seen:
                continue
            seen.add(identity)
            seen.add(title_key)
            selected.append(article)
            picked += 1
            if picked >= per_topic:
                break

    return selected, errors


def html_escape(text: str) -> str:
    return html.escape(text, quote=True)


def format_date_lt(run_date: date) -> str:
    months = {
        1: "sausio",
        2: "vasario",
        3: "kovo",
        4: "balandžio",
        5: "gegužės",
        6: "birželio",
        7: "liepos",
        8: "rugpjūčio",
        9: "rugsėjo",
        10: "spalio",
        11: "lapkričio",
        12: "gruodžio",
    }
    return f"{run_date.year} m. {months[run_date.month]} {run_date.day} d."


def iso_to_local(value: str, timezone_name: str) -> str:
    if not value:
        return "data nenurodyta"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return "data nenurodyta"
    local_dt = parsed.astimezone(ZoneInfo(timezone_name))
    return local_dt.strftime("%Y-%m-%d %H:%M")


def prepare_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = output_dir / "assets"
    assets.mkdir(exist_ok=True)
    if COVER_IMAGE.exists():
        shutil.copy2(COVER_IMAGE, assets / COVER_IMAGE.name)
    return assets


def render_html(output_dir: Path, articles: list[Article], run_date: date, timezone_name: str, pdf_name: str, errors: list[str]) -> None:
    assets_rel = f"assets/{COVER_IMAGE.name}" if COVER_IMAGE.exists() else ""
    cards = []
    for idx, article in enumerate(articles, 1):
        cards.append(
            f"""
            <article class="story">
              <div class="story-meta">
                <span>{idx:02d}</span>
                <span>{html_escape(article.tag)}</span>
              </div>
              <h2>{html_escape(article.title)}</h2>
              <p>{html_escape(article.summary)}</p>
              <div class="why">{html_escape(next(topic["why"] for topic in TOPICS if topic["name"] == article.topic))}</div>
              <a href="{html_escape(article.url)}" target="_blank" rel="noreferrer">Šaltinis: {html_escape(article.source)} · {html_escape(iso_to_local(article.published, timezone_name))}</a>
            </article>
            """
        )

    if not cards:
        cards.append(
            """
            <article class="story">
              <div class="story-meta"><span>!</span><span>Šaltiniai</span></div>
              <h2>Šį rytą nepavyko surinkti RSS naujienų</h2>
              <p>Patikrink GitHub Actions žurnalą. Dažniausia priežastis: laikinas RSS šaltinio arba tinklo sutrikimas.</p>
            </article>
            """
        )

    error_note = ""
    if errors:
        error_items = "".join(f"<li>{html_escape(error)}</li>" for error in errors[:6])
        error_note = f"""
        <details class="source-health">
          <summary>Šaltinių būsena</summary>
          <ul>{error_items}</ul>
        </details>
        """

    cover_style = f"background-image: linear-gradient(90deg, rgba(20,33,61,.92), rgba(20,33,61,.52)), url('{assets_rel}');" if assets_rel else ""
    html_doc = f"""<!doctype html>
<html lang="lt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ryto signalas · {html_escape(str(run_date))}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #14213d;
      --text: #20242a;
      --muted: #5f6570;
      --paper: #f7f1e6;
      --line: #c8b99a;
      --blue: #e8eef5;
      --green: #e7f0ea;
      --gold: #b7853b;
      --white: #fffaf0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--paper);
      color: var(--text);
      line-height: 1.55;
    }}
    .hero {{
      min-height: 64vh;
      display: flex;
      align-items: flex-end;
      background-color: var(--ink);
      background-size: cover;
      background-position: center;
      color: white;
      {cover_style}
    }}
    .hero-inner {{
      width: min(980px, calc(100% - 32px));
      margin: 0 auto;
      padding: 56px 0 46px;
    }}
    .kicker {{
      margin: 0 0 10px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0;
      color: #f4c46c;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(2.5rem, 7vw, 5.6rem);
      line-height: 0.95;
      letter-spacing: 0;
    }}
    .deck {{
      max-width: 760px;
      margin: 18px 0 22px;
      font-size: clamp(1rem, 2vw, 1.25rem);
      color: rgba(255,255,255,.88);
    }}
    .download {{
      display: inline-block;
      padding: 11px 15px;
      border: 1px solid rgba(255,255,255,.42);
      color: white;
      text-decoration: none;
      font-weight: 700;
      background: rgba(255,255,255,.10);
    }}
    main {{
      width: min(980px, calc(100% - 32px));
      margin: 0 auto;
      padding: 26px 0 42px;
    }}
    .intro {{
      display: grid;
      grid-template-columns: 1.2fr .8fr;
      gap: 24px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 22px;
      margin-bottom: 22px;
    }}
    .intro p {{ margin: 0; font-size: 1.03rem; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }}
    .stat {{
      background: var(--blue);
      border: 1px solid #c9d4e2;
      padding: 12px;
    }}
    .stat b {{ display: block; color: var(--ink); font-size: 1.3rem; }}
    .stat span {{ color: var(--muted); font-size: .84rem; }}
    .story {{
      padding: 22px 0;
      border-bottom: 1px solid var(--line);
    }}
    .story-meta {{
      display: flex;
      gap: 10px;
      align-items: center;
      color: var(--gold);
      font-weight: 700;
      font-size: .78rem;
      text-transform: uppercase;
    }}
    .story h2 {{
      margin: 8px 0 8px;
      color: var(--ink);
      font-size: clamp(1.45rem, 3vw, 2.2rem);
      line-height: 1.08;
      letter-spacing: 0;
    }}
    .story p {{ max-width: 760px; margin: 0 0 12px; }}
    .why {{
      max-width: 760px;
      margin: 12px 0;
      padding: 12px 14px;
      background: var(--green);
      border: 1px solid #c6d8cb;
      color: #1f3a5f;
      font-size: .95rem;
    }}
    .story a {{
      color: #1f4d78;
      font-weight: 700;
      text-decoration: none;
    }}
    .source-health {{
      margin-top: 24px;
      padding: 14px;
      background: rgba(255,255,255,.35);
      border: 1px solid var(--line);
      color: var(--muted);
    }}
    footer {{
      width: min(980px, calc(100% - 32px));
      margin: 0 auto;
      padding: 0 0 34px;
      color: var(--muted);
      font-size: .9rem;
    }}
    @media (max-width: 760px) {{
      .hero {{ min-height: 58vh; }}
      .intro {{ grid-template-columns: 1fr; }}
      .stats {{ grid-template-columns: 1fr; }}
      .hero-inner {{ padding: 42px 0 34px; }}
    }}
  </style>
</head>
<body>
  <section class="hero">
    <div class="hero-inner">
      <p class="kicker">Automatinis rytinis numeris</p>
      <h1>RYTO SIGNALAS</h1>
      <p class="deck">AI, smegenys ir longevity · {html_escape(format_date_lt(run_date))}</p>
      <a class="download" href="{html_escape(pdf_name)}">Atsisiųsti PDF</a>
    </div>
  </section>
  <main>
    <section class="intro">
      <p>Šis numeris automatiškai surinktas iš RSS šaltinių. Jis skirtas greitam rytiniam signalui: kas pajudėjo AI, smegenų mokslo ir healthspan temose, su nuorodomis į pirminius šaltinius.</p>
      <div class="stats">
        <div class="stat"><b>{len(articles)}</b><span>atrinktos istorijos</span></div>
        <div class="stat"><b>{len(TOPICS)}</b><span>temos</span></div>
        <div class="stat"><b>06:00</b><span>{html_escape(timezone_name)}</span></div>
      </div>
    </section>
    {''.join(cards)}
    {error_note}
  </main>
  <footer>
    Redaktoriaus pastaba: automatinė versija remiasi šaltinių pateiktais pavadinimais ir santraukomis. Prieš svarbius sprendimus visada skaityk pilną šaltinį.
  </footer>
</body>
</html>
"""
    (output_dir / "index.html").write_text(html_doc, encoding="utf-8")


def register_fonts() -> tuple[str, str, str]:
    regular_candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    bold_candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]
    italic_candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf"),
        Path("C:/Windows/Fonts/ariali.ttf"),
    ]

    def first_existing(candidates: list[Path]) -> Path | None:
        return next((candidate for candidate in candidates if candidate.exists()), None)

    regular = first_existing(regular_candidates)
    bold = first_existing(bold_candidates)
    italic = first_existing(italic_candidates)
    if not regular or not bold or not italic:
        return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"

    pdfmetrics.registerFont(TTFont("RytoSans", regular))
    pdfmetrics.registerFont(TTFont("RytoSans-Bold", bold))
    pdfmetrics.registerFont(TTFont("RytoSans-Italic", italic))
    return "RytoSans", "RytoSans-Bold", "RytoSans-Italic"


def draw_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.7)
    canvas.line(MARGIN_X, PAGE_H - 10 * mm, PAGE_W - MARGIN_X, PAGE_H - 10 * mm)
    canvas.line(MARGIN_X, 10 * mm, PAGE_W - MARGIN_X, 10 * mm)
    canvas.setFont(getattr(doc, "body_font", "Helvetica"), 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN_X, 6.4 * mm, "Ryto signalas | AI, smegenys ir longevity")
    canvas.drawRightString(PAGE_W - MARGIN_X, 6.4 * mm, f"Puslapis {doc.page}")
    canvas.restoreState()


def make_styles(fonts: tuple[str, str, str]):
    regular, bold, italic = fonts
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "Masthead",
            parent=styles["Normal"],
            fontName=bold,
            fontSize=34,
            leading=36,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            "Kicker",
            parent=styles["Normal"],
            fontName=bold,
            fontSize=8.5,
            leading=10,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "Deck",
            parent=styles["Normal"],
            fontName=italic,
            fontSize=11.5,
            leading=15,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=11,
        )
    )
    styles.add(
        ParagraphStyle(
            "Lead",
            parent=styles["Normal"],
            fontName=regular,
            fontSize=11.2,
            leading=16,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionLabel",
            parent=styles["Normal"],
            fontName=bold,
            fontSize=8,
            leading=9.5,
            textColor=GOLD,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            "Headline",
            parent=styles["Normal"],
            fontName=bold,
            fontSize=16,
            leading=19,
            textColor=INK,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName=regular,
            fontSize=10.2,
            leading=14.4,
            textColor=colors.HexColor("#20242A"),
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            "Why",
            parent=styles["Normal"],
            fontName=regular,
            fontSize=9.6,
            leading=12.6,
            textColor=colors.HexColor("#1F3A5F"),
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "Source",
            parent=styles["Normal"],
            fontName=regular,
            fontSize=8.4,
            leading=11,
            textColor=MUTED,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            "Small",
            parent=styles["Normal"],
            fontName=regular,
            fontSize=8.3,
            leading=10.5,
            textColor=MUTED,
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            "IndexItem",
            parent=styles["Normal"],
            fontName=regular,
            fontSize=9.4,
            leading=12.4,
            textColor=INK,
        )
    )
    return styles


def source_link(label: str, url: str) -> str:
    return f'<a href="{html_escape(url)}" color="#1F4D78">{html_escape(label)}</a>'


def article_block(article: Article, timezone_name: str, styles):
    source = source_link(f"{article.source}, {iso_to_local(article.published, timezone_name)}", article.url)
    why = next(topic["why"] for topic in TOPICS if topic["name"] == article.topic)
    why_table = Table(
        [[Paragraph(f"<b>Kodėl tai svarbu:</b> {html_escape(why.split(':', 1)[1].strip())}", styles["Why"])]],
        colWidths=[CONTENT_W],
    )
    why_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT_GREEN),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#C6D8CB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return KeepTogether(
        [
            Spacer(1, 8),
            Table(
                [[Paragraph(html_escape(article.tag).upper(), styles["SectionLabel"])]],
                colWidths=[CONTENT_W],
                style=[
                    ("LINEABOVE", (0, 0), (-1, 0), 0.8, RULE),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
                ],
            ),
            Paragraph(html_escape(article.title), styles["Headline"]),
            Paragraph(html_escape(article.summary), styles["Body"]),
            why_table,
            Spacer(1, 5),
            Paragraph(f"Šaltinis: {source}", styles["Source"]),
        ]
    )


def build_pdf(output_dir: Path, articles: list[Article], run_date: date, timezone_name: str, pdf_name: str) -> None:
    fonts = register_fonts()
    styles = make_styles(fonts)

    pdf_path = output_dir / pdf_name
    doc = BaseDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=f"Ryto signalas - {run_date.isoformat()}",
        author="Ryto signalas",
    )
    doc.body_font = fonts[0]
    frame = Frame(
        MARGIN_X,
        MARGIN_BOTTOM + 3 * mm,
        CONTENT_W,
        PAGE_H - MARGIN_TOP - MARGIN_BOTTOM - 6 * mm,
        id="normal",
        showBoundary=0,
    )
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=draw_page)])

    story = []
    story.append(Paragraph("AUTOMATINIS NUMERIS", styles["Kicker"]))
    story.append(Paragraph("RYTO SIGNALAS", styles["Masthead"]))
    story.append(
        Paragraph(
            f"AI, smegenys ir longevity | {html_escape(format_date_lt(run_date))}",
            styles["Deck"],
        )
    )

    if COVER_IMAGE.exists():
        img = Image(str(COVER_IMAGE), width=CONTENT_W, height=CONTENT_W * 0.50)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 3))
        story.append(
            Paragraph(
                "Viršelio iliustracija temai: AI, smegenys ir sveiko gyvenimo trukmė.",
                styles["Small"],
            )
        )
        story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Šis rytinis numeris automatiškai surinktas iš RSS šaltinių. Jis skirtas greitam "
            "signalui: kas pajudėjo AI, smegenų mokslo ir healthspan temose, su nuorodomis į "
            "šaltinius platesniam skaitymui.",
            styles["Lead"],
        )
    )

    if articles:
        index_rows = []
        for idx, article in enumerate(articles, 1):
            index_rows.append(
                [
                    Paragraph(f"<b>{idx}</b>", styles["IndexItem"]),
                    Paragraph(html_escape(article.title), styles["IndexItem"]),
                ]
            )
        index = Table(index_rows, colWidths=[12 * mm, CONTENT_W - 12 * mm])
        index.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), SOFT_BLUE),
                    ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D4E2")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#DCE4EE")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(index)
        story.append(PageBreak())

        for article in articles:
            story.append(article_block(article, timezone_name, styles))
    else:
        story.append(
            Paragraph(
                "Šį rytą nepavyko surinkti RSS naujienų. Patikrink GitHub Actions žurnalą.",
                styles["Body"],
            )
        )

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>Redaktoriaus pastaba.</b> Automatinė versija remiasi šaltinių pateiktais "
            "pavadinimais ir santraukomis. Prieš svarbius sprendimus visada skaityk pilną šaltinį.",
            styles["Body"],
        )
    )

    doc.build(story)


def write_data(output_dir: Path, articles: list[Article], errors: list[str], run_date: date, timezone_name: str) -> None:
    payload = {
        "generated_for": run_date.isoformat(),
        "timezone": timezone_name,
        "articles": [asdict(article) for article in articles],
        "feed_errors": errors,
    }
    (output_dir / "ryto-signalas.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Ryto signalas morning newspaper.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for the generated website and PDF.")
    parser.add_argument("--timezone", default=os.getenv("NEWS_TIMEZONE", DEFAULT_TIMEZONE), help="IANA timezone for dates.")
    parser.add_argument("--date", help="Publication date in YYYY-MM-DD format. Defaults to today in the selected timezone.")
    parser.add_argument("--per-topic", type=int, default=2, help="Number of stories to select per topic.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    timezone_name = args.timezone
    tz = ZoneInfo(timezone_name)
    run_date = date.fromisoformat(args.date) if args.date else datetime.now(tz).date()
    output_dir = Path(args.output_dir).resolve()

    prepare_output_dir(output_dir)
    articles, errors = collect_articles(per_topic=max(1, args.per_topic))
    pdf_name = f"ryto-signalas-{run_date.isoformat()}.pdf"
    render_html(output_dir, articles, run_date, timezone_name, pdf_name, errors)
    build_pdf(output_dir, articles, run_date, timezone_name, pdf_name)
    shutil.copy2(output_dir / pdf_name, output_dir / "latest.pdf")
    write_data(output_dir, articles, errors, run_date, timezone_name)

    print(f"Generated {output_dir / 'index.html'}")
    print(f"Generated {output_dir / pdf_name}")


if __name__ == "__main__":
    main()
