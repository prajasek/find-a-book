from patchright.sync_api import Page, sync_playwright, expect, TimeoutError
from helpers import login, scrape_books


if __name__ == "__main__":

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False, 
            args=[
                "--disable-dev-shm-usage",  # Crucial: Forces Chrome to use main RAM instead of tiny /dev/shm
                "--no-sandbox",             # Prevents container sandbox restriction crashes
                "--disable-setuid-sandbox",
                "--disable-gpu" 
            ]
        )

        page = browser.new_page()

        login(page)
        scrape_books(page)

        browser.close()
