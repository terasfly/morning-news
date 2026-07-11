# Morning Magazine

Personal daily Morning Magazine in English. It reads selected source articles about brain research, longevity, WHOOP/wearables, AI and ChatGPT, then writes concise English summaries with a complete Lithuanian translation under the heading `Lietuviškai`. Weak or unimportant topics are skipped instead of being used as filler.

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

The generator creates `public/ryto-signalas.json`, `public/latest.pdf`, `public/latest.epub` and a static HTML edition. The React app reads `ryto-signalas.json`; if the file is missing, it uses demo mode.

For best summaries and Lithuanian translations, add a GitHub Actions secret named `OPENAI_API_KEY`. Without it, the generator still works with an extractive fallback and automatic translation.

## Production build

```powershell
npm run build
npm run preview
```

## GitHub Pages

Workflow `.github/workflows/ryto-signalas.yml` is scheduled for 06:00 `Europe/London`. It runs the Python magazine generator, builds the React app and publishes `dist/` to GitHub Pages.
