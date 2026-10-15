from pathlib import Path
import csv
import re
import pandas as pd
from transformers import pipeline

FOLDER = Path(__file__).resolve().parent
INPUT = FOLDER / "test_results.csv"
MODEL = "ZyroGod/distilbert-sentiment-classifier"
LABELS = ["negative", "neutral", "positive"]

with INPUT.open(encoding="utf-8-sig", newline="") as file:
    separator = csv.Sniffer().sniff(file.read(65536), delimiters=",;\t").delimiter

df = pd.read_csv(INPUT, sep=separator, encoding="utf-8-sig", keep_default_na=False)
df.columns = df.columns.str.strip()

# Remove empty spreadsheet columns.
df = df.loc[:, ~df.columns.str.match(r"(?i)^unnamed(?:\s*:|$)")]

# Merge duplicate columns, including names such as explanation.1.
clean = pd.DataFrame(index=df.index)
for position, column in enumerate(df.columns):
    name = re.sub(r"\.\d+$", "", column)
    values = df.iloc[:, position]
    if name not in clean:
        clean[name] = values
    else:
        empty = clean[name].astype(str).str.strip().eq("")
        clean.loc[empty, name] = values.loc[empty]
df = clean

required = {"text", "human_label", "transformer_label"}
if missing := required - set(df.columns):
    raise ValueError(f"Missing columns: {sorted(missing)}")

human = df["human_label"].str.strip().str.lower()
if df.empty or not human.isin(LABELS).all():
    raise ValueError("No test items or invalid human labels.")
if df["text"].str.strip().eq("").any():
    raise ValueError("Empty texts found.")

print(f"Testing DistilBERT on {len(df)} items...")
model = pipeline("sentiment-analysis", model=MODEL, tokenizer=MODEL, device=-1)
model.tokenizer.model_input_names = ["input_ids", "attention_mask"]

predictions = model(
    df["text"].tolist(), truncation=True, max_length=512, batch_size=4
)
df["distilbert_label"] = [item["label"].lower() for item in predictions]
df["distilbert_label_correct"] = df["distilbert_label"] == human

# Place all prediction labels directly beside the human label.
labels = ["human_label", "transformer_label", "distilbert_label"]
if "baseline_label" in df:
    labels.append("baseline_label")

columns = [column for column in df.columns if column not in labels]
position = list(df.columns).index("human_label")
position = sum(column not in labels for column in list(df.columns)[:position])
columns[position:position] = labels
df = df[columns]

output = FOLDER / "test_results_comparison.csv"
df.to_csv(output, sep=separator, index=False, encoding="utf-8-sig")

for name, column in [
    ("RoBERTa", "transformer_label"),
    ("DistilBERT", "distilbert_label"),
    ("Baseline", "baseline_label"),
]:
    if column in df:
        correct = df[column].str.strip().str.lower() == human
        print(f"{name}: {correct.sum()}/{len(df)} ({correct.mean():.1%})")

print(f"\nSaved: {output.name}")