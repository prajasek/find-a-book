import json
from dataclasses import asdict
from flask import Flask, jsonify, request, Response
from patchright.sync_api import Page, sync_playwright
from book import Book
from config import DEBUG_MODE, HEADLESS_MODE, SLOW_MO
from _helpers import _setup_debug
from _formatters import format_by_location, format_detailed, format_want_to_read_books
from goodreads import get_goodreads_books
from library import Library


app = Flask(__name__)


@app.route("/<string:action>")
def index(action):

    if action not in {"library", "goodreads", "run"}:
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

        query_type, books = run(page, action)
    
        print("="*30 + "Search Complete" + "="*100)
        print(books)

        browser.close()


        if not books:
            return "Not Found", 404

        # Format response by type of request

        # list want to read books from goodreads
        if query_type == "goodreads":
            formatted_resp = format_want_to_read_books(books)
            return Response(formatted_resp, mimetype="text/plain")

        # do just library search for json book list persisted from last 
        # goodreads parsing
        if query_type == "library":
            formatted_resp: str = format_detailed(books)
            return Response(formatted_resp, mimetype="text/plain")

        # goodreads -> get want-to-read book -> library -> search
        if query_type == "full_run":
            formatted_resp: str = format_by_location(books)
            return Response(formatted_resp, mimetype="text/plain")
    
        return "Book list empty", 404



def run(page: Page, action: str) -> tuple[str, list[Book] | None]:
    _setup_debug(page)

    books: list[Book] = []

    if action != "run":
        if action == "goodreads":
            books = get_goodreads_books(page)
            return "goodreads", books

        # skipping goodreads parsing, read directly from json file if available
        if not books:
            file = open("goodreads_books.json","r", encoding="utf-8")
            _books_list: list[Book] = [Book(book["title"], book["author"]) for book in json.load(file)]
            if not _books_list:
                return []
            books.extend(_books_list)
            file.close()

        # search library
        if action =="library":
            library_handler = Library(page)
            library_handler.search_books(books)
            return "library", books

    elif action == "run":
        books = get_goodreads_books(page)
        library_handler = Library(page)
        library_handler.search_books(books)
        return "full_run", books

    if DEBUG_MODE:
        with open("search_results_unformatted.json", "w", encoding="utf-8") as output_file:
            json.dump([asdict(book) for book in books], output_file, ensure_ascii=False, indent=4)

    return "error", None




if __name__ == "__main__":
    app.run('0.0.0.0', port=8080)

   
