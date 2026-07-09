# Ryto signalas

Personalizuotas rytinis naujienu agentas. Jis surenka RSS naujienas apie smegenu tyrimus, longevity, WHOOP/wearables medicina, AI ir ChatGPT atnaujinimus, o gale prideda viena populiarios arba naujos knygos signala. Generatorius sukuria JSON/PDF leidima, o React aplikacija parodo prioritetizuota rytini digesta su filtrais, saltiniu busena ir kopijuojama santrauka.

## Atidaryti naujienas

[Atidaryti Ryto signala](https://terasfly.github.io/morning-news/)

## Vietinis paleidimas

```powershell
npm install
npm run dev
```

Vite parodys vietine nuoroda, dazniausiai `http://127.0.0.1:5173/`.

## Atnaujinti rytini leidima

```powershell
python build_ryto_signalas_pdf.py --timezone Europe/London
```

Generatorius sukuria `public/ryto-signalas.json`, `public/latest.pdf` ir statini HTML leidima. React aplikacija naudoja `ryto-signalas.json`; jei failo nera, ji isijungia demo rezimu.

## Produkcinis build

```powershell
npm run build
npm run preview
```

## GitHub Pages

Workflow `.github/workflows/ryto-signalas.yml` suplanuotas 06:00 `Europe/London` laiku. Jis paleidzia Python RSS generatoriu, tada surenka React aplikacija ir publikuoja `dist/` i GitHub Pages.
