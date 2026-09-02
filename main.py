from flask import Flask, send_file
from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from book import Book
from config import HEADLESS_MODE, SLOW_MO
from helpers import _setup_debug
from goodreads import goodreads_login, scrape_books
from library import Library
import os
import json


app = Flask(__name__)

@app.route("/")
def index():

    print("Starting...")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=HEADLESS_MODE,
            slow_mo=SLOW_MO,
            args=[
                "--disable-dev-shm-usage",  # Crucial: Forces Chrome to use main RAM instead of tiny /dev/shm
                "--no-sandbox",             # Prevents container sandbox restriction crashes
                "--disable-setuid-sandbox",
                "--disable-gpu" 
            ]
        )

        page = browser.new_page()
        _setup_debug(page)

        goodreads_books: list[Book] = []    
    
        if "goodreads_books.json" not in os.listdir():
            goodreads_login(page)
            goodreads_books = scrape_books(page)

        else:
            file = open("goodreads_books.json","r", encoding="utf-8")
            _books_list: list[Book] = [Book(**book) for book in json.load(file)]
            goodreads_books.extend(_books_list)
            file.close()

        if not goodreads_books:
            return "No books in want-to-read list."
        
        library_handler = Library(page)
        library_handler.get_books_available(goodreads_books)

        browser.close()




    return send_file(
            "goodreads_books.json", 
            mimetype="application/json")


if __name__ == "__main__":
    app.run('0.0.0.0', port=8080)

   
