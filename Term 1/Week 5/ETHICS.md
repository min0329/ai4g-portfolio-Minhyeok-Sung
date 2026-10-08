# Ethical reflection

Who needs early help? AI for Good, Hackathon 5: Model Showdown, SDG 8
*Lucas Jansze & Minhyeok Sung*

Our model scores people just after they lost their job, and that score helps decide who talks to a work coach in the first weeks and who waits. The people it is about did not ask to be scored. So we wrote this reflection from their side: what can go wrong for a job seeker, what we did about it, and what we could not solve.

We picked the four risks that worry us most, and end with the people in the data. The numbers come from the notebook ([uwv_long_term_unemployment.ipynb](uwv_long_term_unemployment.ipynb), step 8 and 9) and are from the test set of 405 job losses unless we say otherwise. The problem, the user and the sources are in the [README](README.md).

## 1. The model misses the people who do not fit the picture

Think of a 24-year-old who loses a job with a flexible contract and is in good health. The model has learned that long-term unemployment mostly happens to people who are older or have health problems, so it gives this person a low risk. If the prediction is wrong, they start with online services and their first conversation with a coach is in the seventh month of their benefit. For a young person, a year without work early in a career costs experience and confidence that is hard to make up later.

This is not a rare case. The model finds only 18% of the young people (18 to 29) who become long-term unemployed, against 89% of the people aged 50 to 66. On the larger training set, with cross-validation, the gap is just as wide: 12% of the young against 88% of the oldest group. On the test set the model also seemed to miss men more often than women (57% found against 70%). On more data that gap disappeared (60% for both), so we do not count it as a finding. People we know little about are missed more often too: for about 30% of the job losses there was no interview about the job or health in the two years before, and those people are overrepresented among the ones the model missed.

The opposite mistake is much smaller. Someone who is invited but would have found work anyway loses some time, as long as the conversation is help and not pressure.

What we did. We chose balanced accuracy as the main metric, so a model cannot look good by inviting nobody. We checked how many long-term cases the model finds in every age group, for men and women, per education level, per origin group and for people with and without a long-standing disease. We did that twice, on the test set and with cross-validation on the training set, to see which gaps are real and which come from a small group. We advise a lower threshold (0.35 instead of 0.5), which raises the share of long-term cases found from 63% to 86%. The price is that 77% of all job seekers are invited instead of 47%. And we made it a rule in the README and the notebook that a low score may never mean less help. A coach can always invite someone, and we name young people and people with an unknown job history as groups to look at regardless of the score.

We also took gender out of the model. Our first version used it. At the end we tested it against the rule we had set for origin (risk 2), and it failed: with gender the model was not better (0.637 against 0.638 without), and it invited women clearly more often than men (49% against 39%). So we removed it and reran the whole notebook. Without gender the model invites 45% of the women and 42% of the men, and finds the same share of long-term cases in both groups (60%).

What is not solved. We measured the gaps between groups at threshold 0.5 and not at 0.35. And leaving gender out does not make the model blind to it. Women in our data worked fewer hours and earned less in the job they lost, and the model uses both, so it still invites women a little more often.

The deeper problem stays. The model mostly sorts on age. A rule that invites everyone aged 40 or older does almost as well (0.602 against 0.630 on the test set). So young people who get stuck are missed with or without a model, and a better algorithm on the same information will not fix that. The next step would be to repeat the check at the chosen threshold on UWV's own data, and to test whether a separate threshold per age group closes the gap for young people.

## 2. Scoring people on where they were born

In our data, people who migrated to the Netherlands themselves are more often still without work after a year (57%, against 38% for people with a Dutch background). A model that uses origin could send more help their way. But it would also give someone a score because of where they or their parents were born, which is something they cannot change. That is the kind of profiling the District Court of The Hague rejected in the SyRI case in 2020, and that went wrong in the childcare benefits scandal. "You are invited because you are a migrant" is not something a coach should ever have to say.

What we did. Before we looked at any result we agreed to leave origin out unless it made the model clearly better. It did not: the score with origin was 0.642 against 0.638 without, a difference far smaller than the spread between the folds (about 0.02). So migration background is not a feature. We only use it to check whether the model treats groups differently.

