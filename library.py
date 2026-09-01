from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from config import LIBRARY_URL
import re

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

    def __init__(self, page):
        self.page = page
        self.searchbar = self.page.get_by_role("combobox", name="search")



    def _deal_with_cookies(self):
        modal = self.page.get_by_role("dialog", name="Privacy")
        try:
            modal.wait_for(timeout=5000)
            self.page.screenshot(path="modal.png")
            close = modal.get_by_role("button", name="Close")
            close.click()
        except TimeoutError:
            pass


    def _navigate(self, url):
        response = self.page.goto(url)

        print("STATUS:", response.status if response else None)
        print("URL:", self.page.url)
        print("TITLE:", self.page.title())


    def _search_returned_something(self, status):
        match = re.search(r"(\d+)\sresults?", status)

        if not match:
            return 0
        
        return int(match.group(1))


    def _find_match(self, title, author):
        links = self.page.get_by_role("link", name=title)
        if links.count() > 0:
            first_link = links.first
            first_link.click()
            self.page.wait_for_load_state("load", timeout=2000)

            self.page.screenshot(path=f"{title}_MATCH.jpg")

            self.page.go_back()

        

        
    def _check_if_available(self, title, author):
        """ TODO: 
            - Find first 3 results
            - Extract title + author
            - Normalize Title and Author
                - Name format: lastname, firstname 
                    - split by comma
                    - sort list to normalize name
                    - Join 
                    - Replace speical characters using re.sub('[^\w\s,]', "", x). 
                        - Example: "Quigley, Paul., 1977-"  -> "Quigley Paul"
                    - tolowercase() -> "quigley paul"
            - 
            - If title and author match
                - check library - "On Shelf" or "Checked Out"
                - tally and return
        
        """
        self._find_match(title, author)
        

    def _search_books(self, books):

        search_results: list[dict] = []

        for book in books:

            title = book['title']
            author = book['author']
            print(f"searching book: {title} {author}")
            d={}
            d['title'] = title
            d['author'] = author
            d['available'] = False
            d['count'] = 0 
    
            self.searchbar.fill(title)
            self.searchbar.press("Enter")

            result_set =self.page.locator('.search-results').last
            result_set.wait_for()

            status = self.page.locator('.search-results-message').text_content()

            possible_matches = self._search_returned_something(status)

            if possible_matches:
                self._check_if_available(title, author)
                # d['available'] = availability['available']
                # d['count'] = availability['count']

                search_results.append(d)
                


            self.page.screenshot(path=f"searchresult_{title}.png")

        print(search_results)
        
            
            

    def get_books_available(self, books):
        self._navigate(LIBRARY_URL)

        self._deal_with_cookies()

        self._search_books(books)


