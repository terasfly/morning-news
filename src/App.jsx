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
  generated_for: new Date().toISOString().slice(0, 10),
  timezone: "Europe/London",
  articles: [
    {
      topic: "Smegenys",
      tag: "Smegenu tyrimai",
      title: "Smegenu sveikatos tyrimai vis dazniau jungia vaizdus, krauja ir elgsena",
      summary:
        "Tyrimu kryptis juda link pigesniu ankstyvo signalo metodu: biomarkeriai, skaitmeniniai testai ir ilgalaikiai gyvenimo budo duomenys vertinami kartu.",
      url: "https://news.google.com/search?q=brain%20science%20health",
      source: "Demo saltinis",
      published: new Date().toISOString(),
      score: 84
    },
    {
      topic: "Longevity",
      tag: "Longevity ir healthspan",
      title: "Healthspan tema tampa praktiskesne: miegas, raumenys, metabolizmas",
      summary:
        "Ilgaamziskumo diskusija vis maziau sukasi apie vien papildus ir vis daugiau apie ismatuojamus iprocius, rizikos veiksnius bei personalizuota prevencija.",
      url: "https://news.google.com/search?q=longevity%20healthspan",
      source: "Demo saltinis",
      published: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      score: 77
    },
    {
      topic: "WHOOP",
      tag: "WHOOP ir wearables medicina",
      title: "Wearables signalai vertinami kartu su miego, HRV ir medicininiais tyrimais",
      summary:
        "WHOOP ir kiti irenginiai vis dazniau aptariami ne kaip zingsniu skaitikliai, o kaip nuolatinio matavimo sluoksnis salia klinikiniu tyrimu ir sveikatos sprendimu.",
      url: "https://news.google.com/search?q=WHOOP%20wearable%20medical%20study",
      source: "Demo saltinis",
      published: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      score: 70
    },
    {
      topic: "AI",
      tag: "AI ir ChatGPT",
      title: "AI ir ChatGPT atnaujinimai keliasi i kasdienius darbo srautus",
      summary:
        "Nauji agentiniai irankiai jau ne tik atsako i klausimus, bet ir planuoja veiksmus, seka saltinius, rengia santraukas bei padeda mazoms komandoms automatizuoti pasikartojanti darba.",
      url: "https://news.google.com/search?q=ChatGPT%20OpenAI%20updates",
      source: "Demo saltinis",
      published: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      score: 68
    },
    {
      topic: "Knygos",
      tag: "Knygos pabaigai",
      title: "Populiari nauja knyga rytiniam skaitymo radarui",
      summary:
        "Rytinio leidimo pabaigoje visada paliekami bent du kulturos signalai: naujos, aptariamos arba bestselleriuose kylancios knygos.",
      url: "https://news.google.com/search?q=bestseller%20new%20book%20release",
      source: "Demo saltinis",
      published: new Date(Date.now() - 7 * 60 * 60 * 1000).toISOString(),
      score: 52
    },
    {
      topic: "Knygos",
      tag: "Knygos pabaigai",
      title: "Knyga pagal tavo skoni: kelione, laisve ir isgyvenimas",
      summary:
        "Papildomas knygu signalas labiau iesko Shantaram ir Aliaskos nuotaikos: epines keliones, stiprus charakteriai, wilderness, laisve ir nuotykis.",
      url: "https://news.google.com/search?q=adventure%20survival%20wilderness%20travel%20memoir%20book",
      source: "Demo saltinis",
      published: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
      score: 50
    }
  ],
  feed_errors: []
};

const TOPICS = [
  {
    id: "all",
    label: "Visos",
    Icon: Sparkles
  },
  {
    id: "Smegenys",
    label: "Smegenys",
    Icon: Brain
  },
  {
    id: "Longevity",
    label: "Longevity",
    Icon: HeartPulse
  },
  {
    id: "WHOOP",
    label: "WHOOP",
    Icon: Watch
  },
  {
    id: "AI",
    label: "AI",
    Icon: Cpu
  },
  {
    id: "Knygos",
    label: "Knygos",
    Icon: BookOpen
  }
];

const WINDOWS = [
  { id: "all", label: "Visas rytas" },
  { id: "hot", label: "Karsta" },
  { id: "fresh", label: "Nauja" }
];

const topicMeta = {
  Smegenys: {
    Icon: Brain,
    color: "violet"
  },
  Longevity: {
    Icon: HeartPulse,
    color: "green"
  },
  WHOOP: {
    Icon: Watch,
    color: "coral"
  },
  AI: {
    Icon: Cpu,
    color: "cyan"
  },
  Knygos: {
    Icon: BookOpen,
    color: "amber"
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
    ["â€™", "'"],
    ["â€˜", "'"],
    ["â€œ", '"'],
    ["â€", '"'],
    ["â€“", "-"],
    ["â€”", "-"],
    ["â€¦", "..."],
    ["Å¡", "š"],
    ["Å ", "Š"],
    ["Å³", "ų"],
    ["Å«", "ū"],
    ["Å¾", "ž"],
    ["Å½", "Ž"],
    ["Ä…", "ą"],
    ["Ä", "č"],
    ["Ä—", "ė"],
    ["Ä™", "ę"],
    ["Ä¯", "į"],
    ["Ä®", "Į"]
  ];

  return replacements.reduce((text, [bad, good]) => text.replaceAll(bad, good), value);
}

