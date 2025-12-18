import os
import time
import requests
from flask import Flask, request
from google import genai

# 1. Create Flask app
app = Flask(__name__)

# 2. Create Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_URL = "https://newsapi.org/v2/top-headlines"


def summarize_article(text):
    prompt = (
        "Summarize this news in 2 short sentences. "
        "Focus on what changed and why it matters. "
        "Ignore hype and buzzwords.\n\n"
        f"{text}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text.strip()


# 3. Route: /news
@app.route("/news")
def get_news():
    search_query = request.args.get("q")
    category = request.args.get("category", "technology")

    # Base params (always needed)
    params = {
        "language": "en",
        "apiKey": NEWS_API_KEY
    }

    # Decide mode: search OR category
    if search_query:
        params["q"] = search_query
    else:
        params["category"] = category

    response = requests.get(NEWS_URL, params=params)
    data = response.json()

    articles = data.get("articles", [])
    if not articles:
        return "No articles found or API error."

    output = []
    count = 0
    MAX_ARTICLES = 5

    for article in articles:
        if count >= MAX_ARTICLES:
            break

        if not article.get("description"):
            continue

        content = f"{article['title']}. {article['description']}"
        summary = summarize_article(content)

        output.append(
            f"📰 {article['title']}\n"
            f"Source: {article['source']['name']}\n"
            f"Summary: {summary}"
        )

        count += 1

    return "\n\n".join(output)



# 4. Run the server
if __name__ == "__main__":
    app.run()
