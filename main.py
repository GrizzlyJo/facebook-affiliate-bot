import json
import time
import requests
from datetime import datetime, timedelta

PAGE_ID = "618570708006552"
ACCESS_TOKEN = "EAAYKhaZAQ9jEBOZB2TWdsdoPhYDs6PktySHb7Ey3sh89zO09qI1Mqyvg2ZB8kskExuZAJMTRjMJexNZAdE2BWUZCgWjPZAUpkZBONZAjDDiAXLVORYcJ2LFKguGRKZCHZAcHduHsHigiTB0jhEtUikxIsdAMBJnSqUogj9ZCEUFWCvsONIVPn4EJ0ZCX6ZCApDCUAp50ep"

def load_products():
    with open("products.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_posted():
    try:
        with open("posted_deals.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_posted(posted):
    with open("posted_deals.json", "w", encoding="utf-8") as f:
        json.dump(posted, f, indent=2)

def post_to_facebook(product):
    message = f"""🔥 {product['title_fr']} / {product['title_en']}

💥 {product['description_fr']}
💥 {product['description_en']}

💸 Prix régulier: {product['original_price']}$
🎯 Prix réduit: {product['discounted_price']}$
🟢 Rabais: {product['discount']}%

🔗 Lien Amazon affilié / Amazon Affiliate Link:
{product['affiliate_link']}

🛑 *Ce lien est un lien affilié. En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.*
"""

    image_url = product.get("image_url", "")
    url = f"https://graph.facebook.com/{PAGE_ID}/photos"
    payload = {
        "url": image_url,
        "caption": message,
        "access_token": ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    print(response.json())
    return response.status_code == 200

def main_loop():
    print("🔁 Bot démarré...")
    while True:
        try:
            products = load_products()
            posted = load_posted()

            for product in products:
                deal_id = product["id"]
                if deal_id not in posted:
                    print(f"📢 Publication de : {product['title_en']}")
                    success = post_to_facebook(product)
                    if success:
                        posted[deal_id] = str(datetime.now())
                        save_posted(posted)
                        print("✅ Posté avec succès !")
                    else:
                        print("❌ Erreur de publication.")
                    break  # une seule publication par cycle

        except Exception as e:
            print(f"[ERREUR] {e}")
            with open("logs.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"{datetime.now()}: {str(e)}\n")

        print("⏳ Attente de 2 heures...")
        time.sleep(2 * 60 * 60)  # 2 heures

if __name__ == "__main__":
    main_loop()
