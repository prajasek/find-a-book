from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from book import Book
from config import GOODREADS_SIGNIN
from dotenv import load_dotenv
import json
import re
import os
from helpers import _normalize_author, _normalize_title


load_dotenv()  


def login(page: Page):
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
        loaded_books_count = books_table.count()
        books_table.last.scroll_into_view_if_needed()
        next_book = books_table.nth(loaded_books_count)

        try:
            next_book.wait_for(state="visible", timeout=3000)
        except TimeoutError:
            break
        except Exception as e:
            print(f"Error occurred while waiting for the next book: {e}")
            break  

    return True



def _get_books(page) -> list[dict]:
    books_table = page.locator("#booksBody > tr").all()
    books: list[str] = []

    for book in books_table:

        # Title
        title = book.locator("td.field.title  a").inner_text()
        normalized_title = _normalize_title(title)

        # Author
        author = book.locator("td.field.author  a").inner_text()
        normalized_author = _normalize_author(author)

        # add to books list
        books.append({"title": normalized_title, "author": normalized_author})

    print(books)

    _save_books(books)  # Save the books to a JSON file

    # _search_books(page, books)
    return books



def _save_books(books: list[dict]):
    with open("books.json", "w", encoding="utf-8") as file:
        json.dump(books, file, ensure_ascii=False, indent=4)



def _search_books(page, books): 

    search_box = page.get_by_role("textbox", name=re.compile(r'Search.*', re.IGNORECASE)).first

    for book in books[:1]: 
        try:
            search_box.fill(book["title"])
            page.get_by_role("button", name="Search").first.click()

            page.locator('.tableList').first.wait_for(state="visible")

            page.screenshot(path=f"goodreads_search_{book['title']}.png")

            search_box.fill("")
        except Exception as e:
            print(f"Error occurred while searching for book '{book['title']}': {e}")
            break



def scrape_books(page) -> list[Book]:
    page.get_by_role("link", name="My Books").click()
    page.get_by_role("link", name="Want to Read").click()
    page.get_by_role("link", name="table view").click()

    if not _scroll_until_stable(page):
        return []

    books = _get_books(page)

    footer= page.get_by_role("contentinfo")
    expect(footer).to_be_visible()
    page.screenshot(path="goodreads_my_books_page.png")

    return books


# def _normalize_title(title):
#     """
#     Normalize the title by removing special characters and converting to lowercase.
#     """

#     if "(" in title:
#         title = title.split("(")[0].strip()
#     if "[" in title: 
#         title = title.split("[")[0].strip()

#     title = unicodedata.normalize('NFKC', title)
#     title = title.casefold()
#     title = re.sub(r'[^\w\s]', '', title)  # Remove special characters
#     title = re.sub(r'\s+', ' ', title)     # Replace multiple spaces with a single space

#     title = title.strip()

#     return title



# def _normalize_author(author):
#     """
#     Normalize the author by removing special characters and converting to lowercase.
#     """

#     if "(" in author:
#         author = author.split("(")[0].strip()
#     if "[" in author: 
#         author = author.split("[")[0].strip()

#     author = unicodedata.normalize('NFKC', author)
#     author = author.casefold()

#     author = re.sub(r'[^a-zA-Z\s,]', '', author)  # Remove special characters

#     author = author.strip()
#     author = author.lower()

#     name_parts = author.split(",")
#     name_parts = [part.strip() for part in name_parts if part.strip()]  # ['a  ', '  b', ''] => ['a', 'b']

#     name_parts.sort()
#     author = ",".join(name_parts)

#     return author


if __name__ == "__main__":

    with open('books.json', 'r', encoding='utf-8') as file:
        books = json.load(file)
        for book in books:
            title = book.get("title", "Unknown")
            author = book.get("author", "Unknown")
            normalized_title = _normalize_title(title)
            normalized_author = _normalize_author(author)
            print(f" {title}")
            print(f" {normalized_title}")
            print(f" {author}")
            print(f" {normalized_author}")
            print("\n\n")