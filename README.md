# Morning Magazine

Personal daily Morning Magazine in English. It reads only overnight-fresh source articles about brain research, longevity, AI and ChatGPT, plus fresh-only GTA 6 and Northern Ireland trout/Woodburn stocking signals. WHOOP appears only when a newly published study, trial, cohort, experiment, or validation item explicitly uses WHOOP; old WHOOP material is never inserted as filler. The generator also checks each morning for kitchen, bakery and food-production vacancies that explicitly match Knotts Bakery and Forestside, Belfast. It writes concise English summaries with a complete Lithuanian translation under the heading `Lietuviškai`. Weak, stale, or mismatched topics are skipped.

The final section recommends 1-3 books in the atmosphere of `Shantaram` and `The Great Alone`: immersive nature, adventure, survival, strong relationships and emotional journeys.

## Open the magazine

[Open Morning Magazine](https://terasfly.github.io/morning-news/)

## Local development

```powershell
npm install
npm run dev
```

Vite will show a local URL, usually `http://127.0.0.1:5173/`.

## Generate the morning edition

```powershell
python build_ryto_signalas_pdf.py --timezone Europe/London
```

The generator creates `public/ryto-signalas.json`, a phone-friendly `public/latest.pdf`, `public/watch-state.json` for monitored official page changes, and a static HTML edition. The React app reads `ryto-signalas.json`; if the file is missing, it uses demo mode.

For best summaries and Lithuanian translations, add a GitHub Actions secret named `OPENAI_API_KEY`. Without it, the generator still works with an extractive fallback and automatic translation.

## Production build

```powershell
npm run build
npm run preview
```

## GitHub Pages

The primary laptop-independent scheduler is the Cloudflare Worker in `cloudflare-worker/`. It checks at 06:00 `Europe/London`, then retries every three minutes through 06:30. When the public edition is stale it dispatches `.github/workflows/ryto-signalas.yml`, which runs the Python magazine generator, builds the React app and publishes `dist/` to GitHub Pages. GitHub schedules remain as a redundant fallback. A genuinely fresh WHOOP study leads the article order when one exists; otherwise the section is omitted. The freshest suitable ChatGPT/OpenAI update follows immediately after WHOOP when both exist.
