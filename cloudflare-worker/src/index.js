const REPOSITORY = "terasfly/morning-news";
const WORKFLOW = "ryto-signalas.yml";
const EDITION_URL = "https://terasfly.github.io/morning-news/ryto-signalas.json";
const SITE_ORIGINS = new Set([
  "https://terasfly.github.io",
  "http://127.0.0.1:4173",
  "http://127.0.0.1:5173",
  "http://localhost:4173",
  "http://localhost:5173"
]);
const MANUAL_COOLDOWN_SECONDS = 5 * 60;
const LONDON_SLOTS = new Set([
  "06:00",
  "06:03",
  "06:06",
  "06:09",
  "06:12",
  "06:15",
  "06:18",
  "06:21",
  "06:24",
  "06:27",
  "06:30"
]);

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

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": SITE_ORIGINS.has(origin) ? origin : "https://terasfly.github.io",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin"
  };
}

async function manualRateLimit() {
  const cache = caches.default;
  const key = new Request("https://morning-news-trigger.internal/manual-cooldown");
  if (await cache.match(key)) return false;
  await cache.put(
    key,
    new Response("1", {
      headers: { "Cache-Control": `public, max-age=${MANUAL_COOLDOWN_SECONDS}` }
    })
  );
  return true;
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
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS" && url.pathname === "/trigger") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    if (request.method === "POST" && url.pathname === "/trigger") {
      const hasSecret = request.headers.get("Authorization") === `Bearer ${env.TRIGGER_SECRET}`;
      if (!hasSecret && !SITE_ORIGINS.has(origin)) {
        return Response.json({ error: "Unauthorized" }, { status: 401, headers: corsHeaders(origin) });
      }
      if (!hasSecret && !(await manualRateLimit())) {
        return Response.json(
          { error: "An update was already started recently", retry_after: MANUAL_COOLDOWN_SECONDS },
          { status: 429, headers: corsHeaders(origin) }
        );
      }
      try {
        await dispatchWorkflow(env);
        return Response.json(
          { status: "dispatched", at: new Date().toISOString() },
          { headers: corsHeaders(origin) }
        );
      } catch (error) {
        return Response.json(
          { error: error instanceof Error ? error.message : "Could not start the update" },
          { status: 502, headers: corsHeaders(origin) }
        );
      }
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
