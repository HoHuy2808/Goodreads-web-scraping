import re
import requests

from bs4 import BeautifulSoup
from tqdm import tqdm
from dotenv import load_dotenv
from operate import get_book

headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    'Accept-language': 'US-en'}


def get_data():

    book_data = []
    bookList = get_book()

    for idx, book in tqdm(enumerate(bookList)):

        book_url = bookList[idx]
        response = requests.get(book_url, headers=headers) 
        soup = BeautifulSoup(response.text, "html.parser")

        print(f"Scraping book {book_url.split("/book/show/")[-1]}")

        div = soup.find("div",{"class":"BookPage__mainContent"})

        if div is None:
            print(f"Skipping {book_url} — book not found")
            continue

        # Title
        book_title = div.find("h1",{"class":"Text Text__title1"}).text.replace("'"," ")

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
        book_detail = div.find("span",{"class":"Formatted"}).text

        dict = {'Title': book_title,
                    'Author': book_author,
                    'Ratings': book_rating,
                    'Genres': book_genres,
                    'Detail': book_detail}
        book_data.append(dict)

    return book_data

data = get_data()