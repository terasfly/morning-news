import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  Brain,
  CalendarDays,
  CalendarClock,
  Check,
  ChevronLeft,
  ChevronRight,
  Copy,
  Cpu,
  ExternalLink,
  FileText,
  Filter,
  Flame,
  HeartPulse,
  Newspaper,
  Radio,
  RefreshCw,
  Search,
  Sparkles,
  TimerReset,
  Watch,
  Zap
} from "lucide-react";
import coverImage from "../rytinis-virselis.png";

const FALLBACK_DIGEST = {
  title: "Morning Magazine",
  generated_for: new Date().toISOString().slice(0, 10),
  generated_at: new Date().toISOString(),
  timezone: "Europe/London",
  language: "en-lt",
  summary_engine: "demo",
  cover_theme: {
    topic: "Balanced edition",
    label: "Cover theme: AI, brain and healthspan",
    detail: "A compact morning scan across AI tools, brain health, longevity and wearable evidence."
  },
  articles: [
    {
      topic: "Brain Research",
      tag: "Brain research",
      title: "Brain health research is moving toward earlier, more practical signals",
      summary_en:
        "Researchers are increasingly combining imaging, biomarkers, sleep data and cognitive testing to detect changes earlier. The important shift is that brain health is being studied as a measurable system rather than a single late-stage diagnosis. This matters because earlier signals may eventually help people act before symptoms become severe.",
      summary_lt:
        "Mokslininkai vis dažniau jungia vaizdinimo tyrimus, biomarkerius, miego duomenis ir kognityvinius testus, kad pokyčius pastebėtų anksčiau. Svarbiausias pokytis yra tai, kad smegenų sveikata vis dažniau tiriama kaip matuojama sistema, o ne tik kaip vėlyva diagnozė. Tai svarbu, nes ankstesni signalai ateityje gali padėti žmonėms imtis veiksmų dar prieš simptomams tampant sunkiais.",
      summary:
        "Researchers are increasingly combining imaging, biomarkers, sleep data and cognitive testing to detect changes earlier. The important shift is that brain health is being studied as a measurable system rather than a single late-stage diagnosis. This matters because earlier signals may eventually help people act before symptoms become severe.",
      url: "https://news.google.com/search?q=brain%20research%20biomarker",
      source: "Demo source",
      published: new Date().toISOString(),
      score: 84,
      read_status: "demo",
      word_count: 120
    },
    {
      topic: "Longevity",
      tag: "Longevity",
      title: "Longevity coverage is becoming more focused on healthspan than hype",
      summary_en:
        "The strongest longevity updates now tend to focus on muscle, sleep, metabolism, inflammation and prevention rather than miracle claims. That makes the field more useful for everyday decisions because the best signals are measurable and repeatable. The key is to separate real human evidence from marketing.",
      summary_lt:
        "Stipriausios ilgaamžiškumo naujienos dabar dažniau kalba apie raumenis, miegą, metabolizmą, uždegimą ir prevenciją, o ne apie stebuklingus pažadus. Dėl to ši sritis tampa naudingesnė kasdieniams sprendimams, nes geriausi signalai yra matuojami ir pakartojami. Svarbiausia atskirti tikrus žmonių duomenis nuo marketingo.",
      summary:
        "The strongest longevity updates now tend to focus on muscle, sleep, metabolism, inflammation and prevention rather than miracle claims. That makes the field more useful for everyday decisions because the best signals are measurable and repeatable. The key is to separate real human evidence from marketing.",
      url: "https://news.google.com/search?q=longevity%20healthspan%20research",
      source: "Demo source",
      published: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      score: 78,
      read_status: "demo",
      word_count: 115
    },
    {
      topic: "WHOOP & Wearables",
      tag: "WHOOP and wearables",
      title: "Wearables are moving closer to medical interpretation",
      summary_en:
        "WHOOP and other wearables are increasingly discussed alongside sleep, HRV, recovery, remote monitoring and clinical data. The useful updates are not just product features, but whether the measurements are reliable enough to support better decisions. This matters because consumer health devices are slowly moving toward the edge of medicine.",
      summary_lt:
        "WHOOP ir kiti dėvimi įrenginiai vis dažniau aptariami kartu su miegu, HRV, atsistatymu, nuotoliniu stebėjimu ir klinikiniais duomenimis. Vertingi atnaujinimai yra ne tik produkto funkcijos, bet ir klausimas, ar matavimai pakankamai patikimi geresniems sprendimams. Tai svarbu, nes vartotojų sveikatos įrenginiai pamažu artėja prie medicinos ribos.",
      summary:
        "WHOOP and other wearables are increasingly discussed alongside sleep, HRV, recovery, remote monitoring and clinical data. The useful updates are not just product features, but whether the measurements are reliable enough to support better decisions. This matters because consumer health devices are slowly moving toward the edge of medicine.",
      url: "https://news.google.com/search?q=WHOOP%20wearable%20medical%20study",
      source: "Demo source",
      published: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      score: 72,
      read_status: "demo",
      word_count: 110
    },
    {
      topic: "AI & ChatGPT",
      tag: "AI and ChatGPT",
      title: "AI and ChatGPT updates are becoming workflow updates",
      summary_en:
        "The most important AI news is shifting from model announcements alone to how tools change everyday work. ChatGPT, agents and automation matter when they help people research, write, code, plan or operate faster. The useful signal is whether a release changes a real workflow, not whether it creates a loud headline.",
      summary_lt:
        "Svarbiausios AI naujienos vis labiau juda nuo vien modelių pristatymų prie to, kaip įrankiai keičia kasdienį darbą. ChatGPT, agentai ir automatizacija svarbūs tada, kai padeda žmonėms greičiau tirti, rašyti, programuoti, planuoti ar veikti. Vertingas signalas yra tai, ar atnaujinimas pakeičia tikrą darbo eigą, o ne tai, ar sukuria garsų pavadinimą.",
      summary:
        "The most important AI news is shifting from model announcements alone to how tools change everyday work. ChatGPT, agents and automation matter when they help people research, write, code, plan or operate faster. The useful signal is whether a release changes a real workflow, not whether it creates a loud headline.",
      url: "https://news.google.com/search?q=ChatGPT%20OpenAI%20updates",
      source: "Demo source",
      published: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      score: 70,
      read_status: "demo",
      word_count: 112
    }
  ],
  book_recommendations: [
    {
      title: "The Snow Child",
      author: "Eowyn Ivey",
      book_type: "Fiction inspired by folklore",
      description_en:
        "A childless couple tries to build a life in the Alaskan wilderness after years of grief. One winter night they make a girl out of snow, and soon a mysterious child begins appearing near their cabin. The novel stays quiet and atmospheric, blending frontier hardship, family longing, and a touch of wonder without giving easy answers.",
      why_it_may_appeal: "It has the wild Alaska mood of The Great Alone, but with more tenderness, loneliness, and myth.",
      length: "Approx. 10 hours audiobook / 400 pages",
      goodreads_rating: "Approx. 3.9/5",
      cover_url: "https://covers.openlibrary.org/b/isbn/9780316175678-L.jpg",
      summary_en:
        "This is an atmospheric Alaska novel about loneliness, wilderness, wonder, and the fragile bonds that keep people alive through hard winters. It matches your taste because the landscape feels like a character, and the emotional journey is quiet but powerful.",
      summary_lt:
        "Tai atmosferiškas romanas apie Aliaską, vienatvę, laukinę gamtą, stebuklo jausmą ir trapius ryšius, kurie padeda žmonėms išgyventi sunkias žiemas. Jis tinka tavo skoniui, nes gamta čia jaučiasi kaip atskiras veikėjas, o emocinė kelionė tyli, bet stipri.",
      search_url: "https://www.google.com/search?q=The+Snow+Child+Eowyn+Ivey+book"
    },
    {
      title: "Lonesome Dove",
      author: "Larry McMurtry",
      book_type: "Historical fiction",
      description_en:
        "Two aging former Texas Rangers drive cattle north across a dangerous and changing American frontier. The journey becomes a huge human canvas of friendship, violence, loyalty, regret, and endurance. It is long, funny, brutal, and deeply emotional without feeling sentimental.",
      why_it_may_appeal: "It offers the same big lived-in-world feeling that makes Shantaram so immersive.",
      length: "Approx. 36 hours audiobook / 850 pages",
      goodreads_rating: "Approx. 4.5/5",
      cover_url: "https://covers.openlibrary.org/b/isbn/9781439195260-L.jpg",
      summary_en:
        "A big, immersive journey across harsh country, built around friendship, endurance, loyalty, and loss. If you liked the vast human world of Shantaram, this gives a similar feeling of living inside a long road story with unforgettable characters.",
      summary_lt:
        "Tai plati, įtraukianti kelionė per atšiaurų kraštą, paremta draugyste, ištverme, lojalumu ir netektimi. Jei tau patiko didelis žmogiškas Shantaram pasaulis, ši knyga duoda panašų jausmą, lyg gyventum ilgoje kelionės istorijoje su nepamirštamais veikėjais.",
      search_url: "https://www.google.com/search?q=Lonesome+Dove+Larry+McMurtry+book"
    },
    {
      title: "Wild",
      author: "Cheryl Strayed",
      book_type: "Memoir",
      description_en:
        "Cheryl Strayed hikes the Pacific Crest Trail after grief, addiction, and family rupture have upended her life. The trail is physically punishing, but the real movement is emotional and inward. It is a direct, vulnerable story of survival, reckoning, and rebuilding the self.",
      why_it_may_appeal: "It is exactly in the true-life transformation, nature, and survival lane you described.",
      length: "Approx. 13 hours audiobook / 336 pages",
      goodreads_rating: "Approx. 4.0/5",
      cover_url: "https://covers.openlibrary.org/b/isbn/9780307476074-L.jpg",
      summary_en:
        "A grief-struck woman walks the Pacific Crest Trail and turns physical hardship into a reckoning with her life. It fits your interest in emotional journeys, nature, survival, and rebuilding the self.",
      summary_lt:
        "Gedinti moteris eina Pacific Crest Trail keliu ir fizinį sunkumą paverčia akistata su savo gyvenimu. Ji tinka tavo pomėgiui emocinėms kelionėms, gamtai, išgyvenimui ir savęs atkūrimui.",
      search_url: "https://www.google.com/search?q=Wild+Cheryl+Strayed+book"
    }
  ],
  daily_highlights: [
    {
      title: "Brain health signals are becoming more measurable",
      detail: "Brain Research: useful as an early signal, not as immediate medical advice.",
      topic: "Brain Research",
      url: "https://news.google.com/search?q=brain%20research%20biomarker"
    },
    {
      title: "Longevity coverage is shifting toward healthspan evidence",
      detail: "Longevity: stronger items focus on sleep, muscle, metabolism and prevention.",
      topic: "Longevity",
      url: "https://news.google.com/search?q=longevity%20healthspan%20research"
    },
    {
      title: "WHOOP-style metrics need validation, not just feature announcements",
      detail: "WHOOP & Wearables: useful when sleep, HRV and recovery metrics are interpreted carefully.",
      topic: "WHOOP & Wearables",
      url: "https://news.google.com/search?q=WHOOP%20wearable%20medical%20study"
    }
  ],
  save_for_later: [
    {
      title: "Wearables are moving closer to medical interpretation",
      detail: "Longer read: useful if you want to inspect what consumer physiology metrics can prove.",
      topic: "WHOOP & Wearables",
      url: "https://news.google.com/search?q=WHOOP%20wearable%20medical%20study"
    }
  ],
  weekly_summary: [],
  whoop_evidence: {
    title: "Wearables are moving closer to medical interpretation",
    detail: "Older scientific evidence. Use this as a calibration point for what WHOOP-style metrics can and cannot prove.",
    topic: "WHOOP & Wearables",
    url: "https://news.google.com/search?q=WHOOP%20wearable%20medical%20study"
  },
  feed_errors: []
};

