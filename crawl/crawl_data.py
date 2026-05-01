import os
import requests
import json

from bs4 import BeautifulSoup
from tqdm import tqdm
from operate import (
    get_book, 
    get_data_from_script, 
    get_publisher
)
import get_variables as gvar

headers = {
    'User-Agent': gvar.user_agent,
    'Accept-language': 'US-en'}

def get_data(num_genres=40, max_page=20):

    book_data = []
    bookList = get_book(num_genres=num_genres, max_page=max_page)

    for book in bookList:

        book_url = book
        response = requests.get(book_url, headers=headers) 
        soup = BeautifulSoup(response.text, "html.parser")
        div = soup.find("div",{"class":"BookPage__mainContent"})

        script_data = get_data_from_script(soup)

        name = book_url.split("/book/show/")[-1]
        print(f"Scraping book {name}")

        if div is None:
            print(f"Skipping {book_url} — book not found")
            continue

        # Name
        book_name = div.find("h1",{"class":"Text Text__title1"}).text.replace("'"," ").replace(":","")

        # Author
        book_author = div.find("span",{"class":"ContributorLink__name"}).text

        # Publisher
        publisher = get_publisher(soup)

        # ISBN
        isbn = script_data.get("isbn", "null")


        # Book format
        book_format = script_data.get("bookFormat", "null")
        
        # Awards
        award = script_data.get("awards", "null")
        
        # Language
        language = script_data.get("inLanguage", "null")

        # Total pages for each book
        detail = soup.find("div", {"class":"BookDetails"})
        total_pages = detail.find("p", {"data-testid":"pagesFormat"}).text.split(" pages")[0]

        # Genres
        sub_div = soup.find("ul",{"class":"CollapsableList"})
        if sub_div is None:
            print(f"Genres not found")
            book_genres = 'null'
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
            'name': book_name,
            'isbn': isbn,
            'author': book_author,
            'publisher': publisher,
            'award': award,
            'language':language,
            'rating': book_rating,
            'total_ratings': total_rating,
            'total_reviews': total_review,
            'format': book_format,
            'pages': total_pages,
            'genres': book_genres,
            'description': book_description,
            'url': book_url
        }
        book_data.append(dict)

    return book_data

if __name__ == "__main__":
    data = get_data(num_genres=2, max_page=2)

    os.makedirs("data", exist_ok=True)

    with open("data/book_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print("Goodreads crawl successfully")