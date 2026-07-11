from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
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
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

PAGE_W, PAGE_H = 428, 926
MARGIN_X = 22
MARGIN_TOP = 30
MARGIN_BOTTOM = 32
CONTENT_W = PAGE_W - 2 * MARGIN_X

INK = colors.HexColor("#14213D")
MUTED = colors.HexColor("#5F6570")
RULE = colors.HexColor("#C8B99A")
PAPER = colors.HexColor("#F7F1E6")
SOFT_BLUE = colors.HexColor("#E8EEF5")
SOFT_GREEN = colors.HexColor("#E7F0EA")
GOLD = colors.HexColor("#B7853B")

USER_AGENT = "MorningMagazine/2.0 (+https://github.com/terasfly/morning-news)"
PUBLISHED_DATA_URL = os.getenv(
    "PUBLISHED_DATA_URL",
    "https://terasfly.github.io/morning-news/ryto-signalas.json",
)
PUBLISHED_SITE_URL = os.getenv("PUBLISHED_SITE_URL", "https://terasfly.github.io/morning-news").rstrip("/")
ARCHIVE_INDEX_URL = f"{PUBLISHED_SITE_URL}/archive/index.json"
NEWS_WINDOW_START_HOUR = 18


TOPICS: list[dict[str, Any]] = [
    {
        "name": "Brain Research",
        "tag": "Brain research",
        "description": "Neuroscience, cognition, memory, biomarkers, sleep, and brain health.",
        "min_score": 36,
        "strict_fresh": True,
        "keywords": [
            "brain",
            "neuroscience",
            "neuron",
            "neurodegeneration",
            "cognitive",
            "memory",
            "alzheimer",
            "parkinson",
            "dementia",
            "sleep",
            "mri",
            "fmri",
            "biomarker",
            "neuroplasticity",
        ],
        "feeds": [
            ("ScienceDaily Neuroscience", "https://www.sciencedaily.com/rss/mind_brain/neuroscience.xml"),
            ("Neuroscience News", "https://neurosciencenews.com/feed/"),
            ("Nature Neuroscience", "https://www.nature.com/subjects/neuroscience.rss"),
            (
                "Google News Brain Research",
                "https://news.google.com/rss/search?q=neuroscience%20OR%20brain%20research%20OR%20Alzheimer%20OR%20Parkinson%20when%3A2d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
        ],
    },
    {
        "name": "Longevity",
        "tag": "Longevity",
        "description": "Healthspan, aging biology, prevention, metabolism, exercise, and sleep.",
        "min_score": 36,
        "strict_fresh": True,
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
            "sleep",
            "inflammation",
            "biological age",
        ],
        "feeds": [
            ("ScienceDaily Healthy Aging", "https://www.sciencedaily.com/rss/health_medicine/healthy_aging.xml"),
            ("ScienceDaily Dementia", "https://www.sciencedaily.com/rss/mind_brain/dementia.xml"),
            ("Nature Ageing", "https://www.nature.com/subjects/ageing.rss"),
            (
                "Google News Longevity",
                "https://news.google.com/rss/search?q=longevity%20OR%20healthspan%20OR%20aging%20research%20OR%20biological%20age%20when%3A2d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
        ],
    },
    {
        "name": "WHOOP & Wearables",
        "tag": "WHOOP and wearables",
        "description": "WHOOP, wearables, HRV, sleep tracking, bloodwork, and clinical studies.",
        "min_score": 30,
        "keywords": [
            "whoop",
            "wearable",
            "wearables",
            "fitness tracker",
            "smartwatch",
            "heart rate variability",
            "hrv",
            "sleep tracking",
            "recovery",
            "bloodwork",
            "clinical trial",
            "medical study",
            "digital health",
        ],
        "feeds": [
            (
                "Google News WHOOP",
                "https://news.google.com/rss/search?q=WHOOP%20%28medical%20study%20OR%20clinical%20trial%20OR%20bloodwork%20OR%20sleep%20OR%20HRV%29%20when%3A7d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
            (
                "Google News Wearable Medicine",
                "https://news.google.com/rss/search?q=%28wearable%20OR%20smartwatch%20OR%20fitness%20tracker%29%20%28medical%20study%20OR%20clinical%20trial%20OR%20digital%20health%29%20when%3A7d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
            (
                "Google News Sleep HRV",
                "https://news.google.com/rss/search?q=%28sleep%20tracking%20OR%20heart%20rate%20variability%20OR%20HRV%29%20%28study%20OR%20research%29%20when%3A7d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
        ],
    },
    {
        "name": "AI & ChatGPT",
        "tag": "AI and ChatGPT",
        "description": "Official OpenAI updates, ChatGPT releases, agents, models, and AI product shifts.",
        "min_score": 36,
        "strict_fresh": True,
        "keywords": [
            "ai",
            "artificial intelligence",
            "machine learning",
            "openai",
            "chatgpt",
            "gpt",
            "anthropic",
            "claude",
            "google deepmind",
            "model",
            "agent",
            "robot",
            "nvidia",
        ],
        "feeds": [
            ("OpenAI News", "https://openai.com/news/rss.xml"),
            ("ScienceDaily AI", "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml"),
            ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
            ("MIT News AI", "https://news.mit.edu/rss/topic/artificial-intelligence2"),
            (
                "Google News ChatGPT",
                "https://news.google.com/rss/search?q=ChatGPT%20OR%20OpenAI%20OR%20GPT%20when%3A2d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
            (
                "Google News AI",
                "https://news.google.com/rss/search?q=artificial%20intelligence%20OR%20AI%20agents%20when%3A2d&hl=en-US&gl=US&ceid=US%3Aen",
            ),
        ],
    },
]


BOOK_LIBRARY: list[dict[str, str]] = [
    {
        "title": "The Snow Child",
        "author": "Eowyn Ivey",
        "summary_en": "This is an atmospheric Alaska novel about loneliness, wilderness, wonder, and the fragile bonds that keep people alive through hard winters. It matches your taste because the landscape feels like a character, and the emotional journey is quiet but powerful.",
        "summary_lt": "Tai atmosferiškas romanas apie Aliaską, vienatvę, laukinę gamtą, stebuklo jausmą ir trapius ryšius, kurie padeda žmonėms išgyventi sunkias žiemas. Jis tinka tavo skoniui, nes gamta čia jaučiasi kaip atskiras veikėjas, o emocinė kelionė tyli, bet stipri.",
    },
    {
        "title": "Lonesome Dove",
        "author": "Larry McMurtry",
        "summary_en": "A big, immersive journey across harsh country, built around friendship, endurance, loyalty, and loss. If you liked the vast human world of Shantaram, this gives a similar feeling of living inside a long road story with unforgettable characters.",
        "summary_lt": "Tai plati, įtraukianti kelionė per atšiaurų kraštą, paremta draugyste, ištverme, lojalumu ir netektimi. Jei tau patiko didelis žmogiškas Shantaram pasaulis, ši knyga duoda panašų jausmą, lyg gyventum ilgoje kelionės istorijoje su nepamirštamais veikėjais.",
    },
    {
        "title": "A Fine Balance",
        "author": "Rohinton Mistry",
        "summary_en": "This is a deeply human, sweeping novel about people trying to keep dignity and connection under extreme pressure. It has the emotional density and social atmosphere that can appeal to someone who loved Shantaram's human chaos and moral struggle.",
        "summary_lt": "Tai labai žmogiškas, platus romanas apie žmones, bandančius išlaikyti orumą ir ryšį patirdami didžiulį spaudimą. Jame yra emocinio tankio ir socialinės atmosferos, kuri gali patikti žmogui, mėgusiam Shantaram žmogišką chaosą ir moralinę kovą.",
    },
    {
        "title": "The River",
        "author": "Peter Heller",
        "summary_en": "Two friends paddle through remote wilderness as danger closes in, making this a lean survival story with emotional weight. It fits because it combines nature, tension, loyalty, and the question of what people owe each other under pressure.",
        "summary_lt": "Du draugai keliauja upe per atokią laukinę gamtą, o pavojus vis artėja, todėl tai glausta, įtempta išgyvenimo istorija su emociniu svoriu. Ji tinka, nes jungia gamtą, įtampą, lojalumą ir klausimą, ką žmonės vieni kitiems skolingi spaudimo akimirkomis.",
    },
    {
        "title": "Where the Crawdads Sing",
        "author": "Delia Owens",
        "summary_en": "A lonely child grows into herself inside a wild coastal landscape, with nature, survival, love, and suspicion all tied together. It matches the emotional wilderness side of The Great Alone more than the urban sweep of Shantaram.",
        "summary_lt": "Vienišas vaikas auga laukiniame pakrantės kraštovaizdyje, kur susipina gamta, išgyvenimas, meilė ir įtarimas. Ji labiau atitinka emocinę The Great Alone laukinės gamtos pusę nei miesto mastą, būdingą Shantaram.",
    },
    {
        "title": "Papillon",
        "author": "Henri Charriere",
        "summary_en": "A classic escape and survival story driven by freedom, risk, and stubborn life force. It echoes the fugitive energy of Shantaram, with a stronger emphasis on endurance and the hunger to stay free.",
        "summary_lt": "Tai klasikinė pabėgimo ir išgyvenimo istorija apie laisvę, riziką ir užsispyrusią gyvenimo jėgą. Ji primena Shantaram bėglio energiją, tik dar labiau pabrėžia ištvermę ir alkį išlikti laisvam.",
    },
    {
        "title": "The Four Winds",
        "author": "Kristin Hannah",
        "summary_en": "This is another emotional survival story from Kristin Hannah, centered on family, hardship, migration, and endurance. It is a natural match if what stayed with you from The Great Alone was resilience under brutal conditions.",
        "summary_lt": "Tai dar viena Kristin Hannah emocinė išgyvenimo istorija apie šeimą, sunkumus, migraciją ir ištvermę. Ji natūraliai tinka, jei iš The Great Alone labiausiai įstrigo atsparumas žiauriomis sąlygomis.",
    },
    {
        "title": "Cutting for Stone",
        "author": "Abraham Verghese",
        "summary_en": "A rich, emotional novel about family, medicine, exile, and belonging across continents. It has the immersive life-story quality that makes Shantaram feel like a whole world rather than only a plot.",
        "summary_lt": "Tai turtingas, emocingas romanas apie šeimą, mediciną, tremtį ir priklausymo jausmą keliuose žemynuose. Jis turi įtraukiančią gyvenimo istorijos kokybę, dėl kurios Shantaram atrodo kaip visas pasaulis, o ne tik siužetas.",
    },
    {
        "title": "The Poisonwood Bible",
        "author": "Barbara Kingsolver",
        "summary_en": "A family is pulled into a beautiful, dangerous place where belief, survival, and relationships are tested. It fits your taste through its powerful setting, moral complexity, and long emotional consequences.",
        "summary_lt": "Šeima atsiduria gražioje, pavojingoje vietoje, kur išbandomi įsitikinimai, išgyvenimas ir santykiai. Ji tinka tavo skoniui dėl stiprios aplinkos, moralinio sudėtingumo ir ilgų emocinių pasekmių.",
    },
    {
        "title": "Welcome to the Goddamn Ice Cube",
        "author": "Blair Braverman",
        "summary_en": "This memoir moves through Alaska, Norway, sled dogs, cold, fear, and self-reliance. It is a strong match for the raw wilderness and survival atmosphere you liked in The Great Alone.",
        "summary_lt": "Šie memuarai veda per Aliaską, Norvegiją, kinkinius šunis, šaltį, baimę ir savarankiškumą. Tai stiprus pasirinkimas, jei tau patiko The Great Alone laukinės gamtos ir išgyvenimo atmosfera.",
    },
    {
        "title": "The Salt Path",
        "author": "Raynor Winn",
        "summary_en": "A couple loses almost everything and walks the wild coast of England, turning hardship into a physical and emotional journey. It matches your interest in survival, love under pressure, and healing through landscape.",
        "summary_lt": "Pora beveik viską praranda ir leidžiasi pėsčiomis laukine Anglijos pakrante, paversdama sunkumus fizine ir emocine kelione. Ji tinka tavo domėjimuisi išgyvenimu, meile spaudimo sąlygomis ir gijimu per kraštovaizdį.",
    },
    {
        "title": "Damnation Spring",
        "author": "Ash Davidson",
        "summary_en": "A family and a logging community face loyalty, damage, and survival in a landscape that gives and takes away. It fits the Great Alone side of your taste: nature, family pressure, hard choices, and emotional cost.",
        "summary_lt": "Šeima ir medkirčių bendruomenė susiduria su lojalumu, žala ir išgyvenimu kraštovaizdyje, kuris ir duoda, ir atima. Ji tinka The Great Alone tavo skonio pusei: gamta, šeimos spaudimas, sunkūs pasirinkimai ir emocinė kaina.",
    },
    {
        "title": "The Far Pavilions",
        "author": "M. M. Kaye",
        "summary_en": "A sweeping historical adventure set across India, full of identity, danger, loyalty, and romance. It may appeal if the Indian atmosphere and large-scale journey were part of what made Shantaram memorable for you.",
        "summary_lt": "Tai platus istorinis nuotykis Indijoje, kupinas tapatybės, pavojaus, lojalumo ir romantikos. Jis gali patikti, jei Shantaram tau įsiminė dėl Indijos atmosferos ir didelės kelionės pojūčio.",
    },
    {
        "title": "Wild",
        "author": "Cheryl Strayed",
        "summary_en": "A grief-struck woman walks the Pacific Crest Trail and turns physical hardship into a reckoning with her life. It fits your interest in emotional journeys, nature, survival, and rebuilding the self.",
        "summary_lt": "Gedinti moteris eina Pacific Crest Trail keliu ir fizinį sunkumą paverčia akistata su savo gyvenimu. Ji tinka tavo pomėgiui emocinėms kelionėms, gamtai, išgyvenimui ir savęs atkūrimui.",
    },
    {
        "title": "Tracks",
        "author": "Robyn Davidson",
        "summary_en": "A woman crosses the Australian desert with camels, making this a spare, powerful story of solitude, danger, and inner toughness. It belongs beside wilderness survival books, but with a more meditative atmosphere.",
        "summary_lt": "Moteris su kupranugariais kerta Australijos dykumą, todėl tai santūri, stipri istorija apie vienatvę, pavojų ir vidinį kietumą. Ji dera prie laukinės gamtos išgyvenimo knygų, tik jos atmosfera meditatyvesnė.",
    },
    {
        "title": "The Covenant of Water",
        "author": "Abraham Verghese",
        "summary_en": "A multi-generational family novel set in Kerala, filled with medicine, faith, secrets, and emotional inheritance. It matches the immersive, whole-life storytelling you may enjoy from Shantaram and Cutting for Stone.",
        "summary_lt": "Tai kelių kartų šeimos romanas Keraloje, kupinas medicinos, tikėjimo, paslapčių ir emocinio paveldėjimo. Jis atitinka įtraukiantį, viso gyvenimo pasakojimą, kuris gali patikti po Shantaram ar Cutting for Stone.",
    },
    {
        "title": "Shogun",
        "author": "James Clavell",
        "summary_en": "A huge historical adventure about survival, power, culture shock, loyalty, and reinvention in an unfamiliar world. It fits the Shantaram side of your taste because it is long, immersive, and full of human strategy.",
        "summary_lt": "Tai didelis istorinis nuotykis apie išgyvenimą, valdžią, kultūrinį šoką, lojalumą ir persikūrimą svetimame pasaulyje. Jis tinka Shantaram tavo skonio pusei, nes yra ilgas, įtraukiantis ir pilnas žmogiškos strategijos.",
    },
    {
        "title": "The Beach",
        "author": "Alex Garland",
        "summary_en": "A search for paradise turns into a tense story about escape, belonging, danger, and the dark side of adventure. It connects to Shantaram through travel, outsider energy, and a seductive but unstable world.",
        "summary_lt": "Rojaus paieškos virsta įtempta istorija apie pabėgimą, priklausymą, pavojų ir tamsiąją nuotykio pusę. Ji siejasi su Shantaram per kelionę, pašaliečio energiją ir viliojantį, bet nestabilų pasaulį.",
    },
    {
        "title": "The Overstory",
        "author": "Richard Powers",
        "summary_en": "This novel makes trees, activism, grief, and human connection feel vast and alive. It is slower than Shantaram, but it can match your love for stories where nature changes the emotional scale of everything.",
        "summary_lt": "Šis romanas medžius, aktyvizmą, gedulą ir žmonių ryšius paverčia dideliais ir gyvais. Jis lėtesnis nei Shantaram, bet gali atitikti tavo meilę istorijoms, kuriose gamta pakeičia viso pasakojimo emocinį mastelį.",
    },
    {
        "title": "Marching Powder",
        "author": "Rusty Young",
        "summary_en": "A strange, intense true story set inside Bolivia's San Pedro prison, full of danger, friendship, survival, and moral gray zones. It is a strong Shantaram-adjacent pick because it reads like an unbelievable life lived outside normal rules.",
        "summary_lt": "Tai keista, intensyvi tikra istorija Bolivijos San Pedro kalėjime, pilna pavojaus, draugystės, išgyvenimo ir moralinių pilkųjų zonų. Ji labai artima Shantaram nuotaikai, nes skaitosi kaip neįtikėtinas gyvenimas už įprastų taisyklių ribų.",
    },
    {
        "title": "The Call of the Wild",
        "author": "Jack London",
        "summary_en": "A short, fierce classic about instinct, wilderness, and transformation under brutal northern conditions. It is a compact way to revisit the raw survival atmosphere that makes Alaska stories powerful.",
        "summary_lt": "Tai trumpa, stipri klasika apie instinktą, laukinę gamtą ir virsmą žiauriomis šiaurės sąlygomis. Tai glaustas būdas grįžti prie neapdorotos išgyvenimo atmosferos, dėl kurios Aliaskos istorijos tokios paveikios.",
    },
    {
        "title": "The Great Railway Bazaar",
        "author": "Paul Theroux",
        "summary_en": "A restless travel classic built from trains, strangers, discomfort, and curiosity across Asia. It matches the journey side of Shantaram, especially if you enjoy being carried through many human worlds.",
        "summary_lt": "Tai neramus kelionių klasikos kūrinys apie traukinius, nepažįstamuosius, diskomfortą ir smalsumą Azijoje. Jis atitinka Shantaram kelionės pusę, ypač jei tau patinka būti vedamam per daugybę žmogiškų pasaulių.",
    },
    {
        "title": "The Old Ways",
        "author": "Robert Macfarlane",
        "summary_en": "A meditative book about walking, old paths, landscape, memory, and the way places shape people. It is less plot-driven, but very strong if you want nature, emotional depth, and a sense of journey.",
        "summary_lt": "Tai meditatyvi knyga apie ėjimą, senus kelius, kraštovaizdį, atmintį ir tai, kaip vietos formuoja žmones. Ji mažiau siužetinė, bet labai stipri, jei nori gamtos, emocinio gylio ir kelionės jausmo.",
    },
    {
        "title": "This Tender Land",
        "author": "William Kent Krueger",
        "summary_en": "A river journey, found family, danger, and hope carry this story through Depression-era America. It fits because it blends adventure with emotional bonds and the feeling of people trying to find a place in the world.",
        "summary_lt": "Upės kelionė, pasirinkta šeima, pavojus ir viltis neša šią istoriją per Didžiosios depresijos laikų Ameriką. Ji tinka, nes jungia nuotykį su emociniais ryšiais ir žmonių bandymu rasti savo vietą pasaulyje.",
    },
    {
        "title": "The Light Between Oceans",
        "author": "M. L. Stedman",
        "summary_en": "A remote lighthouse, isolation, love, grief, and one impossible choice make this a strong emotional landscape novel. It fits the human-relationship side of your taste more than the adventure side.",
        "summary_lt": "Atokus švyturys, izoliacija, meilė, gedulas ir vienas neįmanomas pasirinkimas paverčia šią knygą stipriu emocinio kraštovaizdžio romanu. Ji labiau tinka tavo žmogiškų santykių, o ne nuotykio pusei.",
    },
    {
        "title": "News of the World",
        "author": "Paulette Jiles",
        "summary_en": "A spare, moving road story about an older man and a young girl crossing dangerous country together. It matches your interest in harsh landscapes, trust built slowly, and emotional journeys.",
        "summary_lt": "Tai santūri, jaudinanti kelio istorija apie vyresnį vyrą ir jauną mergaitę, kartu keliaujančius per pavojingą kraštą. Ji atitinka tavo pomėgį atšiauriems kraštovaizdžiams, lėtai kuriamam pasitikėjimui ir emocinėms kelionėms.",
    },
    {
        "title": "The North Water",
        "author": "Ian McGuire",
        "summary_en": "A dark, brutal Arctic survival novel full of violence, cold, moral danger, and endurance. It is much harsher than The Great Alone, but it delivers the raw wilderness pressure very strongly.",
        "summary_lt": "Tai tamsus, žiaurus Arkties išgyvenimo romanas, pilnas smurto, šalčio, moralinio pavojaus ir ištvermės. Jis daug šiurkštesnis nei The Great Alone, bet labai stipriai perteikia laukinės gamtos spaudimą.",
    },
    {
        "title": "The Signature of All Things",
        "author": "Elizabeth Gilbert",
        "summary_en": "A broad, intelligent life story about science, travel, desire, and the natural world. It fits if you want a slower but immersive emotional journey where curiosity and nature shape a whole life.",
        "summary_lt": "Tai plati, protinga gyvenimo istorija apie mokslą, keliones, troškimą ir gamtos pasaulį. Ji tinka, jei nori lėtesnės, bet įtraukiančios emocinės kelionės, kur smalsumas ir gamta formuoja visą gyvenimą.",
    },
    {
        "title": "State of Wonder",
        "author": "Ann Patchett",
        "summary_en": "A doctor travels deep into the Amazon, where science, danger, ethics, and human attachment collide. It matches your interest in immersive places, moral uncertainty, and emotionally charged journeys.",
        "summary_lt": "Gydytoja keliauja giliai į Amazoniją, kur susiduria mokslas, pavojus, etika ir žmogiškas prisirišimas. Ji tinka tavo domėjimuisi įtraukiančiomis vietomis, moraliniu neapibrėžtumu ir emocingomis kelionėmis.",
    },
    {
        "title": "The Mosquito Coast",
        "author": "Paul Theroux",
        "summary_en": "A family follows a brilliant, obsessive father into the jungle, where idealism becomes danger. It fits the survival and relationship-pressure side of The Great Alone, but in a very different landscape.",
        "summary_lt": "Šeima seka genialų, apsėstą tėvą į džiungles, kur idealizmas virsta pavojumi. Ji tinka The Great Alone išgyvenimo ir santykių spaudimo pusei, tik visiškai kitame kraštovaizdyje.",
    },
    {
        "title": "The Sheltering Sky",
        "author": "Paul Bowles",
        "summary_en": "A hypnotic desert novel about travel, alienation, love, and psychological unraveling. It is less comforting, but it offers the kind of intense atmosphere and outsider journey that can appeal after Shantaram.",
        "summary_lt": "Tai hipnotizuojantis dykumos romanas apie kelionę, svetimumą, meilę ir psichologinį irimą. Jis mažiau guodžiantis, bet turi tokią intensyvią atmosferą ir pašaliečio kelionę, kuri gali patikti po Shantaram.",
    },
    {
        "title": "The Orchardist",
        "author": "Amanda Coplin",
        "summary_en": "A quiet, beautifully written novel about solitude, violence, care, and damaged people finding fragile shelter in a remote landscape. It matches the emotional wilderness and human tenderness you may like.",
        "summary_lt": "Tai tylus, gražiai parašytas romanas apie vienatvę, smurtą, rūpestį ir sužeistus žmones, randančius trapų prieglobstį atokiame kraštovaizdyje. Jis atitinka emocinę laukinę gamtą ir žmogišką švelnumą, kuris tau gali patikti.",
    },
]


TRUE_STORY_BOOK_TYPES = {
    "Memoir",
    "True story",
    "Biography",
    "Narrative nonfiction",
    "Travel memoir",
    "Survival nonfiction",
    "Inspired by real events",
}


BOOK_METADATA: dict[str, dict[str, str]] = {
    "The Snow Child": {
        "book_type": "Fiction inspired by folklore",
        "isbn": "9780316175678",
        "description_en": "A childless couple tries to build a life in the Alaskan wilderness after years of grief. One winter night they make a girl out of snow, and soon a mysterious child begins appearing near their cabin. The novel stays quiet and atmospheric, blending frontier hardship, family longing, and a touch of wonder without giving easy answers.",
        "why_it_may_appeal": "It has the wild Alaska mood of The Great Alone, but with more tenderness, loneliness, and myth.",
        "length": "Approx. 10 hours audiobook / 400 pages",
        "goodreads_rating": "Approx. 3.9/5",
    },
    "Lonesome Dove": {
        "book_type": "Historical fiction",
        "isbn": "9781439195260",
        "description_en": "Two aging former Texas Rangers drive cattle north across a dangerous and changing American frontier. The journey becomes a huge human canvas of friendship, violence, loyalty, regret, and endurance. It is long, funny, brutal, and deeply emotional without feeling sentimental.",
        "why_it_may_appeal": "It offers the same big lived-in-world feeling that makes Shantaram so immersive.",
        "length": "Approx. 36 hours audiobook / 850 pages",
        "goodreads_rating": "Approx. 4.5/5",
    },
    "A Fine Balance": {
        "book_type": "Literary fiction",
        "isbn": "9781400030651",
        "description_en": "Four people from different backgrounds are thrown together in India during political upheaval. Their lives become linked through work, survival, kindness, and terrible pressure from the world around them. The book is expansive, intimate, and emotionally devastating, with a strong sense of place and social reality.",
        "why_it_may_appeal": "It has the Indian atmosphere, human density, and moral struggle that can make Shantaram unforgettable.",
        "length": "Approx. 25 hours audiobook / 624 pages",
        "goodreads_rating": "Approx. 4.4/5",
    },
    "The River": {
        "book_type": "Adventure fiction",
        "isbn": "9780525521877",
        "description_en": "Two college friends paddle through remote Canadian wilderness and sense that danger is moving toward them. A wildfire, a distant argument, and the isolation of the river turn the trip into a survival story. The prose is lean, physical, and tense, with friendship at the center.",
        "why_it_may_appeal": "It is a compact wilderness thriller with emotional loyalty under pressure.",
        "length": "Approx. 7 hours audiobook / 272 pages",
        "goodreads_rating": "Approx. 3.9/5",
    },
    "Where the Crawdads Sing": {
        "book_type": "Fiction",
        "isbn": "9780735219090",
        "description_en": "A girl grows up largely alone in the marshes of North Carolina, learning the natural world as both home and refuge. Her isolation shapes her intelligence, vulnerability, and ability to survive. The story combines nature writing, coming-of-age emotion, and mystery without losing its strong landscape mood.",
        "why_it_may_appeal": "It fits the emotional wilderness and self-reliance side of The Great Alone.",
        "length": "Approx. 12 hours audiobook / 384 pages",
        "goodreads_rating": "Approx. 4.4/5",
    },
    "Papillon": {
        "book_type": "Memoir / autobiographical adventure",
        "isbn": "9780061120667",
        "description_en": "Henri Charriere recounts imprisonment, escape attempts, danger, and survival after being sent to a brutal penal colony. The book reads like a relentless adventure driven by freedom and refusal to be broken. Some details have been debated, but its power as a life-and-escape narrative is hard to deny.",
        "why_it_may_appeal": "It has the fugitive energy, risk, and outsider life force that sits close to Shantaram.",
        "length": "Approx. 21 hours audiobook / 560 pages",
        "goodreads_rating": "Approx. 4.2/5",
    },
    "The Four Winds": {
        "book_type": "Historical fiction",
        "isbn": "9781250178602",
        "description_en": "A woman and her family face drought, poverty, migration, and hard choices during the Dust Bowl. The story is built around endurance, motherhood, dignity, and the cost of survival. It is sweeping and emotional, with the landscape itself acting like a force against the characters.",
        "why_it_may_appeal": "It matches the resilience-under-brutal-conditions feeling of The Great Alone.",
        "length": "Approx. 15 hours audiobook / 464 pages",
        "goodreads_rating": "Approx. 4.3/5",
    },
    "Cutting for Stone": {
        "book_type": "Literary fiction",
        "isbn": "9780375714368",
        "description_en": "Twin brothers are born in Ethiopia under dramatic circumstances and grow up surrounded by medicine, family secrets, and political change. The novel follows them across countries, relationships, and moral choices. It is immersive, humane, and rich with medical and emotional detail.",
        "why_it_may_appeal": "It has the whole-life sweep and emotional world-building that Shantaram readers often like.",
        "length": "Approx. 23 hours audiobook / 688 pages",
        "goodreads_rating": "Approx. 4.3/5",
    },
    "The Poisonwood Bible": {
        "book_type": "Literary fiction",
        "isbn": "9780061577079",
        "description_en": "A missionary family moves to the Belgian Congo, where belief, power, and family bonds are tested by a world they do not understand. The story is told through the women of the family, giving it emotional range and moral tension. It is a big, intelligent novel about place, consequence, and survival.",
        "why_it_may_appeal": "It offers powerful setting, family pressure, and long emotional consequences.",
        "length": "Approx. 24 hours audiobook / 576 pages",
        "goodreads_rating": "Approx. 4.1/5",
    },
    "Welcome to the Goddamn Ice Cube": {
        "book_type": "Memoir",
        "isbn": "9780062311569",
        "description_en": "Blair Braverman writes about Alaska, Norway, sled dogs, cold, fear, and learning self-reliance. The memoir is honest about vulnerability as well as toughness. It is a wilderness book, but also a personal transformation story about boundaries and courage.",
        "why_it_may_appeal": "It strongly matches the raw cold-weather survival atmosphere of The Great Alone.",
        "length": "Approx. 8 hours audiobook / 288 pages",
        "goodreads_rating": "Approx. 3.8/5",
    },
    "The Salt Path": {
        "book_type": "Memoir / true story",
        "isbn": "9781405937184",
        "description_en": "After losing their home and facing a frightening diagnosis, a couple walks the South West Coast Path in England. Their journey is physically hard, emotionally exposing, and quietly restorative. The book is about love, homelessness, landscape, and what remains when ordinary security disappears.",
        "why_it_may_appeal": "It combines survival, marriage under pressure, healing through walking, and real-life resilience.",
        "length": "Approx. 9 hours audiobook / 288 pages",
        "goodreads_rating": "Approx. 4.1/5",
    },
    "Damnation Spring": {
        "book_type": "Literary fiction",
        "isbn": "9781982144401",
        "description_en": "A logging family in Northern California faces loyalty, environmental damage, infertility, and the costs of making a living from the land. The novel is intimate but rooted in a whole community. It is a slow-burn story about marriage, nature, work, and moral pressure.",
        "why_it_may_appeal": "It has the family, landscape, and hard-choice pressure that sits near The Great Alone.",
        "length": "Approx. 15 hours audiobook / 464 pages",
        "goodreads_rating": "Approx. 4.0/5",
    },
    "The Far Pavilions": {
        "book_type": "Historical adventure fiction",
        "isbn": "9780312151256",
        "description_en": "A sweeping story moves across nineteenth-century India through war, identity, loyalty, and romance. It is broad, old-fashioned, and full of journey, danger, and cultural tension. The scale is large, and the setting is a major part of the experience.",
        "why_it_may_appeal": "It may appeal if the India setting and long adventure arc were central to Shantaram for you.",
        "length": "Approx. 48 hours audiobook / 960 pages",
        "goodreads_rating": "Approx. 4.2/5",
    },
    "Wild": {
        "book_type": "Memoir",
        "isbn": "9780307476074",
        "description_en": "Cheryl Strayed hikes the Pacific Crest Trail after grief, addiction, and family rupture have upended her life. The trail is physically punishing, but the real movement is emotional and inward. It is a direct, vulnerable story of survival, reckoning, and rebuilding the self.",
        "why_it_may_appeal": "It is exactly in the true-life transformation, nature, and survival lane you described.",
        "length": "Approx. 13 hours audiobook / 336 pages",
        "goodreads_rating": "Approx. 4.0/5",
    },
    "Tracks": {
        "book_type": "Travel memoir / true story",
        "isbn": "9780679762874",
        "description_en": "Robyn Davidson crosses the Australian desert with camels and a dog, seeking solitude and testing herself against the land. The journey is dangerous, spare, and psychologically intense. It is less about conquest than about independence, silence, and what a person meets inside herself in extreme space.",
        "why_it_may_appeal": "It gives the real-life wilderness endurance of Wild with a more solitary, desert atmosphere.",
        "length": "Approx. 8 hours audiobook / 256 pages",
        "goodreads_rating": "Approx. 4.0/5",
    },
    "The Covenant of Water": {
        "book_type": "Historical literary fiction",
        "isbn": "9780802162175",
        "description_en": "A family in Kerala carries a strange pattern of loss across generations, while medicine, faith, secrets, and love shape their lives. The novel is vast but intimate, following people through illness, devotion, and change. It is a patient, immersive story with deep emotional inheritance.",
        "why_it_may_appeal": "It has the long, absorbing, whole-family life story feeling that can follow Shantaram well.",
        "length": "Approx. 31 hours audiobook / 736 pages",
        "goodreads_rating": "Approx. 4.5/5",
    },
    "Shogun": {
        "book_type": "Historical adventure fiction",
        "isbn": "9780440178002",
        "description_en": "An English sailor is thrown into feudal Japan and must learn a dangerous new world of politics, war, culture, and loyalty. The book is huge, strategic, and deeply immersive. It is about survival in an unfamiliar society as much as it is about power and reinvention.",
        "why_it_may_appeal": "It gives the long-form adventure, outsider energy, and cultural immersion that Shantaram fans often want.",
        "length": "Approx. 53 hours audiobook / 1152 pages",
        "goodreads_rating": "Approx. 4.4/5",
    },
    "The Beach": {
        "book_type": "Adventure fiction",
        "isbn": "9781573226523",
        "description_en": "A backpacker in Thailand hears about a hidden beach and joins a secret community that seems like paradise. The dream gradually becomes tense, unstable, and morally dangerous. It is a travel novel about escape, belonging, and the dark side of chasing intensity.",
        "why_it_may_appeal": "It connects to Shantaram through outsider travel, danger, and seductive worlds with cracks underneath.",
        "length": "Approx. 13 hours audiobook / 448 pages",
        "goodreads_rating": "Approx. 3.9/5",
    },
    "The Overstory": {
        "book_type": "Literary fiction",
        "isbn": "9780393356687",
        "description_en": "Several human lives become connected through trees, ecological loss, activism, and grief. The novel is ambitious and slower than a pure adventure story, but it expands the emotional scale of nature. It asks readers to see human life inside a much larger living system.",
        "why_it_may_appeal": "It is strong if you want nature to feel vast, alive, and morally important.",
        "length": "Approx. 23 hours audiobook / 512 pages",
        "goodreads_rating": "Approx. 4.1/5",
    },
    "Marching Powder": {
        "book_type": "True story / narrative nonfiction",
        "isbn": "9780312330347",
        "description_en": "This book follows life inside Bolivia's San Pedro prison, where the rules are stranger and more dangerous than ordinary prison stories suggest. It is full of survival, corruption, friendship, risk, and moral gray zones. The result reads almost like fiction, but it is grounded in a reported real-life world.",
        "why_it_may_appeal": "It is one of the closest Shantaram-adjacent picks: danger, outsiders, friendship, and unbelievable lived experience.",
        "length": "Approx. 10 hours audiobook / 400 pages",
        "goodreads_rating": "Approx. 4.2/5",
    },
    "The Call of the Wild": {
        "book_type": "Classic adventure fiction",
        "isbn": "9780486264721",
        "description_en": "A domesticated dog is pulled into the brutal northern wilderness and forced toward instinct, endurance, and transformation. The story is short, fierce, and mythic. It captures survival pressure in a compact classic form.",
        "why_it_may_appeal": "It is a quick return to the raw wilderness energy behind many Alaska stories.",
        "length": "Approx. 3 hours audiobook / 160 pages",
        "goodreads_rating": "Approx. 3.9/5",
    },
    "The Great Railway Bazaar": {
        "book_type": "Travel writing / true journey",
        "isbn": "9780618658947",
        "description_en": "Paul Theroux travels by train across Europe and Asia, observing strangers, discomfort, landscapes, and the odd intimacy of long-distance travel. The book is restless, opinionated, and full of movement. It is less plot than journey, but it carries the reader through many human worlds.",
        "why_it_may_appeal": "It suits the travel, observation, and many-worlds side of Shantaram.",
        "length": "Approx. 13 hours audiobook / 384 pages",
        "goodreads_rating": "Approx. 3.9/5",
    },
    "The Old Ways": {
        "book_type": "Nature writing / travel nonfiction",
        "isbn": "9780147509796",
        "description_en": "Robert Macfarlane walks old paths and reflects on landscape, memory, language, and the way places shape people. It is meditative rather than plot-driven. The pleasure is in attention, atmosphere, and the feeling of moving through deep time.",
        "why_it_may_appeal": "It is for mornings when you want nature, journey, and reflection more than action.",
        "length": "Approx. 11 hours audiobook / 448 pages",
        "goodreads_rating": "Approx. 4.1/5",
    },
    "This Tender Land": {
        "book_type": "Historical fiction",
        "isbn": "9781476749303",
        "description_en": "Four children escape a harsh school and travel by river through Depression-era America. Along the way they meet danger, kindness, faith, and found family. The story has adventure, emotional warmth, and an old-fashioned journey structure.",
        "why_it_may_appeal": "It blends road-story momentum with human bonds and survival.",
        "length": "Approx. 14 hours audiobook / 464 pages",
        "goodreads_rating": "Approx. 4.3/5",
    },
    "The Light Between Oceans": {
        "book_type": "Historical fiction",
        "isbn": "9781451681758",
        "description_en": "A lighthouse keeper and his wife live in isolation on a remote island after World War I. A single impossible choice tests love, grief, conscience, and family. The novel is quiet, emotional, and built around the cost of doing what feels right.",
        "why_it_may_appeal": "It fits the human relationship and isolation side of your taste.",
        "length": "Approx. 10 hours audiobook / 352 pages",
        "goodreads_rating": "Approx. 4.1/5",
    },
    "News of the World": {
        "book_type": "Historical fiction",
        "isbn": "9780062409201",
        "description_en": "An elderly former soldier agrees to return a young girl to relatives after she has lived for years with the Kiowa. Their journey across dangerous country becomes a spare story of trust and protection. It is short, beautifully controlled, and emotionally resonant.",
        "why_it_may_appeal": "It offers harsh landscape, slow trust, and a moving road-story bond.",
        "length": "Approx. 6 hours audiobook / 224 pages",
        "goodreads_rating": "Approx. 4.1/5",
    },
    "The North Water": {
        "book_type": "Historical adventure fiction",
        "isbn": "9781627795944",
        "description_en": "A disgraced surgeon joins a nineteenth-century Arctic whaling voyage where violence, cold, greed, and survival collide. The novel is dark, brutal, and tightly driven. It is not gentle, but it is powerful if you want nature at its most hostile.",
        "why_it_may_appeal": "It delivers raw wilderness pressure and moral danger in a compact form.",
        "length": "Approx. 8 hours audiobook / 272 pages",
        "goodreads_rating": "Approx. 4.0/5",
    },
    "The Signature of All Things": {
        "book_type": "Historical literary fiction",
        "isbn": "9780143125846",
        "description_en": "A brilliant woman grows into a life shaped by botany, science, travel, desire, and the natural world. The novel follows curiosity and loneliness across decades. It is slower and more intellectual, but immersive in its portrait of a whole life.",
        "why_it_may_appeal": "It gives a rich life-story arc where nature and transformation matter.",
        "length": "Approx. 21 hours audiobook / 512 pages",
        "goodreads_rating": "Approx. 3.9/5",
    },
    "State of Wonder": {
        "book_type": "Literary adventure fiction",
        "isbn": "9780062049810",
        "description_en": "A doctor travels into the Amazon to investigate a research project that has become secretive and morally complicated. The jungle setting creates danger, uncertainty, and a sense of being far from ordinary rules. The novel blends science, ethics, memory, and emotional pressure.",
        "why_it_may_appeal": "It offers an immersive faraway setting and the moral unease that can make adventure stories linger.",
        "length": "Approx. 12 hours audiobook / 368 pages",
        "goodreads_rating": "Approx. 3.9/5",
    },
    "The Mosquito Coast": {
        "book_type": "Adventure fiction",
        "isbn": "9780618658961",
        "description_en": "A brilliant but obsessive father takes his family into the Honduran jungle to build a new life away from modern society. What begins as idealism becomes dangerous control. The novel is a family survival story as much as a travel adventure.",
        "why_it_may_appeal": "It matches the pressure of family, wilderness, and a charismatic but dangerous dream.",
        "length": "Approx. 15 hours audiobook / 384 pages",
        "goodreads_rating": "Approx. 3.8/5",
    },
    "The Sheltering Sky": {
        "book_type": "Literary travel fiction",
        "isbn": "9780060834821",
        "description_en": "A couple travels through North Africa after World War II, trying to escape emptiness and recover meaning. The desert becomes beautiful, alienating, and psychologically dangerous. It is atmospheric, unsettling, and more existential than plot-driven.",
        "why_it_may_appeal": "It offers intense outsider travel and a powerful sense of place.",
        "length": "Approx. 12 hours audiobook / 352 pages",
        "goodreads_rating": "Approx. 3.8/5",
    },
    "The Orchardist": {
        "book_type": "Literary fiction",
        "isbn": "9780062188502",
        "description_en": "A solitary orchardist in the Pacific Northwest takes in two vulnerable girls and becomes drawn into violence, care, and loss. The book is quiet, patient, and beautifully rooted in landscape. It is about damaged people finding fragile shelter rather than easy rescue.",
        "why_it_may_appeal": "It fits the remote-landscape, wounded-family, human-tenderness side of your taste.",
        "length": "Approx. 13 hours audiobook / 448 pages",
        "goodreads_rating": "Approx. 3.8/5",
    },
}


def book_metadata(title: str) -> dict[str, str]:
    metadata = BOOK_METADATA.get(title, {})
    isbn = metadata.get("isbn", "")
    cover_url = metadata.get("cover_url") or (f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg" if isbn else "")
    return {
        "book_type": metadata.get("book_type", "Fiction"),
        "description_en": metadata.get("description_en", ""),
        "why_it_may_appeal": metadata.get("why_it_may_appeal", "It matches your interest in immersive, human stories with emotional weight."),
        "length": metadata.get("length", "Length varies by edition"),
        "goodreads_rating": metadata.get("goodreads_rating", "Goodreads rating unavailable"),
        "cover_url": cover_url,
    }


def book_key(title: str) -> str:
    return re.sub(r"\W+", "", title.lower())


@dataclass
class Article:
    topic: str
    tag: str
    title: str
    summary: str
    summary_en: str
    summary_lt: str
    url: str
    source: str
    published: str
    score: int
    read_status: str
    word_count: int
    source_type: str = ""
    hype_level: str = ""
    hype_filter: str = ""
    practical_takeaway: str = ""


@dataclass
class BookRecommendation:
    title: str
    author: str
    book_type: str
    description_en: str
    why_it_may_appeal: str
    length: str
    goodreads_rating: str
    cover_url: str
    summary_en: str
    summary_lt: str
    search_url: str


@dataclass
class DigestNote:
    title: str
    detail: str
    topic: str = ""
    url: str = ""


WHOOP_SCIENCE_FALLBACKS: list[Article] = [
    Article(
        topic="WHOOP & Wearables",
        tag="WHOOP scientific validation",
        title="WHOOP sleep, heart-rate and HRV metrics tested against other wearables",
        summary=(
            "A Sensors validation study compared six consumer wearables, including WHOOP 3.0, "
            "against reference measures for sleep, heart rate and heart-rate variability. The useful "
            "takeaway is not that any wearable is perfect, but that WHOOP-style recovery metrics have "
            "published validation data and known limits. This is a good evergreen checkpoint when there "
            "is no fresh WHOOP news because it helps separate measurement evidence from marketing."
        ),
        summary_en=(
            "A Sensors validation study compared six consumer wearables, including WHOOP 3.0, "
            "against reference measures for sleep, heart rate and heart-rate variability. The useful "
            "takeaway is not that any wearable is perfect, but that WHOOP-style recovery metrics have "
            "published validation data and known limits. This is a good evergreen checkpoint when there "
            "is no fresh WHOOP news because it helps separate measurement evidence from marketing."
        ),
        summary_lt=(
            "Sensors validacijos tyrimas palygino šešis vartotojų dėvimus įrenginius, tarp jų WHOOP 3.0, "
            "su etaloniniais miego, širdies ritmo ir HRV matavimais. Naudingiausia išvada nėra ta, kad "
            "kuris nors įrenginys tobulas, o tai, kad WHOOP tipo atsistatymo metrikos turi publikuotų "
            "validacijos duomenų ir aiškesnes ribas. Tai geras atsarginis mokslinis signalas, kai nėra "
            "šviežios WHOOP naujienos, nes jis padeda atskirti matavimo įrodymus nuo marketingo."
        ),
        url="https://pubmed.ncbi.nlm.nih.gov/36016077/",
        source="PubMed / Sensors",
        published="2022-08-27T12:00:00+00:00",
        score=58,
        read_status="evergreen-scientific-fallback",
        word_count=120,
    ),
    Article(
        topic="WHOOP & Wearables",
        tag="WHOOP respiratory-rate signal",
        title="WHOOP respiratory-rate changes studied as an early illness signal",
        summary=(
            "A PLOS ONE study examined whether respiratory-rate changes measured by WHOOP could help "
            "classify COVID-19 illness risk before or around symptom onset. The important idea is broader "
            "than COVID: overnight respiratory rate can behave like a stable personal baseline, and deviations "
            "may flag physiological stress. For a daily magazine, this is a useful scientific anchor for why "
            "wearables can matter beyond step counts."
        ),
        summary_en=(
            "A PLOS ONE study examined whether respiratory-rate changes measured by WHOOP could help "
            "classify COVID-19 illness risk before or around symptom onset. The important idea is broader "
            "than COVID: overnight respiratory rate can behave like a stable personal baseline, and deviations "
            "may flag physiological stress. For a daily magazine, this is a useful scientific anchor for why "
            "wearables can matter beyond step counts."
        ),
        summary_lt=(
            "PLOS ONE tyrimas nagrinėjo, ar WHOOP matuojami kvėpavimo dažnio pokyčiai gali padėti "
            "klasifikuoti COVID-19 ligos riziką prieš simptomus arba jų pradžioje. Svarbi mintis platesnė "
            "nei COVID: naktinis kvėpavimo dažnis gali būti gana stabilus asmeninis bazinis rodiklis, o "
            "nukrypimai gali signalizuoti fiziologinį stresą. Rytiniam žurnalui tai geras mokslinis pagrindas, "
            "kodėl dėvimi įrenginiai gali būti svarbūs ne tik žingsniams skaičiuoti."
        ),
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7728254/",
        source="PLOS ONE / PMC",
        published="2020-11-30T12:00:00+00:00",
        score=56,
        read_status="evergreen-scientific-fallback",
        word_count=125,
    ),
    Article(
        topic="WHOOP & Wearables",
        tag="WHOOP physiological response",
        title="WHOOP biometrics captured temporary physiological changes after vaccination",
        summary=(
            "A Journal of Applied Physiology paper using WHOOP data reported temporary changes in "
            "cardiovascular, respiratory and sleep physiology after COVID-19 vaccination. The practical "
            "point is that large-scale wearable data can detect short-lived physiological shifts in real life, "
            "outside a laboratory. That makes WHOOP-type data interesting for population-scale recovery, sleep "
            "and stress research, as long as it is interpreted with context."
        ),
        summary_en=(
            "A Journal of Applied Physiology paper using WHOOP data reported temporary changes in "
            "cardiovascular, respiratory and sleep physiology after COVID-19 vaccination. The practical "
            "point is that large-scale wearable data can detect short-lived physiological shifts in real life, "
            "outside a laboratory. That makes WHOOP-type data interesting for population-scale recovery, sleep "
            "and stress research, as long as it is interpreted with context."
        ),
        summary_lt=(
            "Journal of Applied Physiology straipsnis, naudodamas WHOOP duomenis, aprašė laikinus "
            "širdies-kraujagyslių, kvėpavimo ir miego fiziologijos pokyčius po COVID-19 vakcinacijos. "
            "Praktinė esmė: didelio masto dėvimų įrenginių duomenys gali aptikti trumpalaikius fiziologinius "
            "pokyčius realiame gyvenime, ne tik laboratorijoje. Todėl WHOOP tipo duomenys įdomūs populiaciniams "
            "atsistatymo, miego ir streso tyrimams, jei jie interpretuojami su kontekstu."
        ),
        url="https://pubmed.ncbi.nlm.nih.gov/35019761/",
        source="Journal of Applied Physiology / PubMed",
        published="2022-01-12T12:00:00+00:00",
        score=55,
        read_status="evergreen-scientific-fallback",
        word_count=124,
    ),
    Article(
        topic="WHOOP & Wearables",
        tag="WHOOP HR and HRV validation",
        title="WHOOP wrist photoplethysmography assessed against ECG-derived HR and HRV",
        summary=(
            "A validation study assessed WHOOP's wrist photoplethysmography-derived heart rate and "
            "heart-rate variability against ECG-derived measures. The result is useful because HRV is one "
            "of the core signals behind recovery-style products, but it is also easy to overinterpret. "
            "Including this older validation work keeps the WHOOP section grounded in measurement quality."
        ),
        summary_en=(
            "A validation study assessed WHOOP's wrist photoplethysmography-derived heart rate and "
            "heart-rate variability against ECG-derived measures. The result is useful because HRV is one "
            "of the core signals behind recovery-style products, but it is also easy to overinterpret. "
            "Including this older validation work keeps the WHOOP section grounded in measurement quality."
        ),
        summary_lt=(
            "Validacijos tyrimas vertino WHOOP riešo fotopletizmografijos būdu gaunamą širdies ritmą ir "
            "HRV, lyginant su EKG pagrindu gaunamais matavimais. Tai naudinga, nes HRV yra vienas svarbiausių "
            "atsistatymo tipo produktų signalų, bet jį lengva per daug sureikšminti. Toks senesnis validacijos "
            "darbas padeda WHOOP skiltį laikyti prie matavimo kokybės, o ne vien prie produkto pažadų."
        ),
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC8160717/",
        source="PMC",
        published="2021-05-27T12:00:00+00:00",
        score=54,
        read_status="evergreen-scientific-fallback",
        word_count=112,
    ),
]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?is)<br\s*/?>", " ", value)
    value = re.sub(r"(?is)</p\s*>", ". ", value)
    value = re.sub(r"(?is)<.*?>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return repair_mojibake(value)


def repair_mojibake(value: str) -> str:
    replacements = {
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "â€¦": "...",
        "Â·": "-",
    }
    for bad, good in replacements.items():
        value = value.replace(bad, good)
    return value


def sanitize_xml(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", text)


def truncate_words(text: str, limit: int = 900) -> str:
    words = clean_text(text).split()
    if len(words) <= limit:
        return " ".join(words)
    return " ".join(words[:limit])


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


def news_window(run_date: date, generated_at: datetime, timezone_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(timezone_name)
    local_end = generated_at.astimezone(tz) if generated_at.tzinfo else generated_at.replace(tzinfo=tz)
    if local_end.date() != run_date:
        local_end = datetime.combine(run_date, time(10, 0), tzinfo=tz)
    local_start = datetime.combine(run_date - timedelta(days=1), time(NEWS_WINDOW_START_HOUR, 0), tzinfo=tz)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def article_published_utc(article: Article) -> datetime | None:
    return parse_datetime(article.published)


def article_is_in_window(article: Article, start_utc: datetime, end_utc: datetime) -> bool:
    published = article_published_utc(article)
    return bool(published and start_utc <= published <= end_utc)


def format_window_for_log(start_utc: datetime, end_utc: datetime, timezone_name: str) -> str:
    tz = ZoneInfo(timezone_name)
    start = start_utc.astimezone(tz).strftime("%Y-%m-%d %H:%M")
    end = end_utc.astimezone(tz).strftime("%Y-%m-%d %H:%M")
    return f"{start} to {end} {timezone_name}"


def fetch_url(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/rss+xml,application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def safe_archive_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""))


def restore_published_archive(output_dir: Path) -> None:
    archive_dir = output_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    cache_bust = int(datetime.now(timezone.utc).timestamp())
    try:
        raw_index = fetch_url(f"{ARCHIVE_INDEX_URL}?t={cache_bust}", timeout=15)
        index_payload = json.loads(raw_index.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        return

    editions = index_payload.get("editions", [])
    if not isinstance(editions, list):
        return

    (archive_dir / "index.json").write_text(json.dumps(index_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for entry in editions:
        if not isinstance(entry, dict):
            continue
        edition_date = entry.get("date")
        if not safe_archive_date(edition_date):
            continue
        edition_dir = archive_dir / edition_date
        edition_dir.mkdir(parents=True, exist_ok=True)
        downloads = [
            (entry.get("json") or f"archive/{edition_date}/ryto-signalas.json", edition_dir / "ryto-signalas.json"),
            (
                entry.get("pdf") or f"archive/{edition_date}/morning-magazine-{edition_date}.pdf",
                edition_dir / f"morning-magazine-{edition_date}.pdf",
            ),
            (
                entry.get("epub") or f"archive/{edition_date}/morning-magazine-{edition_date}.epub",
                edition_dir / f"morning-magazine-{edition_date}.epub",
            ),
            (entry.get("html") or f"archive/{edition_date}/index.html", edition_dir / "index.html"),
        ]
        for relative_url, destination in downloads:
            if destination.exists() or not isinstance(relative_url, str):
                continue
            url = f"{PUBLISHED_SITE_URL}/{relative_url.lstrip('/')}"
            try:
                destination.write_bytes(fetch_url(f"{url}?t={cache_bust}", timeout=20))
            except (urllib.error.URLError, TimeoutError, OSError):
                continue


def build_archive_index(output_dir: Path, generated_at: datetime) -> None:
    archive_dir = output_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    editions: list[dict[str, str]] = []
    for path in sorted(archive_dir.glob("*/ryto-signalas.json"), reverse=True):
        edition_date = path.parent.name
        if not safe_archive_date(edition_date):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            payload = {}
        pdf_name = f"morning-magazine-{edition_date}.pdf"
        epub_name = f"morning-magazine-{edition_date}.epub"
        entry = {
            "date": edition_date,
            "label": format_date_en(date.fromisoformat(edition_date)),
            "generated_at": payload.get("generated_at", ""),
            "json": f"archive/{edition_date}/ryto-signalas.json",
            "pdf": f"archive/{edition_date}/{pdf_name}",
            "html": f"archive/{edition_date}/index.html",
        }
        if (path.parent / epub_name).exists():
            entry["epub"] = f"archive/{edition_date}/{epub_name}"
        editions.append(entry)

    payload = {
        "title": "Morning Magazine Archive",
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "editions": editions,
    }
    (archive_dir / "index.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def archive_current_edition(output_dir: Path, run_date: date, pdf_name: str, epub_name: str, generated_at: datetime) -> None:
    edition_date = run_date.isoformat()
    edition_dir = output_dir / "archive" / edition_date
    edition_dir.mkdir(parents=True, exist_ok=True)
    files = [
        (output_dir / "ryto-signalas.json", edition_dir / "ryto-signalas.json"),
        (output_dir / pdf_name, edition_dir / pdf_name),
        (output_dir / epub_name, edition_dir / epub_name),
        (output_dir / "index.html", edition_dir / "index.html"),
    ]
    for source, destination in files:
        if source.exists():
            shutil.copy2(source, destination)
    build_archive_index(output_dir, generated_at)


def article_keys(url: str | None, title: str | None) -> set[str]:
    keys: set[str] = set()
    if url:
        keys.add(url.split("?", 1)[0].rstrip("/").lower())
    if title:
        keys.add(re.sub(r"\W+", "", title.lower())[:80])
    return {key for key in keys if key}


def load_previous_article_keys(output_dir: Path, run_date: date) -> set[str]:
    keys: set[str] = set()
    payloads: list[dict[str, Any]] = []
    local_json = output_dir / "ryto-signalas.json"

    if local_json.exists():
        try:
            payloads.append(json.loads(local_json.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass

    try:
        cache_bust = int(datetime.now(timezone.utc).timestamp())
        remote_data = fetch_url(f"{PUBLISHED_DATA_URL}?t={cache_bust}", timeout=12)
        payloads.append(json.loads(remote_data.decode("utf-8")))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        pass

    for payload in payloads:
        if payload.get("generated_for") != run_date.isoformat():
            continue
        for item in payload.get("articles", []):
            if not isinstance(item, dict):
                continue
            keys.update(article_keys(item.get("url"), item.get("title")))

    return keys


def whoop_science_fallback(run_date: date, excluded_keys: set[str], seen: set[str]) -> Article | None:
    start = run_date.toordinal() % len(WHOOP_SCIENCE_FALLBACKS)
    for offset in range(len(WHOOP_SCIENCE_FALLBACKS)):
        candidate = WHOOP_SCIENCE_FALLBACKS[(start + offset) % len(WHOOP_SCIENCE_FALLBACKS)]
        keys = article_keys(candidate.url, candidate.title)
        if keys & excluded_keys or keys & seen:
            continue
        seen.update(keys)
        return replace(candidate)
    return None


def parse_feed(data: bytes, fallback_source: str, topic: dict[str, Any]) -> list[Article]:
    root = ET.fromstring(sanitize_xml(data))
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
    topic: dict[str, Any],
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
    summary_bonus = 24 if summary_is_useful(title, summary) else 0
    score = keyword_hits * 6 + title_hits * 4 + summary_bonus + recency
    if "google news" in feed_source.lower():
        score -= 20
    if topic["name"].lower() in topic_text:
        score += 1
    published = published_dt.isoformat() if published_dt else ""
    clean_summary = clean_text(summary)
    return Article(
        topic=topic["name"],
        tag=topic["tag"],
        title=clean_text(title),
        summary=clean_summary,
        summary_en=clean_summary,
        summary_lt="",
        url=url.strip(),
        source=clean_text(source) or "RSS source",
        published=published,
        score=score,
        read_status="rss",
        word_count=len(clean_summary.split()),
    )


def summary_is_useful(title: str, summary: str) -> bool:
    summary_clean = clean_text(summary)
    if len(summary_clean) < 120:
        return False
    title_tokens = set(re.findall(r"[a-zA-Z0-9]{4,}", clean_text(title).lower()))
    summary_tokens = set(re.findall(r"[a-zA-Z0-9]{4,}", summary_clean.lower()))
    return len(summary_tokens - title_tokens) >= 8


def extract_article_text(url: str) -> tuple[str, str]:
    try:
        data = fetch_url(url, timeout=18)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return "", "rss"

    page_html = data.decode("utf-8", errors="replace")

    try:
        import trafilatura  # type: ignore

        extracted = trafilatura.extract(
            page_html,
            url=url,
            include_comments=False,
            include_tables=False,
            favor_recall=True,
        )
        if extracted and len(extracted.split()) >= 80:
            return clean_text(extracted), "article"
    except Exception:
        pass

    paragraphs = re.findall(r"(?is)<p[^>]*>(.*?)</p>", page_html)
    text = clean_text(" ".join(paragraphs))
    if len(text.split()) >= 80:
        return text, "article"
    return "", "rss"


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    sentences = []
    for sentence in raw:
        sentence = re.sub(r"^(summary|abstract|source|credit)\s*:\s*", "", sentence.strip(), flags=re.I)
        words = sentence.split()
        lowered = sentence.lower()
        bad_markers = (
            "doi:",
            "abstract dendritic",
            "copyright",
            "all rights reserved",
            "subscribe",
            "advertisement",
            "sign up",
            "image:",
            "credit:",
            "newsletter",
            "cookie",
            "privacy policy",
        )
        if 8 <= len(words) <= 42 and not any(marker in lowered for marker in bad_markers):
            sentences.append(sentence)
    return sentences


STOPWORDS = {
    "about",
    "after",
    "also",
    "because",
    "been",
    "being",
    "could",
    "from",
    "have",
    "into",
    "more",
    "over",
    "said",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "with",
    "would",
    "will",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
}


def token_set(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{3,}", text.lower()) if token not in STOPWORDS}


def extractive_summary(title: str, source_summary: str, article_text: str, topic: dict[str, Any]) -> str:
    material = article_text if len(article_text.split()) >= 120 else source_summary
    sentences = split_sentences(material)
    if not sentences:
        fallback = clean_text(source_summary) or f"{title} was selected as a relevant update in {topic['name']}."
        return normalize_sentence_count(fallback, 3)

    title_tokens = token_set(title)
    topic_tokens = {keyword.lower() for keyword in topic["keywords"]}
    scored: list[tuple[int, int, str]] = []
    for idx, sentence in enumerate(sentences[:32]):
        tokens = token_set(sentence)
        score = len(tokens & title_tokens) * 4 + sum(1 for keyword in topic_tokens if keyword in sentence.lower()) * 3
        if any(marker in sentence.lower() for marker in ("study", "research", "announced", "found", "released", "trial", "data", "model", "patients")):
            score += 4
        if idx < 5:
            score += 5 - idx
        scored.append((score, idx, sentence))

    picked = sorted(sorted(scored, reverse=True)[:3], key=lambda item: item[1])
    summary = " ".join(sentence for _, _, sentence in picked)
    return normalize_sentence_count(summary, 3)


def normalize_sentence_count(text: str, target: int = 3) -> str:
    sentences = split_sentences(text)
    if len(sentences) >= target:
        return " ".join(sentences[:target])
    clean = clean_text(text)
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def strip_summary_prefixes(text: str) -> str:
    text = clean_text(text)
    return re.sub(
        r"^(english summary|summary|lithuanian translation|lithuanian|lietuviškai|lietuviskai|angliška santrauka)\s*:\s*",
        "",
        text,
        flags=re.I,
    ).strip()


def translate_to_lithuanian(text: str) -> str:
    text = clean_text(text)
    if not text:
        return ""
    try:
        from deep_translator import GoogleTranslator  # type: ignore

        translated = GoogleTranslator(source="en", target="lt").translate(text[:4500])
        return clean_text(translated)
    except Exception:
        return "Lietuviškas vertimas laikinai nepavyko. Anglišką esmę skaityk kairėje."


def extract_openai_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    parts: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            text = value.get("text")
            if isinstance(text, str):
                parts.append(text)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload.get("output"))
    return "\n".join(parts).strip()


def call_openai_json(prompt: str, max_output_tokens: int = 900) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    body = {
        "model": OPENAI_MODEL,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    text = extract_openai_text(payload)
    if not text:
        return None
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        text = match.group(0)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def ai_summarize_article(article: Article, article_text: str, topic: dict[str, Any]) -> tuple[str, str] | None:
    prompt = f"""
You are editing a personal daily Morning Magazine.

Task:
- Read the article material below.
- Write a concise English summary in up to 3 sentences.
- Include only the main essence: what happened, why it matters, and the one key update.
- Avoid long background, quotes, and secondary details.
- Do not add facts not supported by the material.
- Then translate the summary completely into Lithuanian, also in up to 3 sentences.
- Return only valid JSON with keys "summary_en" and "summary_lt".

Section: {topic["name"]}
Title: {article.title}
Source: {article.source}
RSS summary: {article.summary}

Article material:
{truncate_words(article_text or article.summary, 950)}
""".strip()
    parsed = call_openai_json(prompt, max_output_tokens=900)
    if not parsed:
        return None
    summary_en = strip_summary_prefixes(str(parsed.get("summary_en", "")))
    summary_lt = strip_summary_prefixes(str(parsed.get("summary_lt", "")))
    summary_en = normalize_sentence_count(summary_en, 3)
    summary_lt = normalize_sentence_count(summary_lt, 3)
    if len(split_sentences(summary_en)) < 2 or not summary_lt:
        return None
    return summary_en, summary_lt


def enrich_article(article: Article, topic: dict[str, Any]) -> Article:
    article_text, read_status = extract_article_text(article.url)
    word_count = len(article_text.split()) if article_text else len(article.summary.split())

    ai_summary = ai_summarize_article(article, article_text, topic)
    if ai_summary:
        summary_en, summary_lt = ai_summary
        read_status = f"{read_status}+ai"
    else:
        summary_en = strip_summary_prefixes(extractive_summary(article.title, article.summary, article_text, topic))
        summary_lt = strip_summary_prefixes(translate_to_lithuanian(summary_en))

    summary_en = normalize_sentence_count(summary_en, 3)
    summary_lt = normalize_sentence_count(summary_lt, 3)
    article.summary_en = summary_en
    article.summary_lt = summary_lt
    article.summary = summary_en
    article.read_status = read_status
    article.word_count = word_count
    if read_status.startswith("article"):
        article.score += 8
    return annotate_article(article)


def is_meaningful(article: Article, topic: dict[str, Any]) -> bool:
    if article.score < int(topic.get("min_score", 30)):
        return False
    summary_words = len(article.summary_en.split())
    if summary_words < 35:
        return False
    if article.source.lower().startswith("google news") and article.word_count < 80:
        return False
    return True


def classify_source_type(article: Article) -> str:
    source = f"{article.source} {article.url} {article.read_status}".lower()
    if "evergreen-scientific-fallback" in source:
        return "Older scientific evidence"
    if any(marker in source for marker in ("pubmed", "pmc", "nature", "plos", "journal", "sensors")):
        return "Peer-reviewed / scientific source"
    if any(marker in source for marker in ("university", "sciencedaily", "medicalxpress", "news-medical")):
        return "Research report"
    if any(marker in source for marker in ("openai", "anthropic", "whoop.com", "google", "meta", "deepmind")):
        return "Company / product update"
    if "google news" in source:
        return "News search result"
    return "Media report"


def estimate_hype_level(article: Article, source_type: str) -> str:
    text = f"{article.title} {article.summary_en} {article.summary}".lower()
    hype_words = (
        "breakthrough",
        "revolutionary",
        "miracle",
        "cure",
        "anti-aging",
        "anti ageing",
        "game changer",
        "secret",
        "stunning",
        "shocking",
    )
    if any(word in text for word in hype_words):
        return "High"
    if source_type in {"Peer-reviewed / scientific source", "Older scientific evidence", "Research report"}:
        return "Low"
    if article.topic in {"Longevity", "AI & ChatGPT"}:
        return "Medium"
    return "Low"


def build_hype_filter(article: Article, source_type: str, hype_level: str) -> str:
    if hype_level == "Low":
        return "Low. Treat this as evidence-backed signal, but still read the source and limits."
    if hype_level == "High":
        return "High. Interesting, but do not treat the headline as proof until stronger evidence is clear."
    if source_type == "Company / product update":
        return "Medium. Useful update, but company/product framing may emphasize the upside."
    return "Medium. Worth tracking, but the practical impact is not settled yet."


def build_practical_takeaway(article: Article, source_type: str) -> str:
    if article.topic == "Brain Research":
        return "Useful to track as an early signal for brain health, cognition, sleep, or diagnosis, not as immediate medical advice."
    if article.topic == "Longevity":
        return "File it under healthspan evidence; wait for human validation before changing habits or supplements."
    if article.topic == "WHOOP & Wearables":
        if source_type == "Older scientific evidence":
            return "This is a calibration point for what WHOOP-style metrics can and cannot prove."
        return "Useful if it improves how you interpret sleep, HRV, recovery, respiratory rate, or wearable accuracy."
    if article.topic == "AI & ChatGPT":
        return "Watch whether this changes real tools, model access, safety, or daily workflows."
    return "Useful context, but read the source before treating it as a decision signal."


def annotate_article(article: Article) -> Article:
    article.source_type = article.source_type or classify_source_type(article)
    article.hype_level = article.hype_level or estimate_hype_level(article, article.source_type)
    article.hype_filter = article.hype_filter or build_hype_filter(article, article.source_type, article.hype_level)
    article.practical_takeaway = article.practical_takeaway or build_practical_takeaway(article, article.source_type)
    return article


def collect_articles(
    run_date: date,
    generated_at: datetime,
    timezone_name: str,
    per_topic: int,
    excluded_keys: set[str] | None = None,
) -> tuple[list[Article], list[str]]:
    selected: list[Article] = []
    errors: list[str] = []
    seen: set[str] = set()
    excluded_keys = excluded_keys or set()
    skipped_existing = 0
    window_start_utc, window_end_utc = news_window(run_date, generated_at, timezone_name)

    for topic in TOPICS:
        candidates: list[Article] = []
        for source, url in topic["feeds"]:
            try:
                feed = fetch_url(url)
                candidates.extend(parse_feed(feed, source, topic))
            except (urllib.error.URLError, TimeoutError, ET.ParseError, ValueError, OSError) as exc:
                errors.append(f"{source}: {exc}")

        if topic.get("strict_fresh"):
            original_count = len(candidates)
            candidates = [article for article in candidates if article_is_in_window(article, window_start_utc, window_end_utc)]
            skipped_stale = original_count - len(candidates)
            if skipped_stale:
                errors.append(
                    f"Skipped {skipped_stale} stale or undated {topic['name']} items outside "
                    f"{format_window_for_log(window_start_utc, window_end_utc, timezone_name)}."
                )

        ranked = sorted(candidates, key=lambda article: (article.score, article.published), reverse=True)
        picked = 0
        checked = 0
        for article in ranked:
            keys = article_keys(article.url, article.title)
            if keys & seen:
                continue
            if keys & excluded_keys:
                skipped_existing += 1
                continue
            checked += 1
            enriched = enrich_article(article, topic)
            if not is_meaningful(enriched, topic):
                if checked >= 10:
                    break
                continue
            seen.update(keys)
            selected.append(enriched)
            picked += 1
            if picked >= per_topic:
                break
            if checked >= 10:
                break

        if topic["name"] == "WHOOP & Wearables" and picked == 0:
            fallback = whoop_science_fallback(run_date, excluded_keys, seen)
            if fallback:
                selected.append(annotate_article(fallback))
                errors.append("Used an evergreen WHOOP scientific validation item because no stronger fresh WHOOP update was selected.")

    if skipped_existing:
        errors.append(f"Skipped {skipped_existing} articles already shown in today's published edition.")

    return selected, errors


def rotated_books(books: list[dict[str, str]], seed: int) -> list[dict[str, str]]:
    if not books:
        return []
    start = seed % len(books)
    return books[start:] + books[:start]


def make_book_recommendation(book: dict[str, str]) -> BookRecommendation:
    metadata = book_metadata(book["title"])
    description = metadata["description_en"] or book["summary_en"]
    query = urllib.parse.quote_plus(f"{book['title']} {book['author']} book")
    return BookRecommendation(
        title=book["title"],
        author=book["author"],
        book_type=metadata["book_type"],
        description_en=description,
        why_it_may_appeal=metadata["why_it_may_appeal"],
        length=metadata["length"],
        goodreads_rating=metadata["goodreads_rating"],
        cover_url=metadata["cover_url"],
        summary_en=book["summary_en"],
        summary_lt=book["summary_lt"],
        search_url=f"https://www.google.com/search?q={query}",
    )


def load_previous_book_titles(output_dir: Path, run_date: date) -> set[str]:
    used: set[str] = set()
    archive_dir = output_dir / "archive"
    if not archive_dir.exists():
        return used

    for path in archive_dir.glob("*/ryto-signalas.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        generated_for = payload.get("generated_for")
        if generated_for == run_date.isoformat():
            continue
        for book in payload.get("book_recommendations", []):
            if isinstance(book, dict) and book.get("title"):
                used.add(book_key(book["title"]))
    return used


def select_book_recommendations(run_date: date, output_dir: Path, count: int = 3) -> list[BookRecommendation]:
    count = 3
    previous_titles = load_previous_book_titles(output_dir, run_date)
    available = [book for book in BOOK_LIBRARY if book_key(book["title"]) not in previous_titles]
    if len(available) < count:
        available = BOOK_LIBRARY[:]

    seed = run_date.toordinal()
    primary_pool = [
        book
        for book in available
        if book_metadata(book["title"])["book_type"] in TRUE_STORY_BOOK_TYPES
    ]
    if not primary_pool:
        primary_pool = [
            book
            for book in BOOK_LIBRARY
            if book_metadata(book["title"])["book_type"] in TRUE_STORY_BOOK_TYPES
        ]
    if not primary_pool:
        primary_pool = available

    picks: list[dict[str, str]] = []
    first_pick = rotated_books(primary_pool, seed)[0]
    picks.append(first_pick)

    remaining = [book for book in available if book_key(book["title"]) != book_key(first_pick["title"])]
    if len(remaining) < count - 1:
        remaining = [book for book in BOOK_LIBRARY if book_key(book["title"]) != book_key(first_pick["title"])]
    for book in rotated_books(remaining, seed * 3 + 7):
        if len(picks) >= count:
            break
        if book_key(book["title"]) in {book_key(item["title"]) for item in picks}:
            continue
        picks.append(book)

    return [make_book_recommendation(book) for book in picks[:count]]


def build_daily_highlights(articles: list[Article]) -> list[DigestNote]:
    notes = []
    for article in sorted(articles, key=lambda item: item.score, reverse=True)[:3]:
        notes.append(
            DigestNote(
                title=article.title,
                detail=f"{article.topic}: {article.practical_takeaway}",
                topic=article.topic,
                url=article.url,
            )
        )
    return notes


def select_whoop_evidence(articles: list[Article]) -> DigestNote | None:
    candidates = [article for article in articles if article.topic == "WHOOP & Wearables"]
    if not candidates:
        return None
    article = sorted(candidates, key=lambda item: (item.read_status == "evergreen-scientific-fallback", item.score), reverse=True)[0]
    return DigestNote(
        title=article.title,
        detail=f"{article.source_type}. {article.practical_takeaway}",
        topic=article.topic,
        url=article.url,
    )


def select_save_for_later(articles: list[Article]) -> list[DigestNote]:
    selected: list[DigestNote] = []
    sorted_articles = sorted(
        articles,
        key=lambda item: (
            item.source_type in {"Peer-reviewed / scientific source", "Older scientific evidence", "Research report"},
            item.score,
        ),
        reverse=True,
    )
    for article in sorted_articles:
        if len(selected) >= 3:
            break
        selected.append(
            DigestNote(
                title=article.title,
                detail=f"Longer read: {article.source_type}. Best saved if you want to inspect the source carefully.",
                topic=article.topic,
                url=article.url,
            )
        )
    return selected


def build_weekly_summary(run_date: date, articles: list[Article]) -> list[DigestNote]:
    if run_date.weekday() != 6:
        return []

    notes: list[DigestNote] = []
    for topic in TOPIC_NAMES:
        topic_articles = [article for article in articles if article.topic == topic]
        if not topic_articles:
            continue
        lead = max(topic_articles, key=lambda article: article.score)
        notes.append(
            DigestNote(
                title=f"{topic}: {lead.title}",
                detail=lead.practical_takeaway,
                topic=topic,
                url=lead.url,
            )
        )
        if len(notes) >= 5:
            break
    return notes


TOPIC_NAMES = [topic["name"] for topic in TOPICS]


def build_cover_theme(articles: list[Article]) -> dict[str, str]:
    if not articles:
        return {
            "topic": "Morning briefing",
            "label": "Balanced edition",
            "detail": "A quiet morning scan across AI, brain research, longevity and wearables.",
        }
    scores: dict[str, int] = {}
    for article in articles:
        scores[article.topic] = scores.get(article.topic, 0) + max(article.score, 1)
    topic = max(scores.items(), key=lambda item: item[1])[0]
    details = {
        "Brain Research": "Brain signals, cognition, diagnosis and nervous-system research lead today's edition.",
        "Longevity": "Healthspan, aging biology and prevention signals lead today's edition.",
        "WHOOP & Wearables": "Wearable physiology, sleep, HRV, recovery and measurement evidence lead today's edition.",
        "AI & ChatGPT": "AI tools, model access, safety and workflow changes lead today's edition.",
    }
    return {
        "topic": topic,
        "label": f"Cover theme: {topic}",
        "detail": details.get(topic, "A balanced edition across your main topics."),
    }


def html_escape(text: str) -> str:
    return html.escape(text, quote=True)


def format_date_en(run_date: date) -> str:
    return run_date.strftime("%B %-d, %Y") if os.name != "nt" else run_date.strftime("%B %#d, %Y")


def iso_to_local(value: str, timezone_name: str) -> str:
    if not value:
        return "date unavailable"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return "date unavailable"
    local_dt = parsed.astimezone(ZoneInfo(timezone_name))
    return local_dt.strftime("%Y-%m-%d %H:%M")


def prepare_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = output_dir / "assets"
    assets.mkdir(exist_ok=True)
    if COVER_IMAGE.exists():
        shutil.copy2(COVER_IMAGE, assets / COVER_IMAGE.name)
    return assets


def render_html(
    output_dir: Path,
    articles: list[Article],
    books: list[BookRecommendation],
    daily_highlights: list[DigestNote],
    save_for_later: list[DigestNote],
    weekly_summary: list[DigestNote],
    whoop_evidence: DigestNote | None,
    cover_theme: dict[str, str],
    run_date: date,
    generated_at: datetime,
    timezone_name: str,
    pdf_name: str,
    epub_name: str,
    errors: list[str],
) -> None:
    generated_time = generated_at.strftime("%H:%M")
    generated_date = generated_at.strftime("%Y-%m-%d")
    assets_rel = f"assets/{COVER_IMAGE.name}" if COVER_IMAGE.exists() else ""
    save_cards = "".join(
        f"""
        <article class="note-card">
          <span>{html_escape(note.topic or "Later")}</span>
          <h3>{html_escape(note.title)}</h3>
          <p>{html_escape(note.detail)}</p>
          <a href="{html_escape(note.url)}" target="_blank" rel="noreferrer">Save source</a>
        </article>
        """
        for note in save_for_later
    )
    weekly_cards = "".join(
        f"""
        <article class="note-card">
          <span>{html_escape(note.topic or "Week")}</span>
          <h3>{html_escape(note.title)}</h3>
          <p>{html_escape(note.detail)}</p>
        </article>
        """
        for note in weekly_summary
    )
    whoop_card = ""
    if whoop_evidence:
        whoop_card = f"""
        <section class="note-section">
          <h2>WHOOP evidence corner</h2>
          <article class="note-card">
            <span>{html_escape(whoop_evidence.topic)}</span>
            <h3>{html_escape(whoop_evidence.title)}</h3>
            <p>{html_escape(whoop_evidence.detail)}</p>
            <a href="{html_escape(whoop_evidence.url)}" target="_blank" rel="noreferrer">Read evidence</a>
          </article>
        </section>
        """
    save_section = ""
    if save_cards:
        save_section = f"""
        <section class="note-section">
          <h2>Save for later</h2>
          <div class="note-grid">{save_cards}</div>
        </section>
        """
    weekly_section = ""
    if weekly_cards:
        weekly_section = f"""
        <section class="note-section">
          <h2>Savaitinis signalas</h2>
          <div class="note-grid">{weekly_cards}</div>
        </section>
        """
    cards = []
    current_topic = ""
    for idx, article in enumerate(articles, 1):
        topic_heading = ""
        if article.topic != current_topic:
            current_topic = article.topic
            topic_heading = f"<h2 class=\"section-title\">{html_escape(current_topic)}</h2>"
        cards.append(
            f"""
            {topic_heading}
            <article class="story">
              <div class="story-meta">
                <span>{idx:02d}</span>
                <span>Publikavo: {html_escape(article.source)}</span>
                <span>Publikuota: {html_escape(iso_to_local(article.published, timezone_name))}</span>
                <a href="{html_escape(article.url)}" target="_blank" rel="noreferrer">Skaityti visą straipsnį</a>
              </div>
              <h3>{html_escape(article.title)}</h3>
              <div class="story-tags">
                <span>{html_escape(article.source_type)}</span>
                <span>Hype: {html_escape(article.hype_level)}</span>
              </div>
              <p>{html_escape(article.summary_en)}</p>
              <h4>Lietuviškai</h4>
              <p>{html_escape(article.summary_lt)}</p>
              <div class="story-insight">
                <p><b>Praktiškai:</b> {html_escape(article.practical_takeaway)}</p>
                <p><b>Hype filtras:</b> {html_escape(article.hype_filter)}</p>
              </div>
            </article>
            """
        )

    if not cards:
        cards.append(
            """
            <article class="story">
              <div class="story-meta"><span>!</span><span>Sources</span></div>
              <h3>No high-quality updates today</h3>
              <p>The magazine skipped the news sections because the available feeds did not contain meaningful updates.</p>
            </article>
            """
        )

    book_cards = []
    for book in books:
        book_cards.append(
            f"""
            <article class="story book-story">
              <div class="book-layout">
                <img src="{html_escape(book.cover_url)}" alt="{html_escape(book.title)} cover">
                <div>
              <div class="story-meta"><span>{html_escape(book.book_type)}</span><span>{html_escape(book.author)}</span></div>
              <h3>{html_escape(book.title)}</h3>
              <div class="story-tags">
                <span>{html_escape(book.length)}</span>
                    <span>Goodreads: {html_escape(book.goodreads_rating)}</span>
              </div>
              <p>{html_escape(book.description_en)}</p>
              <div class="story-insight">
                <p><b>Why it may appeal:</b> {html_escape(book.why_it_may_appeal)}</p>
              </div>
              <p>{html_escape(book.summary_en)}</p>
              <h4>Lietuviškai</h4>
              <p>{html_escape(book.summary_lt)}</p>
              <a href="{html_escape(book.search_url)}" target="_blank" rel="noreferrer">Search book</a>
                </div>
              </div>
            </article>
            """
        )

    error_note = ""
    if errors:
        error_items = "".join(f"<li>{html_escape(error)}</li>" for error in errors[:8])
        error_note = f"""
        <details class="source-health">
          <summary>Source health</summary>
          <ul>{error_items}</ul>
        </details>
        """

    cover_style = f"background-image: linear-gradient(90deg, rgba(20,33,61,.92), rgba(20,33,61,.52)), url('{assets_rel}');" if assets_rel else ""
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Morning Magazine - {html_escape(str(run_date))}</title>
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
      line-height: 1.58;
    }}
    .hero {{
      min-height: 62vh;
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
      color: #f4c46c;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(2.5rem, 7vw, 5.8rem);
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
      padding: 28px 0 42px;
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
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }}
    .stat {{
      background: var(--blue);
      border: 1px solid #c9d4e2;
      padding: 12px;
    }}
    .stat b {{ display: block; color: var(--ink); font-size: 1.3rem; }}
    .stat span {{ color: var(--muted); font-size: .84rem; }}
    .section-title {{
      margin: 30px 0 6px;
      color: var(--ink);
      font-size: 1.65rem;
    }}
    .story {{
      padding: 22px 0;
      border-bottom: 1px solid var(--line);
    }}
    .note-section {{
      margin: 22px 0;
      padding: 18px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.42);
    }}
    .note-section h2 {{
      margin: 0 0 12px;
      color: var(--ink);
      font-size: 1.25rem;
    }}
    .note-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }}
    .note-card {{
      display: grid;
      gap: 7px;
      padding: 13px;
      border: 1px solid #d8caae;
      background: rgba(255,250,240,.8);
    }}
    .note-card span {{
      color: var(--gold);
      font-size: .76rem;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .note-card h3 {{
      margin: 0;
      color: var(--ink);
      font-size: 1rem;
      line-height: 1.22;
    }}
    .note-card p {{
      margin: 0;
      color: var(--muted);
      font-size: .9rem;
    }}
    .note-card a {{
      color: #1f4d78;
      font-size: .86rem;
      font-weight: 700;
      text-decoration: none;
    }}
    .story-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      color: var(--gold);
      font-weight: 700;
      font-size: .78rem;
      text-transform: uppercase;
    }}
    .story h3 {{
      margin: 8px 0 8px;
      color: var(--ink);
      font-size: clamp(1.35rem, 3vw, 2rem);
      line-height: 1.12;
    }}
    .story h4 {{
      margin: 16px 0 4px;
      color: #31446c;
      font-size: 0.92rem;
    }}
    .story-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0 0 10px;
    }}
    .story-tags span {{
      padding: 5px 8px;
      border: 1px solid #c9d4e2;
      color: #31446c;
      background: var(--blue);
      font-size: .78rem;
      font-weight: 700;
    }}
    .story p {{ max-width: 790px; margin: 0 0 12px; }}
    .story-insight {{
      max-width: 790px;
      margin: 12px 0;
      padding: 12px;
      border-left: 3px solid var(--gold);
      background: rgba(255,255,255,.36);
    }}
    .story-insight p {{ margin: 0 0 6px; }}
    .story a {{
      color: #1f4d78;
      font-weight: 700;
      text-decoration: none;
    }}
    .book-section {{
      margin-top: 32px;
      padding-top: 18px;
      border-top: 2px solid var(--ink);
    }}
    .book-story {{
      background: rgba(255,255,255,.28);
      padding-left: 12px;
      padding-right: 12px;
    }}
    .book-layout {{
      display: grid;
      grid-template-columns: 128px 1fr;
      gap: 16px;
      align-items: start;
    }}
    .book-layout img {{
      width: 128px;
      aspect-ratio: 2 / 3;
      object-fit: cover;
      border: 1px solid var(--line);
      background: var(--white);
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
      .note-grid {{ grid-template-columns: 1fr; }}
      .book-layout {{ grid-template-columns: 1fr; }}
      .book-layout img {{ width: 112px; }}
      .hero-inner {{ padding: 42px 0 34px; }}
    }}
  </style>
</head>
<body>
  <section class="hero">
    <div class="hero-inner">
      <p class="kicker">Personal daily edition</p>
      <h1>MORNING MAGAZINE</h1>
      <p class="deck">{html_escape(cover_theme.get("label", "Balanced edition"))}. {html_escape(cover_theme.get("detail", ""))} - {html_escape(format_date_en(run_date))}</p>
      <a class="download" href="{html_escape(pdf_name)}">Download PDF</a>
    </div>
  </section>
  <main>
    <section class="intro">
      <p>This edition reads selected source articles, keeps only meaningful updates, and gives each item an English summary followed by the full Lithuanian translation.</p>
      <div class="stats">
        <div class="stat"><b>{len(articles)}</b><span>news articles</span></div>
        <div class="stat"><b>{len(books)}</b><span>book picks</span></div>
        <div class="stat"><b>06:00</b><span>scheduled {html_escape(timezone_name)}</span></div>
        <div class="stat"><b>{html_escape(generated_time)}</b><span>updated {html_escape(generated_date)} {html_escape(timezone_name)}</span></div>
      </div>
    </section>
    {whoop_card}
    {''.join(cards)}
    {save_section}
    {weekly_section}
    <section class="book-section">
      <h2 class="section-title">Books Section</h2>
      {''.join(book_cards)}
    </section>
    {error_note}
  </main>
  <footer>
    Editor's note: the magazine is generated automatically from source material. For medical or financial decisions, read the original source and consult a qualified professional.
  </footer>
</body>
</html>
"""
    (output_dir / "index.html").write_text(html_doc, encoding="utf-8")


def epub_modified_timestamp(generated_at: datetime) -> str:
    return generated_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epub_section(title: str, notes: list[DigestNote]) -> str:
    if not notes:
        return ""
    items = []
    for note in notes:
        source_link = f'<p><a href="{html_escape(note.url)}">Source</a></p>' if note.url else ""
        items.append(
            f"""
      <section class="note">
        <p class="kicker">{html_escape(note.topic or "Signal")}</p>
        <h3>{html_escape(note.title)}</h3>
        <p>{html_escape(note.detail)}</p>
        {source_link}
      </section>
            """
        )
    return f"<h2>{html_escape(title)}</h2>{''.join(items)}"


def build_epub(
    output_dir: Path,
    articles: list[Article],
    books: list[BookRecommendation],
    daily_highlights: list[DigestNote],
    save_for_later: list[DigestNote],
    weekly_summary: list[DigestNote],
    whoop_evidence: DigestNote | None,
    cover_theme: dict[str, str],
    run_date: date,
    generated_at: datetime,
    timezone_name: str,
    epub_name: str,
) -> None:
    title = f"Morning Magazine - {run_date.isoformat()}"
    identifier = f"urn:morning-magazine:{run_date.isoformat()}"
    modified = epub_modified_timestamp(generated_at)
    cover_item = ""
    cover_meta = ""
    cover_img = ""
    if COVER_IMAGE.exists():
        cover_item = '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>'
        cover_meta = '<meta name="cover" content="cover-image"/>'
        cover_img = '<img class="cover" src="images/cover.png" alt="Morning Magazine cover"/>'

    article_sections = []
    current_topic = ""
    for idx, article in enumerate(articles, 1):
        heading = ""
        if article.topic != current_topic:
            current_topic = article.topic
            heading = f"<h2>{html_escape(current_topic)}</h2>"
        article_sections.append(
            f"""
      {heading}
      <article>
        <p class="kicker">{idx:02d} / Publikavo: {html_escape(article.source)} / Publikuota: {html_escape(iso_to_local(article.published, timezone_name))} / <a href="{html_escape(article.url)}">Skaityti visa straipsni</a></p>
        <h3>{html_escape(article.title)}</h3>
        <p class="tags">{html_escape(article.source_type)} | Hype: {html_escape(article.hype_level)}</p>
        <p>{html_escape(article.summary_en)}</p>
        <h4>Lietuviskai</h4>
        <p>{html_escape(article.summary_lt)}</p>
        <aside>
          <p><b>Praktiskai:</b> {html_escape(article.practical_takeaway)}</p>
          <p><b>Hype filtras:</b> {html_escape(article.hype_filter)}</p>
        </aside>
      </article>
            """
        )
    if not article_sections:
        article_sections.append(
            """
      <article>
        <h2>No high-quality updates today</h2>
        <p>The magazine skipped the news sections because the available feeds did not contain meaningful updates.</p>
      </article>
            """
        )

    whoop_section = ""
    if whoop_evidence:
        whoop_section = f"""
      <h2>WHOOP evidence corner</h2>
      <section class="note">
        <p class="kicker">{html_escape(whoop_evidence.topic)}</p>
        <h3>{html_escape(whoop_evidence.title)}</h3>
        <p>{html_escape(whoop_evidence.detail)}</p>
        <p><a href="{html_escape(whoop_evidence.url)}">Read evidence</a></p>
      </section>
        """

    book_sections = []
    for book in books:
        book_sections.append(
            f"""
      <article>
        <p class="kicker">{html_escape(book.book_type)} / {html_escape(book.author)}</p>
        <h3>{html_escape(book.title)}</h3>
        <p class="tags">{html_escape(book.length)} | Goodreads: {html_escape(book.goodreads_rating)}</p>
        <p>{html_escape(book.description_en)}</p>
        <aside><p><b>Why it may appeal:</b> {html_escape(book.why_it_may_appeal)}</p></aside>
        <p>{html_escape(book.summary_en)}</p>
        <h4>Lietuviskai</h4>
        <p>{html_escape(book.summary_lt)}</p>
      </article>
            """
        )

    content_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
  <head>
    <title>{html_escape(title)}</title>
    <link rel="stylesheet" type="text/css" href="styles.css"/>
  </head>
  <body>
    <section class="hero">
      {cover_img}
      <p class="kicker">Personal daily edition</p>
      <h1>Morning Magazine</h1>
      <p>{html_escape(cover_theme.get("label", "Balanced edition"))}. {html_escape(cover_theme.get("detail", ""))}</p>
      <p>{html_escape(format_date_en(run_date))} / Updated {html_escape(generated_at.strftime("%H:%M"))} {html_escape(timezone_name)}</p>
    </section>
    {whoop_section}
    {''.join(article_sections)}
    {epub_section("Save for later", save_for_later)}
    {epub_section("Savaitinis signalas", weekly_summary)}
    <h2>Book recommendations</h2>
    {''.join(book_sections)}
  </body>
</html>
"""

    nav_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
  <head>
    <title>{html_escape(title)} navigation</title>
  </head>
  <body>
    <nav epub:type="toc" id="toc">
      <h1>{html_escape(title)}</h1>
      <ol>
        <li><a href="content.xhtml">Read edition</a></li>
      </ol>
    </nav>
  </body>
</html>
"""

    package_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{html_escape(identifier)}</dc:identifier>
    <dc:title>{html_escape(title)}</dc:title>
    <dc:language>en</dc:language>
    <dc:creator>Morning Magazine</dc:creator>
    <meta property="dcterms:modified">{modified}</meta>
    {cover_meta}
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
    <item id="style" href="styles.css" media-type="text/css"/>
    {cover_item}
  </manifest>
  <spine>
    <itemref idref="content"/>
  </spine>
</package>
"""

    container_xml = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    styles_css = """
body {
  font-family: Georgia, serif;
  line-height: 1.55;
  color: #20242a;
}
h1, h2, h3, h4 {
  color: #14213d;
}
.hero {
  border-bottom: 2px solid #c8b99a;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
}
.cover {
  display: block;
  max-width: 100%;
  margin-bottom: 1rem;
}
.kicker, .tags {
  color: #5f6570;
  font-size: .9rem;
  font-family: Arial, sans-serif;
}
article, .note {
  border-bottom: 1px solid #c8b99a;
  margin: 1.1rem 0;
  padding-bottom: 1rem;
}
aside {
  background: #f7f1e6;
  border-left: 4px solid #b7853b;
  padding: .2rem .8rem;
}
"""

    epub_path = output_dir / epub_name
    with zipfile.ZipFile(epub_path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/package.opf", package_opf, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/content.xhtml", content_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/styles.css", styles_css, compress_type=zipfile.ZIP_DEFLATED)
        if COVER_IMAGE.exists():
            archive.write(COVER_IMAGE, "OEBPS/images/cover.png", compress_type=zipfile.ZIP_DEFLATED)


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

    pdfmetrics.registerFont(TTFont("MorningSans", regular))
    pdfmetrics.registerFont(TTFont("MorningSans-Bold", bold))
    pdfmetrics.registerFont(TTFont("MorningSans-Italic", italic))
    return "MorningSans", "MorningSans-Bold", "MorningSans-Italic"


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
    canvas.drawString(MARGIN_X, 6.4 * mm, "Morning Magazine | English + Lietuviškai")
    canvas.drawRightString(PAGE_W - MARGIN_X, 6.4 * mm, f"Page {doc.page}")
    canvas.restoreState()


def make_styles(fonts: tuple[str, str, str]):
    regular, bold, italic = fonts
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Masthead", parent=styles["Normal"], fontName=bold, fontSize=27, leading=30, textColor=INK, alignment=TA_CENTER, spaceAfter=3))
    styles.add(ParagraphStyle("Kicker", parent=styles["Normal"], fontName=bold, fontSize=9.2, leading=11, textColor=GOLD, alignment=TA_CENTER, spaceAfter=5))
    styles.add(ParagraphStyle("Deck", parent=styles["Normal"], fontName=italic, fontSize=11.6, leading=15, textColor=MUTED, alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle("Lead", parent=styles["Normal"], fontName=regular, fontSize=11.6, leading=16.2, textColor=INK, alignment=TA_LEFT, spaceAfter=10))
    styles.add(ParagraphStyle("SectionLabel", parent=styles["Normal"], fontName=bold, fontSize=8.4, leading=10, textColor=GOLD, spaceAfter=2))
    styles.add(ParagraphStyle("ColumnLabel", parent=styles["Normal"], fontName=bold, fontSize=8.4, leading=10, textColor=INK, spaceAfter=3))
    styles.add(ParagraphStyle("SectionTitle", parent=styles["Normal"], fontName=bold, fontSize=18, leading=21, textColor=INK, spaceAfter=7))
    styles.add(ParagraphStyle("Headline", parent=styles["Normal"], fontName=bold, fontSize=16, leading=19, textColor=INK, spaceAfter=5))
    styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontName=regular, fontSize=11, leading=15.2, textColor=colors.HexColor("#20242A"), alignment=TA_LEFT, spaceAfter=7))
    styles.add(ParagraphStyle("BodyColumn", parent=styles["Normal"], fontName=regular, fontSize=9.8, leading=13.1, textColor=colors.HexColor("#20242A"), alignment=TA_LEFT, spaceAfter=0))
    styles.add(ParagraphStyle("LithuanianColumn", parent=styles["Normal"], fontName=regular, fontSize=9.8, leading=13.1, textColor=colors.HexColor("#2E3C5E"), alignment=TA_LEFT, spaceAfter=0))
    styles.add(ParagraphStyle("Lithuanian", parent=styles["Normal"], fontName=regular, fontSize=10.8, leading=15, textColor=colors.HexColor("#2E3C5E"), alignment=TA_LEFT, spaceAfter=7))
    styles.add(ParagraphStyle("Source", parent=styles["Normal"], fontName=regular, fontSize=8.8, leading=11.2, textColor=MUTED, spaceAfter=2))
    styles.add(ParagraphStyle("Insight", parent=styles["Normal"], fontName=regular, fontSize=9.4, leading=12.4, textColor=colors.HexColor("#31446C"), leftIndent=7, spaceBefore=3, spaceAfter=4))
    styles.add(ParagraphStyle("Small", parent=styles["Normal"], fontName=regular, fontSize=8.6, leading=11, textColor=MUTED, alignment=TA_CENTER))
    styles.add(ParagraphStyle("IndexItem", parent=styles["Normal"], fontName=regular, fontSize=9.6, leading=12.6, textColor=INK))
    return styles


def source_link(label: str, url: str) -> str:
    return f'<a href="{html_escape(url)}" color="#1F4D78">{html_escape(label)}</a>'


def article_block(article: Article, timezone_name: str, styles):
    article_url = source_link("Skaityti visą straipsnį", article.url)
    column_gap = 8
    column_w = (CONTENT_W - column_gap) / 2
    summary_table = Table(
        [
            [
                Paragraph("English", styles["ColumnLabel"]),
                Paragraph("Lietuviskai", styles["ColumnLabel"]),
            ],
            [
                Paragraph(html_escape(article.summary_en), styles["BodyColumn"]),
                Paragraph(html_escape(article.summary_lt), styles["LithuanianColumn"]),
            ],
        ],
        colWidths=[column_w, column_w],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SOFT_BLUE),
                ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#FFFAF0")),
                ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#F3F7FF")),
                ("BOX", (0, 0), (-1, -1), 0.35, RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#E2D6BD")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return KeepTogether(
        [
            Spacer(1, 8),
            Table(
                [[Paragraph(html_escape(article.topic).upper(), styles["SectionLabel"])]],
                colWidths=[CONTENT_W],
                style=[
                    ("LINEABOVE", (0, 0), (-1, 0), 0.8, RULE),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
                ],
            ),
            Paragraph(html_escape(article.title), styles["Headline"]),
            Paragraph(
                f"<b>Publikavo:</b> {html_escape(article.source)} &nbsp; <b>Publikuota:</b> {html_escape(iso_to_local(article.published, timezone_name))} &nbsp; {article_url}",
                styles["Source"],
            ),
            Paragraph(
                f"<b>Source type:</b> {html_escape(article.source_type)} &nbsp; <b>Hype:</b> {html_escape(article.hype_level)}",
                styles["Source"],
            ),
            summary_table,
            Spacer(1, 4),
            Paragraph(f"<b>Praktiškai:</b> {html_escape(article.practical_takeaway)}", styles["Insight"]),
            Paragraph(f"<b>Hype filtras:</b> {html_escape(article.hype_filter)}", styles["Insight"]),
        ]
    )


def notes_block(title: str, notes: list[DigestNote], styles):
    if not notes:
        return []
    rows = []
    for note in notes:
        link = source_link("Source", note.url) if note.url else ""
        rows.append(
            [
                Paragraph(html_escape(note.topic or "Signal"), styles["SectionLabel"]),
                Paragraph(
                    f"<b>{html_escape(note.title)}</b><br/>{html_escape(note.detail)}"
                    + (f"<br/>{link}" if link else ""),
                    styles["IndexItem"],
                ),
            ]
        )
    table = Table(rows, colWidths=[34 * mm, CONTENT_W - 34 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFAF0")),
                ("BOX", (0, 0), (-1, -1), 0.35, RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#E2D6BD")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return [
        Spacer(1, 8),
        KeepTogether(
            [
                Paragraph(title, styles["SectionTitle"]),
                table,
            ]
        ),
        Spacer(1, 8),
    ]

def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def local_book_cover(output_dir: Path, book: BookRecommendation) -> Path | None:
    if not book.cover_url:
        return None
    cover_dir = output_dir / "assets" / "book-covers"
    cover_dir.mkdir(parents=True, exist_ok=True)
    cover_path = cover_dir / f"{slugify(book.title + '-' + book.author)}.jpg"
    if not cover_path.exists():
        try:
            data = fetch_url(book.cover_url, timeout=12)
            if len(data) > 800:
                cover_path.write_bytes(data)
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
    return cover_path if cover_path.exists() else None


def book_block(book: BookRecommendation, styles, output_dir: Path):
    cover_path = local_book_cover(output_dir, book)
    cover_cell = ""
    if cover_path:
        try:
            cover_cell = Image(str(cover_path), width=26 * mm, height=39 * mm)
        except Exception:
            cover_cell = ""

    details = [
        Paragraph(html_escape(f"{book.title} - {book.author}"), styles["Headline"]),
        Paragraph(
            f"<b>{html_escape(book.book_type)}</b> | {html_escape(book.length)} | Goodreads: {html_escape(book.goodreads_rating)}",
            styles["Source"],
        ),
        Paragraph(html_escape(book.description_en), styles["Body"]),
        Paragraph(f"<b>Why it may appeal:</b> {html_escape(book.why_it_may_appeal)}", styles["Insight"]),
    ]
    book_table = Table([[cover_cell, details]], colWidths=[31 * mm, CONTENT_W - 31 * mm])
    book_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return KeepTogether(
        [
            Spacer(1, 8),
            Table(
                [[Paragraph("BOOKS SECTION", styles["SectionLabel"])]],
                colWidths=[CONTENT_W],
                style=[
                    ("LINEABOVE", (0, 0), (-1, 0), 0.8, RULE),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
                ],
            ),
            book_table,
            Paragraph(html_escape(book.summary_en), styles["Body"]),
            Paragraph("<b>Lietuviškai</b>", styles["Source"]),
            Paragraph(html_escape(book.summary_lt), styles["Lithuanian"]),
        ]
    )


def build_pdf(
    output_dir: Path,
    articles: list[Article],
    books: list[BookRecommendation],
    daily_highlights: list[DigestNote],
    save_for_later: list[DigestNote],
    weekly_summary: list[DigestNote],
    whoop_evidence: DigestNote | None,
    cover_theme: dict[str, str],
    run_date: date,
    generated_at: datetime,
    timezone_name: str,
    pdf_name: str,
) -> None:
    fonts = register_fonts()
    styles = make_styles(fonts)

    pdf_path = output_dir / pdf_name
    doc = BaseDocTemplate(
        str(pdf_path),
        pagesize=(PAGE_W, PAGE_H),
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=f"Morning Magazine - {run_date.isoformat()}",
        author="Morning Magazine",
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
    story.append(Paragraph("PERSONAL DAILY EDITION", styles["Kicker"]))
    story.append(Paragraph("MORNING MAGAZINE", styles["Masthead"]))
    story.append(
        Paragraph(
            f"{html_escape(cover_theme.get('label', 'Balanced edition'))}. {html_escape(cover_theme.get('detail', ''))}",
            styles["Deck"],
        )
    )
    story.append(Paragraph(f"English summaries with Lietuviškai translations | {html_escape(format_date_en(run_date))}", styles["Deck"]))

    if COVER_IMAGE.exists():
        img = Image(str(COVER_IMAGE), width=CONTENT_W, height=CONTENT_W * 0.50)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(html_escape(cover_theme.get("detail", "AI, brain research, healthspan and a morning reading ritual.")), styles["Small"]))
        story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "This magazine reads selected source articles, skips weak updates, and gives each item a short English summary followed by a complete Lithuanian translation.",
            styles["Lead"],
        )
    )
    generated_time = generated_at.strftime("%H:%M")
    stats = Table(
        [
            [
                Paragraph(f"<b>{len(articles)}</b><br/>news articles", styles["IndexItem"]),
                Paragraph(f"<b>{len(books)}</b><br/>book picks", styles["IndexItem"]),
                Paragraph("<b>06:00</b><br/>scheduled", styles["IndexItem"]),
                Paragraph(f"<b>{html_escape(generated_time)}</b><br/>updated {html_escape(timezone_name)}", styles["IndexItem"]),
            ]
        ],
        colWidths=[CONTENT_W / 4] * 4,
    )
    stats.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D4E2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#DCE4EE")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(stats)
    story.append(Spacer(1, 10))

    if whoop_evidence:
        story.extend(notes_block("WHOOP evidence corner", [whoop_evidence], styles))
    story.extend(notes_block("Save for later", save_for_later, styles))
    story.extend(notes_block("Savaitinis signalas", weekly_summary, styles))

    if articles:
        index_rows = []
        for idx, article in enumerate(articles, 1):
            index_rows.append(
                [
                    Paragraph(f"<b>{idx}</b>", styles["IndexItem"]),
                    Paragraph(html_escape(f"{article.topic}: {article.title}"), styles["IndexItem"]),
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
        story.append(Paragraph("No high-quality news updates were selected today.", styles["Body"]))

    story.append(PageBreak())
    story.append(Paragraph("Books Section", styles["SectionTitle"]))
    for book in books:
        story.append(book_block(book, styles, output_dir))

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>Editor's note.</b> This is an automated magazine generated from source material. Read the original source before making important medical, financial or professional decisions.",
            styles["Body"],
        )
    )

    doc.build(story)


def write_data(
    output_dir: Path,
    articles: list[Article],
    books: list[BookRecommendation],
    daily_highlights: list[DigestNote],
    save_for_later: list[DigestNote],
    weekly_summary: list[DigestNote],
    whoop_evidence: DigestNote | None,
    cover_theme: dict[str, str],
    errors: list[str],
    run_date: date,
    generated_at: datetime,
    timezone_name: str,
    epub_name: str,
) -> None:
    payload = {
        "title": "Morning Magazine",
        "generated_for": run_date.isoformat(),
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "timezone": timezone_name,
        "language": "en-lt",
        "summary_engine": "openai" if os.getenv("OPENAI_API_KEY") else "extractive-fallback",
        "articles": [asdict(article) for article in articles],
        "book_recommendations": [asdict(book) for book in books],
        "daily_highlights": [asdict(note) for note in daily_highlights],
        "save_for_later": [asdict(note) for note in save_for_later],
        "weekly_summary": [asdict(note) for note in weekly_summary],
        "whoop_evidence": asdict(whoop_evidence) if whoop_evidence else None,
        "cover_theme": cover_theme,
        "archive": {
            "date": run_date.isoformat(),
            "json": f"archive/{run_date.isoformat()}/ryto-signalas.json",
            "pdf": f"archive/{run_date.isoformat()}/morning-magazine-{run_date.isoformat()}.pdf",
            "epub": f"archive/{run_date.isoformat()}/{epub_name}",
            "html": f"archive/{run_date.isoformat()}/index.html",
        },
        "feed_errors": errors,
    }
    (output_dir / "ryto-signalas.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the personal Morning Magazine.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for the generated website, PDF, and EPUB.")
    parser.add_argument("--timezone", default=os.getenv("NEWS_TIMEZONE", DEFAULT_TIMEZONE), help="IANA timezone for dates.")
    parser.add_argument("--date", help="Publication date in YYYY-MM-DD format. Defaults to today in the selected timezone.")
    parser.add_argument("--per-topic", type=int, default=2, help="Maximum number of news stories to select per topic.")
    parser.add_argument("--book-count", type=int, default=3, help="Book recommendation count; daily editions publish exactly 3.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    timezone_name = args.timezone
    tz = ZoneInfo(timezone_name)
    run_date = date.fromisoformat(args.date) if args.date else datetime.now(tz).date()
    generated_at = datetime.now(tz).replace(microsecond=0)
    output_dir = Path(args.output_dir).resolve()

    prepare_output_dir(output_dir)
    restore_published_archive(output_dir)
    excluded_article_keys = load_previous_article_keys(output_dir, run_date)
    articles, errors = collect_articles(
        run_date,
        generated_at,
        timezone_name,
        per_topic=max(1, args.per_topic),
        excluded_keys=excluded_article_keys,
    )
    books = select_book_recommendations(run_date, output_dir, count=args.book_count)
    daily_highlights = build_daily_highlights(articles)
    save_for_later = select_save_for_later(articles)
    weekly_summary = build_weekly_summary(run_date, articles)
    whoop_evidence = select_whoop_evidence(articles)
    cover_theme = build_cover_theme(articles)
    pdf_name = f"morning-magazine-{run_date.isoformat()}.pdf"
    epub_name = f"morning-magazine-{run_date.isoformat()}.epub"
    render_html(
        output_dir,
        articles,
        books,
        daily_highlights,
        save_for_later,
        weekly_summary,
        whoop_evidence,
        cover_theme,
        run_date,
        generated_at,
        timezone_name,
        pdf_name,
        epub_name,
        errors,
    )
    build_pdf(
        output_dir,
        articles,
        books,
        daily_highlights,
        save_for_later,
        weekly_summary,
        whoop_evidence,
        cover_theme,
        run_date,
        generated_at,
        timezone_name,
        pdf_name,
    )
    build_epub(
        output_dir,
        articles,
        books,
        daily_highlights,
        save_for_later,
        weekly_summary,
        whoop_evidence,
        cover_theme,
        run_date,
        generated_at,
        timezone_name,
        epub_name,
    )
    shutil.copy2(output_dir / pdf_name, output_dir / "latest.pdf")
    shutil.copy2(output_dir / epub_name, output_dir / "latest.epub")
    write_data(
        output_dir,
        articles,
        books,
        daily_highlights,
        save_for_later,
        weekly_summary,
        whoop_evidence,
        cover_theme,
        errors,
        run_date,
        generated_at,
        timezone_name,
        epub_name,
    )
    archive_current_edition(output_dir, run_date, pdf_name, epub_name, generated_at)

    print(f"Generated {output_dir / 'index.html'}")
    print(f"Generated {output_dir / pdf_name}")
    print(f"Generated {output_dir / epub_name}")


if __name__ == "__main__":
    main()
