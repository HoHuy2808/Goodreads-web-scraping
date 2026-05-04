import os
import requests
import json

from bs4 import BeautifulSoup
from tqdm import tqdm
from operate import (
    # get_asin,
    get_price,
    get_data_from_script, 
    get_publisher,
    get_publish_date,
    get_publish_date_approximate
)
import get_variables as gvar

headers = {
    'User-Agent': gvar.user_agent,
    'Accept-language': 'US-en'}

def get_data(start=1, end=100):

    book_data = []
    
    for book_id in tqdm(range(start, end+1)):

        book_url = f"{gvar.goodreads}/book/show/{book_id}"
        response = requests.get(book_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        print(f"Scraping book ID {book_id}")
        div = soup.find("div",{"class":"BookPage__mainContent"})
    
        if div is None:
            print(f"Skipping {book_url} — book not found")
            continue
        script_data = get_data_from_script(soup)

        # Name
        book_name = div.find("h1",{"class":"Text Text__title1"}).text.replace("'"," ").replace(":","")

        # Author
        book_author = div.find("span",{"class":"ContributorLink__name"}).text

        # Book's ISBN
        isbn = script_data.get("isbn", "null")
        
        # Book's ASIN
        # asin = get_asin(soup)
        
        # Book format
        book_format = script_data.get("bookFormat", "null")

        # Publisher
        publisher = get_publisher(soup)

        # Publish date
        if isbn != "null":
            publish_date = get_publish_date(isbn, soup)
        else:
            publish_date = get_publish_date_approximate(soup)

        # Awards
        award = script_data.get("awards", "null")
        
        # Price
        price = get_price(soup)

        # Language
        language = script_data.get("inLanguage", "null")

        # Total pages for each book
        pages = script_data.get("numberOfPages","null")

        # Genres
        sub_div = soup.find("ul",{"class":"CollapsableList"})
        if sub_div is None:
            print(f"Genres not found")
            book_genres = None
        else:
            raw_genres = sub_div.find_all("span",{"class":"Button__labelItem"})
            genres = [genre.get_text(strip=True) for genre in raw_genres if genre.get_text(strip=True)!="...more"]
            book_genres = ", ".join(genres)


        # Ratings
        book_rating = div.find("div", {"class":"RatingStatistics__rating"}).text

        # Total number of ratings
        total_rating = soup.find("span", {"data-testid":"ratingsCount"}).text.split()[0]

        # Total reviews
        total_review = soup.find("span",{"data-testid":"reviewsCount"}).text.split()[0]

        # Descriptions
        book_description = div.find("span",{"class":"Formatted"}).text

        dict = {
            'Goodreads ID': book_id,
            'name': book_name,
            'isbn': isbn,
            # 'asin': asin,
            'format': book_format,
            'author': book_author,
            'publisher': publisher,
            'publish date': publish_date,
            'genres': book_genres,
            'award': award,
            'price': price,
            'language':language,
            'rating': book_rating,
            'total_ratings': total_rating,
            'total_reviews': total_review,
            'pages': pages,
            'description': book_description,
            'url': book_url
        }
        book_data.append(dict)

    return book_data

if __name__ == "__main__":
    # data = get_data(num_genres=1, max_page=2)
    data = get_data(start=1,end=100)

    os.makedirs("data", exist_ok=True)

    with open("data/book_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print("Goodreads crawl successfully")