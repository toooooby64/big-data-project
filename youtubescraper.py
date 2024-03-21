from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from youtube_transcript_api import YouTubeTranscriptApi
import googleapiclient.discovery
import re
import time
import requests
import json
import os
from dotenv import load_dotenv

# Create a new instance of the Chrome driver
driver = webdriver.Chrome("webdriver/chromedriver_mac")
# Navigate to the YouTube search page
driver.get("https://www.youtube.com/results?search_query=United+States+Presidential+Election+Joe+Biden&sp=EgYIAhABGAM%253D")


# Wait for the initial search results to load
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]')))

# Extract the video IDs from the URLs
video_ids = []
last_height = driver.execute_script("return document.documentElement.scrollHeight")
while True:
    video_elements = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
    for video_element in video_elements:
        video_url = video_element.get_attribute("href")
        match = re.search(r"v=(\w+)", video_url)
        if match:
            video_id = match.group(1)
            video_ids.append(video_id)

    # Scroll down to load more videos
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
    time.sleep(2)  # Wait for the page to load

    # Calculate the new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.documentElement.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

    # Check if we have enough video IDs
    if len(video_ids) >= 1:
        break

# Close the browser
driver.quit()

load_dotenv()
DEVELOPER_KEY = os.getenv('GOOGLE_API_KEY')

api_service_name = "youtube"
api_version = "v3"
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey = DEVELOPER_KEY)

for i in range(len(video_ids)):
    data = {}
    request = youtube.videos().list(
    part="snippet,contentDetails,statistics",
    id=video_ids[i]
    )
    response = request.execute()
    data = {}
    items = response.get('items')
    if items:
        data['title'] = items[0].get('snippet').get('title')
        data['description'] = items[0].get('snippet').get('description')
        data['publishedAt'] = items[0].get('snippet').get('publishedAt')
        data['viewCount'] = items[0].get('statistics').get('viewCount')
        data['likeCount'] = items[0].get('statistics').get('likeCount')
    else:
        print(f"No items returned for video id {video_ids[i]}")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_ids[i])
        for j in range(len(transcript)):
                data['transcript'] += transcript[j].get('text') + " "
                
        filename = f"{data['title']}.txt"
        with open(f"files/unprocessedfiles/{filename}", 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error retrieving transcript for video id {video_ids[i]}: {str(e)}")
        continue

