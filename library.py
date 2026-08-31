from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from config import LIBRARY_URL

#TODO:
# navigate to library
# cookies
# find search bar
# find top 10 matches
# match book name
# match author
# find associated library - "ON SHELF" > 1 or  Checked out
# return list


class Library:

    def __init__(page):
        self.page = page

    def _navigate(self):
        self.page.goto(LIBRARY_URL)
        expect()

    def get_books_available(self):
        
        pass