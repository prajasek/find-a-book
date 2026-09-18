from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from app.config import DEBUG_MODE, NEW_BOOK_THRESHOLD_HRS
from app.book import Book
from app.utils._helpers import _delta_hours, _normalize_author, _normalize_title


####   LOAD SETTINGS AND BOOKS ###############
from dotenv import load_dotenv
load_dotenv()

BOOKS_FILE = os.getenv("BOOKS_FILE", "/database/books.json")
SETTINGS_FILE = os.getenv("SETTINGS_FILE", "/database/settings.json")
print("loaded files")

######## STORE BOOK DETAILS #####################


# Store book information from goodreads - books.json.

# When a fresh parse from goodreads is done during /run or
# /goodreads, the parsed result is compared against the 
# existing stored information.

# Properties in books.json:
# - id
# - title
# - author
# - goodreads_url
# - watch: default False
# - added_at: timestamp
# - available
# - libraries: {Chester: 1, Henriatte: 2}

# if books dont exist in json, then add them with timestamp 
# if books exist, let it be
# if books were removed, then add them to a removed list for response



class Storage:
        def get_notification_status(self):
                try:
                        with open(SETTINGS_FILE, 'r', encoding='utf-8') as file:
                                data = json.load(file)
                        return True, data["notifications"], "Succesfully loaded notification"
                except:
                       return False, None, "Error getting notification status"
             
                
        def toggle_notification(self):
                try:
                        success, status, msg = self.get_notification_status()

                        if not success:
                               return success, status, msg
                        
                        status = not status
                        status_dict = {"notifications": status}

                        print("trying to toggle notification: ", status_dict["notifications"])

                        with open(SETTINGS_FILE, 'w', encoding='utf-8') as file:
                                json.dump(status_dict, file, ensure_ascii=False, indent=4)

                        return True, status, f"notification set to {status}"

                except:
                       return False, None,  f"Could not toggle notification status."
                

        def _save_books(self, books: list[dict]):
                with open(BOOKS_FILE, 'w') as file:
                        json.dump(books, file, ensure_ascii=False, indent=4)


        def _get_stored_books(self) -> list[dict]:
            try:
                with open(BOOKS_FILE, 'r') as file:
                    books = json.load(file)
                    return books
            except FileNotFoundError:
                   f = open(BOOKS_FILE, 'w')
                   f.close()
                   return []
            except: 
                   return []


        def _get_stored_books_by_id(self):
                stored_books = self._get_stored_books()
                return {
                       _book["id"]:_book
                        for _book in stored_books
                }



        def _get_recently_added_books(self, books: list[dict], hrs: float = NEW_BOOK_THRESHOLD_HRS):
                now = datetime.now(timezone.utc)

                hrs = hrs or 12

                return [
                       book
                       for book in books
                       if _delta_hours(book["added_at"], now) < hrs
                       and book["removed"] is False
                ]


        def _get_previously_removed_books(self, books: list[dict]):
                return [
                       book
                       for book in books
                       if book["removed"]
                ]


        def update_booklist(self, books:list[Book]) -> list[dict]:
                """
                Properties in books.json:
                - id
                - title
                - author
                - goodreads_url
                - watch: default False
                - added_at: timestamp
                - available
                - libraries: {Chester: 1, Henriatte: 2}

                Steps:
                1) read current books.json into memory
                2) Compare new 'books' list to stored data
                3) if anything new, add to the json with timestamp
                """

                updated_booklist = {
                            "books": [], 
                            "new": [], 
                            "removed": []
                        }

                stored_by_ids = self._get_stored_books_by_id()
            
                for book in books:
                        # Pre-existing books. Add them back.
                        if book.id in stored_by_ids:
                                stored_book = stored_by_ids[book.id]
                                updated_booklist["books"].append(stored_book)

                        # Newly added to want-to-read list
                        else:
                                new_book = {
                                        "id": book.id, 
                                        "title": book.title, 
                                        "author": book.author, 
                                        "url": book.goodreads_url,
                                        "source": "goodreads", 
                                        "watch": False, 
                                        "added_at": datetime.now(timezone.utc).isoformat(),
                                        "removed": False
                                    }
                                updated_booklist["books"].append(new_book)


                updated_booklist["new"] = self._get_recently_added_books(updated_booklist["books"])
                updated_booklist["removed"] = self._get_previously_removed_books(updated_booklist["books"])


                # Update removed books from goodreads
                latest_book_ids = [_.id for _ in books]

                for _id, _stored_book in stored_by_ids.items():
                        if _id not in latest_book_ids:

                                # If this was added through "Add to list", then add it back and move on
                                if _stored_book["source"] == "manual":
                                      updated_booklist["books"].append(_stored_book)
                                      continue

                                # This was a previously added goodreads book thats now removed from
                                # want-to-read
                                _removed_book = _stored_book
                                _removed_book["removed"] = True

                                updated_booklist["removed"].append(_removed_book)
                                updated_booklist["books"].append(_removed_book)


                if DEBUG_MODE:
                    from pprint import pprint
                    pprint(updated_booklist)

                self._save_books(updated_booklist["books"])
                return updated_booklist


        def all_books_from_json(self) -> dict[str, list]:
                stored_books = self._get_stored_books()
                if stored_books:
                        return {
                                "books": stored_books, 
                                "new": self._get_recently_added_books(stored_books), 
                                "removed": self._get_previously_removed_books(stored_books)
                        }

                # to maintain consistent interface for the front-end
                return {"books": [], "new": [], "removed": []}


        def _titles_match(self, title1, title2):

                words1 = set(_normalize_title(title1).split())
                words2 = set(_normalize_title(title2).split())

                return words1 <= words2 or words2 <= words1
        

        def book_exists(self, book:Book):
                stored_books = self._get_stored_books()
                
                for _b in stored_books:
                       if (
                        self._titles_match(_b["title"], book.title)
                        and book.normalized_author == _normalize_author(_b["author"])
                        ):      
                                print("already in json")
                                return True

                return False


        def add_book(self, book:Book):
                if self.book_exists(book):
                       return False, "Book already exists."
                       
                new_book = {
                        "id": book.id, 
                        "title": book.title, 
                        "author": book.author, 
                        "url": book.goodreads_url,
                        "source": "manual", 
                        "watch": False, 
                        "added_at": datetime.now(timezone.utc).isoformat(),
                        "removed": False
                }

                stored_books = self._get_stored_books()
                stored_books.append(new_book)
                self._save_books(stored_books)
                return True, "Book added."



        def remove_book(self, id: str):
                stored_books = self._get_stored_books()

                for book in stored_books:
                       if book["id"] == id:
                              stored_books.remove(book)
                              self._save_books(stored_books)
                              return True, "Book removed."

                return False, "Book not found."
                



        def get_watchlist(self) -> list[dict]:
            stored_books = self._get_stored_books()
            watchlist = [book for book in stored_books if book["watch"]]
            print("watchlist", watchlist)

            _b = {
                "books": watchlist, 
                "new": self._get_recently_added_books(watchlist), 
                "removed": self._get_previously_removed_books(watchlist)
            }

            print(_b)
            return _b

            
        def update_watchlist(self, book_id: str, watch: bool) -> bool:
            stored_books = self._get_stored_books()
            for book in stored_books:
                    if book_id == book["id"]:
                            book["watch"] = watch
                            self._save_books(stored_books)
                            if watch is True:
                                return True, f"{book['title']} added to watchlist."
                    
                            return True, f"{book['title']} removed from watchlist."
            
            return False, None



