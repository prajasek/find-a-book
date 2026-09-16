from flask import Flask, render_template, request, jsonify
from patchright.sync_api import sync_playwright
from book import Book
from config import HEADLESS_MODE, SLOW_MO
from _helpers import _normalize_before_search
from storage import Storage
from services import run
from browser import Browser

app = Flask(__name__)


@app.route("/")
def home():
    print(f"Starting...path={request.path}")
    return render_template("index.html", username="Prasanth")


@app.route("/stored-books")
def stored_books():
    print("stored book called")
    storage = Storage()
    books_info = storage.all_books_from_json()
    books_info["type"] = "home"
    return jsonify(books_info)


@app.route("/watch", methods=["POST"])
def watchlist():
    details = request.get_json()

    book_id = details["book_id"]
    watch_status = details["watch"]

    storage = Storage()
    update_sucess, msg = storage.update_watchlist(book_id, watch_status)

    if not update_sucess:
        return jsonify({
            "msg": "Update Failed", 
            "status":500
        })
    
    return jsonify({
            "msg": msg, 
            "status":200
        })


@app.route("/add", methods=["POST"])
def add_book():
    book_details = request.get_json()

    title = _normalize_before_search(book_details["title"])
    author = _normalize_before_search(book_details["author"])

    book = Book(title, author)

    storage = Storage()
    add_success, msg = storage.add_book(book)

    if not add_success:
        return {"msg": msg, "status":409}
    
    return {"msg": msg, "status":200}



@app.route("/library")
def library_watchlist():
    with Browser() as browser:
        page = browser.new_page()
        books_info = run(page, "library")

    if not books_info:
        return "Not Found", 404

    return jsonify(books_info)


@app.route("/goodreads")
def goodreads():
    with Browser() as browser:
        page = browser.new_page()
        books_info = run(page, "goodreads")

    if not books_info:
        return "Not Found", 404

    return jsonify(books_info)



@app.route("/search")
def search_a_book():
    title = request.args.get("title")
    author = request.args.get("author")

    if not title or not author: 
        return "Incomplete/Bad Request", 400

    with Browser() as browser:
        page = browser.new_page()
        books_info = run(page, "search", title, author)    

    if not books_info:
        return "Not Found", 404
    
    return jsonify(books_info)


        
if __name__ == "__main__":
    app.run("0.0.0.0", port=8080)
