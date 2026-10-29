# Data card and ethical reflection: Hornet Check NL

## 1. The dataset
| | |
|---|---|
| **What** | Photos of 5 insects: Asian hornet (*Vespa velutina*), European hornet (*Vespa crabro*), wasp (*Vespula vulgaris* / *germanica*), hornet hoverfly (*Volucella zonaria*) and honeybee (*Apis mellifera*). |
| **Source** | iNaturalist open data (the public export on AWS). Only **research-grade** observations, meaning the species was confirmed by other users. |
| **Where** | **The Netherlands only.** We first filtered with a bounding box, then checked each location against the nearest town. That removed about half the observations, which were in Belgium or Germany. |
| **When** | Observed 2006–2026. Most photos are from 2021–2026, and the Asian hornet photos start in 2018. |
| **How many** | 1,215 downloaded. After cleaning: **887 training photos** (asian_hornet 170, european_hornet 170, wasp 197, honeybee 168, hornet_hoverfly 182), plus **121 "unseen" photos** that were never uploaded to Roboflow. |
| **Labels** | The species name from iNaturalist is the label, with one folder per class. Roboflow uses the folder names as classes, so we drew no boxes ourselves. |
| **Selection** | Random, with **at most 5 photos per photographer** so that a few people don't dominate the data. 539 different photographers in total. One photo per observation. |
| **Licences** | Only open licences: CC BY-NC (839), CC BY (93), CC0 (49), CC BY-NC-SA (18), CC BY-SA (9). Photos with "no derivatives" (ND) licences were left out, because training resizes them. Each photo's author and licence is in `attribution.csv`. This is a non-commercial student project. |
| **Roboflow version** | Split 70/20/10, auto-orient, resize to 224×224, augmentation ×3 (horizontal flip, rotation ±15°, brightness ±20 %, blur up to 1 px). Model: DINOv3 Base. |

## 2. What we changed, v1 → v2
In v1, the Asian hornet scored worst (F1 58.5 %). When we looked at the photos, **22 % of the Asian hornet photos showed no usable insect**: nests, traps, phone screenshots, people, or an insect too small to see. We checked **all 1,094 training photos by eye and removed 207** (listed with reasons in `removed_in_v2.csv`).

| Test set | v1 | v2 |
|---|---|---|
| Precision / recall / F1 (all) | 75.7 / 72.0 / 73.5 % | 84.2 / 67.2 / 73.4 % |
| Asian hornet precision / recall / F1 | 57.1 / 60.0 / 58.5 % | 81.8 / 56.2 / 66.7 % |
| Confidently wrong answers | 25 of 109 (23 %) | 12 of 94 (13 %) |
| Wasp → "Asian hornet" | 5 | 1 |
| Asian hornet → "European hornet" | 3 | 1 |

## 3. Limitations and failure modes
- **It misses about half of Asian hornets** when it is unsure (recall 56 %). Most misses are "unsure" cases, not wrong answers.
- **Small test sets** (about 16–20 Asian hornets), so the numbers can shift a few percent by chance. v1 and v2 were tested on different test sets, so the comparison is indicative, not exact.
- **Photo style bias:** most photos are sharp close-ups taken by nature enthusiasts, often of insects sitting still or dead. Real users, for example beekeepers photographing a hornet hovering at the hive, will take blurrier photos from further away. We expect lower accuracy there.
- **Only 5 classes.** Any other insect (bumblebee, giant woodwasp, a fly) still gets forced into one of the 5. The "I don't know" threshold catches some of these, but not all.
- **Only the Netherlands.** Look-alike species and photo conditions differ elsewhere.
- **Few Asian hornet photos:** only 429 Dutch ones existed to choose from, against 800–2,500 for the other insects.

## 4. Ethical reflection: risk → consequence → what we did / would do next
| Risk | Consequence | What we did | Next step |
|---|---|---|---|
| **Missed Asian hornet** (false negative) | The nest isn't reported. New queens spread and more bee colonies are lost. | Below 45 % the app says "I don't know, report it anyway". The footer warns that it misses about half of the hornets when unsure. | More Asian hornet photos, especially flying and at the hive. |
| **Native insect called "Asian hornet"** (false positive) | Someone kills a useful European hornet or wasp, or the gemeente wastes time on a false report. | The clear warning only appears at ≥ 70 % confidence. The app shows the second guess and how to tell the species apart. Experts on waarneming.nl check every report. | Track the false-alarm rate on real user photos. |
| **People approaching nests** | Stings, which are dangerous for people with allergies. | The advice says to keep a few metres away and never to destroy a nest yourself. | Add an emergency note for allergic reactions. |
| **Over-trust** | Users treat the app as an expert and stop looking for themselves. | Every answer shows the confidence, and the footer says it is "a helper, not an official identification". | User test with beekeepers. |
| **Bias in the data** | Worse results for blurry photos, flying insects or unusual angles, so exactly the beekeeper situation. | Stated as a limit here and in the README. | Collect our own photos at an apiary. |
| **Photo licences and privacy** | Using other people's photos without credit. Photos with people in them. | Only open licences, ND left out, every author credited in `attribution.csv`, photos with people removed in v2. | — |
| **Dependence on Roboflow** | If the free plan or credits run out, the app stops working. | The API key stays private (Streamlit secrets, not in the repo). | Export the model to run offline. |