const TOPICS = [
  { id: "all", label: "All", Icon: Sparkles },
  { id: "Brain Research", label: "Brain", Icon: Brain },
  { id: "Longevity", label: "Longevity", Icon: HeartPulse },
  { id: "WHOOP & Wearables", label: "WHOOP", Icon: Watch },
  { id: "AI & ChatGPT", label: "AI", Icon: Cpu }
];

const WINDOWS = [
  { id: "all", label: "All" },
  { id: "hot", label: "Strong" },
  { id: "fresh", label: "Fresh" }
];

const topicMeta = {
  "Brain Research": {
    Icon: Brain,
    color: "violet"
  },
  Longevity: {
    Icon: HeartPulse,
    color: "green"
  },
  "WHOOP & Wearables": {
    Icon: Watch,
    color: "coral"
  },
  "AI & ChatGPT": {
    Icon: Cpu,
    color: "cyan"
  }
};

const TOPIC_ORDER = TOPICS.filter((topic) => topic.id !== "all").map((topic) => topic.id);
const BASE_URL = import.meta.env.BASE_URL;

function topicRank(topic) {
  const index = TOPIC_ORDER.indexOf(topic);
  return index === -1 ? TOPIC_ORDER.length : index;
}

function repairText(value) {
  if (typeof value !== "string") return value;

  const replacements = [
    ["Ã¢â‚¬â„¢", "'"],
    ["Ã¢â‚¬Ëœ", "'"],
    ["Ã¢â‚¬Å“", '"'],
    ["Ã¢â‚¬Â", '"'],
    ["Ã¢â‚¬â€œ", "-"],
    ["Ã¢â‚¬â€", "-"],
    ["Ã¢â‚¬Â¦", "..."],
    ["Ã…Â¡", "š"],
    ["Ã…Â ", "Š"],
    ["Ã…Â³", "ų"],
    ["Ã…Â«", "ū"],
    ["Ã…Â¾", "ž"],
    ["Ã…Â½", "Ž"],
    ["Ã„â€¦", "ą"],
    ["Ã„Â", "č"],
    ["Ã„â€”", "ė"],
    ["Ã„â„¢", "ę"],
    ["Ã„Â¯", "į"],
    ["Ã„Â®", "Į"]
  ];

  return replacements.reduce((text, [bad, good]) => text.replaceAll(bad, good), value);
}

