from dataclasses import asdict

from flask import Flask, request
from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from book import Book
from config import HEADLESS_MODE, SLOW_MO
from helpers import _setup_debug
from goodreads import goodreads_login, scrape_books
from library import Library
import os
import json


app = Flask(__name__)

@app.route("/<string:action>")
def index(action):

    if action not in {"search", "goodreads_update"}:
        return "Not Found", 404

    print(f"Starting...path={request.path}, action={action}")
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
    
        if action == "goodreads_update":
            goodreads_login(page)
            goodreads_books = scrape_books(page)

        elif action == "search":
            file = open("goodreads_books.json","r", encoding="utf-8")
            _books_list: list[Book] = [Book(book["title"], book["author"]) for book in json.load(file)]
            goodreads_books.extend(_books_list)
            file.close()
  


        if not goodreads_books:
            return "No books in want-to-read list."

        if action == "search":
            library_handler = Library(page)
            library_handler.get_books_available(goodreads_books)


        with open("search_results.json", "w", encoding="utf-8") as output_file:
            json.dump([asdict(book) for book in goodreads_books], output_file, ensure_ascii=False, indent=4)


        print(goodreads_books)

        print("FINISHED." + "="*30)
        # print(asdict(goodreads_books[0]))

        browser.close()

        result = [asdict(book) for book in goodreads_books]

        print(result)

        return result

if __name__ == "__main__":
    app.run('0.0.0.0', port=8080)

   
