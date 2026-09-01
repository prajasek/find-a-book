from flask import Flask, send_file
from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from config import HEADLESS_MODE
from helpers import _setup_debug
from goodreads import login, scrape_books
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
            args=[
                "--disable-dev-shm-usage",  # Crucial: Forces Chrome to use main RAM instead of tiny /dev/shm
                "--no-sandbox",             # Prevents container sandbox restriction crashes
                "--disable-setuid-sandbox",
                "--disable-gpu" 
            ]
        )

        page = browser.new_page()
        _setup_debug(page)


        books: list[dict] = []    
    
        if "books.json" not in os.listdir():
            login(page)
            print("Login Done...")
            books.extend(scrape_books(page))

        else:
            file = open("books.json","r")
            books.extend(json.load(file))
            file.close()

        if not books:
            return "No books in want-to-read list."
        
        library_handler = Library(page)
        library_handler.get_books_available(books)

        browser.close()




    return send_file(
            "books.json", 
            mimetype="application/json")


if __name__ == "__main__":
    app.run('0.0.0.0', port=8080)

   
