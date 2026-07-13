const REPOSITORY = "terasfly/morning-news";
const WORKFLOW = "ryto-signalas.yml";
const EDITION_URL = "https://terasfly.github.io/morning-news/ryto-signalas.json";
const LONDON_SLOTS = new Set(["06:52", "07:02", "07:12", "07:22"]);

function londonNow(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/London",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23"
  }).formatToParts(date);
  const values = Object.fromEntries(parts.map(({ type, value }) => [type, value]));
  return {
    date: `${values.year}-${values.month}-${values.day}`,
    time: `${values.hour}:${values.minute}`
  };
}

async function publicEdition() {
  try {
    const response = await fetch(`${EDITION_URL}?t=${Date.now()}`, {
      headers: { "Cache-Control": "no-cache" }
    });
    if (!response.ok) return "";
    const edition = await response.json();
    return edition.generated_for || "";
  } catch {
    return "";
  }
}

async function dispatchWorkflow(env) {
  const response = await fetch(
    `https://api.github.com/repos/${REPOSITORY}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        "User-Agent": "morning-news-cloudflare-trigger",
        "X-GitHub-Api-Version": "2022-11-28"
      },
      body: JSON.stringify({ ref: "main" })
    }
  );

  if (response.status !== 204) {
    throw new Error(`GitHub dispatch failed with HTTP ${response.status}: ${await response.text()}`);
  }
}

async function runScheduledUpdate(env, scheduledTime) {
  const london = londonNow(new Date(scheduledTime));
  if (!LONDON_SLOTS.has(london.time)) {
    return { status: "skipped", reason: "outside London schedule", ...london };
  }

  const publishedFor = await publicEdition();
  if (publishedFor === london.date) {
    return { status: "skipped", reason: "edition already published", publishedFor, ...london };
  }

  await dispatchWorkflow(env);
  return { status: "dispatched", publishedFor, ...london };
}

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(
      runScheduledUpdate(env, controller.scheduledTime).then((result) => console.log(JSON.stringify(result)))
    );
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/trigger") {
      if (request.headers.get("Authorization") !== `Bearer ${env.TRIGGER_SECRET}`) {
        return Response.json({ error: "Unauthorized" }, { status: 401 });
      }
      await dispatchWorkflow(env);
      return Response.json({ status: "dispatched", at: new Date().toISOString() });
    }

    const london = londonNow();
    return Response.json({
      service: "Morning Magazine cloud trigger",
      status: "ready",
      london,
      schedule: [...LONDON_SLOTS]
    });
  }
};
