import json
from dataclasses import asdict
from datetime import datetime
from patchright.sync_api import Page
from flask import request
from book import Book
from config import DEBUG_MODE,  NOTIFICATION_ON
from _helpers import _setup_debug, _normalize_before_search
from storage import Storage
from _formatters import format_by_book
from goodreads import get_goodreads_books, goodreads_login
from library import Library
from push import push_message


def run(page: Page, action: str, 
        title: str="", author: str="") -> tuple[str, list[Book] | None]:

    _setup_debug(page)

    # parse Goodreads want-to-read and update book list
    if action == "goodreads":
        return goodreads_workflow(page)

    # search library for all book in watch list
    if action == "library":
        return library_workflow(page)

    # search a single book availability in library 
    # using title and author search box on front-end
    if action == "search":
        return single_book_search_workflow(page, title, author)

    # all books in booklist -> library search 
    # VERY SLOW AND TIME INEFFICIENT
    # USE /library or /search INSTEAD
    if action == "run":
        return full_run_workflow(page)

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

        book_objects = [Book(book["title"], book["author"]) for book in books]
        print("bookobjects:", book_objects)
        
        library_handler = Library(page)
        library_handler.search_books(book_objects)

        formatted_resp = format_by_book(book_objects)

        with open("_____formatted.txt", 'w', encoding="utf-8") as file:
            file.write(formatted_resp)

        if NOTIFICATION_ON:
            push_success = push_message(formatted_resp)

            if not push_success:
                print(f"Push Notification Failed.  {datetime.now().strftime('%b %d, %Y at %I:%M %p')} ")
            else:
                print(f"Pushed notification at {datetime.now().strftime('%b %d, %Y at %I:%M %p')}")


        # convert [Book(), Book()...] -> [{book}, {book}...]
        books_info["books"] =  [asdict(book) for book in book_objects]
        books_info["type"]= "library"
        return books_info



def full_run_workflow(page):
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


def single_book_search_workflow(page, title, author):
   
        if not title or not author:
            return "search_book", []
        
        book = Book(title=title, author=author)
        library_handler = Library(page)

        books = [book]

        library_handler.search_books(books)

        return {"type": "search", "books": books, "new": [], "removed": []}


