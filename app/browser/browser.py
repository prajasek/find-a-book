from patchright.sync_api import sync_playwright
from app.config import HEADLESS_MODE, SLOW_MO


class Browser:

    def __enter__(self):
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=HEADLESS_MODE,
            slow_mo=SLOW_MO,
            args=[
                # Crucial: Forces Chrome to use main RAM instead of tiny /dev/shm
                "--disable-dev-shm-usage",
                # Prevents container sandbox restriction crashes
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
            ],
        )
        return self.browser


    def __exit__(self, exc_type, exc, tb):
        self.browser.close()
        self.playwright.stop()