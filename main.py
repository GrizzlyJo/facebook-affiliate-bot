import json
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

FACEBOOK_PAGE_ID = "618570708006552"
FACEBOOK_PAGE_TOKEN = "EAAYKhaZAQ9jEBOZB2TWdsdoPhYDs6PktySHb7Ey3sh89zO09qI1Mqyvg2ZB8kskExuZAJMTRjMJexNZAdE2BWUZCgWjPZAUpkZBONZAjDDiAXLVORYcJ2LFKguGRKZCHZAcHduHsHigiTB0jhEtUikxIsdAMBJnSqUogj9ZCEUFWCvsONIVPn4EJ0ZCX6ZCApDCUAp50ep"
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
