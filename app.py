import os
import time
import requests
from flask import Flask, request
from google import genai

# 1. Create Flask app
app = Flask(__name__)

# 2. Create Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

NEWS_API_KEY = "2483ca61c27a4074ba9436f0fc9686c5"
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
    # Get category from URL, example: /news?category=technology
    category = request.args.get("category", "technology")

    params = {
        "category": category,
        "language": "en",
        "apiKey": NEWS_API_KEY
    }

    response = requests.get(NEWS_URL, params=params)
    data = response.json()

    articles = data.get("articles", [])

    output = []
    count = 0
    MAX_ARTICLES = 5

    for article in articles:
        if count >= MAX_ARTICLES:
            break

        if not articles:
            return "No articles found or API error."


        if not article.get("description"):
            continue

        content = f"{article['title']}. {article['description']}"
        summary = summarize_article(content)

        output.append(
            f"📰 {article['title']}\n"
            f"Source: {article['source']['name']}\n"
            f"Summary: {summary}\n"
        )

        count += 1
        time.sleep(15)  # rate-limit Gemini

    return "\n\n".join(output)


# 4. Run the server
if __name__ == "__main__":
    app.run(debug=True)
