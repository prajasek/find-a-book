from dataclasses import asdict
from patchright.sync_api import Page, expect, TimeoutError
from book import Book
from config import GOODREADS_SIGNIN
from dotenv import load_dotenv
import json
import re
import os


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
        loaded_books_count = books_table.count()
        books_table.last.scroll_into_view_if_needed()
        next_book = books_table.nth(loaded_books_count)

        # 10 of 30  loaded, 30 of 30  loaded
        books_load_status = page.locator("#pagestuff #infiniteStatus").text_content().strip()

        # 40 of 50 loaded => ('40', '50')
        exp = r"(\d+)\sof\s(\d+)\sloaded"
        match = re.search(exp, books_load_status)

        loaded = match.group(1)
        total_books_in_list = match.group(2)

        # all books loaded, end scrolling
        if int(loaded) == int(total_books_in_list):
            break

        try:
            next_book.wait_for(state="visible", timeout=3000)
        except TimeoutError:
            break
        except Exception as e:
            print(f"Error occurred while waiting for the next book: {e}")
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

        _book = Book(title=title, author=author) 

        books.append(_book)

    print(books)

    _save_books(books)  # Save the books to a JSON file

    # _search_books(page, books)
    return books



def _save_books(books: list[Book]):
    with open("books.json", "w", encoding="utf-8") as file:
        json.dump([asdict(book) for book in books], file, ensure_ascii=False, indent=4)



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


if __name__ == "__main__":

    book = Book(title="The Great Gatsby (Special Edition)", author="F. Scott Fitzgerald [Author]")
    print(asdict(book))

    # with open('books.json', 'r', encoding='utf-8') as file:
    #     books_from_file = json.load(file)
    #     for book in books_from_file:
    #         title = book.get("title", "Unknown")
    #         author = book.get("author", "Unknown")
    #         normalized_title = _normalize_title(title)
    #         normalized_author = _normalize_author(author)
    #         print(f" {title}")
    #         print(f" {normalized_title}")
    #         print(f" {author}")
    #         print(f" {normalized_author}")
    #         print("\n\n")