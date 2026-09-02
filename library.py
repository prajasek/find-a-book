from patchright.sync_api import Locator, Page, sync_playwright, expect, TimeoutError
from book import Book
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
        self.final_results: list[Book] = []

        # locator
        self.searchbar = self.page.get_by_role("combobox", name="search")



    def _deal_with_cookies(self):
        modal = self.page.get_by_role("dialog", name="Privacy")
        try:
            modal.wait_for(timeout=5000)
            self.page.screenshot(path="SCREENSHOTS_DIR/modal.png")
            close = modal.get_by_role("button", name="Close")
            close.click()
        except TimeoutError:
            pass


    def _navigate(self, url):
        self.page.goto(url)


    def _get_search_results_count(self, status_msg: Locator):
        if not status_msg.count():
            return 0

        # Ex: 12 results shown, 0 results found, 1 result found
        match = re.search(r"(\d+)\+?\sresults?", status_msg.text_content())

        if not match:
            return 0
        
        return int(match.group(1))



    def _get_search_results(self):
        pass


    def _find_match(self, title, author):

        # TODO: Normalize title and author before searching for a match
        links = self.page.get_by_role("link", name=title)

        if links.count() > 0:
            first_link = links.first
            first_link.click()
            
            description = self.page.locator('[data-automation-id="full-card-title"]')
            description.wait_for()

            print(f"{title} FOUND. {self.page.url}")

            self.page.screenshot(path=f"SCREENSHOTS_DIR/_{title}_MATCH.jpg")

            self.page.go_back()

            return {"title": title, "author": author, "available": True, "count": 1}
        
        return {"title": title, "author": author, "available": False, "count": 0}


        
    def _check_availability(self, title, author):
        """ TODO: Normalization
            _get_search_results()
        """
        self._get_search_results()
        return self._find_match(title, author)


        
    def _initialize_search(self):
        self.searchbar.wait_for()

        self.searchbar.fill("1")
        self.searchbar.press("Enter")

        self.page.get_by_role("region", name="Refine Results").wait_for()



    def _apply_search_filters(self):
        side_panel = self.page.get_by_role("region", name="Refine Results")
        side_panel.wait_for()

        format_dropdown_button = side_panel.locator(
            '[data-automation-id="FORMATS"]'
            ).get_by_role("button").first
        
        format_group = side_panel.get_by_role(
            "group", name=re.compile(r"^format")
            )
        
        book_checkbox = format_group.locator(
            '[data-automation-id="facet-checkbox"]'
            ).filter(
                has_text=re.compile(r"^BOOK")
                )

        # open drop-down if not already opened
        if not book_checkbox.is_visible():
            format_dropdown_button.click()

        book_checkbox.click()



    def _search_books(self, books):

        self._initialize_search()

        for book in books:
            
            self.title = book['title']
            self.author = book['author']

            print(f"Searching book: {self.title} ---  {self.author}")

            d={}
            d['title'] = self.title
            d['author'] = self.author
            d['available'] = False
            d['count'] = 0
    
            self.searchbar.fill(self.title)
            self.searchbar.press("Enter")

            self._apply_search_filters()

            result_set =self.page.locator('.search-results').last
            result_set.wait_for()

            # Ex: 12 results shown, 0 results found, 1 result found
            search_status = self.page.locator('.search-results-message')
                
            search_hits_count = self._get_search_results_count(search_status)

            if search_hits_count > 0:
                availability = self._check_availability(self.title, self.author)

                d['available'] = availability['available']
                d['count'] = availability['count']

            
                final_search_results.append(d)
                try:
                    title = re.sub(r'[^\w\s]', '', self.title)  # Remove special characters from title for filename
                    self.page.screenshot(path=f"SCREENSHOTS_DIR/_____searchresult_{title}.jpg")
                except Exception as e:
                    print(f"Error occurred while taking screenshot for book '{title}': {e}")

            print(f"RESULT: \n{d}\n")

        print(final_search_results)
        
            
            

    def get_books_available(self, books):
        self._navigate(LIBRARY_URL)

        self._deal_with_cookies()

        self._search_books(books)
