# Term 1 - Week 7: Computer Vision
 
---
 
## 1. Homework & workshop assignments -> [`homework/`](homework/)
 
**What was the assignment?**
 
**What did I hand in?** _List the files, or link to them. Notebook exports, screenshots, scripts._
 
**What did I find difficult, and how did I solve it?**
 
### Checklist - [ ] My workshop / homework files are in `homework/` - [ ] Everything runs without errors, or I explained what does not and why
 
---
 
 
## 2. Hackathon prototype -> [`hackathon/`](hackathon/)
 
**Project title:** Hornet Check NL
 
**My pair partner:** Sam Kempers
 
**Tool we had to use:** Roboflow
 
**SDG we had to address:** 15 — Life on Land (target 15.8: invasive alien species, and 15.5: biodiversity loss)
 
**What problem does it solve, and for whom?** Beekeepers and bee enthusiasts in the Netherlands who spot a big wasp-like insect and need to know if it's the invasive Asian hornet. This hornet hunts honeybees and wild pollinators, and its nests must be reported early so an expert can remove it. More than 2,500 nests were reported in 2024, and the number grows 5–6 times a year. Most people can't tell it apart from the native European hornet, wasps or the harmless hornet hoverfly, which leads to missed reports, false alarms and useful and important insects getting killed.
 
**What did you build?** A web app where you upload or take a photo of an insect. Our own Roboflow classification model (trained on 887 cleaned Dutch iNaturalist photos) says which of 5 look-alikes it is and how sure it is. The app then tells you what to do: a warning and a report button for waarneming.nl if it's an Asian hornet, "leave it alone" for native insects, and "check it yourself" or "I don't know, report it if in doubt" when the model is unsure.
 
**Link to the live thing (if any):** App: https://ai4g-portfolio-sambam-hornetcheck.streamlit.app · Demo video: [video link]
 
**How do I run it?** Open the app link above, no install needed. An API key is needed.
 
**Who did what?** We brainstormed together on our idea for the hackathon. With the help of AI we scraped images from the internet. Sam trained the model, removed pictures with AI for improvements of quality from the model. Sam provided a website where the user can upload images to see what species they've found. Sam will make the demo video. Min contributed to making the PowerPoint
 
**Ethical reflection - what are the risks of your tool? Who could it harm?** The first risk is that the app invites people to get closer to insects. To take a good photo, someone might walk up to a hornet, a bee or a nest. They could get stung, which is dangerous for people with allergies, or they could disturb the very animals we want to protect. We don’t want anyone to harm or interfere with bees or any other species, so the app tells people to keep a few meters away, to take the photo from a distance, and never to touch or remove a nest themselves.
 
 
### Checklist - [x] Prototype code (or export / workflow file) is in `hackathon/` - [x] This week's slides are in `hackathon/` - [x] The prototype actually runs, and I wrote down how to run it - [x] Ethical reflection written above
 
---
 
## 3. Presentation -> [`presentation/`](presentation/)
 
*Only fill this in for the week your group was selected to present. You need at least **one** of these across the whole term.*
 
- [ ] My group presented in this week - [ ] Slides are in `presentation/` - [ ] Proof of the live demo is in `presentation/` (recording, screenshots, or link)
 
**How did it go? What would I do differently next time?**
 
---
 
## 4. Reflection
 
**What is the most important thing I learned this week?** That it is important to have a good dataset, without good data you cannot have proper results.
 
**Where does this connect to "AI for Good"?** Most importantly, people don’t know what species they are looking at. Right now, not everyone in the Netherlands knows about this new invasive species or the damage it can do. Our app helps users identify the insect they have found and tells them what to do next. That is why it fits AI for Good: we use AI to turn a quick photo into action that protects bees, pollinators and biodiversity (SDG 15), while being honest about when the model is unsure.
