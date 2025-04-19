import json
import time
import requests
import threading
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import feedparser
from flask import Flask

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN")
AFFILIATE_TAG = "facebook_page01-20"
POSTED_FILE = "posted_deals.json"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

RSS_FEED_URL = "https://www.amazon.ca/gp/rss/bestsellers/aps"

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def start_web():
    app.run(host="0.0.0.0", port=10000)

def load_posted():
    try:
        with open(POSTED_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_posted(data):
    with open(POSTED_FILE, "w") as f:
        json.dump(data, f)

def should_post(product_id, posted):
    if product_id in posted:
        last_posted = datetime.fromisoformat(posted[product_id])
        return datetime.now() - last_posted > timedelta(days=30)
    return True

def cleanup_old_posts(posted, days=30):
    cutoff = datetime.now() - timedelta(days=days)
    return {k: v for k, v in posted.items() if datetime.fromisoformat(v) > cutoff}

def add_affiliate_tag(url, tag):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["tag"] = tag
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def send_discord_notification(message):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
    except Exception as e:
        print("Failed to send Discord notification:", e)

def get_rss_deals():
    feed = feedparser.parse(RSS_FEED_URL)
    deals = []
    for entry in feed.entries:
        try:
            title = entry.title
            link = entry.link
            affiliate_link = add_affiliate_tag(link, AFFILIATE_TAG)
            deals.append({
                "id": entry.id.split('/')[-1],
                "title": title,
                "title_en": title,
                "title_fr": title,
                "url": link,
                "affiliate_link": affiliate_link,
                "image": entry.media_content[0]['url'] if 'media_content' in entry else ""
            })
        except Exception as e:
            print("Erreur parsing RSS:", e)
    return deals

def post_to_facebook(product):
    try:
        message = (
            f"{product['title_fr']}\n\n"
            f"🔗 {product['affiliate_link']}\n"
            f"(Contient un lien affilié Amazon)\n\n"
            f"#deal #rabais #promo #amazon #bonplan\n\n"
            f"{product['title_en']}\n"
            f"Affiliate link: {product['affiliate_link']}\n"
            f"(This is an Amazon affiliate link)"
        )

        payload = {
            'url': product['image'],
            'caption': message,
            'access_token': FACEBOOK_PAGE_TOKEN
        }

        response = requests.post(
            f"https://graph.facebook.com/{FACEBOOK_PAGE_ID}/photos",
            data=payload
        )

        print("Posted to Facebook:", response.status_code, response.text)
        send_discord_notification(f"✅ Deal posted to Facebook: {product['title_en']}")
    except Exception as e:
        error_msg = f"Erreur lors de la publication Facebook: {e}"
        print(error_msg)
        send_discord_notification(f"❌ {error_msg}")

def run_bot_loop():
    while True:
        posted = load_posted()
        posted = cleanup_old_posts(posted)
        deals = get_rss_deals()

        found = False
        for deal in deals:
            if should_post(deal["id"], posted):
                post_to_facebook(deal)
                posted[deal["id"]] = datetime.now().isoformat()
                save_posted(posted)
                found = True
                break

        if not found:
            print("No new deals to post right now.")
        print("Waiting 1 hour before next post...")
        time.sleep(60 * 60)

if __name__ == "__main__":
    threading.Thread(target=start_web).start()
    run_bot_loop()
