# Term 1 - Week 6: Language Models

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

**Project title:**\
Live Sentiment for ChatGPT, Claude and Gemini

**My pair partner:**\
Jalie Vermeegen
\
**Tool we had to use:**
A pre-trained Hugging Face transformer, run locally from Python: `cardiffnlp/twitter-xlm-roberta-base-sentiment`. Streamlit provides the dashboard and SQLite stores the collected items and predictions. 

See [The hackaton map](https://github.com/JiwiKiwi/AI-For-Good-JalieVermeegen/tree/main/Term%201/Week%206/hackathon/Hackaton%206) for the full hackaton files

**Demo video:** [Demo](https://www.youtube.com/watch?v=9hcIeNFz49A) Wish I had more time to make a better demo video, I did not explain everything properly so sorry about that

# 1.SDG we had to address:
SDG 9: Industry, Innovation and Infrastructure, especially target 9.5, which includes encouraging innovation and improving technological capabilities. Our project focuses on how people respond to AI assistants as digital innovations, including everyday experiences, updates and broader opinions about AI. The dashboard helps product analysts identify changes in sentiment, inspect recurring words and read the original messages. Their decision is which recurring issues need further investigation by the product or communications team.

Innovation is not a single launch but a cycle: a company releases an update, people use it, and their experiences should flow back into the next improvement. For AI assistants this cycle is unusually fast, since models change every few weeks and reach hundreds of millions of people, while the feedback is scattered across thousands of posts, comments and reviews. Our dashboard strengthens the step where public reactions are turned into something a product team can act on. 

For example, if several negative messages mention incorrect answers, the analyst can check the context and pass relevant examples to the product team for testing. This supports a feedback loop: people’s experiences help teams investigate problems and guide improvements. OpenAI’s rollback of a GPT-4o update shows how feedback can influence an AI product [2].
Our setup runs locally without a paid sentiment API or subscription, making it possible for smaller teams to adapt it to their own products. It is mainly English for now, but more languages can be added and tested. Our contribution to target 9.5 is indirect: supporting the evaluation of digital innovations. We do not measure research spending or prove that products improve. Because most messages come from Bluesky, the results are signals for investigation, not everyone’s opinion about AI.


# 2. What problem does it solve, and for whom?
Our intended users are ***product and communications analysts*** at OpenAI, Anthropic and Google who want to understand how people talk about ChatGPT, Claude and Gemini. Other product analysts can also use the dashboard to follow public reactions to competing AI assistants and snoop on the stuff they did right or wrong. For instance, Elon is a fictional analyst in the ChatGPT team at OpenAI. He follows public discussions to see whether reactions are becoming more positive or negative and reads the messages behind these changes. These discussions can include excitement about useful features, frustration with answers, concerns about privacy or jobs, and opinions about AI in general.

The dashboard helps Elon decide which topics need further investigation and should be brought to the product or communications team. For example, if he finds repeated concerns about privacy, he can recommend that the communications team review whether its explanations are clear enough. A good example of a real trend that popped up was on *Bluesky*, where people who are proud that they never used AI and basically posted "Retweet if you've never had a tab open of ChatGPT". Tracking trends like these is also important to be able to take actions.

Continuously collecting new messages helps Elon follow discussions while they are developing. News, announcements or widely shared posts can change the conversation within hours. A current overview helps him decide whether a topic needs attention that day or can be included in a later report.  The dashboard shows sentiment in the public messages we collect. It does not represent everyone's opinion about AI, and a danger is that a negative message mentioning ChatGPT does not always express a negative opinion about ChatGPT itself.

Manually monitoring reactions across several platforms becomes time-consuming as the number of posts and reviews grows[1]. The volume of text across digital platforms can overwhelm human teams, this is where sentiment analysis can help organisations monitor reactions to their products. This allows analysts to identify periods worth investigating without first reading every collected item individually. Manual review remains necessary to understand the context and check whether the model’s classifications are correct. 

An example of where monitoring user sentiments worked and had an influence on a product was during OpenAI’s ChatGPT GPT-4o case[2], where this update got reverted after an increase of negative feedback regarding the model. Beyond that, if these analysts see that a competitor has more positive reactions in a day than them, they can also analyze what caused this.

The stream represents public Bluesky posters, Hacker News commenters and reviewers in the US App Store. **Most of our collected data comes from Bluesky, so the dataset is uneven across sources.** It is not a representative sample of all AI users, and product use is not verified. People who do not post online, people outside the searched language communities, Android-only users in the app-review source and people who do not use these platforms may be missing or underrepresented. 

[1] [What Is Sentiment Analysis? | IBM](https://www.ibm.com/think/topics/sentiment-analysis) \
[2] [Sycophancy in GPT-4o: What happened and what we’re doing about it | OpenAI](https://openai.com/index/sycophancy-in-gpt-4o/) 

# 3. What did you build?
We built *a Python collector* that repeatedly fetches public items about ChatGPT, Claude and Gemini and stores them in SQLite, together with locally generated sentiment predictions. The Streamlit dashboard shows the three assistants side by side, with positive in green, negative in red and neutral in grey, grouped by hour or day as counts or percentages. The user can inspect the source items behind a peak or dip and view collection status.

XLM-RoBERTa-base was trained on approximately 198 million tweets and fine-tuned for sentiment in Arabic, English, French, German, Hindi, Italian, Spanish and Portuguese. We chose it because much of our data consists of short social-media messages, similar to its training domain. This does not guarantee the same accuracy across our sources. Hugging Face model card: [https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment](https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment). We picked RoBERTa because it is a widely used sentiment model trained on tweets. Our main source is Bluesky, where posts have a similar short format and quite honestly the same amount of sarcasm/sass from the people who post these tweets. We also later added other sources, that are not similar to bluesky/twitter and thus may have slightly worse results, but RoBERTa also had the highest agreement with our labels in our comparison.

**Model licence:**  
We checked the hugging face model card and repository on 14/15th of October 2026, but found no explicit licence for this checkpoint. We therefore cannot confirm permission for unrestricted reuse or redistribution. Our code downloads the model from its original repository; we do not include its weights in our submission. Licence clarification would be needed before deploying this prototype commercially.

- Fetch: hackaton6.py polls Bluesky search, Hacker News comments through Algolia and the three official apps' US App Store RSS feeds with a five-minute wait between collection rounds. These endpoints are currently accessed without an API key; availability can change if the platform paywalls/removes access. 

- Filter: keyword and context rules identify each assistant. Items mentioning multiple assistants go into a separate Comparisons group and receive one prediction for the whole message. They are excluded from the individual assistant charts.

- Model: hackaton6.py also runs the transformer on collected text, predicting positive, neutral or negative. It analyses up to 512 tokens per message; the confidence score is not verified accuracy. 

- Storage: database.db stores text, source links, timestamps, product groups, predictions, collection status and saved word explanations. Source IDs prevent repeated storage of the same item; there is no cross-platform deduplication.

- View: Streamlit refreshes approximately every 15 seconds while open. Users can select a period, hourly or daily grouping, and counts or percentages. Times are shown in Europe/Amsterdam. Historical items can be included separately. Message tabs provide sentiment/day filters and links to the original posts. 



# 4. Which word-analysis features did we add?

We added three ways to inspect the predictions:
- Common contributing words: Captum's Integrated Gradients estimates which words support RoBERTa's prediction. We select up to five contributing words per explained message, filter common words and model names, and count their occurrences in separate positive and negative lists. These counts are selected contributions, not every occurrence in the database.\
- Sentiment-word filter: an extra list uses the VADER English lexicon to show recognised positive or negative words from those contribution lists. VADER does not change RoBERTa's message labels.\
- Individual explanations: choose a message to highlight words supporting the prediction in blue and opposing it in orange. Explanations are saved and reused. Positive and negative messages are processed automatically; individual requests get priority.

The overview follows the selected period and assistant and shows explanation coverage. Processing can take time, so not all messages may be included yet. These are approximate explanations, not proof that a prediction is correct. These features were added to allow users to get a better understanding of why some messages were labeled the way they did and allow them to take action if they see a surge in specific words, an example of this is "suing", maybe that could mean that multiple agencies are suing LLMs and their companies.

**Source access, terms and sharing limitations:**  
We reviewed the available documentation from the datastreams we use

- **Bluesky:** The [Terms of Service](https://bsky.social/about/support/tos) state that users retain ownership of their posts. Public access does not give us an unrestricted licence to republish their texts.
- **Hacker News:** The [Algolia API documentation](https://hn.algolia.com/api) supports programmatic searches and specifies a limit of 10,000 requests per hour per IP. However, API access does not establish permission to redistribute comments. We have not confirmed a licence allowing publication of the full collected texts.
- **App Store:** The [Apple Media Services terms, section F](https://www.apple.com/legal/internet-services/itunes/us/terms.html) prohibit automated scraping, analysis and monitoring of the service or its content. We found no separate permission covering our review-analysis workflow. The availability of the RSS feed therefore does not establish that our use is permitted.

These checks identified unresolved permissions rather than confirming that every source is unrestricted. Before further use, the App Store source should be disabled unless permission is obtained. Before publishing the database or CSV files, sharing rights for the original texts must be resolved. Removing usernames alone does not make posts anonymous, because their wording and source links can identify their authors. The dashboard runs locally to limit exposure of the collected data. The database and CSV files should not be published openly until sharing permissions have been changed. Running this dashboard and hackaton file locally does not remove the restrictions described above.

# 5. Own testing & comparison:
To see big overview of testing, see [our testing reports](https://github.com/JiwiKiwi/AI-For-Good-JalieVermeegen/blob/main/Term%201/Week%206/hackathon/Testing.md)

We also added roughly 2000 of our recent datastream entries to a .csv file for more visibility, since the database itself is extremely messy, they can be found [here](https://github.com/JiwiKiwi/AI-For-Good-JalieVermeegen/blob/main/Term%201/Week%206/hackathon/Hackaton%206/entries_2000_20261015_082220_525181.csv). Sadly though the source time & export time are not all in the Amsterdam timezone so that can be a mess to navigate.


# 6.How do I run it?

1. Download the hackaton folder. Remove additions such as (1) from the filenames. Include database.db if you want to use the collected data; otherwise a new database is created.

2. Install Python and open PowerShell in that folder in that folderor open this file in your preferred IDE and open a terminal. Create a virtual environment and install the requirements:

```powershell
python -m venv .venv
```\
Then use the command:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The model downloads on first use. The VADER lexicon downloads when its section is first opened; the VADER Python package is not needed.

3. Start the collector:\
Go to the directory with the command : cd “C:Users/Wherever you put the file/Hackaton 6”

```powershell
.\.venv\Scripts\python.exe hackaton6.py
```

4. Open a second PowerShell terminal in the same folder and start the dashboard:\
Same as above, go to the directory of the map first.

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Open the local URL shown in the terminal. Keep both terminals running: the collector handles new messages, sentiment predictions and word explanations. The dashboard displays the results. The first model load and explanations can take time on a CPU.

Optional commands:

```powershell
.\.venv\Scripts\python.exe hackaton6.py --export 
```
(Exports up to 2,000 recent stored items to CSV.)

```powershell
.\.venv\Scripts\python.exe hackaton6.py --make-test
```

(Creates the human-label template. Keep an existing labelled file safe before running this.)

```powershell
.\.venv\Scripts\python.exe hackaton6.py --test human_labels.csv 
```
(Runs the evaluation after you label at least 50 relevant items. Fill relevant with yes/no and human_label with positive/neutral/negative.)

Stop a process with Ctrl+C. Keep database.db when replacing the Python files, since it contains your collected data and saved explanations.

# 7. Who did what:
Jalie: Brainstorming ideas with me, making the python program, README (mostly), and the testing.md file. She also made the demo.

Minhyeok: Brainstorming ideas together with my partner, and researching on it for reasonale and supportive resources. Working on the presentation slides.


# 8. Ethical reflection 

Our stream comes from Bluesky posters, Hacker News commenters and US App Store reviewers. These are mostly English-speaking, tech-savvy people who chose to post. \
Most of our data comes from Bluesky, so the dataset is uneven across sources. The combined graph mainly reflects the Bluesky discussions we captured, rather than all AI users. A viral discussion can dominate the results and hide concerns from the smaller sources. This could cause false alarms or make one assistant look less liked because of the platform's audience. We document this imbalance and provide counts, sources and original messages so the analyst can check a change before acting.

It is mainly English for now, but more languages can be added. People who do not post publicly, use other platforms or only use Android in the app-review source are missing or underrepresented. People who don’t use these platforms that we get our data from, people who aren’t tech-savy or android app-store users are not represented/underrepresented in this datastream. An example of this is an older man who isn’t too tech-savy and who also isn’t too keen on the AI/LLM bubble, this man and many others like him will not be taken with the datastream so they cannot ‘voice’ their opinions like the users who do use these platforms.

The model can misread sarcasm, slang and mixed opinions. A negative post mentioning ChatGPT is not always negative about ChatGPT. Integrated Gradients is also only an estimate, and the English word filter can miss context such as “not bad”. Word lists cover processed explanations, not necessarily the full dataset. Active accounts or repeated posts can influence both graphs and word counts, which represent messages rather than unique people.

We store real people's words and source links. Cleaning mentions, emails and links inside the text does not fully anonymise it, because the original post can still identify someone. Public access also does not automatically allow republication. We therefore need to limit shared personal details and check source terms. Separate comparison messages, visible counts and manual inspection help reduce misleading conclusions. The dashboard should guide further investigation, rather than automatically rank products or claim to represent everyone's opinion.

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

**Where does this connect to "AI for Good"?**
_One concrete link to ethics, sustainability or social impact._
