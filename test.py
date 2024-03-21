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
biden_pattern = re.compile(r'([\w\W]{400})biden([\w\W]{400})')
trump_pattern = re.compile(r'([\w\W]{400})trump([\w\W]{400})')

directory = os.fsencode("files/unprocessedfiles")

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    with open(f"files/processedfiles/{filename}") as f:
        data = json.load(f)
    title = data['title']
    description = data['description']
    transcript = data['transcript']
    biden_mentions = biden_pattern.findall(transcript)
    trump_mentions = trump_pattern.findall(transcript)



    for segment in biden_mentions:
        segment = ' '.join(segment)
        scores = sentiment_task(segment)
        print(f"Joe Biden mention: '{segment}' \nScores: {scores}")
    for segment in trump_mentions:
        segment = ' '.join(segment)
        scores = sentiment_task(segment)
        print(f"Trump mention: '{segment}' \nScores: {scores}")
        # Analyze the sentiment of a text
