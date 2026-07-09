# Ryto signalas

Personalizuotas rytinis naujienų agentas. Jis surenka RSS naujienas apie AI, smegenų mokslą ir longevity, sugeneruoja JSON/PDF leidimą, o React aplikacija parodo prioritetizuotą rytinį digestą su filtrais, šaltinių būsena ir kopijuojama santrauka.

## Atidaryti naujienas

[Atidaryti Ryto signalą](https://terasfly.github.io/morning-news/)

## Vietinis paleidimas

```powershell
npm install
npm run dev
```

Vite parodys vietinę nuorodą, dažniausiai `http://127.0.0.1:5173/`.

## Atnaujinti rytinį leidimą

```powershell
python build_ryto_signalas_pdf.py --timezone Europe/London
```

Generatorius sukuria `public/ryto-signalas.json`, `public/latest.pdf` ir statinį HTML leidimą. React aplikacija naudoja `ryto-signalas.json`; jei failo nėra, ji įsijungia demo režimu.

## Produkcinis build

```powershell
npm run build
npm run preview
```

## GitHub Pages

Workflow `.github/workflows/ryto-signalas.yml` suplanuotas 06:00 `Europe/London` laiku. Jis paleidžia Python RSS generatorių, tada surenka React aplikaciją ir publikuoja `dist/` į GitHub Pages.
