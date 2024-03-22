import re
import os
import json
from transformers import pipeline, AutoTokenizer, AutoConfig

MODEL = f"cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
config = AutoConfig.from_pretrained(MODEL)

# Replace 'model_path' with the path to your pre-trained model
sentiment_task = pipeline("sentiment-analysis", model=MODEL, tokenizer=tokenizer)

# Precompile the regular expressions
biden_pattern = re.compile(r'([\w\W]{400})joe biden([\w\W]{400})')
trump_pattern = re.compile(r'([\w\W]{400})trump([\w\W]{400})')

directory = os.fsencode("files/unprocessedfiles")
biden_scores = {'negative': 0, 'neutral': 0, 'positive': 0}
trump_scores = {'negative': 0, 'neutral': 0, 'positive': 0}

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    with open(f"files/processedfiles/{filename}") as f:
        data = json.load(f)
    title = data['title']
    description = data['description']
    transcript = data['transcript']
    biden_mentions = biden_pattern.findall(transcript)
    trump_mentions = trump_pattern.findall(transcript)


    for mention in biden_mentions:
        mention = ' '.join(mention)
        scores = sentiment_task(mention)
        biden_scores[scores[0]['label'].lower()] += scores[0]['score']

    for mention in trump_mentions:
        mention = ' '.join(mention)
        scores = sentiment_task(mention)
        trump_scores[scores[0]['label'].lower()] += scores[0]['score']

total = sum(biden_scores.values())
biden_scores = {k: v / total for k, v in biden_scores.items()}

total = sum(trump_scores.values())
trump_scores = {k: v / total for k, v in trump_scores.items()}

print("Biden Sentiment Distribution:")
print(biden_scores)

print("Trump Sentiment Distribution:")
print(trump_scores)