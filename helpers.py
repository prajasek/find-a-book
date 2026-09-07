import re
import unicodedata
from patchright.sync_api import Page
from config import VIEWPORT

# clear the log file for each run
file = open("time_logs.txt", 'w')
file.close()


def _setup_debug(page: Page):
        """ Debugging setup for the page.
        """
        # page.on("console", lambda msg: print(f"------------\n\nCONSOLE: {msg.text}\n\n"))
        page.on("pageerror", lambda e: print(f"\n\nPage Error: {e} \n\n"))
        page.set_viewport_size(VIEWPORT)



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


def log_time(timer, book):

        lines = []
        lines.append(f"{book.title}")
        with open("time_logs.txt", "a") as file:
                for func, s in timer.items():
                        lines.append(f"{func}: {s} seconds.")

                lines.append("\n")
                file.write("\n".join(lines))




# if __name__ =="__main__":
#         test_authors = [
#                         # Normal
#                         "Stephen King",
#                         "Lucy Foley",
#                         "George Orwell",
#                         "Jane Austen",

#                         # Inverted catalog names
#                         "King, Stephen",
#                         "Foley, Lucy",
#                         "Orwell, George",
#                         "Austen, Jane",

#                         # Inverted + birth/death years
#                         "King, Stephen, 1947-",
#                         "Orwell, George, 1903-1950",
#                         "Austen, Jane, 1775-1817",
#                         "Foley, Lucy, 1986-",

#                         # Inverted + middle initial
#                         "Finn, A. J.",
#                         "Finn, A.J.",
#                         "Finn, A. J., 1979-",
#                         "Foley, Lucy A.",
#                         "Foley, Lucy A., 1986-",

#                         # Initials, normal order
#                         "A. J. Finn",
#                         "A.J. Finn",
#                         "A J Finn",
#                         "AJ Finn",

#                         # Multiple initials
#                         "J. R. R. Tolkien",
#                         "J.R.R. Tolkien",
#                         "J R R Tolkien",
#                         "Tolkien, J. R. R.",
#                         "Tolkien, J.R.R., 1892-1973",

#                         # Single initials
#                         "A. Finn",
#                         "Finn, A.",
#                         "Finn, A., 1979-",
#                         "Finn A.",

#                         # Multiple names
#                         "George R. R. Martin",
#                         "Martin, George R. R.",
#                         "Martin, George R. R., 1948-",

#                         # Apostrophes / hyphens
#                         "Flannery O'Connor",
#                         "O'Connor, Flannery",
#                         "O'Connor, Flannery, 1925-1964",
#                         "Jean-Claude Van Damme",
#                         "Van Damme, Jean-Claude",

#                         # Parenthetical metadata
#                         "Stephen King (Author)",
#                         "King, Stephen (1947-)",
#                         "Lucy Foley [Author]",
#                         "Foley, Lucy [Author]",

#                         # Extra commas / catalog-style garbage
#                         "King, Stephen, 1947-",
#                         "King, Stephen, 1947- , author",
#                         "Foley, Lucy, 1986- , author",
#                         "Tolkien, J. R. R., 1892-1973, author",

#                         # Multiple-word last names
#                         "Gabriel García Márquez",
#                         "García Márquez, Gabriel",
#                         "García Márquez, Gabriel, 1927-2014",

#                         # Names with suffixes
#                         "Martin Luther King Jr.",
#                         "King, Martin Luther, Jr.",
#                         "King, Martin Luther, Jr., 1929-1968",

#                         # More initial edge cases
#                         "A. B. C. Smith",
#                         "A.B.C. Smith",
#                         "A B C Smith",
#                         "Smith, A. B. C.",
#                         "Smith, A.B.C., 1950-",

#                         # One initial mixed with real name
#                         "Foley, L. Lucy",
#                         "L. Lucy Foley",
#                         "Smith, John A.",
#                         "John A. Smith",
#         ]

#         for name in test_authors:
#                 print(f"{name}  => {_normalize_author(name)}")
