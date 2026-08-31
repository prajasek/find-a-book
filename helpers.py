from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
import json
import re
from dotenv import load_dotenv
import os
from config import GOODREADS_SIGNIN


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




def scroll_until_stable(page):

    books_table = page.locator("#booksBody > tr")

    while True:
        # page.evaluate("window.scrollBy(0, document.body.scrollHeight)")

        # # page.wait_for_timeout(2000)

        # current_height = page.evaluate("document.body.scrollHeight")

        # if current_height == previous_height:
        #     break

        # previous_height = current_height

        loaded_books_count = books_table.count()
        next_book_index = loaded_books_count

        books_table.last.scroll_into_view_if_needed()

        next_book = books_table.nth(next_book_index)

        try:
            next_book.wait_for(state="visible", timeout=3000)
        except TimeoutError:
            break
        except Exception as e:
            print(f"Error occurred while waiting for the next book: {e}")
            break  



def get_books(page):
    books_table = page.locator("#booksBody > tr").all()

    books: list[str] = []

    for book in books_table:
        title = book.locator("td.field.title  a").inner_text().strip()

        if "(" in title:
            title = title.split("(")[0].strip()

        author = book.locator("td.field.author  a").inner_text().strip()

        books.append({"title": title, "author": author})

    json.dumps(books)

    print(books)
    with open("books.json", "w", encoding='utf-8') as output_file:
        json.dump(books, output_file, ensure_ascii=False, indent=4)
        
    search_books(page, books)



def search_books(page, books): 

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



def scrape_books(page):
    
    page.get_by_role("link", name="My Books").click()
    page.get_by_role("link", name="Want to Read").click()
    page.get_by_role("link", name="table view").click()

    scroll_until_stable(page)

    get_books(page)


    footer= page.get_by_role("contentinfo")

    expect(footer).to_be_visible()

    page.screenshot(path="goodreads_my_books_page.png")
