import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  Brain,
  CalendarClock,
  Check,
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
      summary_en:
        "This is an atmospheric Alaska novel about loneliness, wilderness, wonder, and the fragile bonds that keep people alive through hard winters. It matches your taste because the landscape feels like a character, and the emotional journey is quiet but powerful.",
      summary_lt:
        "Tai atmosferiškas romanas apie Aliaską, vienatvę, laukinę gamtą, stebuklo jausmą ir trapius ryšius, kurie padeda žmonėms išgyventi sunkias žiemas. Jis tinka tavo skoniui, nes gamta čia jaučiasi kaip atskiras veikėjas, o emocinė kelionė tyli, bet stipri.",
      search_url: "https://www.google.com/search?q=The+Snow+Child+Eowyn+Ivey+book"
    },
    {
      title: "Lonesome Dove",
      author: "Larry McMurtry",
      summary_en:
        "A big, immersive journey across harsh country, built around friendship, endurance, loyalty, and loss. If you liked the vast human world of Shantaram, this gives a similar feeling of living inside a long road story with unforgettable characters.",
      summary_lt:
        "Tai plati, įtraukianti kelionė per atšiaurų kraštą, paremta draugyste, ištverme, lojalumu ir netektimi. Jei tau patiko didelis žmogiškas Shantaram pasaulis, ši knyga duoda panašų jausmą, lyg gyventum ilgoje kelionės istorijoje su nepamirštamais veikėjais.",
      search_url: "https://www.google.com/search?q=Lonesome+Dove+Larry+McMurtry+book"
    }
  ],
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
    "Book Recommendation:",
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

  useEffect(() => {
    let active = true;

    async function loadDigest() {
      setLoading(true);

      try {
        const response = await fetch(`${BASE_URL}ryto-signalas.json?t=${Date.now()}`);
        if (!response.ok) throw new Error("Digest not found");
        const data = cleanObject(await response.json());
        if (!active) return;

        setDigest({
          ...data,
          articles: data.articles ?? [],
          book_recommendations: data.book_recommendations ?? []
        });
        setSourceState(data.summary_engine === "openai" ? "Live magazine + AI summaries" : "Live magazine");
      } catch {
        if (!active) return;
        setDigest(cleanObject(FALLBACK_DIGEST));
        setSourceState("Demo mode");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadDigest();
    return () => {
      active = false;
    };
  }, []);

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
          article.tag,
          article.topic
        ]
          .join(" ")
          .toLowerCase()
          .includes(search);
      });
  }, [digest.articles, query, selectedTopic, windowFilter]);

  const books = digest.book_recommendations ?? [];
  const lead = articles[0] ?? digest.articles?.[0];
  const topScore = Math.max(...(digest.articles ?? []).map((article) => article.score ?? 0), 0);
  const sourceHealth = digest.feed_errors?.length ? "Some source issues" : "Sources OK";
  const generatedLabel = formatDate(digest.generated_for, digest.timezone);
  const updatedTime = digest.generated_at ? formatTime(digest.generated_at, digest.timezone) : "--:--";
  const updatedDate = digest.generated_at ? formatDate(digest.generated_at, digest.timezone) : "update time unavailable";
  const copiedLabel = copied ? "Copied" : "Copy";

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
            <a className="ghost-button" href={`${BASE_URL}latest.pdf`} target="_blank" rel="noreferrer">
              <FileText size={17} />
              PDF
            </a>
            <button className="primary-button" type="button" onClick={handleCopy}>
              {copied ? <Check size={17} /> : <Copy size={17} />}
              {copiedLabel}
            </button>
          </div>
        </header>

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
              <ArticleCard article={article} index={index} key={`${article.url}-${index}`} />
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

function ArticleCard({ article, index }) {
  const meta = topicMeta[article.topic] ?? topicMeta["AI & ChatGPT"];
  const Icon = meta.Icon;
  const score = article.score ?? 0;
  const summaryEn = article.summary_en || article.summary;

  return (
    <article className={`article-card magazine-card tone-${meta.color}`}>
      <div className="article-rank">{String(index + 1).padStart(2, "0")}</div>
      <div className="article-main">
        <div className="article-meta">
          <span>
            <Icon size={15} />
            {article.tag || article.topic}
          </span>
          <time>{formatTime(article.published)}</time>
        </div>

        <h2>{article.title}</h2>
        <p>{summaryEn}</p>

        <section className="translation-block" aria-label="Lithuanian translation">
          <h3>Lietuviškai</h3>
          <p>{article.summary_lt || "Vertimas laikinai nepateiktas."}</p>
        </section>

        <div className="article-footer">
          <a href={article.url} target="_blank" rel="noreferrer">
            <ExternalLink size={15} />
            {article.source}
          </a>
          <span className="score-chip">
            <Zap size={14} />
            {score}
          </span>
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
    <section className="book-recs" aria-label="Book Recommendation">
      <div className="book-recs-head">
        <div>
          <span>Book Recommendation</span>
          <h2>For the Shantaram / Great Alone mood</h2>
        </div>
        <BookOpen size={22} />
      </div>

      <div className="book-list">
        {books.slice(0, 3).map((book) => (
          <article className="book-card" key={`${book.title}-${book.author}`}>
            <div className="article-meta">
              <span>
                <BookOpen size={15} />
                {book.author}
              </span>
            </div>
            <h3>{book.title}</h3>
            <p>{book.summary_en}</p>
            <section className="translation-block">
              <h4>Lietuviškai</h4>
              <p>{book.summary_lt}</p>
            </section>
            <a href={book.search_url} target="_blank" rel="noreferrer">
              <ExternalLink size={15} />
              Search book
            </a>
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
