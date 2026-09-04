from patchright.sync_api import Locator, Page, sync_playwright, expect, TimeoutError
from book import Book, LibraryBook
from config import LIBRARY_URL, TARGET_LIBRARIES
from dataclasses import asdict
import re
import json



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


    def _navigate(self, url: str):
        self.page.goto(url)


    def _go_back(self):
        self.page.go_back()
        

    def _is_exact_match(self, candidate: LibraryBook, target_book: Book) -> bool:
        return (
            candidate.normalized_title == target_book.normalized_title
            and candidate.normalized_author == target_book.normalized_author
        )
        

    def _is_close_match(self, candidate: LibraryBook, target_book: Book) -> bool:
        if candidate.normalized_author != target_book.normalized_author:
            return False

        candidate_words = set(candidate.normalized_title.split())
        target_book_words = set(target_book.normalized_title.split())

        return (
            candidate_words <= target_book_words
            or target_book_words <= candidate_words
        )

        
    def _find_match(self, candidates: list[LibraryBook], target_book: Book) -> LibraryBook | None:
        for candidate_book in candidates:
            if self._is_exact_match(candidate_book, target_book):
                candidate_book.match_type = "exact"
                return candidate_book
            
            elif self._is_close_match(candidate_book, target_book):
                candidate_book.match_type = "close"
                return candidate_book

        return None


    def _extract_book_info_from_card(self, card: Locator) -> LibraryBook | None:
        """ Get title, author, url from each card panel from 
            search results        
        """
        print("Extracting...")
        title_locator = card.locator('[data-automation-id="search-card-title"]')
        author_locator = card.locator('[data-automation-id="author"]')

        print("CARD: ", title_locator.text_content().strip())

        if author_locator.count() == 0:
            return None

        title = title_locator.text_content().strip()
        author = author_locator.text_content().strip()
        href = title_locator.get_attribute("href")

        return LibraryBook(
            title=title,
            author=author,
            url= LIBRARY_URL + href if href.startswith("/search") else LIBRARY_URL + "/" + href
        )


    def _collect_search_results(self, target_book) -> list[LibraryBook] :
        print(f"-------Collecting search results for {target_book.title}-------------")

        candidates: list[LibraryBook] = []
        candidate_book_cards = self.page.locator('[data-automation-id="search-card"]').all()

        for card in candidate_book_cards:
            library_book = self._extract_book_info_from_card(card)

            if library_book:
                candidates.append(library_book)

            with open(f"SEARCH_RESULTS/results_{target_book.normalized_title}.json", "w", encoding="utf-8") as file:
                json.dump([asdict(book) for book in candidates], file, ensure_ascii=False, indent=4)

        return candidates


    def _check_availability_at(self, location: str):
        locations_search_input = self.page.locator('[data-automation-id="locations-search-input"]')
        locations_search_input.wait_for()



    def _update_available_locations(self, target_book: Book) -> bool:

        self._navigate(target_book.library_book.url)

        all_locations_locator = self.page.locator('[data-automation-id="all-locations"]')
        all_locations_locator.wait_for()

        if all_locations_locator.count() == 0:
            return False

        all_locations_locator.click()

        for location in TARGET_LIBRARIES: 
            self._check_availability_at(location)


        self._go_back()
        return True

        
    def _update_availability(self, target_book: Book):
        """ 1. collect search results
            2. check for matches with target book.
            3. check availability in target libraries
        """
        print("check availability function: START")
        candidates: list[LibraryBook] = self._collect_search_results(target_book)
        print("returning from collection.....-------------------------------------------------")

        # possible matching book found in search results
        matching_library_book = self._find_match(candidates, target_book)

        retries = 0

        if matching_library_book:
            target_book.library_book = matching_library_book

            # try to load the book page couple of times, if failure
            while retries < 2:
                if self._update_available_locations(target_book):
                    break
                retries = retries + 1


            

            




    def _get_search_results_count(self, status_msg: Locator):
        if not status_msg.count():
            print("not status_msg")
            return 0

        # Ex: 12 results shown, 0 results found, 1 result found
        match = re.search(r"^(\d+)\+?\sresults?", status_msg.text_content().strip())

        if not match:
            return 0

        # 12, 0, 1
        return int(match.group(1))


    def _apply_format_filters(self, book_format: str):
        side_panel = self.page.get_by_role("region", name="Refine Results")
        side_panel.wait_for()

        format_section = side_panel.locator(
            '[data-automation-id="FORMATS"]'
            )

        if format_section.count() == 0:
            return False

        # get Format section 
        format_dropdown_button = format_section.get_by_role("button").first

        # get format group - {BOOK, AUDIOBOOK, EBOOK}
        format_group = side_panel.get_by_role(
            "group", name=re.compile(r"^format")
            )
        
        # get the checkbox for the desired format (BOOK)
        book_checkbox = format_group.locator(
            '[data-automation-id="facet-checkbox"]'
            ).filter(
                has_text=re.compile(fr"^{book_format}")
                )

        # open drop-down if not already opened
        if not book_checkbox.is_visible():
            format_dropdown_button.click()
        
        try:
            book_checkbox.wait_for(state="visible", timeout=3000)
        except TimeoutError:
            return False

        book_checkbox.click()
        return True



    def _initialize_search(self):
        self.searchbar.wait_for()

        self.searchbar.fill("1")
        self.searchbar.press("Enter")

        self.page.get_by_role("region", name="Refine Results").wait_for()



    def _search_books(self, books: list[Book]) -> list[Book]:

        # do a random initial search to go to main search page
        self._initialize_search()

        for book in books:
            print(f"SEARCHING ----------  {book.title}")

            self.searchbar.wait_for()
            self.searchbar.fill(book.title)
            self.searchbar.press("Enter")

            if not self._apply_format_filters("BOOK"):
                # book not available in library, move on to next book
                print("search filter failure")
                continue

            print("available book filter: contiuining")
            # Ex: 12 results shown, 0 results found, 1 result found
            search_status = self.page.locator('.search-results-message')
            search_status.wait_for()
            search_hits_count = self._get_search_results_count(search_status)

            print(f"Search count: {search_hits_count} ")

            # search returned 0 books, continue to next book
            if search_hits_count == 0:
                continue

            self._update_availability(book)

                  

    def get_books_available(self, books: list[Book]):
        self._navigate(LIBRARY_URL)

        self._deal_with_cookies()

        self._search_books(books)
