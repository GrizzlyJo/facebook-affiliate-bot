import json
import time
import random
import requests
from datetime import datetime, timedelta

PAGE_ID = "618570708006552"
ACCESS_TOKEN = "EAAYKhaZAQ9jEBOZB2TWdsdoPhYDs6PktySHb7Ey3sh89zO09qI1Mqyvg2ZB8kskExuZAJMTRjMJexNZAdE2BWUZCgWjPZAUpkZBONZAjDDiAXLVORYcJ2LFKguGRKZCHZAcHduHsHigiTB0jhEtUikxIsdAMBJnSqUogj9ZCEUFWCvsONIVPn4EJ0ZCX6ZCApDCUAp50ep"
AFFILIATE_TAG = "facebook_page01-20"
POSTED_FILE = "posted_deals.json"

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

def get_mock_deals():
    return [
        {
            "id": "B0CXYZ123",
            "title_en": "Smartwatch HD for Men and Women with 120+ Sport Modes - 81% OFF!",
            "title_fr": "Montre intelligente HD pour hommes et femmes avec plus de 120 modes sportifs - 81% DE RABAIS!",
            "image": "https://m.media-amazon.com/images/I/61Jw1rBmf4L._AC_SX679_.jpg",
            "url": "https://www.amazon.ca/dp/B0CXYZ123",
            "old_price": "199.99$",
            "new_price": "39.99$"
        }
    ]

def create_facebook_post(deal):
    message = f"{deal['title_en']} / {deal['title_fr']}\nWas {deal['old_price']} now only {deal['new_price']}!\nAmazon Affiliate Link: {deal['url']}?tag={AFFILIATE_TAG}\n#Deals #Amazon #Rabais #Promo"
    image_url = deal["image"]
    post_url = f"https://graph.facebook.com/{PAGE_ID}/photos"
    payload = {
        "url": image_url,
        "caption": message,
        "access_token": ACCESS_TOKEN
    }
    response = requests.post(post_url, data=payload)
    print("Posted to Facebook:", response.status_code, response.text)

def main():
    posted = load_posted()
    deals = get_mock_deals()

    for deal in deals:
        if should_post(deal["id"], posted):
            create_facebook_post(deal)
            posted[deal["id"]] = datetime.now().isoformat()
            save_posted(posted)
        else:
            print(f"Deal {deal['id']} already posted in the last 30 days.")

if __name__ == "__main__":
    main()