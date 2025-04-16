
import json
import requests
import time
from datetime import datetime

PAGE_ID = "618570708006552"
ACCESS_TOKEN = "EAAYKhaZAQ9jEBOZB2TWdsdoPhYDs6PktySHb7Ey3sh89zO09qI1Mqyvg2ZB8kskExuZAJMTRjMJexNZAdE2BWUZCgWjPZAUpkZBONZAjDDiAXLVORYcJ2LFKguGRKZCHZAcHduHsHigiTB0jhEtUikxIsdAMBJnSqUogj9ZCEUFWCvsONIVPn4EJ0ZCX6ZCApDCUAp50ep"

PRODUCTS_FILE = "products.json"
POSTED_FILE = "posted_deals.json"
LOG_FILE = "logs.txt"

def load_json(file_path, default):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def log_error(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def post_to_facebook(message):
    url = f"https://graph.facebook.com/{PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    return response.status_code == 200

def format_post(product):
    return f"""🔥 {product['title_fr']}
{product['description_fr']}
💸 Prix régulier : {product['regular_price']} $ | Rabais : {product['discount_percent']} %
🔗 {product['affiliate_link']}

🔥 {product['title_en']}
{product['description_en']}
💸 Regular Price: ${product['regular_price']} | Discount: {product['discount_percent']} %
🔗 {product['affiliate_link']}

📌 Lien affilié Amazon / Amazon affiliate link."""

def main():
    posted = load_json(POSTED_FILE, [])
    products = load_json(PRODUCTS_FILE, [])
    count = 0

    for product in products:
        if product["id"] in posted:
            continue
        try:
            message = format_post(product)
            if post_to_facebook(message):
                posted.append(product["id"])
                save_json(posted, POSTED_FILE)
                count += 1
                if count >= 5:
                    break
            time.sleep(2)
        except Exception as e:
            log_error(str(e))

if __name__ == "__main__":
    main()
