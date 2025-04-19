import json
import time
import requests
import threading
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import feedparser
from flask import Flask

# Environment Variables
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN")
AFFILIATE_TAG = "facebook_page01-20"
POSTED_FILE = "posted_deals.json"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# RSS Feed URL
RSS_FEED_URL = "https://www.amazon.ca/gp/rss/bestsellers/aps"

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def start_web():
    app.run(host="0.0.0.0", port=10000)

def load_posted():
    """Loads the posted deals from a file."""
    try:
        with open(POSTED_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_posted(data):
    """Saves the posted deals to a file."""
    with open(POSTED_FILE, "w") as f:
        json.dump(data, f)

def should_post(product_id, posted):
    """Checks whether the product should be posted again."""
    if product_id in posted:
        last_posted = datetime.fromisoformat(posted[product_id])
        return datetime.now() - last_posted > timedelta(days=30)
    return True

def cleanup_old_posts(posted, days=30):
    """Cleans up the old posts."""
    cutoff = datetime.now() - timedelta(days=days)
    return {k: v for k, v in posted.items() if datetime.fromisoformat(v) > cutoff}

def add_affiliate_tag(url, tag):
    """Adds the affiliate tag to the URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["tag"] = tag
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def send_discord_notification(message):
    """Sends a Discord notification."""
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
    except Exception as e:
        print("Failed to send Discord notification:", e)

def get_rss_deals():
    """Fetches the best-selling deals from the Amazon Canada RSS feed."""
    feed = feedparser.parse(RSS_FEED_URL)
    deals = []
    for entry in feed.entries:
        try:
            title = entry.title
            link = entry.link
            affiliate_link = add_affiliate_tag(link, AFFILIATE_TAG)
            deals.append({
                "id": entry.id.split('/')[-1],  # Use the last part of the URL as the ID
                "title": title,
                "title_en": title,
                "title_fr": title,
                "url": link,
                "affiliate_link": affiliate_link,
                "image": entry.media_content[0]['url'] if 'media_content' in entry else ""
            })
        except Exception as e:
            print("Error parsing RSS:", e)
    return deals

def post_to_facebook(product):
    """Posts the product deal to Facebook."""
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
        error_msg = f"Error posting to Facebook: {e}"
        print(error_msg)
        send_discord_notification(f"❌ {error_msg}")

def run_bot_loop():
    """Runs the bot loop that checks deals and posts them."""
    while True:
        posted = load_posted()
        posted = cleanup_old_posts(posted)  # Cleanup any old posts

        deals = get_rss_deals()  # Get new deals from the RSS feed

        found = False
        for deal in deals:
            if should_post(deal["id"], posted):  # Check if deal should be posted
                post_to_facebook(deal)  # Post to Facebook
                posted[deal["id"]] = datetime.now().isoformat()  # Mark as posted
                save_posted(posted)  # Save the updated list of posted deals
                found = True
                break  # Stop after posting one deal (remove this if you want multiple posts)

        if not found:
            print("No new deals to post right now.")
        print("Waiting 1 hour before next post...")
        time.sleep(60 * 60)  # Wait 1 hour before checking again

if __name__ == "__main__":
    # Start the web server on a separate thread
    threading.Thread(target=start_web).start()
    # Run the bot loop
    run_bot_loop()
