import os
import json
import time
import requests
import get_variables as gvar
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

headers = {
    'User-Agent': gvar.user_agent,
    'Accept-language': 'US-en'}

# load env
load_dotenv()
EMAIL = os.getenv("GOODREADS_EMAIL")
PASSWORD = os.getenv("GOODREADS_PASSWORD")

# Crawl genres
def get_genres():
    genres_url = f"{gvar.goodreads}/genres"
    response = requests.get(genres_url, headers=headers) 
    soup = BeautifulSoup(response.text, "html.parser")
    container = soup.find_all('div', {'class': 'left'})

    genres = []
    for div in container:
        links = div.find_all('a', class_='gr-hyperlink')
        for link in links:

            name = link.text.lower().replace(" ","-").replace("'","")
            genres.append(name)

    return genres


# Crawl book url
def get_genres():
    genres_url = f"{gvar.goodreads}/genres"
    response = requests.get(genres_url, headers=headers) 
    soup = BeautifulSoup(response.text, "html.parser")
    container = soup.find_all('div', {'class': 'left'})

    genres = []
    for div in container:
        links = div.find_all('a', class_='gr-hyperlink')
        for link in links:

            name = link.text.lower().replace(" ","-").replace("'","")
            genres.append(name)

    return genres


# Crawl
def get_book(num_genres=40, max_page=20):

    book_list = []
    genres = get_genres()[:num_genres]

    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # Login
    driver.get(f"{gvar.goodreads}/user/sign_in")

    time.sleep(10)

    if "sign_in" in driver.current_url:
        driver.find_element(By.LINK_TEXT, "Sign in with email").click()

        wait.until(EC.presence_of_element_located((By.ID, "ap_email")))

        driver.find_element(By.ID, "ap_email").send_keys(EMAIL)
        time.sleep(2)

        driver.find_element(By.ID, "ap_password").send_keys(PASSWORD)
        time.sleep(2)
        
        driver.find_element(By.ID, "signInSubmit").click()
        time.sleep(5)
        
        print("Logged in successfully!")
    else:
        print("Already logged in")

        
    for genre in genres:
        print(f"\n Crawling genre: {genre}")

        for page in range(1, max_page + 1):
            url = f"{gvar.goodreads}/shelf/show/{genre}?page={page}"
            driver.get(url)

            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bookTitle")))

            books = driver.find_elements(By.CLASS_NAME, "bookTitle")

            for book in books:
                href = book.get_attribute("href")
                if href:
                    book_list.append(href)

            print(f"Page {page}: {len(books)} books")

        os.makedirs("data", exist_ok=True)
        with open("data/book.json", "w", encoding="utf-8") as f:
            json.dump(book_list, f, indent=2)

    return book_list