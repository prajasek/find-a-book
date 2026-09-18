from flask import Flask, render_template, request, jsonify
from patchright.sync_api import sync_playwright
from app.book import Book
from app.utils._helpers import _normalize_before_search
from app.storage.storage import Storage
from app.workflows.services import run
from app.browser.browser import Browser

app = Flask(__name__)


@app.route("/")
def home():
    print(f"Starting...path={request.path}")
    return render_template("index.html", username="Prasanth")


@app.route("/stored-books")
def stored_books():
    print(f"Request: {request.path}")
    storage = Storage()
    books_info = storage.all_books_from_json()
    books_info["type"] = "home"
    return jsonify(books_info)


@app.route("/watch", methods=["POST"])
def watchlist():
    details = request.get_json()

    print(f"Request: {request.path}, Book: {details}")

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


@app.route("/add-book", methods=["POST"])
def add_book():
    print(f"Request: {request.path}")
    book_details = request.get_json()

    title = _normalize_before_search(book_details["title"])
    author = _normalize_before_search(book_details["author"])

    book = Book(title, author)

    storage = Storage()
    add_success, msg = storage.add_book(book)

    if not add_success:
        return {"msg": msg}, 409

    return {"msg": msg}, 200


@app.route("/remove-book", methods=["POST"])
def remove_book():
    print(f"Request: {request.path}")

    book_details = request.get_json()
    book_id = book_details["book_id"]

    storage = Storage()
    remove_success, msg = storage.remove_book(book_id)

    if not remove_success:
        return {"msg": msg}, 404
    
    return {"msg": msg}, 200


@app.route("/library")
def library_watchlist():
    print(f"Request: {request.path}")
    with Browser() as browser:
        page = browser.new_page()
        books_info = run(page, "library")

    if not books_info:
        return "Not Found", 404

    return jsonify(books_info)



@app.route("/push")
def scheduled_push():
    print(f"Request: {request.path}")

    storage = Storage()
    success, notification_status, msg = storage.get_notification_status()

    if not success:
        return jsonify({"success":False, "msg": msg}), 500
    
    if not notification_status:
        return jsonify({"success": True, 
                        "msg":"Notification Disabled."}), 200

    with Browser() as browser:
        page = browser.new_page()
        msg, status_code = run(page, "scheduled_push")
        return jsonify({"msg":msg}), status_code


@app.route("/toggle-notification")
def toggle_notifications():
    print(f"Request: {request.path}")

    storage = Storage()
    success, notif_status,  msg = storage.toggle_notification()

    if not success:
        return {"success":False, "msg": msg}, 500
    
    return {"success":True, "status":notif_status, "msg": msg}, 200


@app.route("/get-notification-status")
def get_nofification_status():
    print(f"Request: {request.path}")

    storage = Storage()
    success, notif_status, msg = storage.get_notification_status()
    print(success, notif_status, msg)
    if not success:
        return {"success": False, "msg": msg}, 500

    return {"success": True, "status": notif_status, "msg": msg}, 200



@app.route("/goodreads")
def goodreads():
    print(f"Request: {request.path}")
    with Browser() as browser:
        page = browser.new_page()
        books_info = run(page, "goodreads")

    if not books_info:
        return "Not Found", 404

    return jsonify(books_info)



@app.route("/search")
def search_a_book():
    print(f"Request: {request.path}")
    title = request.args.get("title")
    author = request.args.get("author")

    if not title or not author: 
        return "Incomplete/Bad Request", 400
    try:
        with Browser() as browser:
            page = browser.new_page()
            books_info = run(page, "search", title, author)

        if not books_info:
            return "Not Found", 404

        print("SEARCH: ", books_info)
        
        return jsonify(books_info)

    except TimeoutError:
        return jsonify({"type": "error", 
                        "message": "Library search failed after multiple attempts."
                        }), 503


        
if __name__ == "__main__":
    app.run("0.0.0.0", port=8080)
