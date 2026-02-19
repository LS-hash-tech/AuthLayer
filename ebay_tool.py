#we need to compelete the following to get this working:

#A function that takes an eBay URL or item ID
#Extracts the item ID from the URL if needed
#Calls that endpoint with your auth headers
#Returns the relevant fields

import requests
import os
from dotenv import load_dotenv

load_dotenv()

url = "https://www.ebay.co.uk/itm/386728815164"

extract_item_id = url.split("/")[-1]

print(extract_item_id)

def get_id_from_url(url):
    return url.split("/")[-1]

print(get_id_from_url(url))

def get_ebay_token():
    app_id=os.getenv("EBAY_APP_ID")
    cert_id= os.getenv("EBAY_CERT_ID")

    url = "https://api.ebay.com/identity/v1/oauth2/token"

    response = requests.post(
        url,
        auth=(app_id, cert_id),
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
    )

    token = response.json()["access_token"]
    return token

def get_listing(item_id, token):
    url = f"https://api.ebay.com/buy/browse/v1/item/v1|{item_id}|0"

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
    }

    response = requests.get(url, headers=headers)
    return response.json()

token = get_ebay_token()
print("token:", token[:20], "...")

item_id = get_id_from_url("https://www.ebay.co.uk/itm/386728815164")
listing = get_listing(item_id, token)

print(listing["title"])
print(listing["description"])
print(listing["brand"])
print(listing["condition"])
print(listing["type"])
print(listing["category"])