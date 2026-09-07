import json
from dataclasses import asdict
from flask import Flask, jsonify, request, send_file
from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from book import Book
from config import DEBUG_MODE, HEADLESS_MODE, SLOW_MO
from helpers import _setup_debug
from goodreads import goodreads_login, scrape_books
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

        books: list[Book] = run(page, action)
    
        print("="*30 + "Search Complete" + "="*100)
        print(books)
        print("="*30 + "Search Complete" + "="*100)

        browser.close()

        # # serialize
        # results: list[dict] = serialize(books)
        # print(results)

        # format response for pushover integration
        if books:
            formatted_resp: str = format_notification(books)

            with open("formatted_response.txt", 'w', encoding="utf-8") as fr:
                fr.write(formatted_resp)

            print(formatted_resp)
            return send_file("formatted_response.txt")
       
        return "Book list empty", 404



def run(page: Page, action: str) -> list[Book]:
    _setup_debug(page)

    goodreads_books: list[Book] = []
    
    if action in {"goodreads", "run"}:
        goodreads_login(page)
        goodreads_books = scrape_books(page)

    if not goodreads_books:
        return []

    if action in {"library", "run"}:
        library_handler = Library(page)
        library_handler.search_books(goodreads_books)

    # elif action == "search" or action == "run":
    #     file = open("goodreads_books.json","r", encoding="utf-8")
    #     _books_list: list[Book] = [Book(book["title"], book["author"]) for book in json.load(file)]
    #     goodreads_books.extend(_books_list)
    #     file.close()

    if DEBUG_MODE:
        with open("search_results_unformatted.json", "w", encoding="utf-8") as output_file:
            json.dump([asdict(book) for book in goodreads_books], output_file, ensure_ascii=False, indent=4)

    return goodreads_books



def serialize(books: list[Book]) -> list[dict]:
    response = []
    for book in books:
        result = {}

        result['title'] = book.title
        result['author'] = book.author

        library_book = book.library_book

        if not library_book:
            result["library_book"] = None
            response.append(result)
            continue

        result['match_type'] = library_book.match_type
        result['library_title'] = library_book.title
        result['library_author'] = library_book.author

        libraries = library_book.libraries

        total = 0
        for location in libraries:
            if location.available:
                total += location.available_count

        result['total available'] = total
        result['libaries'] = [asdict(location) for location in libraries]

        response.append(result)

    return response



def format_notification(books: list[Book]) -> str:
    lines = []

    for book in books:
        lines.append(f"📚 {book.title}")
        lines.append(f"{book.author}")
        if not book.library_book:
            lines.append("❌ Book not found.")
            lines.append("\n")
            continue

        if book.library_book.match_type == "close":
            lines.append("≈ Close match")

        elif book.library_book.match_type == "exact":
            lines.append("✅ Exact match")

        lines.append("")
        lines.append("Library Book:")
        lines.append(f"{book.library_book.title}")
        lines.append(f"{book.library_book.author}")
        lines.append(f"{book.library_book.url}")

        lines.append("")

        libraries = book.library_book.libraries

        if not libraries:
            lines.append("{No copies available anywhere.}")

        for library in libraries:
            location = library.location
            total_available = library.available_count

            lines.append(f"{location}")

            for status, count in library.status.items():
                lines.append(f"\t-{status}: {count}")

            lines.append(f"Total available at {location}: {total_available}")
            lines.append("")

        lines.append("\n")

    return "\n".join(lines)



if __name__ == "__main__":
    app.run('0.0.0.0', port=8080)

   
