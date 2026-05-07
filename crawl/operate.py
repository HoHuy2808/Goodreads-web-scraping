import os
import json
import re
import requests
import get_variables as gvar
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

headers = {
    'User-Agent': gvar.user_agent,
    'Accept-language': 'US-en'}

# load env
load_dotenv()
EMAIL = os.getenv("GOODREADS_EMAIL")
PASSWORD = os.getenv("GOODREADS_PASSWORD")

def parse_awards(award_text):
    if not award_text or award_text == "null":
        return []

    awards_list = []

    pattern = r'(.+?)\s*\((\d{4})\)'

    for item in award_text.split(", "):
        match = re.match(pattern, item.strip())

        if match:
            awards_list.append({
                "award_name": match.group(1).strip(),
                "year_won": int(match.group(2))
            })
        else:
            awards_list.append({
                "award_name": item.strip(),
                "year_won": None
            })

    return awards_list

def get_price(soup):
    script = soup.find("script", {"type": "application/json"}).string
    result = json.loads(script)
    json_data = result["props"]["pageProps"]["apolloState"]

    for key, value in json_data.items():
        if key.startswith("Book:"):
            
            links_key = next(
                (k for k in value if k.startswith("links")),
                None
            )
            if links_key:
                details = value[links_key]
                aff = details.get("primaryAffiliateLink", {})
                price = aff.get("ebookPrice")
    
    return price


def get_publish_date_approximate(soup):
    script = soup.find("script", {"type": "application/json"})

    if not script:
        return "null"

    try:
        result = json.loads(script.string)

        json_data = result["props"]["pageProps"]["apolloState"]

        for key, value in json_data.items():

            if key.startswith("Book:"):

                details = value.get("details")

                if details and details.get("publicationTime"):

                    timestamp = details["publicationTime"]

                    date = datetime.fromtimestamp(timestamp / 1000)

                    publish_date = f"{date.strftime('%B')} {date.day}, {date.year}"

                    return publish_date

        return "null"

    except Exception as e:
        print(f"Error extracting publish date: {e}")
        return "null"

def get_publish_date(isbn, soup):

    openlib_url = f"{gvar.openlibrary}/isbn/{isbn}"
    response = requests.get(openlib_url, headers=headers)
    if response == 200:
        openlib = BeautifulSoup(response.text, "html.parser")
        publish_date = openlib.find("span",{"itemprop":"datePublished"}).text
    else:
        publish_date = get_publish_date_approximate(soup)

    return publish_date


def get_publisher(soup):
    script = soup.find("script",{"type":"application/json"}).string
    result = json.loads(script)
    json_data = result["props"]["pageProps"]["apolloState"]
    for key, value in json_data.items():
        if key.startswith("Book:"):
            details = value.get("details")

            if details and details.get("publisher"):
                publisher = details["publisher"]
    return publisher


def get_data_from_script(soup):
    """Crawl data from structured metada embedded inside HTML page """
    script = soup.find("script", {"type": "application/ld+json"}).string
    result = json.loads(script)
    
    return result