function cleanArticle(article) {
  return Object.fromEntries(
    Object.entries(article).map(([key, value]) => [key, repairText(value)])
  );
}

function formatDate(value, timezone = "Europe/London") {
  return new Intl.DateTimeFormat("lt-LT", {
    weekday: "long",
    month: "long",
    day: "numeric",
    timeZone: timezone
  }).format(new Date(value));
}

function formatTime(value, timezone = "Europe/London") {
  return new Intl.DateTimeFormat("lt-LT", {
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

function buildBrief(articles, digest) {
  const date = formatDate(digest.generated_for, digest.timezone);
  const lead = articles[0];
  const lines = [
    `Ryto signalas - ${date}`,
    lead ? `Svarbiausia: ${lead.title}` : "Svarbiausia: dar nera naujienu.",
    "",
    ...articles.slice(0, 5).map((article, index) => {
      return `${index + 1}. ${article.title} (${article.source})`;
    })
  ];

  return lines.join("\n");
}

function App() {
  const [digest, setDigest] = useState(FALLBACK_DIGEST);
  const [loading, setLoading] = useState(true);
  const [sourceState, setSourceState] = useState("Jungiama");
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
        const data = await response.json();
        if (!active) return;

        setDigest({
          ...data,
          articles: (data.articles ?? []).map(cleanArticle)
        });
        setSourceState("Gyvas RSS");
      } catch {
        if (!active) return;
        setDigest({
          ...FALLBACK_DIGEST,
          articles: FALLBACK_DIGEST.articles.map(cleanArticle)
        });
        setSourceState("Demo režimas");
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
        return [article.title, article.summary, article.source, article.tag]
          .join(" ")
          .toLowerCase()
          .includes(search);
      });
  }, [digest.articles, query, selectedTopic, windowFilter]);

  const lead = articles[0] ?? digest.articles?.[0];
  const topScore = Math.max(...(digest.articles ?? []).map((article) => article.score ?? 0), 0);
  const sourceHealth = digest.feed_errors?.length ? "Yra klaidų" : "Šaltiniai OK";
  const generatedLabel = formatDate(digest.generated_for, digest.timezone);
  const copiedLabel = copied ? "Nukopijuota" : "Kopijuoti";

  async function handleCopy() {
    const brief = buildBrief(articles, digest);
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
      <section className="dashboard-shell" aria-label="Ryto signalas">
        <header className="topbar">
          <a className="brand" href={BASE_URL} aria-label="Ryto signalas">
            <span className="brand-icon">
              <Newspaper size={22} />
            </span>
            <span>
              <strong>Ryto signalas</strong>
              <small>news every morning</small>
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
            </div>

            <h1>{lead?.title ?? "Rytinis naujienų signalas"}</h1>
            <p>{lead?.summary ?? "Agentas ruošia trumpą, prioritetizuotą naujienų digestą."}</p>

            <div className="signal-stats" aria-label="Digest metrics">
              <Metric value={digest.articles?.length ?? 0} label="naujienos" Icon={Newspaper} />
              <Metric value={topScore} label="signalas" Icon={Zap} />
              <Metric value="06:00" label={digest.timezone} Icon={TimerReset} />
            </div>
          </div>

          <aside className="brief-panel">
            <div className="brief-title">
              <span>Agentas</span>
              <Activity size={18} />
            </div>
            <div className="agent-steps">
              <Step done label="RSS surinkimas" detail={sourceHealth} />
              <Step done label="Prioritetas" detail="balas pagal naujumą ir temą" />
              <Step done={!loading} label="Rytinis leidimas" detail="HTML, JSON, PDF" />
            </div>
          </aside>
        </section>

        <section className="controls-row" aria-label="Filtrai">
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
                placeholder="Paieška"
                aria-label="Paieška"
              />
            </div>

            <div className="segmented" aria-label="Langas">
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

            <button className="icon-action" type="button" onClick={resetFilters} aria-label="Išvalyti filtrus" title="Išvalyti">
              <Filter size={18} />
            </button>
          </div>
        </section>

        <section className="content-grid">
          <div className="article-list" aria-label="Naujienos">
            {articles.map((article, index) => (
              <ArticleCard article={article} index={index} key={`${article.url}-${index}`} />
            ))}

            {articles.length === 0 && (
              <div className="empty-state">
                <Search size={28} />
                <strong>Neradau atitikmenų</strong>
                <span>Pabandyk kitą temą arba trumpesnę frazę.</span>
              </div>
            )}
          </div>

          <aside className="right-rail">
            <section className="rail-section">
              <div className="section-head">
                <span>Temų pulsas</span>
                <Flame size={17} />
              </div>
              <TopicPulse articles={digest.articles ?? []} />
            </section>

            <section className="rail-section">
              <div className="section-head">
                <span>Šaltiniai</span>
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
  const meta = topicMeta[article.topic] ?? topicMeta.AI;
  const Icon = meta.Icon;
  const score = article.score ?? 0;

  return (
    <article className={`article-card tone-${meta.color}`}>
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
        <p>{article.summary}</p>

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
      <a className="open-link" href={article.url} target="_blank" rel="noreferrer" aria-label="Atidaryti šaltinį">
        <ArrowUpRight size={19} />
      </a>
    </article>
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
