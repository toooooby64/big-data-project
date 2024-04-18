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

@dag(schedule_interval='@daily', start_date=pendulum.datetime(2024, 3, 22))

def project():
    @task()
    def get_ids():
        # Create a new instance of the Chrome driver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Remote(
        command_executor='http://192.168.1.148:4444/wd/hub',  # Replace with the URL of your Selenium Grid server
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
        for video_id in ids:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            print(transcript)
            with open(f"files/unprocessedfiles/{video_id}.json", "w") as f:
                json.dump(transcript, f)
    ids = get_ids()
    get_transcript(ids)
project = project()