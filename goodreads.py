from dataclasses import asdict
from patchright.sync_api import Page, expect, TimeoutError
from book import Book
from config import GOODREADS_SIGNIN
from dotenv import load_dotenv
import json
import re
import os

from helpers import _normalize_before_search


load_dotenv()  



def goodreads_login(page: Page):
    print("Attempting Login...")
    page.goto(GOODREADS_SIGNIN)
    page.get_by_role("button", name="Sign in with email").click()
    page.screenshot(path="goodreads_login_page.png")

    page.get_by_role("textbox", name="Email").fill(os.getenv("GOODREADS_USER"))
    page.get_by_role("textbox", name="Password").fill(os.getenv("GOODREADS_PASSWORD"))
    page.get_by_role("button", name="Sign in").click()

    expect(page.get_by_role("main")).to_be_visible()

    page.screenshot(path="goodreads_logged_in.png")
    print("Login Function Ended...")



def _scroll_until_stable(page):
    books_table = page.locator("#booksBody > tr")

    try:
        books_table.first.wait_for(state="visible", timeout=10000)
    except TimeoutError:
        print("No books in list.")
        return False

    while True:
        books_table.last.scroll_into_view_if_needed()

        # 10 of 30  loaded, 30 of 30  loaded
        books_load_status = (
            page.locator("#pagestuff #infiniteStatus")
            .text_content()
            .strip()
        )

        # 40 of 50 loaded => ('40', '50')
        exp = r"(\d+)\s+of\s+(\d+)\s+loaded"
        match = re.search(exp, books_load_status)

        if not match:
            print("Failed to parse book load status from footer.")
            return False

        loaded = match.group(1)
        total_books_in_list = match.group(2)

        # all books loaded, end scrolling
        if int(loaded) == int(total_books_in_list):
            break

    return True



def _get_books(page) -> list[Book]:
    # locator
    books_table = page.locator("#booksBody > tr").all()

    # list of want-to-read books
    books: list[Book] = []

    for book in books_table:
        title = book.locator("td.field.title  a").inner_text().strip()
        author = book.locator("td.field.author  a").inner_text().strip()

        # clean up before search. Example, apostrophes
        normalized_title_pre_search = _normalize_before_search(title)
        normalized_author_pre_search = _normalize_before_search(author)

        _book = Book(
            title=normalized_title_pre_search,
            author=normalized_author_pre_search
        )

        books.append(_book)

    print(books)

    _save_books(books)  # Save the books to a JSON file

    return books



def _save_books(books: list[Book]):
    with open("goodreads_books.json", "w", encoding="utf-8") as file:
        json.dump([asdict(book) for book in books], file, ensure_ascii=False, indent=4)



def _navigate_to_want_to_read(page):
    page.get_by_role("link", name="My Books").click()
    page.get_by_role("link", name="Want to Read").click()
    page.get_by_role("link", name="table view").click()


def _sanity_footer_visibility_check(page):
    """ Sanity check to ensure the footer is visible 
        after loading all books.
    """
    footer = page.get_by_role("contentinfo")
    expect(footer).to_be_visible()
    page.screenshot(path="goodreads_my_books_page.png")



def scrape_books(page) -> list[Book]:
    _navigate_to_want_to_read(page)

    # scroll the want-to-read list until all books are loaded
    if not _scroll_until_stable(page):
        return []

    books: list[Book] = _get_books(page)

    _sanity_footer_visibility_check(page)

    return books
