import os
import requests
import json

from bs4 import BeautifulSoup
from tqdm import tqdm
from operate import get_book

headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    'Accept-language': 'US-en'}

def get_data(num_genres=40, max_page=20):

    book_data = []
    bookList = get_book(num_genres=num_genres, max_page=max_page)

    for book in bookList:

        book_url = book
        response = requests.get(book_url, headers=headers) 
        soup = BeautifulSoup(response.text, "html.parser")
        div = soup.find("div",{"class":"BookPage__mainContent"})

        name = book_url.split("/book/show/")[-1]
        print(f"Scraping book {name}")

        if div is None:
            print(f"Skipping {book_url} — book not found")
            continue

        # Title
        book_title = div.find("h1",{"class":"Text Text__title1"}).text.replace("'"," ").replace(":","")

        # Author
        book_author = div.find("span",{"class":"ContributorLink__name"}).text

        # Ratings
        book_rating = div.find("div", {"class":"RatingStatistics__rating"}).text

        # Genres
        sub_div = soup.find("ul",{"class":"CollapsableList"})
        if sub_div is None:
            print(f"Genres not found")
            book_genres = 'null'
        else:
            raw_genres = sub_div.find_all("span",{"class":"Button__labelItem"})
            genres = [genre.get_text(strip=True) for genre in raw_genres if genre.get_text(strip=True)!="...more"]
            book_genres = ", ".join(genres)

        # Details
        book_detail = div.find("span",{"class":"Formatted"}).text.replace("\"", "'")

        dict = {'Title': book_title,
                    'Author': book_author,
                    'Ratings': book_rating,
                    'Genres': book_genres,
                    'Detail': book_detail}
        book_data.append(dict)


    return book_data

if __name__ == "__main__":
    data = get_data(num_genres=2, max_page=2)

    os.makedirs("data", exist_ok=True)

    with open("data/book_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
