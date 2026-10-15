## 1. Testing  human labels v.s the transformer

### How we tested

We manually labelled 74 relevant items from our own datastream as positive, neutral or negative before comparing them with the transformer, to see this see [our human labels](https://github.com/JiwiKiwi/AI-For-Good-JalieVermeegen/blob/main/Term%201/Week%206/hackathon/Hackaton%206/human_labels.csv). The .csv contained 30 negative, 26 neutral and 18 positive items. We also noted down explanations for our labels. We tested `cardiffnlp/twitter-xlm-roberta-base-sentiment`, the transformer used in our dashboard, and a simple word-list baseline on the same texts. The test script checked that the labels were valid and that the original IDs and texts matched the database records.  We calculated agreement by dividing the number of matching predictions by the total number of tested items.

### What the baseline does

The baseline is a simple reference method, not a trained language model. It counts words from two predefined lists:

| **Positive words**                                     | **Negative words**                                       |
| ------------------------------------------------------ | -------------------------------------------------------- |
| good, great, love, helpful, useful, better, easy, fast | bad, hate, broken, annoying, worse, slow, crash, useless |

More positive matches cause a positive label and more negative matches produce a negative label. Equal negative/positive words, including no recognised words, cause a neutral label. The baseline cannot understand context, negation or sarcasm. For example, “not good” becomes positive because it recognises “good” without interpreting “not.” 

### Results

| **Method**         | **Matches with human labels** | **Disagreements** | **Agreement** |
| ------------------ | ----------------------------- | ----------------- | ------------- |
| XLM-RoBERTa        | 52/74                         | 22                | **70.3%**     |
| Word-list baseline | 31/74                         | 43                | **41.9%**     |

| **Human-labelled category** | **Items** | **RoBERTa matches** | **Baseline matches** |
| --------------------------- | --------- | ------------------- | -------------------- |
| Negative                    | 30        | 23                  | 3                    |
| Neutral                     | 26        | 17                  | 22                   |
| Positive                    | 18        | 12                  | 6                    |

The baseline predicted neutral for 59 of the 74 items, including 25 items we labelled negative and 12 we labelled positive. Its comparatively high agreement on neutral items therefore reflects its tendency to return neutral when its vocabulary does not capture the sentiment.

### Three selected failures

We selected the following three highlighted disagreements to examine where RoBERTa differed from our interpretation. To see the full differences in the labels, see [our test results!](https://github.com/JiwiKiwi/AI-For-Good-JalieVermeegen/blob/main/Term%201/Week%206/hackathon/Hackaton%206/test_results.csv)

| **Item**                                                                                                                                                    | **Human label** | **RoBERTa prediction** | **Explanation**                                                                                                                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| “collecting AI subs like infinity stones,” followed by an explanation that Gemini and ChatGPT blocked an attempt to edit a meme                             | Neutral         | Negative               | We interpreted the main message as a funny tweet of having multiple AI subscriptions. But then the blocked was something negative, so we went with the neutral label.                                                                                 |
| “There's your advertising slogan — ‘ChatGPT — Not quite as bad as heroin!’”                                                                                 | Negative        | Neutral                | The slogan is super sarcastic, comparing ChatGPT with heroin is just negative. Even though “not quite as bad softens the comparison, the transformer just does not see that this is still meant to be negative                                        |
| A user describing a family member sharing AI content, using ChatGPT during their conversation and becoming defensive when the user questioned AI’s accuracy | Negative        | Neutral                | We interpreted the account as frustration about AI’s influence on their family member. However, the text also describes the family member enjoying AI content. It contains different people’s attitudes, potentially making the transformer confused. |

These explanations describe possible reasons for the disagreements; they do not establish the model’s internal reasoning. The first and third examples also show that human labels can be subjective because a message may contain several attitudes or targets. I for example did not know how to properly label several items because of my own attitude towards certain messages.

### Limitations

RoBERTa agreed with our views more often than the baseline we set, however, 22 of the 74 predictions were still different from our judgement, so the dashboard’s classifications still require more caution and human reviewing.

Some messages were difficult to label because their meaning was unclear or they described a problem without giving an opinion. Our own labels may therefore not always be right. Clearer rules and another person checking the labels could help. These results only apply to the items we tested, so the model may perform differently on other messages. Also, a post mentioning ChatGPT, Claude or Gemini is not always expressing an opinion about that assistant, it could be about another person, an event or AI in general.

For the dashboard’s user, missed negative reactions could hide complaints, while neutral messages classified as negative could exaggerate peoples opinions or sentiments about AI. We would use RoBERTa to identify trends for investigation and keep the underlying messages available for review before action can be taken.

## 2. Comparison: RoBERTa v.s DistilBERT

After the first test, we tested a second pretrained model: `ZyroGod/distilbert-sentiment-classifier`. Like RoBERTa, it gives positive, neutral or negative labels. We used the same 74 messages and kept our human labels and transformer labels unchanged. Our comparison script read the existing test results, kept the RoBERTa and baseline predictions, and ran the messages through DistilBERT. We then placed the labels next to each other to see where the models agreed with us and where they were different. To do this comparison, there is a compare.py file that contains both models, they have to be loaded when you first run them as usual but other than that all you have to do is run '.\.venv\Scripts\python.exe compare.py'

### Results

| **Method**                   | **Matches with our labels** | **Disagreements** | **Agreement** |
| ---------------------------- | --------------------------- | ----------------- | ------------- |
| RoBERTa                      | 52/74                       | 22                | **70.3%**     |
| DistilBERT                   | 39/74                       | 35                | **52.7%**     |
| Baseline from the first test | 31/74                       | 43                | **41.9%**     |

RoBERTa matched 13 more messages than DistilBERT. Both models performed better than the word-list baseline, but RoBERTa had the highest agreement with our labels.

| **Human-labelled category** | **Messages** | **RoBERTa matches** | **DistilBERT matches** |
| --------------------------- | ------------ | ------------------- | ---------------------- |
| Negative                    | 30           | 23                  | 18                     |
| Neutral                     | 26           | 17                  | 13                     |
| Positive                    | 18           | 12                  | 8                      |

RoBERTa matched more of our labels in all three categories. DistilBERT labelled ten messages we considered negative as neutral, compared with six for RoBERTa. This matters because negative reactions could be missed in the dashboard.

### Where the models differed

The models gave different labels on 23 messages. RoBERTa matched our label on 18 of those messages, while DistilBERT matched on five.

| **Message**                                                                                    | **Human** | **RoBERTa** | **DistilBERT** |
| ---------------------------------------------------------------------------------------------- | --------- | ----------- | -------------- |
| “Excelente Amplio base de datos”                                                               | Positive  | Positive    | Neutral        |
| “The best thing since sliced bread,” followed by a review calling the product a “game changer” | Positive  | Positive    | Negative       |
| “when gemini models go off the rails they *really* go off the rails”                           | Negative  | Neutral     | Negative       |
| A user describing everyday bugs in Claude Code, despite improvements                           | Negative  | Neutral     | Negative       |

The Spanish review expresses praise, which RoBERTa matched, while DistilBERT returned neutral. However, DistilBERT did better on some messages. It matched our negative labels for the Gemini complaint and the comment about Claude Code’s bugs, where RoBERTa returned neutral. So even though RoBERTa performed better overall, DistilBERT picked up some complaints that RoBERTa missed. To see the full differences, see [the full comparison results](https://github.com/JiwiKiwi/AI-For-Good-JalieVermeegen/blob/main/Term%201/Week%206/hackathon/Hackaton%206/test_results_comparison.csv)

### Which model would we use?

We would keep RoBERTa for our dashboard because it matched our labels more often overall and in each category. It is also multilingual, while this DistilBERT model was trained for English sentiment only which is probably why it struggled with the spanish/japanese messages. Our stream includes messages in other languages, so that is another reason to keep RoBERTa. 

The results still have limitations. Our labels are our own interpretation, and some messages were difficult to judge. The sample also contains repeated posts to try and detect trends, so similar messages can influence the scores more than once.

We would use RoBERTa to help our user notice changes and find messages worth checking. We would not treat every prediction as correct. The user should still read the posts behind a peak or dip before deciding what to do instead of blindly following either transformer.
