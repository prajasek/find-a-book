from dataclasses import asdict
import re
import json
from patchright.sync_api import (
    Locator,
    Page,
    Response,
    sync_playwright,
    expect,
    TimeoutError,
)
from book import Book, LibraryBook, LibraryLocation
from config import (
    LIBRARY_URL,
    LONG_LONG_TIMEOUT,
    TARGET_LIBRARIES,
    TIMEOUT,
    LONG_TIMEOUT,
    SHORT_TIMEOUT,
    DEBUG_MODE,
)


class Library:
    """
    # navigate to library
    # cookies
    # find search bar
    # find top 10 matches
    # match book name
    # match author
    # find associated library - "ON SHELF" > 1 or  Checked out
    # update books list`
    """

    def __init__(self, page):
        self.page = page
        self.final_results: list[Book] = []

        # locator
        self.searchbar = self.page.get_by_role("combobox", name="search")

    def _deal_with_cookies(self, t):
        modal = self.page.get_by_role("dialog", name="Privacy")
        try:
            modal.wait_for(timeout=t)
        except TimeoutError:
            return
        
        close_btn = modal.get_by_role("button", name="Close")
        close_btn.click(timeout=TIMEOUT)

        modal.wait_for(state="hidden", timeout=TIMEOUT)

 

    def _navigate(self, url: str):
        self.page.goto(url)

    def _go_back(self):
        self.page.go_back()

    def _update_book_with_location(self, target_book: Book, library: LibraryLocation):
        """Get availability status for this location
        - ON SHELF
        - ON HOLD
        - CHECKED OUT
        etc...
        """
        #print(f"Updating book availability at {library.location}.\n")
        items = self.page.locator('[data-automation-id="item-info"]')
        try:
            items.first.wait_for(timeout=TIMEOUT)
        except TimeoutError as e:
            raise e

        for item_info in items.all():
            status_text = (
                item_info.locator('[data-automation-id="drawer-status"]')
                .text_content()
                .strip()
                .lower()
            )
            #print(f"Item: {item_info}: {status_text}")

            library.status[status_text] = library.status.get(status_text, 0) + 1

        target_book.library_book.libraries.append(library)

    def _close_modal_if_visible(self):
        # If modal is open, close it

        #print("\ncheck if modal open.")
        modal = self.page.locator(".modal-content").filter(visible=True)

        if not modal.count():
            return

        # modal is visible, try to close it.
        book_drawer_close = modal.locator('[data-automation-id="close-drawer-btn"]')
        locations_drawer_close = modal.locator(
            '[data-automation-id="close-locations-drawer-btn"]'
        )

        try:
            #print("checking books drawer")
            book_drawer_close.wait_for(timeout=500)
            book_drawer_close.click()
            #print("closed books drawer")
            return

        except TimeoutError:
            pass

        try:
            #print("checking locations drawer")
            locations_drawer_close.wait_for(timeout=500)
            locations_drawer_close.click()
            #print("closed locations drawer")
            return

        except TimeoutError as exc:
            raise TimeoutError("Could not close the modal window.") from exc

    def _check_availability_at(
        self, target_locations: list[LibraryLocation], target_book: Book
    ):
        """
        Check each library location for book availability.
        """
        for library in target_locations:
            #print(f"Checking library location: {library.location}")

            self._close_modal_if_visible()

            all_locations_locator = self.page.locator(
                '[data-automation-id="all-locations"]'
            )

            # 'View all locations' button not loading
            try:
                all_locations_locator.wait_for(timeout=LONG_TIMEOUT)
            except TimeoutError as e:
                raise e

            #print("Clicking all locations.\n")
            all_locations_locator.click()
            locations_search_input = self.page.locator(
                '[data-automation-id="locations-search-input"]'
            )
            locations_search_input.wait_for()

            #print("Entering location search.\n")
            locations_search_input.fill(library.location)
            locations_search_input.press("Enter")

            available_locations_block = self.page.locator(
                '[data-automation-id="available-locations-block"]'
            )

            # book not present at location that we searched for, continue to next location
            try:
                available_locations_block.wait_for(timeout=TIMEOUT)
            except TimeoutError:
                continue

            available_locations_list = available_locations_block.get_by_role("list")
            available_locations_list.wait_for(timeout=TIMEOUT)

            locations_listitems = available_locations_list.get_by_role("listitem")
            locations_listitems.first.wait_for(timeout=TIMEOUT)

            # check if target location is available, and update book with availability status
            for location_listitem in locations_listitems.all():

                location_link: Locator = location_listitem.locator(
                    '[data-automation-id="drawer-location-item-available"]'
                )

                location_text: str = location_link.text_content()

                #print(f"Checking location: {location_text} \n")

                if library.location.lower().strip() == location_text.lower().strip():
                    location_link.click()
                    self._update_book_with_location(target_book, library)

        self._close_modal_if_visible()

    def _update_available_locations(self, target_book: Book):
        """Check target libraries for availability"""

        # library locations to search at
        target_locations = [
            LibraryLocation(location=location) for location in TARGET_LIBRARIES
        ]

        # retry loading book page couple of times, if failing to load
        # the library website is sometimes laggy
        for attempt in range(2):
            try:
                #print(f"Navigating to book url for {target_book.title}: {target_book.library_book.url}")
         
                self._navigate(target_book.library_book.url)
                self._check_availability_at(target_locations, target_book)
                break

            except TimeoutError:
                #print(f"TimeoutError. Retrying location search for {target_book.title}.")
                if attempt == 1:
                    #print(f"Location search for {target_book.title} failed.")
                    raise

    def _is_exact_match(self, candidate: LibraryBook, target_book: Book) -> bool:
        """
        If title and author are exact matches character by character.
        """
        return (
            candidate.normalized_title == target_book.normalized_title
            and candidate.normalized_author == target_book.normalized_author
        )

    def _is_close_match(self, candidate: LibraryBook, target_book: Book) -> bool:
        """
        If normalized target book is a subset of candidate library book title,
        or vice-versa, consider it a close match.

        Ex:
        - target:    Paris Apartment
        - candidate: Paris Apartment A Novel
        """
        if candidate.normalized_author != target_book.normalized_author:
            return False

        candidate_words = set(candidate.normalized_title.split())
        target_book_words = set(target_book.normalized_title.split())

        return (
            candidate_words <= target_book_words or target_book_words <= candidate_words
        )

    def _find_match(
        self, candidates: list[LibraryBook], target_book: Book
    ) -> LibraryBook | None:
        for candidate_book in candidates:
            if self._is_exact_match(candidate_book, target_book):
                candidate_book.match_type = "exact"
                return candidate_book

            elif self._is_close_match(candidate_book, target_book):
                candidate_book.match_type = "close"
                return candidate_book

        return None

    def _extract_book_info_from_card(self, card: Locator) -> LibraryBook | None:
        """Get title, author, url from each card panel from
        search results and return a LibraryBook.
        """
        #print("Extracting info")

        title_locator = card.locator('[data-automation-id="search-card-title"]')
        author_locator = card.locator('[data-automation-id="author"]')

        if author_locator.count() == 0:
            return None

        title = title_locator.text_content().strip()
        author = author_locator.text_content().strip()
        href = title_locator.get_attribute("href")

        if title and author and href:
            return LibraryBook(
                title=title,
                author=author,
                url=(
                    LIBRARY_URL + href
                    if href.startswith("/search")
                    else LIBRARY_URL + "/" + href
                ),
            )

        return None

    def _collect_search_results(self, target_book: Book) -> list[LibraryBook]:
        """Collect all search results from first page, and
        return list of LibraryBook candidates.
        """
        #print(f"-------Collecting search results for {target_book.title}-------------")

        candidates: list[LibraryBook] = []
        candidate_book_cards = self.page.locator('[data-automation-id="search-card"]')

        try:
            # wait for atleast one search card, and return list of search cards.
            candidate_book_cards.first.wait_for(timeout=TIMEOUT)
            candidate_book_cards = candidate_book_cards.all()

        except TimeoutError:
            # no search cards
            return

        for card in candidate_book_cards:
            library_book = self._extract_book_info_from_card(card)

            if library_book:
                candidates.append(library_book)

        if DEBUG_MODE:
            with open(
                f"SEARCH_RESULTS/results_{target_book.normalized_title}.json",
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    [asdict(book) for book in candidates],
                    file,
                    ensure_ascii=False,
                    indent=4,
                )

        return candidates

    def _update_availability(self, target_book: Book) -> bool:
        """
        1. Collect search results
        2. Check for matches with target book.
        3. Check availability in target library locations.
        """

        #print("START: check availability function")
        candidates: list[LibraryBook] = self._collect_search_results(target_book)
        #print("Collected search results.")

        if not candidates:
            #print(f"Zero candidates for {target_book.title}.")
            return False

        # possible matching book found in search results
        #print("Finding match...")
        matching_library_book: LibraryBook = self._find_match(candidates, target_book)

        # search candidates available but no match found.
        if not matching_library_book:
            #print(f"No match found for {target_book.title}.")
            return False

        #print(f" --> Found matching book for {target_book.title}:{matching_library_book}\n")

        target_book.library_book = matching_library_book

        self._update_available_locations(target_book)

        return True

    def _get_search_results_count(self, status_msg: Locator):
        if not status_msg.count():
            #print("not status_msg")
            return 0

        # Ex: 12 results shown, 0 results found, 1 result found
        match = re.search(r"^(\d+)\+?\sresults?", status_msg.text_content().strip())

        if not match:
            return 0

        # 12, 0, 1
        return int(match.group(1))

    def _apply_format_filters(self, book_format: str):
        #print("Format section...")
        side_panel = self.page.get_by_role("region", name="Refine Results")
        side_panel.wait_for(timeout=TIMEOUT)

        format_section = side_panel.locator('[data-automation-id="FORMATS"]')

        try:
            format_section.wait_for(timeout=TIMEOUT)
        except TimeoutError:
            return False

        # get Format section
        format_dropdown_button = format_section.get_by_role("button")

        try:
            format_dropdown_button.first.wait_for(timeout=TIMEOUT)
        except TimeoutError:
            return False

        # get format group - {BOOK, AUDIOBOOK, EBOOK}
        format_group = side_panel.get_by_role("group", name=re.compile(r"^format"))

        # get the checkbox for the desired format (BOOK)
        book_checkbox = format_group.locator(
            '[data-automation-id="facet-checkbox"]'
        ).filter(has_text=re.compile(rf"^{book_format}"))

        # If checkbox is not visible, try opening the format section
        # and check again
        try:
            book_checkbox.wait_for(state="visible", timeout=TIMEOUT)
            #print("Book format selected.")
        except TimeoutError:
            try:
                #print("Open dropdown if not visible")
                format_dropdown_button.click()

                book_checkbox.wait_for(state="visible", timeout=TIMEOUT)
                #print("Book format selected.")
            except TimeoutError:
                return False

        #print("Trying to click book checkbox")
        book_checkbox.click()

        return True

    def _has_format_results(self, response_info: Response) -> bool:
        """
        Check if format material_type API returned any results.
        """
        response_body = response_info.value.json()

        return response_body.get("totalResults", 0)

    def _search_book(self, book: Book) -> tuple[bool, str]:

        #print(f"SEARCHING ----------  {book.title}")

        self.searchbar.wait_for(timeout=TIMEOUT)
        self.searchbar.fill(book.title)

        # Wait for 'material_type' API response that responds with available formats for the book.
        # Anything will 0 results => no formats available, we can skip to next book.
        with self.page.expect_response(
            lambda response: "material_Type" in response.url
            and response.request.method == "POST"
            and response.status == 200
        ) as response_info:
            self.searchbar.press("Enter")

        if not self._has_format_results(response_info):
            return False, f"No copies available for {book.title}."

        # Book not available in requested format Ex: "BOOK"
        if not self._apply_format_filters("BOOK"):
            return False, f"Book format not available for {book.title}."

        # Check search results status
        # Ex: 12 results shown, 0 results found, 1 result found
        search_status = self.page.locator(".search-results-message")
        search_status.wait_for()
        search_hits_count = self._get_search_results_count(search_status)

        #print(f"Search count: {search_hits_count} ")

        # search returned 0 books, continue to next book
        if search_hits_count == 0:
            return False, f"No hits for {book.title}."

        if self._update_availability(book):
            self._go_back()

        return True, f"Search for {book.title} complete."

    def _initialize_search(self):
        """
        Do a random search, so we land on the main search page with filters.
        Resulting page is where the main book search happens.
        """
        self.searchbar.wait_for(timeout=LONG_TIMEOUT)
        self.searchbar.fill("1")
        self.searchbar.press("Enter")
        self.page.get_by_role("region", name="Refine Results").wait_for(
            timeout=LONG_TIMEOUT
        )

    def _get_fresh_search_session(self):
        """Provide the main search page for new search session."""
        for attempt in range(2):
            try:
                self._navigate(LIBRARY_URL)
                self._deal_with_cookies(LONG_LONG_TIMEOUT)
                self._initialize_search()
                # just to check if cookies modal still visible
                self._deal_with_cookies(SHORT_TIMEOUT)       
                break

            except TimeoutError:
                #print("Failed to initialize search session. Retrying...")

                if attempt == 1:
                    raise


    def search_books(self, books: list[Book]):

        self._get_fresh_search_session()

        for book in books:
            for attempt in range(2):
                try:
                    # handle normal failure like 0 books hits, or BOOK format not available
                    _, msg = self._search_book(book)
                    print(f"MESSAGE: {msg}\n")
                    break

                except TimeoutError:
                    print(f"Search for {book.title} errored. Retrying...")

                    if attempt == 1:
                        print(f"Search for {book.title} failed. Moving on to next book...")

                    self._get_fresh_search_session()
