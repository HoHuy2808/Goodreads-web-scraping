import os
import json
import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime

import get_variables as gvar

headers = {
    'User-Agent': gvar.user_agent,
    'Accept-language': 'US-en'}

def get_genres(soup):
    sub_div = soup.find("ul",{"class":"CollapsableList"})
    if sub_div is None:
        print(f"Genres not found")
        book_genres = None
    else:
        raw_genres = sub_div.find_all("span",{"class":"Button__labelItem"})
        genres = [genre.get_text(strip=True) for genre in raw_genres if genre.get_text(strip=True)!="...more"]
        book_genres = ", ".join(genres)

    return book_genres

def get_author(soup):
    div_tag = soup.find("div", {'class':'ContributorLinksList'})
    authors = div_tag.find_all("a", {"class": "ContributorLink"})

    unique_authors = {}
    for author in authors:
        href = author.get("href", "")
        
        author_id = href.split("/author/show/")[1].split(".")[0]
        
        author_name = author.find(
            "span",
            {"class": "ContributorLink__name"}
        ).text.strip()

        # Use author_id as key to remove duplicate author_id
        unique_authors[author_id] = {
            "author_id": author_id,
            "author_name": author_name
        }

    return list(unique_authors.values())

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
                if aff:
                    price = aff.get("ebookPrice")
                else:
                    price = None
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
    """Crawl data from structured metadata embedded inside HTML page """
    script = soup.find("script", {"type": "application/ld+json"}).string
    result = json.loads(script)
    
    return result