function cleanObject(value) {
  if (Array.isArray(value)) return value.map(cleanObject);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, cleanObject(item)]));
  }
  return repairText(value);
}

function formatDate(value, timezone = "Europe/London") {
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: timezone
  }).format(new Date(value));
}

function formatTime(value, timezone = "Europe/London") {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: timezone
  }).format(new Date(value));
}

function formatPublished(value, timezone = "Europe/London") {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "date unavailable";
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: timezone
  }).format(date);
}

function dateParamFromLocation() {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("date");
}

function shiftIsoDate(value, days) {
  const date = new Date(`${value}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function monthKey(value) {
  return value?.slice(0, 7) || new Date().toISOString().slice(0, 7);
}

function getArticleAge(article) {
  const published = new Date(article.published).getTime();
  if (!Number.isFinite(published)) return Infinity;
  return Date.now() - published;
}

function isFresh(article) {
  return getArticleAge(article) <= 18 * 60 * 60 * 1000;
}

function getTopicCount(articles, topic) {
  if (topic === "all") return articles.length;
  return articles.filter((article) => article.topic === topic).length;
}

function buildBrief(articles, books, digest) {
  const date = formatDate(digest.generated_for, digest.timezone);
  const lines = [
    `Morning Magazine - ${date}`,
    "",
    ...articles.slice(0, 5).map((article, index) => {
      return `${index + 1}. ${article.title}: ${article.summary_en || article.summary}`;
    }),
    "",
    "Books Section:",
    ...books.slice(0, 3).map((book) => `${book.title} - ${book.author}`)
  ];

  return lines.join("\n");
}

function App() {
  const [digest, setDigest] = useState(FALLBACK_DIGEST);
  const [loading, setLoading] = useState(true);
  const [sourceState, setSourceState] = useState("Connecting");
  const [selectedTopic, setSelectedTopic] = useState("all");
  const [windowFilter, setWindowFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [copied, setCopied] = useState(false);
  const [selectedDate, setSelectedDate] = useState(dateParamFromLocation);
  const [archiveIndex, setArchiveIndex] = useState({ editions: [] });
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [navNotice, setNavNotice] = useState("");

  useEffect(() => {
    let active = true;

    async function loadArchive() {
      try {
        const response = await fetch(`${BASE_URL}archive/index.json?t=${Date.now()}`);
        if (!response.ok) throw new Error("Archive not found");
        const data = cleanObject(await response.json());
        if (active) setArchiveIndex({ ...data, editions: data.editions ?? [] });
      } catch {
        if (active) setArchiveIndex({ editions: [] });
      }
    }

    loadArchive();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    function handlePopState() {
      setSelectedDate(dateParamFromLocation());
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDigest() {
      setLoading(true);
      setNavNotice("");
      try {
        const digestPath = selectedDate
          ? `${BASE_URL}archive/${selectedDate}/ryto-signalas.json?t=${Date.now()}`
          : `${BASE_URL}ryto-signalas.json?t=${Date.now()}`;
        const response = await fetch(digestPath);
        if (!response.ok) throw new Error("Digest not found");
        const data = cleanObject(await response.json());
        if (!active) return;

        setDigest({
          ...data,
          articles: data.articles ?? [],
          book_recommendations: data.book_recommendations ?? [],
          daily_highlights: data.daily_highlights ?? [],
          save_for_later: data.save_for_later ?? [],
          weekly_summary: data.weekly_summary ?? [],
          whoop_evidence: data.whoop_evidence ?? null,
          cover_theme: data.cover_theme ?? FALLBACK_DIGEST.cover_theme
        });
        setSourceState(data.summary_engine === "openai" ? "Live magazine + AI summaries" : "Live magazine");
      } catch {
        if (!active) return;
        setDigest(cleanObject(FALLBACK_DIGEST));
        setSourceState(selectedDate ? "Archive unavailable" : "Demo mode");
        if (selectedDate) setNavNotice("This saved edition is not available yet.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadDigest();
    return () => {
      active = false;
    };
  }, [selectedDate]);

  const articles = useMemo(() => {
    const search = query.trim().toLowerCase();

    return [...(digest.articles ?? [])]
      .sort((a, b) => {
        if (selectedTopic === "all") {
          const topicDelta = topicRank(a.topic) - topicRank(b.topic);
          if (topicDelta !== 0) return topicDelta;
        }
        const scoreDelta = (b.score ?? 0) - (a.score ?? 0);
        if (scoreDelta !== 0) return scoreDelta;
        return new Date(b.published).getTime() - new Date(a.published).getTime();
      })
      .filter((article) => selectedTopic === "all" || article.topic === selectedTopic)
      .filter((article) => {
        if (windowFilter === "hot") return (article.score ?? 0) >= 70;
        if (windowFilter === "fresh") return isFresh(article);
        return true;
      })
      .filter((article) => {
        if (!search) return true;
        return [
          article.title,
          article.summary_en,
          article.summary_lt,
          article.summary,
          article.source,
          article.source_type,
          article.hype_filter,
          article.practical_takeaway,
          article.tag,
          article.topic
        ]
          .join(" ")
          .toLowerCase()
          .includes(search);
      });
  }, [digest.articles, query, selectedTopic, windowFilter]);

  const books = digest.book_recommendations ?? [];
  const saveForLater = digest.save_for_later ?? [];
  const weeklySummary = digest.weekly_summary ?? [];
  const whoopEvidence = digest.whoop_evidence ?? null;
  const coverTheme = digest.cover_theme ?? FALLBACK_DIGEST.cover_theme;
  const topSignals = [...(digest.articles ?? [])]
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    .slice(0, 3);
  const lead = articles[0] ?? digest.articles?.[0];
  const sourceHealth = digest.feed_errors?.length ? "Some source issues" : "Sources OK";
  const generatedLabel = formatDate(digest.generated_for, digest.timezone);
  const updatedTime = digest.generated_at ? formatTime(digest.generated_at, digest.timezone) : "--:--";
  const updatedDate = digest.generated_at ? formatDate(digest.generated_at, digest.timezone) : "update time unavailable";
  const copiedLabel = copied ? "Copied" : "Copy";
  const archiveEditions = archiveIndex.editions ?? [];
  const archiveDates = new Set(archiveEditions.map((edition) => edition.date));
  const latestArchiveDate = archiveEditions[0]?.date ?? digest.generated_for;
  const activeDate = digest.generated_for;
  const previousDate = activeDate ? shiftIsoDate(activeDate, -1) : null;
  const nextDate = activeDate ? shiftIsoDate(activeDate, 1) : null;
  const previousAvailable = previousDate && archiveDates.has(previousDate);
  const nextAvailable = nextDate && archiveDates.has(nextDate);
  const fileVersion = encodeURIComponent(digest.generated_at || activeDate || Date.now());
  const pdfHref = selectedDate && digest.archive?.pdf
    ? `${BASE_URL}${digest.archive.pdf}?v=${fileVersion}`
    : `${BASE_URL}latest.pdf?v=${fileVersion}`;

  function openEdition(date) {
    if (!date || !archiveDates.has(date)) {
      setNavNotice(date && date > activeDate ? "The next edition has not been published yet." : "This edition is not available in the archive.");
      return;
    }
    const url = new URL(window.location.href);
    if (date === latestArchiveDate) {
      url.searchParams.delete("date");
      setSelectedDate(null);
    } else {
      url.searchParams.set("date", date);
      setSelectedDate(date);
    }
    window.history.pushState({}, "", url);
    setArchiveOpen(false);
    setNavNotice("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleCopy() {
    const brief = buildBrief(articles, books, digest);
    try {
      await navigator.clipboard.writeText(brief);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  function resetFilters() {
    setSelectedTopic("all");
    setWindowFilter("all");
    setQuery("");
  }

  return (
    <main className="news-app">
      <section className="dashboard-shell" aria-label="Morning Magazine">
        <header className="topbar">
          <a className="brand" href={BASE_URL} aria-label="Morning Magazine">
            <span className="brand-icon">
              <Newspaper size={22} />
            </span>
            <span>
              <strong>Morning Magazine</strong>
              <small>English + Lietuviškai</small>
            </span>
          </a>

          <div className="topbar-actions">
            <a className="ghost-button" href={pdfHref} target="_blank" rel="noreferrer">
              <FileText size={17} />
              PDF
            </a>
            <button className="primary-button" type="button" onClick={handleCopy}>
              {copied ? <Check size={17} /> : <Copy size={17} />}
              {copiedLabel}
            </button>
          </div>
        </header>

        <section className="date-navigator" aria-label="Edition navigation">
          <button
            className="date-arrow"
            type="button"
            onClick={() => openEdition(previousDate)}
            disabled={!previousAvailable}
            title={previousAvailable ? "Previous Day" : "Previous edition unavailable"}
          >
            <ChevronLeft size={18} />
            Previous Day
          </button>

          <div className="date-display">
            <button
              className="calendar-button"
              type="button"
              onClick={() => setArchiveOpen((open) => !open)}
              aria-expanded={archiveOpen}
              title="Open archive calendar"
            >
              <CalendarDays size={18} />
            </button>
            <strong>{generatedLabel}</strong>
          </div>

          <button
            className="date-arrow"
            type="button"
            onClick={() => openEdition(nextDate)}
            disabled={!nextAvailable}
            title={nextAvailable ? "Next Day" : "The next edition has not been published yet."}
          >
            Next Day
            <ChevronRight size={18} />
          </button>
        </section>

        {(navNotice || !nextAvailable) && (
          <div className="archive-notice">
            {navNotice || "The next edition has not been published yet."}
          </div>
        )}

        {archiveOpen && (
          <ArchiveCalendar
            activeDate={activeDate}
            editions={archiveEditions}
            onSelect={openEdition}
          />
        )}

        <section className="summary-band">
          <div className="morning-visual" aria-hidden="true">
            <img src={coverImage} alt="" />
          </div>

          <div className="morning-copy">
            <div className="status-row">
              <span className={`status-pill ${loading ? "loading" : "live"}`}>
                <Radio size={14} />
                {sourceState}
              </span>
              <span>
                <CalendarClock size={14} />
                {generatedLabel}
              </span>
              <span className="updated-pill">
                <RefreshCw size={14} />
                Updated {updatedTime}
              </span>
            </div>

            <h1>{lead?.title ?? "Your personal Morning Magazine"}</h1>
            <p>
              {lead?.summary_en ??
                "Important news only, summarized in English with a complete Lithuanian translation under each item."}
            </p>

            <div className="context-strip">
              <span>
                <Sparkles size={15} />
                {coverTheme.label}
              </span>
              <p>{coverTheme.detail}</p>
            </div>

            {topSignals.length > 0 && (
              <div className="quick-read" aria-label="Quick morning signals">
                <strong>Greitas rytinis vaizdas</strong>
                <ol>
                  {topSignals.map((article) => (
                    <li key={`quick-${article.url}`}>
                      <a href={article.url} target="_blank" rel="noreferrer">
                        {article.title}
                      </a>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            <div className="signal-stats" aria-label="Magazine metrics">
              <Metric value={digest.articles?.length ?? 0} label="articles" Icon={Newspaper} />
              <Metric value={books.length} label="book picks" Icon={BookOpen} />
              <Metric value="06:00" label={`scheduled ${digest.timezone}`} Icon={TimerReset} />
              <Metric value={updatedTime} label={`updated ${updatedDate}`} Icon={RefreshCw} />
            </div>
          </div>

          <aside className="brief-panel">
            <div className="brief-title">
              <span>Editor</span>
              <Activity size={18} />
            </div>
            <div className="agent-steps">
              <Step done label="Reads sources" detail={sourceHealth} />
              <Step done label="Summarizes" detail={digest.summary_engine ?? "automatic"} />
              <Step done={!loading} label="Publishes" detail="HTML, JSON, PDF" />
            </div>
          </aside>
        </section>

        <section className="controls-row" aria-label="Filters">
          <div className="topic-tabs">
            {TOPICS.map(({ id, label, Icon }) => (
              <button
                className={selectedTopic === id ? "topic-tab active" : "topic-tab"}
                type="button"
                key={id}
                onClick={() => setSelectedTopic(id)}
              >
                <Icon size={16} />
                <span>{label}</span>
                <strong>{getTopicCount(digest.articles ?? [], id)}</strong>
              </button>
            ))}
          </div>

          <div className="toolstrip">
            <div className="search-box">
              <Search size={17} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search"
                aria-label="Search"
              />
            </div>

            <div className="segmented" aria-label="Time window">
              {WINDOWS.map((item) => (
                <button
                  className={windowFilter === item.id ? "active" : ""}
                  key={item.id}
                  type="button"
                  onClick={() => setWindowFilter(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <button className="icon-action" type="button" onClick={resetFilters} aria-label="Clear filters" title="Clear">
              <Filter size={18} />
            </button>
          </div>
        </section>

        <section className="content-grid">
          <div className="article-list" aria-label="Magazine articles">
            {articles.map((article, index) => (
              <ArticleCard article={article} index={index} timezone={digest.timezone} key={`${article.url}-${index}`} />
            ))}

            {articles.length === 0 && (
              <div className="empty-state">
                <Search size={28} />
                <strong>No meaningful updates</strong>
                <span>This section was skipped instead of filling space with weak news.</span>
              </div>
            )}

            <BookRecommendations books={books} />
          </div>

          <aside className="right-rail">
            {whoopEvidence && <WhoopEvidence note={whoopEvidence} />}

            <NoteSection title="Save for later" notes={saveForLater} Icon={FileText} compact />

            {weeklySummary.length > 0 && (
              <NoteSection title="Savaitinis signalas" notes={weeklySummary} Icon={Activity} compact />
            )}

            <section className="rail-section">
              <div className="section-head">
                <span>Section pulse</span>
                <Flame size={17} />
              </div>
              <TopicPulse articles={digest.articles ?? []} />
            </section>

            <section className="rail-section">
              <div className="section-head">
                <span>Sources</span>
                <RefreshCw size={17} className={loading ? "spin" : ""} />
              </div>
              <SourceList articles={digest.articles ?? []} errors={digest.feed_errors ?? []} />
            </section>
          </aside>
        </section>
      </section>
    </main>
  );
}

function ArchiveCalendar({ activeDate, editions, onSelect }) {
  const savedDates = new Set(editions.map((edition) => edition.date));
  const [visibleMonth, setVisibleMonth] = useState(monthKey(activeDate));

  useEffect(() => {
    setVisibleMonth(monthKey(activeDate));
  }, [activeDate]);

  const firstDay = new Date(`${visibleMonth}-01T12:00:00Z`);
  const daysInMonth = new Date(Date.UTC(firstDay.getUTCFullYear(), firstDay.getUTCMonth() + 1, 0)).getUTCDate();
  const leadingBlanks = (firstDay.getUTCDay() + 6) % 7;
  const cells = [
    ...Array.from({ length: leadingBlanks }, (_, index) => ({ key: `blank-${index}` })),
    ...Array.from({ length: daysInMonth }, (_, index) => {
      const day = String(index + 1).padStart(2, "0");
      const date = `${visibleMonth}-${day}`;
      return { key: date, date, day: index + 1, saved: savedDates.has(date), active: date === activeDate };
    })
  ];
  const monthLabel = new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric", timeZone: "UTC" }).format(firstDay);

  function moveMonth(delta) {
    const next = new Date(`${visibleMonth}-01T12:00:00Z`);
    next.setUTCMonth(next.getUTCMonth() + delta);
    setVisibleMonth(next.toISOString().slice(0, 7));
  }

  return (
    <section className="archive-calendar" aria-label="Archive calendar">
      <div className="archive-calendar-head">
        <button type="button" onClick={() => moveMonth(-1)} aria-label="Previous month">
          <ChevronLeft size={17} />
        </button>
        <strong>{monthLabel}</strong>
        <button type="button" onClick={() => moveMonth(1)} aria-label="Next month">
          <ChevronRight size={17} />
        </button>
      </div>

      <div className="calendar-weekdays" aria-hidden="true">
        {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => (
          <span key={day}>{day}</span>
        ))}
      </div>

      <div className="calendar-grid">
        {cells.map((cell) =>
          cell.date ? (
            <button
              type="button"
              key={cell.key}
              className={cell.active ? "calendar-day active" : cell.saved ? "calendar-day saved" : "calendar-day"}
              onClick={() => onSelect(cell.date)}
              disabled={!cell.saved}
              title={cell.saved ? `Open ${cell.date}` : "No edition saved"}
            >
              {cell.day}
            </button>
          ) : (
            <span className="calendar-blank" key={cell.key} />
          )
        )}
      </div>
    </section>
  );
}

function NoteSection({ title, notes, Icon, compact = false }) {
  if (!notes?.length) return null;

  return (
    <section className={compact ? "note-section compact" : "note-section"} aria-label={title}>
      <div className="section-head">
        <span>{title}</span>
        <Icon size={17} />
      </div>
      <div className="note-list">
        {notes.map((note) => (
          <article className="note-card" key={`${title}-${note.url}-${note.title}`}>
            <small>{note.topic || "Signal"}</small>
            <h3>{note.title}</h3>
            <p>{note.detail}</p>
            {note.url && (
              <a href={note.url} target="_blank" rel="noreferrer">
                <ExternalLink size={14} />
                Source
              </a>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function WhoopEvidence({ note }) {
  return (
    <section className="note-section whoop-evidence" aria-label="WHOOP evidence corner">
      <div className="section-head">
        <span>WHOOP evidence corner</span>
        <Watch size={17} />
      </div>
      <article className="note-card">
        <small>{note.topic}</small>
        <h3>{note.title}</h3>
        <p>{note.detail}</p>
        <a href={note.url} target="_blank" rel="noreferrer">
          <ExternalLink size={14} />
          Read evidence
        </a>
      </article>
    </section>
  );
}

function Metric({ value, label, Icon }) {
  return (
    <article className="metric">
      <Icon size={18} />
      <strong>{value}</strong>
      <span>{label}</span>
    </article>
  );
}

function Step({ done, label, detail }) {
  return (
    <article className={done ? "step done" : "step"}>
      <span>{done ? <Check size={14} /> : <RefreshCw size={14} />}</span>
      <div>
        <strong>{label}</strong>
        <small>{detail}</small>
      </div>
    </article>
  );
}

function ArticleCard({ article, index, timezone }) {
  const meta = topicMeta[article.topic] ?? topicMeta["AI & ChatGPT"];
  const Icon = meta.Icon;
  const summaryEn = article.summary_en || article.summary;
  const sourceType = article.source_type || "Source checked";
  const hypeLevel = article.hype_level || "Low";
  const practicalTakeaway = article.practical_takeaway || "Read the original source before treating this as a decision signal.";
  const hypeFilter = article.hype_filter || "Useful signal, but the practical impact is not settled yet.";
  const publisher = article.source || "Source unavailable";
  const publishedLabel = formatPublished(article.published, timezone);

  return (
    <article className={`article-card magazine-card tone-${meta.color}`}>
      <div className="article-rank">{String(index + 1).padStart(2, "0")}</div>
      <div className="article-main">
        <div className="article-meta">
          <span>
            <Icon size={15} />
            {article.tag || article.topic}
          </span>
          <span className="source-type-chip">{sourceType}</span>
          <span className={`hype-chip hype-${hypeLevel.toLowerCase()}`}>Hype {hypeLevel}</span>
        </div>

        <h2>{article.title}</h2>
        <div className="article-source-line" aria-label="Publication details">
          <span>
            Publikavo: <strong>{publisher}</strong>
          </span>
          <span>
            Publikuota: <time dateTime={article.published}>{publishedLabel}</time>
          </span>
        </div>
        <p>{summaryEn}</p>

        <section className="translation-block" aria-label="Lithuanian translation">
          <h3>Lietuviškai</h3>
          <p>{article.summary_lt || "Vertimas laikinai nepateiktas."}</p>
        </section>

        <section className="insight-block" aria-label="Practical reading notes">
          <p>
            <strong>Praktiškai:</strong> {practicalTakeaway}
          </p>
          <p>
            <strong>Hype filtras:</strong> {hypeFilter}
          </p>
        </section>

        <div className="article-footer">
          <a href={article.url} target="_blank" rel="noreferrer">
            <ExternalLink size={15} />
            {article.source}
          </a>
        </div>
      </div>
      <a className="open-link" href={article.url} target="_blank" rel="noreferrer" aria-label="Open source">
        <ArrowUpRight size={19} />
      </a>
    </article>
  );
}

function BookRecommendations({ books }) {
  return (
    <section className="book-recs" aria-label="Book Recommendations">
      <div className="book-recs-head">
        <div>
          <span>Books Section</span>
          <h2>Three books for the Shantaram / Great Alone mood</h2>
        </div>
        <BookOpen size={22} />
      </div>

      <div className="book-list">
        {books.slice(0, 3).map((book) => (
          <article className="book-card" key={`${book.title}-${book.author}`}>
            {book.cover_url && <img className="book-cover" src={book.cover_url} alt={`${book.title} cover`} loading="lazy" />}
            <div className="book-details">
            <div className="article-meta">
              <span>
                <BookOpen size={15} />
                {book.book_type || "Fiction"}
              </span>
              <span>{book.author}</span>
            </div>
            <h3>{book.title}</h3>
            <div className="book-facts">
              <span>{book.length || "Length varies by edition"}</span>
              <span>Goodreads: {book.goodreads_rating || "rating unavailable"}</span>
            </div>
            <p>{book.description_en || book.summary_en}</p>
            <section className="insight-block">
              <p>
                <strong>Why it may appeal:</strong>{" "}
                {book.why_it_may_appeal || "It matches your interest in immersive, emotional human stories."}
              </p>
            </section>
            <section className="translation-block">
              <h4>Lietuviškai</h4>
              <p>{book.summary_lt}</p>
            </section>
            <a href={book.search_url} target="_blank" rel="noreferrer">
              <ExternalLink size={15} />
              Search book
            </a>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function TopicPulse({ articles }) {
  return (
    <div className="pulse-list">
      {TOPICS.filter((topic) => topic.id !== "all").map(({ id, label, Icon }) => {
        const items = articles.filter((article) => article.topic === id);
        const max = Math.max(...items.map((article) => article.score ?? 0), 0);
        const width = Math.max(8, Math.min(100, max));

        return (
          <article className="pulse-row" key={id}>
            <span>
              <Icon size={16} />
              {label}
            </span>
            <div className="pulse-meter">
              <i style={{ width: `${width}%` }} />
            </div>
            <strong>{items.length}</strong>
          </article>
        );
      })}
    </div>
  );
}

function SourceList({ articles, errors }) {
  const sources = [...new Set(articles.map((article) => article.source).filter(Boolean))];

  return (
    <div className="source-list">
      {sources.slice(0, 8).map((source) => (
        <div className="source-row" key={source}>
          <span>{source}</span>
          <Check size={15} />
        </div>
      ))}

      {errors.map((error) => (
        <div className="source-row error" key={error}>
          <span>{repairText(error)}</span>
          <Zap size={15} />
        </div>
      ))}
    </div>
  );
}

export default App;
