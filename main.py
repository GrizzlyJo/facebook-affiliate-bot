import json
import time
import requests
import threading
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from flask import Flask

FACEBOOK_PAGE_ID = "618570708006552"
FACEBOOK_PAGE_TOKEN = "EAAYKhaZAQ9jEBOZB2TWdsdoPhYDs6PktySHb89zO09qI1Mqyvg2ZB8kskExuZAJMTRjMJexNZAdE2BWUZCgWjPZAUpkZBONZAjDDiAXLVORYcJ2LFKguGRKZCHZAcHduHsHigiTB0jhEtUikxIsdAMBJnSqUogj9ZCEUFWCvsONIVPn4EJ0ZCX6ZCApDCUAp50ep"
AFFILIATE_TAG = "facebook_page01-20"
POSTED_FILE = "posted_deals.json"

# Faux serveur web pour Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def start_web():
    app.run(host="0.0.0.0", port=10000)  # Port 10000 = requis par Render (ou autre que tu veux)

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

def get_mock_deals():
    return [
        {
            "id": "B0CXYZ123",
            "title": "Montre intelligente HD pour hommes et femmes avec plus de 120 modes sportifs",
            "title_en": "Smartwatch HD for Men and Women with 120+ Sport Modes",
            "image": "https://m.media-amazon.com/images/I/61Jw1rBmf4L._AC_SX679_.jpg",
            "url": "https://www.amazon.ca/dp/B0CXYZ123",
            "old_price": "199.99",
            "price": "39.99",
            "discount": 81
        }
    ]

def post_to_facebook(product):
    message = f"""🔥 {product['title']}

💸 {product['discount']}% de rabais
💰 Était {product['old_price']}$, maintenant {product['price']}$

📦 Lien affilié : {product['affiliate_link']}
(Contient un lien affilié Amazon)

#deal #rabais #promotion #amazon #bonplan

🔥 {product['title_en']}
💸 {product['discount']}% off
💰 Was ${product['old_price']}, now ${product['price']}

📦 Affiliate link: {product['affiliate_link']}
(This is an Amazon affiliate link)
"""
    image_url = product['image']
    payload = {
        'url': image_url,
        'caption': message,
        'access_token': FACEBOOK_PAGE_TOKEN
    }

    response = requests.post(
        f'https://graph.facebook.com/{FACEBOOK_PAGE_ID}/photos',
        data=payload
    )

    print("Posted to Facebook:", response.status_code, response.text)

def run_bot_loop():
    while True:
        posted = load_posted()
        posted = cleanup_old_posts(posted)
        deals = get_mock_deals()

        found = False
        for deal in deals:
            if should_post(deal["id"], posted):
                deal["affiliate_link"] = add_affiliate_tag(deal["url"], AFFILIATE_TAG)
                post_to_facebook(deal)
                posted[deal["id"]] = datetime.now().isoformat()
                save_posted(posted)
                found = True
                break

        if not found:
            print("No new deals to post right now.")

        print("Waiting 2 hours before next post...")
        time.sleep(2 * 60 * 60)  # 2 heures

if __name__ == "__main__":
    threading.Thread(target=start_web).start()  # Lancer faux serveur web
    run_bot_loop()  # Lancer le bot
