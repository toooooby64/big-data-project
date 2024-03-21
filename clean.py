import json
import os
import re

def remove_between_square_brackets(text):
  return re.sub(r'\[[^]]*\]', '', text)

def remove_special_characters(text, remove_digits=True):
  pattern=r'[^a-zA-z0-9\s]'
  text=re.sub(pattern,'',text) 
  return text

directory = os.fsencode("files/unprocessedfiles")

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    data = json.load(open(f"files/unprocessedfiles/{filename}"))
    transcript = data['transcript']

    transcript = remove_between_square_brackets(transcript)
    transcript = remove_special_characters(transcript)  
    transcript = transcript.lower()
    data['transcript'] = transcript
    
    with open(f"files/processedfiles/{filename}", 'w') as file:
        json.dump(data, file, indent=4)
    
