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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"



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

def send_telegram_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)


# 3. Route:
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

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json()

    if "message" not in data:
        return "ok"

    message = data["message"]
    text = message.get("text", "")
    chat_id = message["chat"]["id"]

    # Expected format:
    # /news tech
    # /news q=gta 6
    if not text.startswith("/news"):
        send_telegram_message(chat_id, "Use: /news <category> or /news q=<search>")
        return "ok"

    parts = text.split(" ", 1)

    category = "technology"
    query = None

    if len(parts) > 1:
        arg = parts[1]
        if arg.startswith("q="):
            query = arg.replace("q=", "")
        else:
            category = arg

    # Call your own API internally
    params = {}
    if query:
        params["q"] = query
    else:
        params["category"] = category

    response = requests.get(
        request.url_root + "news",
        params=params
    )

    send_telegram_message(chat_id, response.text)
    return "ok"




# 4. Run the server
if __name__ == "__main__":
    app.run()
