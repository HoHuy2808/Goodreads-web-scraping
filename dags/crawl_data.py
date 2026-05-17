import os
import requests
import json

from bs4 import BeautifulSoup
from operate import (
    get_genres,
    get_author,
    parse_awards,
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

def get_data(start=1, end=100, **kwargs) -> list:
    ti = kwargs['ti']

    book_data = []
    
    for book_id in range(start, end+1):
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
        author = get_author(soup)

        # Book's ISBN
        isbn = script_data.get("isbn", "null")
        
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
        raw_award = script_data.get("awards", "null")
        award = parse_awards(raw_award)

        # Price
        price = get_price(soup)

        # Language
        language = script_data.get("inLanguage", "null")

        # Total pages for each book
        pages = str(script_data.get("numberOfPages","null"))

        # Genres
        book_genres = get_genres(soup)

        # Ratings
        book_rating = div.find("div", {"class":"RatingStatistics__rating"}).text

        # Total number of ratings
        total_rating = soup.find("span", {"data-testid":"ratingsCount"}).text.split()[0]

        # Total reviews
        total_review = soup.find("span",{"data-testid":"reviewsCount"}).text.split()[0]

        # Descriptions
        book_description = div.find("span",{"class":"Formatted"}).text

        book_dict = {
            'Goodreads ID': book_id,
            'name': book_name,
            'isbn': isbn,
            'format': book_format,
            'authors': author,
            'publisher': publisher,
            'publish_date': publish_date,
            'genres': book_genres,
            'awards': award,
            'price': price,
            'language':language,
            'rating': book_rating,
            'total_ratings': total_rating,
            'total_reviews': total_review,
            'pages': pages,
            'description': book_description,
            'url': book_url
        }
        book_data.append(book_dict)

        ti.xcom_push(key='book_data', value=json.dumps(book_data))
        
    return book_data

# if __name__ == "__main__":
#     data = get_data(start=238,end=238)

#     os.makedirs("data", exist_ok=True)

#     with open("data/book_data.json", "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2)
    
#     print("Goodreads crawl successfully")