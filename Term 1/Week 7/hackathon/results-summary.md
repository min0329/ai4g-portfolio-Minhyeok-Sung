# Hornet Check NL: what happened, and what the results mean

## The task
The model looks at a photo of an insect and picks one of **5 classes**: Asian hornet (invasive), European hornet, wasp, hornet hoverfly and honeybee. It is an image **classification** model, trained in Roboflow (DINOv3 Base).

## The data
- **1,215 photos** from iNaturalist: research-grade observations (confirmed by other users) taken **in the Netherlands**. About half of the candidate observations were just over the border in Belgium or Germany, and we filtered those out.
- At most 5 photos per photographer, so a few people don't dominate the data.
- Only open licences (CC0, CC BY, CC BY-NC, CC BY-SA). Every photo's author and licence is in `attribution.csv`.
- **125 photos (`unseen/`)** were never uploaded to Roboflow. We keep them for testing on images the model has never seen.

## Version 1: trained on all photos
| | Result |
|---|---|
| Correct on the test set | 77 of 109 (≈71 %) |
| F1 / precision / recall (all classes) | 73.5 % / 75.7 % / 72.0 % |
| Asian hornet F1 / precision / recall | 58.5 % / 57.1 % / 60.0 % |

**Problem:** the Asian hornet, the most important class, was the weakest. The model often called wasps "Asian hornet" (5 false alarms), and mistook Asian hornets for European hornets (3 times, which would mean a nest goes unreported).

**Why:** when we looked at the training photos, **22 % of the Asian hornet photos showed no usable insect.** They showed nests, traps, phone screenshots, people, or an insect too small to see. The other classes had the same problem, to a lesser degree.

## Cleaning the data
We checked all 1,094 training photos by eye and **removed 207** (nests, traps, beehives, swarms, screenshots, photos with people, insect not visible). The full list with reasons is in `removed_in_v2.csv`.

| Class | v1 | v2 |
|---|---|---|
| asian_hornet | 219 | 170 |
| european_hornet | 220 | 170 |
| wasp | 218 | 197 |
| honeybee | 220 | 168 |
| hornet_hoverfly | 217 | 182 |

## Version 2: trained on the cleaned photos
| | v1 | v2 |
|---|---|---|
| F1 (all classes) | 73.5 % | 73.4 % |
| **Precision** (all classes) | 75.7 % | **84.2 %** |
| Recall (all classes) | 72.0 % | 67.2 % |
| **Asian hornet F1** | 58.5 % | **66.7 %** |
| **Asian hornet precision** | 57.1 % | **81.8 %** |
| Asian hornet recall | 60.0 % | 56.2 % |
| Wasp predicted as Asian hornet (false alarm) | 5 | **1** |
| Asian hornet predicted as European hornet (missed nest) | 3 | **1** |
| **Confidently wrong answers** | 25 of 109 (23 %) | **12 of 94 (13 %)** |

### What the words mean
- **Precision:** when the model *says* "Asian hornet", how often is it right? v2 went from 57 % to **82 %**, so there are far fewer false alarms.
- **Recall:** of all the real Asian hornets, how many does the model find? Both versions find about **half to 60 %**.
- **F1:** one number that combines precision and recall.
- **Confidence threshold:** below this level of certainty the model gives no answer. In the confusion matrix those cases appear as "False Neg.".

### The main conclusion
v2 is **not right more often**, but it is **much less often confidently wrong**. Most of its mistakes are now cases where it is *unsure* rather than cases where it gives a wrong answer with confidence. That is much safer for users, and it is why the app says *"I'm not sure, check it yourself"* at low confidence and *"I don't know, report it anyway"* when confidence is very low.

**One sentence for the presentation:** *"By removing 207 bad photos, we halved the confident mistakes (23 % → 13 %), and the most dangerous error, an Asian hornet mistaken for a European hornet, dropped from 3 to 1."*

## Honest limits (for the data card)
- The model still **misses about half of Asian hornets** when it is unsure, so the app tells users to report anything doubtful.
- The test sets are small (about 16–20 Asian hornets), so the numbers can move a few percent by chance.
- v1 and v2 were tested on different test sets, so the comparison is indicative, not exact. The `unseen/` photos are the same for both and can be used for a fair comparison.
- The photos are mostly sharp close-ups taken by nature enthusiasts. Real users, such as beekeepers photographing a flying hornet at the hive, will take blurrier photos.
- There are only 5 classes. Any other insect (bumblebee, a fly, the giant woodwasp) will still be forced into one of the 5, which is why the "I don't know" threshold matters.
- **Next step to improve it:** more, and more varied, Asian hornet photos. This class had the fewest available in the Netherlands (429).
