# 🐝 Hornet Check NL

**Try it:** https://ai4g-portfolio-sambam-hornetcheck.streamlit.app

## Problem
The Asian hornet (*Vespa velutina*) is an invasive species that is spreading fast in the Netherlands. The first Dutch nest was found in 2017 (Dreischor, Zeeland). In 2024, **more than 2,500 nests** were reported via waarneming.nl, and the number grows about **5–6× per year** ([Zeegers, EIS Kenniscentrum Insecten, *Kijk op Exoten* 50, Sept. 2025](https://natuurtijdschriften.nl/pub/1031248/Exoten2025013003010.pdf)). It hunts honeybees and wild pollinators in front of their nests, which weakens bee colonies and threatens pollinators, and so the plants and crops that depend on them. Nests must be **reported early**, so the gemeente can remove them before new queens spread.
The catch is that most people can't tell it apart from the native **European hornet**, a **wasp** or the harmless **hornet hoverfly**. The result is missed reports, false alarms, and useful native insects getting killed.

## Users
**For:** beekeepers and bee enthusiasts in the Netherlands who see a large wasp-like insect and want to know whether to report it. They aren't insect experts, the insect may fly off quickly, and they only have a phone.
**Not for:** getting close to insects or nests (take the photo from a distance), destroying nests yourself (that's for professionals), official species identification (experts on waarneming.nl confirm reports), or use outside the Netherlands. The app only knows 5 insects.

## How it works
```
photo ──► Roboflow classification model ──► confidence rules (our code) ──► answer + advice
          5 classes: asian_hornet,          ≥ 70 %: clear answer             ⚠️ Asian hornet: report it (button
          european_hornet, wasp,            45–70 %: "probably X, check it"     to waarneming.nl) + keep away from nest
          hornet_hoverfly, honeybee         < 45 %: "I don't know,           ✅ native: leave it alone + how to tell
          + a confidence score each                  report it if in doubt"   🤔 / ❓ unsure: check it, or report anyway
```
1. **Input:** the user uploads a photo or takes one with the camera.
2. **Roboflow (the essential step):** our own classification model (DINOv3 Base, trained in Roboflow on 887 cleaned Dutch photos) returns a confidence score for each of the 5 insects. **Without it the app can't tell the look-alikes apart.**
3. **Rules (our code, `app.py`):** these turn the scores into a clear answer, a "check it yourself" warning or an "I don't know". The app also shows the model's second guess.
4. **Output:** the species, how sure the model is, why it matters, what to do, and (for the Asian hornet) a button to report it on waarneming.nl.

## Why AI, and not something simpler
An identification poster needs a calm, close look at small details (leg colour, abdomen bands), but in practice the insect is moving and the photo is blurry. General apps recognise thousands of species, but they don't tell you what to do next. Our model focuses on exactly these five look-alikes, gives a clear action, and **flags doubtful cases instead of guessing**.

## Data and results
1,215 research-grade iNaturalist photos taken in the Netherlands (open licences, credited in `attribution.csv`). After cleaning, 887 are used for training and 121 are kept apart as never-seen test photos.
**v1 → v2:** removing 207 bad photos (nests, traps, screenshots, insect not visible) halved the confident mistakes, **from 23 % to 13 %**. When v2 says "Asian hornet" it is right **82 %** of the time (v1: 57 %). It still misses about half of Asian hornets when unsure, which is why the app says "report it if in doubt". Details: [`DATA_CARD.md`](DATA_CARD.md) · [`results-summary.md`](results-summary.md).

## Run it
Online: https://ai4g-portfolio-sambam-hornetcheck.streamlit.app (no install needed).
Locally:
```bash
pip install streamlit requests pillow
streamlit run app.py
```
The app opens in your browser. Paste your Roboflow private API key in the sidebar; the model ID `hornet-checkv2/1` is filled in already. Optionally, put both in `.streamlit/secrets.toml` (see the `.example` file).
