import json
from dataclasses import asdict
from flask import Flask, render_template, request, Response, jsonify
from patchright.sync_api import Page, sync_playwright
from book import Book
from config import DEBUG_MODE, HEADLESS_MODE, SLOW_MO
from _helpers import _setup_debug
from storage import Storage
from _formatters import format_by_location, format_detailed, format_want_to_read_books
from goodreads import get_goodreads_books, goodreads_login
from library import Library

app = Flask(__name__)

@app.route("/")
def index():
    print(f"Starting...path={request.path}")
    return render_template("index.html", username="Prasanth")


@app.route("/stored-books")
def retrieve_books():
    print("stored book called")
    storage = Storage()
    books_info = storage.all_books_from_json()
    books_info["type"] = "home"
    return jsonify(books_info)


@app.route("/watch", methods=["POST"])
def watch():
    if request.method != "POST":
        return "Method Not Allowed", 405

    details = request.get_json()

    book_id = details["book_id"]
    watch_status = details["watch"]

    storage = Storage()
    update_sucess, msg = storage.update_watchlist(book_id, watch_status)

    if not update_sucess:
        return {
            "msg": "Update Failed", 
            "status":500
        }
    
    return {
            "msg": msg, 
            "status":200
        }



@app.route("/<string:action>")
def search(action):
    if action not in {"library", "goodreads", "run", "search"}:
        return "Not Found", 404


    if action=="search":
        if not request.args.get("title") or not request.args.get("author"):
            return "Incomplete Request", 400

    print(f"Starting...path={request.path}, action={action}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=HEADLESS_MODE,
            slow_mo=SLOW_MO,
            args=[
                # Crucial: Forces Chrome to use main RAM instead of tiny /dev/shm
                "--disable-dev-shm-usage",
                # Prevents container sandbox restriction crashes
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
            ],
        )

        page = browser.new_page()

        books_info = run(page, action)
        query_type = books_info["type"]

        print("=" * 30 + "Search Complete" + "=" * 100)
        print(books_info)

        browser.close()

        if not books_info["books"]:
            if query_type == "search":
                return "Incomplete/Bad Request", 400
            
            return "Not Found", 404

        # Format response by type of request
        # -----------------------------------
        # list want to read books from goodreads
        if query_type == "goodreads":
            # formatted_resp = format_want_to_read_books(books)
            # return Response(formatted_resp, mimetype="text/plain")
            return jsonify(books_info)

        # do just library search for json book list persisted from last
        # goodreads parsing
        if query_type == "library":
            # formatted_resp: str = format_detailed(books)
            # return Response(formatted_resp, mimetype="text/plain")
            return jsonify(books_info)

        # goodreads -> get want-to-read book -> library -> search
        if query_type == "full_run":
            # formatted_resp: str = format_by_location(books)
            # return Response(formatted_resp, mimetype="text/plain")
            return jsonify(books_info)

        # goodreads -> get want-to-read book -> library -> search
        if query_type == "search":
            # formatted_resp: str = format_by_location(books)
            # return Response(formatted_resp, mimetype="text/plain")
            return jsonify(books_info)



def run(page: Page, action: str) -> tuple[str, list[Book] | None]:
    _setup_debug(page)
    books: list[Book] = []


    if action == "goodreads":
        goodreads_login(page)
        books = get_goodreads_books(page)
        storage = Storage()
        books_info = storage.update_booklist(books)
        books_info["type"]= "goodreads"
        return books_info

    # search library for watch list
    if action == "library":
        storage = Storage()
        books_info: list[dict] = storage.get_watchlist()
        books = books_info["books"]

        book_objects = [Book(book["title"], book["author"]) for book in books]
        print("bookobjects:", book_objects)
        
        library_handler = Library(page)
        library_handler.search_books(book_objects)

        books_info["books"] =  [asdict(book) for book in book_objects]
        books_info["type"]= "library"
        return books_info

    if action == "run":
        goodreads_login(page)
        _books = get_goodreads_books(page)

        # books_info -> {books: [], new: [], removed: []} 
        storage = Storage()
        books_info = storage.update_booklist(_books)
        books = books_info["books"]

        book_objects = [Book(book["title"], book["author"]) for book in books]

        library_handler = Library(page)
        library_handler.search_books(book_objects)

        books_info["books"] = [asdict(book) for book in book_objects]
        books_info["type"] = "full_run"
        return books_info

    if action == "search":
        title = request.args.get("title")
        author = request.args.get("author")

        if not title or not author:
            return "search_book", []
        
        book = Book(title=title, author=author)
        library_handler = Library(page)

        books = [book]

        library_handler.search_books(books)
        return {"type": "search", "books": books, "new": [], "removed": []}

    if DEBUG_MODE:
        with open(
            "search_results_unformatted.json", "w", encoding="utf-8"
        ) as output_file:
            json.dump(
                [asdict(book) for book in books],
                output_file,
                ensure_ascii=False,
                indent=4,
            )

    return "error", None






if __name__ == "__main__":
    app.run("0.0.0.0", port=8080)
