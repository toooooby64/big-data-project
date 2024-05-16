from airflow.decorators import dag, task
import pendulum
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from youtube_transcript_api import YouTubeTranscriptApi
import googleapiclient.discovery
from google.auth import default
import re
import time
import requests
import json
import os
from dotenv import load_dotenv
from transformers import pipeline, AutoTokenizer, AutoConfig
import matplotlib.pyplot as plt


@dag(schedule_interval='@daily', start_date=pendulum.datetime(2024, 3, 22))

def project():
    @task()
    def get_ids():
        # Create a new instance of the Chrome driver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Remote(
        command_executor='http://192.168.1.162:4444/wd/hub',  # Replace with the URL of your Selenium Grid server
        options=options
        )        
        print("Driver created")
        # Navigate to the YouTube search page
        driver.get("https://www.youtube.com/results?search_query=2024+United+States+Presidential+Election&sp=EgYIAhABGAM%253D")
        print("Navigated to the page")

        # Wait for the initial search results to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]')))

        # Extract the video IDs from the URLs
        video_ids = set()
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        while True:
            print("Getting video IDs")
            video_elements = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
            for video_element in video_elements:
                video_url = video_element.get_attribute("href")
                match = re.search(r"v=(\w+)", video_url)
                if match:
                    video_id = match.group(1)
                    video_ids.add(video_id)

            # Scroll down to load more videos
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)  # Wait for the page to load

            # Calculate the new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

            # Check if we have enough video IDs
            if len(video_ids) >= 250:
                break

        # Close the browser
        driver.quit()
        return video_ids


    @task()
    def get_transcript(ids):
        load_dotenv()
        DEVELOPER_KEY = os.getenv('DEVELOPER_KEY')
        api_service_name = "youtube"
        api_version = "v3"
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey = DEVELOPER_KEY)

        count = 0
        for id in ids:
            data = {}
            request = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=id
            )
            try:
                response = request.execute()
                data = {}
                items = response.get('items')
                if items:
                    data['title'] = items[0].get('snippet').get('title')
                    data['description'] = items[0].get('snippet').get('description')
                    data['publishedAt'] = items[0].get('snippet').get('publishedAt')
                    data['viewCount'] = items[0].get('statistics').get('viewCount')
                    data['likeCount'] = items[0].get('statistics').get('likeCount')
                    data['transcript'] = ""
                else:
                    print(f"No items returned for video id {id}")
                    continue

                try:
                    transcript = YouTubeTranscriptApi.get_transcript(id)
                    print('Processing transcript for video id:', id)
                    for j in range(len(transcript)):
                        data['transcript'] += transcript[j].get('text') + " "
                    filename = f"{id}.txt"
                    with open(f"/files/unprocessedfiles/{filename}", 'w') as file:
                        json.dump(data, file, indent=4)
                        file.close()
                except Exception as e:
                    print(f"Error retrieving transcript for video id {id}: {str(e)}")
                    continue
                count += 1
            except Exception as e:
                print(f"Error retrieving video id {id}: {str(e)}")
                continue
        print(f"{count} / {len(ids)} videos processed successfully")
            


    @task()
    def clean_transcript():
        def remove_between_square_brackets(text):
            return re.sub(r'\[[^]]*\]', '', text)

        def remove_special_characters(text, remove_digits=True):
            pattern=r'[^a-zA-z0-9\s]'
            text=re.sub(pattern,'',text) 
            return text

        directory = os.fsencode("/files/unprocessedfiles")

        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            data = json.load(open(f"/files/unprocessedfiles/{filename}"))
            transcript = data['transcript']

            transcript = remove_between_square_brackets(transcript)
            transcript = remove_special_characters(transcript)  
            transcript = transcript.lower()
            data['transcript'] = transcript
            with open(f"/files/processedfiles/{filename}", 'w') as file:
                json.dump(data, file, indent=4)
                print(f"Cleaned transcript for video id {filename}")
    @task()
    def process_transcript():
        MODEL = f"cardiffnlp/twitter-roberta-base-sentiment-latest"
        tokenizer = AutoTokenizer.from_pretrained(MODEL)
        config = AutoConfig.from_pretrained(MODEL)

        # Replace 'model_path' with the path to your pre-trained model
        sentiment_task = pipeline("sentiment-analysis", model=MODEL, tokenizer=tokenizer)

        # Precompile the regular expressions
        biden_pattern = re.compile(r'([\w\W]{400})biden([\w\W]{400})')
        trump_pattern = re.compile(r'([\w\W]{400})trump([\w\W]{400})')

        directory = os.fsencode("/files/unprocessedfiles")
        biden_scores = {'negative': 0, 'neutral': 0, 'positive': 0}
        trump_scores = {'negative': 0, 'neutral': 0, 'positive': 0}

        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            print(filename)
            with open(f"/files/processedfiles/{filename}") as f:
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
                total = sum(biden_scores.values())
            biden_scores = {k: v / total for k, v in biden_scores.items()}
            data['biden_sentiment'] = biden_scores

            for mention in trump_mentions:
                mention = ' '.join(mention)
                scores = sentiment_task(mention)
                trump_scores[scores[0]['label'].lower()] += scores[0]['score']
                data['trump_sentiment'] = scores[0]['label'].lower()
                total = sum(trump_scores.values())
            trump_scores = {k: v / total for k, v in trump_scores.items()}
            data['trump_sentiment'] = trump_scores
                
            with open(f"/files/processedfiles/{filename}", 'w') as f:
                json.dump(data, f, indent=4)
                print(f"Processed transcript for video id {filename}")
    @task()
    def highest_feature():
        path_of_the_directory = '/files/processedfiles'
        output_image_path = '/usr/local/airflow/output/highest_feature.png'
        biden_features = {"positive": 0, "neutral": 0, "negative": 0}
        trump_features = {"positive": 0, "neutral": 0, "negative": 0}

        for filename in os.listdir(path_of_the_directory):
            f = os.path.join(path_of_the_directory, filename)
            if os.path.isfile(f):
                with open(f, "r") as file:
                    lines = file.readlines()
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if "biden_sentiment" in line:
                            current_sentiment = biden_features
                            values = []
                            for next_line in lines[i+1:i+4]:
                                value = float(next_line.split(": ")[1].strip().rstrip(','))
                                values.append(value)
                            max_value = max(values)
                            if max_value == values[0]:
                                biden_features["positive"] += 1
                            elif max_value == values[1]:
                                biden_features["neutral"] += 1
                            else:
                                biden_features["negative"] += 1
                        elif "trump_sentiment" in line:
                            current_sentiment = trump_features
                            values = []
                            for next_line in lines[i+1:i+4]:
                                value = float(next_line.split(": ")[1].strip().rstrip(','))
                                values.append(value)
                            max_value = max(values)
                            if max_value == values[0]:
                                trump_features["positive"] += 1
                            elif max_value == values[1]:
                                trump_features["neutral"] += 1
                            else:
                                trump_features["negative"] += 1

        print("Biden Features:")
        for feature, value in biden_features.items():
            print(f"{feature.capitalize()}: {value}")

        print("\nTrump Features:")
        for feature, value in trump_features.items():
            print(f"{feature.capitalize()}: {value}")

        categories = list(biden_features.keys())
        biden_values = list(biden_features.values())
        trump_values = list(trump_features.values())

        bar_width = 0.35
        index = range(len(categories))

        fig, ax = plt.subplots()
        bar1 = ax.bar(index, biden_values, bar_width, label='Biden')
        bar2 = ax.bar([i + bar_width for i in index], trump_values, bar_width, label='Trump')

        ax.set_xlabel('Sentiment')
        ax.set_ylabel('Values')
        ax.set_title('Sentiment Analysis Comparison between Biden and Trump')
        ax.set_xticks([i + bar_width / 2 for i in index])
        ax.set_xticklabels(categories)
        ax.legend()

        plt.savefig(output_image_path)
        plt.close()

        print(f"Graph saved at: {output_image_path}")
        
    @task()
    def sort_data():
        path_of_the_directory= '/files/processedfiles'
        biden_vs_trump = {"biden": 0, "trump": 0}
        for filename in os.listdir(path_of_the_directory):
            f = os.path.join(path_of_the_directory,filename)   
            if os.path.isfile(f):
                # Open the text file and read its contents
                with open(f, "r") as file:
                    lines = file.readlines()
                    for i, line in enumerate(lines):
                        line = line.strip()  # Remove leading/trailing whitespace
                        # Check if the line starts with "biden_sentiment" or "trump_sentiment"
                        if "viewCount" in line:
                            views = float((line.split(": ")[1].strip().rstrip(',')).replace('"',''))
                        elif "likeCount" in line:
                            likes = float((line.split(": ")[1].strip().rstrip(',')).replace('"',''))
                        elif "biden_sentiment" in line:
                            # Read the next three lines and get the float values
                            next_line = lines[i+1]
                            value = float(next_line.split(": ")[1].strip().rstrip(','))      
                            biden_vs_trump["biden"] += value * likes / views * 100
                        elif "trump_sentiment" in line:
                            # Read the next three lines and get the float values
                            next_line = lines[i+1]
                            value = float(next_line.split(": ")[1].strip().rstrip(','))      
                            biden_vs_trump["trump"] += value * likes / views * 100

                print("\nBiden vs Trump:")
                for feature, value in biden_vs_trump.items():
                    print(f"{feature.capitalize()}: {value}")

                # Extracting the keys (categories) and values for both Biden and Trump
                categories = list(biden_vs_trump.keys())
                values = list(biden_vs_trump.values())
                # Setting the positions and width for the bars
                bar_width = 0.35
                index = range(len(categories))

                # Creating the bar graph
                fig, ax = plt.subplots()
                bar1 = ax.bar(0, values[0], bar_width, label='Biden')
                bar2 = ax.bar(1, values[1], bar_width, label='Trump')

                # Adding labels, title, and legend
                ax.set_xlabel('Canidate')
                ax.set_ylabel('Values')
                ax.set_title('Vid Rating * Num Likes / Views * 100')
                ax.set_xticks([i + bar_width / 2 for i in index])
                ax.set_xticklabels(categories)
                ax.legend()

                # Save the bar graph to a file
                output_image_path = '/usr/local/airflow/output/sort_data.png'
                plt.savefig(output_image_path)
                plt.close()

                print(f"Graph saved at: {output_image_path}")



    ids = get_ids()
    get_transcript(ids) >> clean_transcript() >> process_transcript() >> highest_feature() >> sort_data()
project = project()