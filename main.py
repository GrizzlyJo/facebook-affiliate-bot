import requests
import json
import time
import random
from datetime import datetime, timedelta

FACEBOOK_PAGE_ID = '618570708006552'
FACEBOOK_PAGE_TOKEN = 'TON_TOKEN_ICI'
TRACKING_ID = 'facebook_page01-20'
POSTED_DEALS_FILE = 'posted_deals.json'
POST_INTERVAL_HOURS = 2

MOCK_DEALS = [
    {
        "title": "Winter Running Gloves - Touchscreen, Thermal, Anti-Slip",
        "url": "https://amzn.to/4jAeKBW",
        "image": "https://m.media-amazon.com/images/I/71A7AzW6MML._AC_SL1500_.jpg",
        "old_price": 17.99,
        "new_price": 8.99,
        "discount_code": "992KHXGG"
    },
    {
        "title": "Smartwatch HD 4.7cm - IP68, Calls, Heart Monitor",
        "url": "https://amzn.to/4ipG0C9",
        "image": "https://m.media-amazon.com/images/I/71qghTAI3tL._AC_SL1500_.jpg",
        "old_price": 99.99,
        "new_price": 18.99
    }
]

def load_posted_deals():
    try:
        with open(POSTED_DEALS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_posted_deal(asin):
    deals = load_posted_deals()
    deals[asin] = datetime.now().isoformat()
    with open(POSTED_DEALS_FILE, 'w') as f:
        json.dump(deals, f)

def was_posted_recently(asin):
    deals = load_posted_deals()
    if asin not in deals:
        return False
    last_posted = datetime.fromisoformat(deals[asin])
    return datetime.now() - last_posted < timedelta(days=30)

def publish_to_facebook(title, image_url, price, old_price, link, code=None):
    discount_text = f"🔥 Save {int((1 - price / old_price) * 100)}% — Was ${old_price:.2f}, now ${price:.2f}!"
    if code:
        discount_text += f"\n🎁 Promo Code: {code}"

    post_text = (
        f"{title}\n\n"
        f"{discount_text}\n\n"
        f"🛒 Shop now (Amazon Affiliate): {link}\n\n"
        f"📦 Livraison rapide | 🇨🇦 Amazon Canada\n\n"
        f"🔗 Lien affilié Amazon - Merci de votre soutien!"
    )

    url = f"https://graph.facebook.com/{FACEBOOK_PAGE_ID}/photos"
    payload = {
        'url': image_url,
        'caption': post_text,
        'access_token': FACEBOOK_PAGE_TOKEN
    }

    response = requests.post(url, data=payload)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Post sent: {response.status_code}")
    return response.status_code == 200

def run_bot():
    while True:
        print("🔍 Looking for new deals...")

        random.shuffle(MOCK_DEALS)
        for deal in MOCK_DEALS:
            asin = deal['url'].split("/")[-1]
            if was_posted_recently(asin):
                print(f"⏩ Skipping already posted deal: {asin}")
                continue

            success = publish_to_facebook(
                title=deal["title"],
                image_url=deal["image"],
                price=deal["new_price"],
                old_price=deal["old_price"],
                link=deal["url"],
                code=deal.get("discount_code")
            )

            if success:
                save_posted_deal(asin)
                break

        print(f"🕒 Sleeping for {POST_INTERVAL_HOURS}h...")
        time.sleep(POST_INTERVAL_HOURS * 3600)

if __name__ == '__main__':
    run_bot()