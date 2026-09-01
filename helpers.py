from patchright.sync_api import Page

def _setup_debug(page: Page):
        # page.on("console", lambda msg: print(f"------------\n\nCONSOLE: {msg.text}\n\n"))
        page.on("pageerror", lambda e: print(f"\n\nPage Error: {e} \n\n"))


def _normalize_title(title):
        pass

def _normalize_author(title):
        pass