from datetime import datetime
import hashlib
import re
import unicodedata
from patchright.sync_api import Page
from config import VIEWPORT

# # clear the log file for each run
# file = open("time_logs.txt", 'w')
# file.close()

####### PLAYWRIGHT CONFIG ############################################################################################
def _setup_debug(page: Page):
        """ Debugging setup for the page.
        """
        # page.on("console", lambda msg: print(f"------------\n\nCONSOLE: {msg.text}\n\n"))
        page.on("pageerror", lambda e: print(f"\n\nPage Error: {e} \n\n"))
        page.set_viewport_size(VIEWPORT)



####### TITLE/AUTHOR NORMALIZATION ####################################################################################
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


def _normalize_initials(author):
    tokens = author.replace(".", " ").split()

    result = []
    initials = []

    for token in tokens:
        if len(token) == 1 and token.isalpha():
            initials.append(token)
        else:
            if len(initials) >= 2:
                result.append("".join(initials))
            initials = []

            result.append(token)

    if len(initials) >= 2:
        result.append("".join(initials))

    return " ".join(result)



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

        # Finn, King A.J, 1945-  => [Finn, King A.J.]
        parts = author.split(",")

        # [Finn, King A.J.] => Finn King A.J.
        author = " ".join(parts[:2])

        # Finn King A.J. => Finn King AJ
        author = _normalize_initials(author)

        # 'Foley   Lucy A. '  => foley lucy a
        author = re.sub(r'[^a-zA-Z\s,]', '', author)  # Remove special characters
        author = re.sub(r'\s+', ' ', author)          # Replace multiple spaces with a single space
        author = author.strip()

        # strip empty spaces
        # 'foley lucy a '  => ["foley", "lucy a"]
        name_parts = author.split(",")
        name_parts = [part.strip() for part in name_parts if part.strip()]


        # Treat names as just word vectors:
        # - Remove one character words/initials.
        # - Split words, sort them to compare.
        # ['foley', 'lucy a'] -> ['foley', 'lucy']
        words_in_name = []
        for part in name_parts:
                parts = [
                        word for word in part.split()
                        if len(word) > 1
                ]

                words_in_name.extend(parts)
        
        words_in_name.sort()

        # ['foley', 'lucy'] -> 'foley lucy'
        normalized_author = " ".join(words_in_name)

        return normalized_author


#### TIME ###########################################

def _delta_hours(before, now):

        if type(before) == str:
               before = datetime.fromisoformat(before)
        if type(now) == str:
               now = datetime.fromisoformat(now)
        return (now - before).total_seconds() / 3600
