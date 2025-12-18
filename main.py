#Install python on device and extension in the software

#List of commands:

#Installing requests:
#pip install requests

#Enter in virtual environment:
#python -m venv .venv
#.venv\Scripts\activate

#Upgrade pip: python -m pip install --upgrade pip

#Gemini: pip install requests google-genai

#Setting API as environmental variables in windows: 
#setx GOOGLE_API_KEY "your_google_api_key_here"
#setx GEMINI_API_KEY "your_gemini_api_key_here" (Restart app later)

#Setting API as environmental variables in macos/linux:
#export GOOGLE_API_KEY="your_google_api_key_here"
#export GEMINI_API_KEY="your_gemini_api_key_here"
#If you want it permanent, add those lines to: ~/.bashrc or ~/.zshrc

import os
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

import requests
import time
url = "https://newsapi.org/v2/top-headlines"

user_query = input("Enter the category of news you want: ")

params = {
    "q": user_query,
    "language": "en",
    "apiKey": "2483ca61c27a4074ba9436f0fc9686c5"
}

response = requests.get(url, params=params)
data = response.json()

def summarize_article(text):
    prompt = (
        "Summarize this tech news in 2 short sentences. "
        "Focus on what changed and why it matters. "
        "Ignore hype and buzzwords.\n\n"
        f"{text}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text.strip()



articles = data["articles"]

MAX_AI_CALLS = 5
count = 0

for article in articles:
    if count >= MAX_AI_CALLS:
        break

    title = article["title"].lower()

    if not article.get("description"):
        continue

    content = f"{article['title']}. {article['description']}"

    summary = summarize_article(content)
    count += 1

    print(article["title"])
    print(article["source"]["name"])
    print("Summary:", summary)
    print()

    time.sleep(15)

