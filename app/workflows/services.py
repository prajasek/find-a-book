import os
from dataclasses import asdict
from datetime import datetime
from patchright.sync_api import Page
from flask import request
from app.book import Book
from app.config import DEBUG_MODE
from app.utils._helpers import _setup_debug, _normalize_before_search
from app.storage.storage import Storage
from app.utils._formatters import format_by_book
from app.scrapers.goodreads import get_goodreads_books, goodreads_login
from app.scrapers.library import Library
from app.notifications.push import push_message



def run(page: Page, action: str,
        title: str="", author: str=""):

    _setup_debug(page)

    # parse Goodreads want-to-read and update book list
    if action == "goodreads":
        return goodreads_workflow(page)

    # search library for all book in watch list
    if action == "library":
        return library_workflow(page)

    if action == "scheduled_push":
        return scheduled_push_workflow(page)

    # search a single book availability in library 
    # using title and author search box on front-end
    if action == "search":
        return search_a_book_workflow(page, title, author)

    # all books in booklist -> library search
    # VERY SLOW AND TIME INEFFICIENT
    # USE /library or /search INSTEAD
    # if action == "run":
    #     return full_run_workflow(page)

    return "error", None



def goodreads_workflow(page: Page):
        books: list[Book] = []

        goodreads_login(page)
        books = get_goodreads_books(page)

        storage = Storage()
        books_info = storage.update_booklist(books)
        books_info["type"]= "goodreads"

        return books_info



def library_workflow(page: Page):
        storage = Storage()
        books_info: list[dict] = storage.get_watchlist()
        books = books_info["books"]

        book_objects:list[Book] = [Book(book["title"], book["author"]) for book in books]
        print("bookobjects:", book_objects)
        
        library_handler = Library(page)
        library_handler.search_books(book_objects)

        # convert [Book(), Book()...] -> [{book}, {book}...]
        books_info["books"] =  [asdict(book) for book in book_objects]
        books_info["type"]= "library"
        return books_info


def search_a_book_workflow(page, title, author):
        if not title or not author:
            return "search_book", []
        
        library_handler = Library(page)

        # expects a [Book(), Book(), ..] as parameter
        book_object = Book(title=title, author=author)
        library_handler.search_books([book_object])

        # No library book found for this search
        if not book_object.library_book:
            return {"type": "search", "books": [], "new": [], "removed": [], "exists": ""}

        
        # check if matched library book already exists in our book-list
        library_book = book_object.library_book

        matched_book = Book(
             title=library_book.title, 
             author=library_book.author
        )

        print("Matched Library Book: ", matched_book)

        storage = Storage()
        exists = storage.book_exists(matched_book)

        return {"type": "search", "books": [asdict(book_object)], "new": [], "removed": [], "exists": exists}



def scheduled_push_workflow(page: Page):
        storage = Storage()
        books_info: list[dict] = storage.get_watchlist()
        books = books_info["books"]

        book_objects:list[Book] = [Book(book["title"], book["author"]) for book in books]
        print("bookobjects:", book_objects)
        
        library_handler = Library(page)
        library_handler.search_books(book_objects)

        return push_notification(book_objects)


def push_notification(book_objects: list[Book]):
    formatted_resp = format_by_book(book_objects)

    if not book_objects:
        return f"No books to push.  {datetime.now().strftime('%b %d, %Y at %I:%M %p')}", 500
        
    push_success = push_message(formatted_resp)

    if not push_success:
        return f"Push Notification Failed.  {datetime.now().strftime('%b %d, %Y at %I:%M %p')}", 500
    else:
        return f"Pushed notification at {datetime.now().strftime('%b %d, %Y at %I:%M %p')}", 200