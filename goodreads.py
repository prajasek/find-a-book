from flask import Flask, send_file
from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from helpers import login, scrape_books
import os

app = Flask(__name__)

@app.route("/scrape")
def index():

    if "books.json" not in os.listdir():
        print("Starting...")
        with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=False, 
                    args=[
                        "--disable-dev-shm-usage",  # Crucial: Forces Chrome to use main RAM instead of tiny /dev/shm
                        "--no-sandbox",             # Prevents container sandbox restriction crashes
                        "--disable-setuid-sandbox",
                        "--disable-gpu" 
                    ]
                )
        
                page = browser.new_page()
        
                login(page)
                print("Login Done...")

                scrape_books(page)
        
                browser.close()

    return send_file(
            "books.json", 
            mimetype="application/json", 
            as_attachment=False)


if __name__ == "__main__":
    app.run('0.0.0.0', port=8080)

   
