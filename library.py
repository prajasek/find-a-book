from patchright.sync_api import Locator, Page, sync_playwright, expect, TimeoutError
from book import Book, BookStatus, LibraryBook, LibraryLocation
from config import LIBRARY_URL, TARGET_LIBRARIES, TIMEOUT
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
        modal.wait_for(timeout=3000)
        self.page.screenshot(path="SCREENSHOTS_DIR/modal.png")
        close_btn = modal.get_by_role("button", name="Close")
        close_btn.click()



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




    def _update_book_with_location(self, target_book: Book, library: LibraryLocation):
        """ Get availability status for this location
            - ON SHELF
            - ON HOLD
            - CHECKED OUT
            etc...
        """
        items = self.page.locator('[data-automation-id="item-info"]')
        try:
            items.first.wait_for(timeout=TIMEOUT)
        except TimeoutError:
            raise

        for item_info in items.all():
            print(f"item: {item_info}")
            status_text = item_info.locator('[data-automation-id="drawer-status"]').text_content().strip().lower()

            library.status[status_text] = library.status.get(status_text, 0) + 1

        target_book.library_book.libraries.append(library)



    def _close_modal_if_visible(self):
        # If modal is open, close it

        print("\ncheck if modal open.")
        modal = self.page.locator('.modal-content').filter(visible=True)

        if not modal.count():
            return

        # modal is visible, try to close it.
        book_drawer_close = modal.locator('[data-automation-id="close-drawer-btn"]')
        locations_drawer_close = modal.locator('[data-automation-id="close-locations-drawer-btn"]')
                    
        try:
            locations_drawer_close.wait_for(timeout=TIMEOUT)
            locations_drawer_close.click()
            return
        except TimeoutError:
            pass

        try:
            book_drawer_close.wait_for(timeout=TIMEOUT)
            book_drawer_close.click()
            return
        
        except TimeoutError as exc:
            raise TimeoutError("Could not close the modal window.") from exc

        print("closed modal\n")



    def _check_availability_at(self, target_locations: list[LibraryLocation], target_book: Book) -> bool:

        for library in target_locations:
            print("checking library", library.location)

            self._close_modal_if_visible()
        
            all_locations_locator = self.page.locator('[data-automation-id="all-locations"]')

            # 'View all locations' button not loading
            try:
                all_locations_locator.wait_for(timeout=3000)
            except TimeoutError:
                raise
            
            print("\nclicking all locations\n")
            all_locations_locator.click()
            locations_search_input = self.page.locator('[data-automation-id="locations-search-input"]')
            locations_search_input.wait_for()

            locations_search_input.fill(library.location)
            locations_search_input.press("Enter")

            available_locations_block = self.page.locator('[data-automation-id="available-locations-block"]')

            # book not present at location that we searched for, continue to next location
            try:
                available_locations_block.wait_for(timeout=TIMEOUT)
            except TimeoutError:
                continue
 
            available_locations_list = available_locations_block.get_by_role("list")
            available_locations_list.wait_for(timeout=TIMEOUT)

            locations_listitems = available_locations_list.get_by_role("listitem")
            locations_listitems.first.wait_for(timeout=TIMEOUT)

            # check if target location is available, and update book with 
            # availability status
            for location_listitem in locations_listitems.all():

                location_link: Locator = location_listitem.locator(
                                                '[data-automation-id="drawer-location-item-available"]'
                                            )

                location_str: str = location_link.text_content()

                print(f"CHECKING LOCATION: {location_str} \n")

                if library.location.lower().strip() == location_str.lower().strip():
                    location_link.click()
                    self._update_book_with_location(
                        target_book,
                        library
                    )

        self._close_modal_if_visible()



    def _update_available_locations(self, target_book: Book) -> bool:
        """ Check target libraries for availability       
        """

        # retry loading book page couple of times, if failing to load
        # the library website is sometimes laggy
        for attempt in range(2):
            try:
                print(f"navigating to {target_book.library_book.url}")
                self._navigate(target_book.library_book.url)
                
                target_locations = [
                            LibraryLocation(location=location)
                            for location in TARGET_LIBRARIES
                        ]
                
                self._check_availability_at(target_locations, target_book)

            except TimeoutError:
                print(f"Attemping location availability again for {target_book.title}")
                if attempt == 1:
                    print(f"Location update failed for {target_book.title}")
                    raise




    def _update_availability(self, target_book: Book):
        """ 1. collect search results
            2. check for matches with target book.
            3. check availability in target libraries
        """
        print("check availability function: START")
        candidates: list[LibraryBook] = self._collect_search_results(target_book)
        print("returning from collection.....-------------------------------------------------")

        # possible matching book found in search results

        print("Findign match")
        matching_library_book = self._find_match(candidates, target_book)
        print("Finished finding match")

        if matching_library_book:
            print(" --> found matching book", matching_library_book)
            target_book.library_book = matching_library_book
            print(f"TARGET BOOK:  {target_book}")
            
            self._update_available_locations(target_book)



    

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



    def _search_book(self, book: Book) -> tuple[bool, str]:
    
        print(f"SEARCHING ----------  {book.title}")
    
        self.searchbar.wait_for(timeout=TIMEOUT)
        self.searchbar.fill(book.title)
        self.searchbar.press("Enter")

        if not self._apply_format_filters("BOOK"):
            # book not available in library, move on to next book
            return False, f"Book format not available for {book.title}."

        print("available book filter: contiuining")
        # Ex: 12 results shown, 0 results found, 1 result found
        search_status = self.page.locator('.search-results-message')
        search_status.wait_for()
        search_hits_count = self._get_search_results_count(search_status)

        print(f"Search count: {search_hits_count} ")

        # search returned 0 books, continue to next book
        if search_hits_count == 0:
            return False, f"No hits for {book.title}."

        self._update_availability(book)

        self._go_back()

        return True, f"Search for {book.title} complete."



    def _initialize_search(self):
        self.searchbar.wait_for()
        self.searchbar.fill("1")
        self.searchbar.press("Enter")
        self.page.get_by_role("region", name="Refine Results").wait_for()



    def _get_fresh_search_session(self):
        self._navigate(LIBRARY_URL)
        self._deal_with_cookies()
        self._initialize_search()



    def _search_books(self, books: list[Book]):

        self._get_fresh_search_session()

        for book in books:
            for attempt in range(2):
                try:
                    # handle normal failure like 0 books hits, or BOOK format not available
                    status, msg = self._search_book(book)
                    if not status:
                        print(msg)
                        break
                    
                    print(msg)
                    break

                except TimeoutError:
                    print(f"Search for {book.title} errored. Retrying...")

                    if attempt == 1:
                        print(f"Search for {book.title} failed. Moving on to next book...")

                    self._get_fresh_search_session()

                    

            

    def get_books_available(self, books: list[Book]):

        self._search_books(books)
