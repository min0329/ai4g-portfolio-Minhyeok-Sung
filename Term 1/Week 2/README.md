# Term 1 - Week 2: Loops & Functions

---

## 1. Homework & workshop assignments -> [`homework/`](homework/)

**What was the assignment?**

**What did I hand in?**
_List the files, or link to them. Notebook exports, screenshots, scripts._

**What did I find difficult, and how did I solve it?**

### Checklist
- [ ] My workshop / homework files are in `homework/`
- [ ] Everything runs without errors, or I explained what does not and why

---


## 2. Hackathon prototype -> [`hackathon/`](hackathon/)

> Your tool and your SDG for this hackathon are announced at the **start of Friday's class**.
> Write them down here once you know them.

**Project title:** NutriPlan AI

**My pair partner:** Benjamin

**Tool we had to use:** N8N

**SDG we had to address:** SDG 3 - Good Health & Well-being. 
: NutriPlan AI supports healthier lifestyles by helping people plan balanced meals, make informed food choices, and reduce the stress associated with daily meal preparation. Although it does not replace professional nutritional advice, it provides an accessible tool that encourages healthier everyday habits.

**What problem does it solve, and for whom?**
: NutriPlan AI solves the problem of difficulty planning healthy, affordable, and practical meals. Many people struggle to choose what to cook because of limited time, budget, dietary preferences, or a lack of meal-planning knowledge. Our target audience is busy individuals including international students and workers as well as families who want to improve their eating habits and save time when preparing meals.

Most European adults do not meet dietary guidelines. In 2019, one in three EU residents (33%) consumed no fruit or vegetables on a daily basis, and only 12% ate the recommended five or more portions daily (Eurostat, 2022). In the Netherlands, despite improvements, only 29% of adults meet the vegetable guideline and approximately 20% meet the fruit guideline (RIVM DNFCS 2019–2021). More than half of the EU population is overweight (50.6%), and 16.3% are obese (Eurostat, 2024; Eurostat, 2026).

**What did you build?**
: We built NutriPlan AI, an automated meal-planning assistant using n8n. Users submit their email, budget, dietary preferences, allergies, available ingredients, and cooking time through an online form. The AI generates a personalized 7-day meal plan with preparation instructions and a categorized shopping list, which can be sent to the user by email and recorded in Google Sheets.

**Link to the live thing (if any):**
https://drive.google.com/file/d/1d4ciwxrA_CrR_wb6s6U4cQ7Va9pN5NWQ/view?usp=sharing

Database link: https://docs.google.com/spreadsheets/d/1CowcwdtQwRkZ9L6BGVhFSwG9ZzUBqxyOWgztkfIxRUw/edit?usp=sharing

**How do I run it?**
: You execute the workflow and it runs in this order:
•⁠  ⁠Form pop-up asking for information
•⁠  ⁠AI writes a meal plan fitting to the users preferences
•⁠  ⁠The meal plan gets sent to the database
•⁠  ⁠2nd automation starts every day at 9AM
•⁠  ⁠Data gets collected from the database
•⁠  ⁠The day of the week is determined
•⁠  ⁠An email with a daily meal plan is sent to the user

**Who did what?**
Benjamin has created the automation workflows of NutriPlan through n8n platform and he was in charge of texting the prototype actively. Also, he worked on recording the demo.

Min came up with the NutriPlan idea and created basic logics of NutriPlan. And Min worked on presentation slides and general execution for the project.

**Ethical reflection - what are the risks of your tool? Who could it harm?**
: NutriPlan AI is designed to support people in planning healthier meals, but because it relates to health and nutrition, errors could have real consequences. For example, if the AI overlooks a user's allergy, recommends an unsuitable ingredient, or generates an unbalanced meal plan, the user could make an unhealthy decision. The automation could also be delayed, fail to send the email, or become unavailable, meaning users should not depend on it as their only source of nutritional guidance. I would trust NutriPlan AI for general meal inspiration and planning, but not for managing medical conditions, serious allergies, or specific dietary requirements. Users should always check ingredients, food labels, and nutritional suitability themselves. Automation should stop when a situation requires professional judgment, such as medical diets or complex health needs, and a qualified healthcare professional or dietitian should take over. This ensures that NutriPlan AI remains a supportive tool rather than replacing human responsibility and professional care.

### Checklist
- [ ] Prototype code (or export / workflow file) is in `hackathon/`
- [ ] This week's slides are in `hackathon/`
- [ ] The prototype actually runs, and I wrote down how to run it
- [ ] Ethical reflection written above

---

## 3. Presentation -> [`presentation/`](presentation/)

*Only fill this in for the week your group was selected to present. You need at least **one** of these across the whole term.*

- [ ] My group presented in this week
- [ ] Slides are in `presentation/`
- [ ] Proof of the live demo is in `presentation/` (recording, screenshots, or link)

**How did it go? What would I do differently next time?**

---

## 4. Reflection

**What is the most important thing I learned this week?**
: This week, I was surprised a lot by this new AI tool: n8n. I did not expect that there was such incredible tool that could automate a lot of things for our daily life.

**Where does this connect to "AI for Good"?**
:This project (NutriPlan) supports healthier everyday food choices through structured meal planning. It makes meal planning more accessible by considering time, budget, and preferences, and it may reduce decision-making stress around what to cook. But, it does not diagnose, treat medical conditions, or replace a dietitian or healthcare professional.

