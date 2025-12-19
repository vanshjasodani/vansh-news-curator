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

def fetch_news(search_query=None, category="technology"):
    params = {
        "language": "en",
        "apiKey": NEWS_API_KEY
    }

    if search_query:
        params["q"] = search_query
    else:
        params["category"] = category

    response = requests.get(NEWS_URL, params=params)
    data = response.json()

    articles = data.get("articles", [])
    if not articles:
        return "No articles found."

    output = []
    count = 0
    MAX_ARTICLES = 3

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



# 3. Route:
@app.route("/news")
def get_news():
    search_query = request.args.get("q")
    category = request.args.get("category", "technology")

    return fetch_news(search_query, category)


@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(silent=True)

    if not data or "message" not in data:
        return "ok"

    message = data["message"]
    text = message.get("text", "").strip()
    chat_id = message["chat"]["id"]

    # Only respond to /news
    if not text.startswith("/news"):
        send_telegram_message(
            chat_id,
            "Use:\n/news <category>\n/news q=<search>\n\nExample:\n/news technology\n/news q=gta 6"
        )
        return "ok"

    # Defaults
    category = "technology"
    query = None

    parts = text.split(" ", 1)

    if len(parts) > 1:
        arg = parts[1].strip()
        if arg.startswith("q="):
            query = arg[2:].strip()
        else:
            category = arg

    try:
        # DIRECT function call — no HTTP, no recursion, no SIGKILL
        result = fetch_news(search_query=query, category=category)
    except Exception as e:
        result = "Something broke internally. Server didn’t die, but it tripped."

    send_telegram_message(chat_id, result)
    return "ok"



# 4. Run the server
if __name__ == "__main__":
    app.run()
