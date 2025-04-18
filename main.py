
import json
import time
import requests
import threading
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from flask import Flask

FACEBOOK_PAGE_ID = "618570708006552"
FACEBOOK_PAGE_TOKEN = "EAAYKhaZAQ9jEBOZB2TWdsdoPhYDs6PktySHb89zO09qI1Mqyvg2ZB8kskExuZAJMTRjMJexNZAdE2BWUZCgWjPZAUpkZBONZAjDDiAXLVORYcJ2LFKguGRKZCHZAcHduHsHigiTB0jhEtUikxIsdAMBJnSqUogj9ZCEUFWCvsONIVPn4EJ0ZCX6ZCApDCUAp50ep"
AFFILIATE_TAG = "facebook_page01-20"
ACCESS_KEY = os.environ.get("AMAZON_ACCESS_KEY")
SECRET_KEY = os.environ.get("AMAZON_SECRET_KEY")
POSTED_FILE = "posted_deals.json"

REGION = "ca"
SERVICE = "ProductAdvertisingAPI"
HOST = "webservices.amazon.ca"
ENDPOINT = f"https://{HOST}/paapi5/searchitems"

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def start_web():
    app.run(host="0.0.0.0", port=10000)

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def get_signature_key(key, dateStamp, regionName, serviceName):
    kDate = sign(("AWS4" + key).encode("utf-8"), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, "aws4_request")
    return kSigning

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

def get_real_deals():
    now = datetime.utcnow()
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    datestamp = now.strftime('%Y%m%d')

    payload = {
        "Keywords": "deal",
        "SearchIndex": "All",
        "Resources": [
            "Images.Primary.Large",
            "ItemInfo.Title",
            "Offers.Listings.Price",
            "Offers.Listings.SavingBasis"
        ],
        "PartnerTag": AFFILIATE_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.ca"
    }


    request_payload = json.dumps(payload)
    canonical_uri = "/paapi5/searchitems"
    canonical_headers = f"content-encoding:utf-8\ncontent-type:application/json; charset=utf-8\nhost:{HOST}\nx-amz-date:{amz_date}\n"
    signed_headers = "content-encoding;content-type;host;x-amz-date"
    payload_hash = hashlib.sha256(request_payload.encode("utf-8")).hexdigest()

    canonical_request = f"POST\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{datestamp}/{REGION}/{SERVICE}/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    signing_key = get_signature_key(SECRET_KEY, datestamp, REGION, SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    headers = {
        "Content-Encoding": "utf-8",
        "Content-Type": "application/json; charset=utf-8",
        "Host": HOST,
        "X-Amz-Date": amz_date,
        "Authorization": f"{algorithm} Credential={ACCESS_KEY}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    }

    response = requests.post(ENDPOINT, data=request_payload, headers=headers)
    if response.status_code != 200:
        print("Amazon API error:", response.status_code, response.text)
        return []

    data = response.json()
    deals = []

    for item in data.get("SearchResult", {}).get("Items", []):
        try:
            title = item["ItemInfo"]["Title"]["DisplayValue"]
            image = item["Images"]["Primary"]["Large"]["URL"]
            asin = item["ASIN"]
            url = f"https://www.amazon.ca/dp/{asin}"
            price_info = item["Offers"]["Listings"][0]["Price"]
            saving_basis = item["Offers"]["Listings"][0].get("SavingBasis", {}).get("Amount")
            new_price = float(price_info["Amount"])
            old_price = float(saving_basis) if saving_basis else new_price
            discount = int(100 - ((new_price / old_price) * 100)) if old_price > new_price else 0

            if discount >= 30:
                deals.append({
                    "id": asin,
                    "title": title,
                    "title_en": title,
                    "image": image,
                    "url": url,
                    "old_price": f"{old_price:.2f}",
                    "price": f"{new_price:.2f}",
                    "discount": discount
                })
        except Exception as e:
            print("Erreur parsing produit:", e)

    return deals

def post_to_facebook(product):
    message = (
        f"{product['title_fr']}\n\n"
        f"{product['discount_percent']}% de rabais\n"
        f"Prix régulier : {product['regular_price']}$\n\n"
        f"Lien affilié : {product['affiliate_link']}\n"
        f"(Contient un lien affilié Amazon)\n\n"
        f"#deal #rabais #promo #amazon #bonplan\n\n"
        f"{product['title_en']}\n"
        f"{product['discount_percent']}% off\n"
        f"Regular price: ${product['regular_price']}\n\n"
        f"Affiliate link: {product['affiliate_link']}\n"
        f"(This is an Amazon affiliate link)"
    )

    image_url = "https://m.media-amazon.com/images/I/61Jw1rBmf4L._AC_SX679_.jpg"  # Si tu n'as pas d'image dans le JSON

    payload = {
        'url': image_url,
        'caption': message,
        'access_token': FACEBOOK_PAGE_TOKEN
    }

    response = requests.post(
        f"https://graph.facebook.com/{FACEBOOK_PAGE_ID}/photos",
        data=payload
    )

    print("Posted to Facebook:", response.status_code, response.text)



def run_bot_loop():
    while True:
        posted = load_posted()
        posted = cleanup_old_posts(posted)
        deals = get_real_deals()

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
        time.sleep(2 * 60 * 60)

if __name__ == "__main__":
    threading.Thread(target=start_web).start()
    run_bot_loop()