What is not solved. Leaving the column out does not make the model blind to origin. When we tried to predict migration background from the other features, such as education, household and sector, that worked better than chance (ROC-AUC 0.68, where 0.5 means no information). And children of migrants are the group the model finds least often, although that is based on only 18 long-term cases in the test set. It is also the lowest group in cross-validation (0.47, on 58 cases). That is why the check per origin group has to be repeated with every new version of the model. It is not something to tick off once.

## 3. Health is private, and people may not want to share it

Three features are about health: how someone rates their own health, whether they have a long-standing disease and how much health limits their daily life. Under the GDPR this is a special category of personal data. A job seeker may not want UWV to know, or may be afraid it will be used against them. And if "no answer" were treated the same as "healthy", people who keep their health private would quietly get less help.

What we did. We tested whether the model needs health at all. Overall it adds very little. But for people with a long-standing disease it matters: with health the model finds 81% of the long-term cases among them, without it 66% (cross-validation on the training set). They are more often long-term unemployed, so here the information sends help to people who need it. We kept health in under two conditions. Answering is voluntary. And when someone declines, UWV scores them both with and without health and uses the higher risk, so declining can never cost someone an invitation.

What is not solved. In our data a missing health answer means "did not take part in the Health survey that year". At UWV it would mean "did not want to say". The model has never seen that situation, so we do not know how it behaves there. Whether UWV may ask these questions at intake at all is a legal question we cannot answer. It would need a data protection impact assessment.

## 4. A score that turns into a decision, or into pressure

A number with two decimals looks objective. A coach with little time may follow it without thinking: the model says 0.31, so online services. Then the 58 people the model missed in our test set would never get the early conversation, even when the coach had a good reason to invite them. That would be a step back from how coaches work now, because today they invite about three in ten people with a good score earlier on their own judgement (UWV, 2022).

A second danger is that the score gets reused. A risk of long-term unemployment could be used to check how hard someone is searching, or to decide who gets obligations. Then the people predicted to stay unemployed would get more pressure instead of more help. A UWV experiment studied by Leiden University (2024) showed where that leads: the extra conversation with a coach helped people find work, but imposing an obligation to search more broadly had the opposite effect.

What we did. We present the model as support for the coach in the notebook and the README, never as the one who decides. We chose a model the coach can explain over an equally good random forest that cannot be explained, so the coach can see why someone gets a score and disagree with it. The README lists who must not use the model: employers, fraud and enforcement teams, and municipalities for bijstand clients.

What is not solved. A README cannot stop anyone from using a model differently. In a real deployment this has to be in UWV's own rules for the tool and in its public algorithm register, and coaches need to be told that most of the model's mistakes fall on young people.

## The people in the data

LISS panel members agreed to take part in scientific research. They did not agree to be shown, and everyone who uses LISS data signs a statement not to pass the data on and not to publish anything about individual persons or households. A table with a group of three people, or a saved model, could make someone recognisable to people who know them.

So the data is not in this repository and `data/liss/` is in `.gitignore`. The notebook never shows rows, person numbers or real cases, only counts, percentages and scores for groups, and a group smaller than 10 people is shown as "< 10". The job seeker in step 10 is made up. We do not save trained models, because a KNN model contains its training rows.

Using panel data for a study prototype fits what people agreed to. Building a model that decides about real job seekers does not. A real version would need UWV's own data and a legal basis.

The panel is also not the same as the people UWV sees. Not everyone in our data claimed WW, the period 2007 to 2025 includes the financial crisis and COVID, and the questionnaires are in Dutch. That last point matters most. UWV's own research says that people with poor job chances relatively often have trouble with Dutch (UWV, 2022), and they are hardly in our data. Their scores would be the least reliable, and nobody would notice. We cannot measure how well the model works for people who are not in the data, which is one more reason it must be retrained on UWV data before any real use.

## Would we hand this model to UWV?

Not as it is. It is the best of our three models, and it clearly beats "invite everyone over 50": it finds 63% of the people who become long-term unemployed, against 41%. But it is only a little better than "invite everyone aged 40 or older", it still gets roughly four in ten people wrong, and the mistakes fall hardest on young people. What we would hand over is the approach: a model a coach can explain, a threshold that follows from capacity, health only with consent, origin and gender left out, a check per group on enough data for every new version, and the rule that a score can only add help. And with it the honest message that a model of this kind, on what is known at intake, is a weak tool.
