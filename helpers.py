import re
import unicodedata
from patchright.sync_api import Page



def _setup_debug(page: Page):
        """ Debugging setup for the page.
        """
        # page.on("console", lambda msg: print(f"------------\n\nCONSOLE: {msg.text}\n\n"))
        page.on("pageerror", lambda e: print(f"\n\nPage Error: {e} \n\n"))



def _normalize_before_search(string: str):
        return string.replace("’", "'")



def _normalize_title(title):
        """
        Normalize the title by removing special characters and converting to lowercase.
        """

        if "(" in title:
                title = title.split("(")[0].strip()
        if "[" in title: 
                title = title.split("[")[0].strip()

        title = unicodedata.normalize('NFKC', title)
        title = title.casefold()
        title = re.sub(r'[^\w\s]', '', title)  # Remove special characters
        title = re.sub(r'\s+', ' ', title)     # Replace multiple spaces with a single space

        title = title.strip()

        return title



def _normalize_author(author):
        """
        Normalize the author by removing special characters and converting to lowercase.
        """

        if "(" in author:
                author = author.split("(")[0].strip()
        if "[" in author: 
                author = author.split("[")[0].strip()

        author = unicodedata.normalize('NFKC', author)
        author = author.casefold()

        parts = author.split(",")
        author = ",".join(parts[:2])

        author = re.sub(r'[^a-zA-Z\s,]', '', author)  # Remove special characters
        author = re.sub(r'\s+', ' ', author)     # Replace multiple spaces with a single spac
        author = author.strip()

        # re-arrange name
        name_parts = author.split(",")
        name_parts = [part.strip() for part in name_parts if part.strip()]  # ['a  ', '  b', ''] => ['a', 'b']


        # Treat names as just word vectors:
        # - Remove one character words (initials).
        # - Split words, sort them to compare.
        words_in_name = []
        for part in name_parts:
        
                parts = [
                        word for word in part.split()
                        if len(word) > 1
                ]

                words_in_name.extend(parts)
        
        words_in_name.sort()
        normalized_author = " ".join(words_in_name)

        return normalized_author
