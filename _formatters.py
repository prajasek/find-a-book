from book import Book
from config import TARGET_LIBRARIES



####### RESPONSE FORMATTERS  #########################################################################################

def format_want_to_read_books(books: list[Book]) -> str:
        lines = []
        lines.append("Goodreads Want-to-Read List")
        lines.append("----------------------------")
        for index, book in enumerate(books, 1):
                lines.append(f"{index}. {book.title} - {book.author}")
                

        return "\n".join(lines)


def format_detailed(books: list[Book]) -> str:
    lines = []

    for book in books:
        lines.append(f"📚 {book.title}")
        lines.append(f"{book.author}")
        if not book.library_book:
            lines.append("❌ Book not found.")
            lines.append("\n")
            continue

        if book.library_book.match_type == "close":
            lines.append("≈ Close match")

        elif book.library_book.match_type == "exact":
            lines.append("✅ Exact match")

        lines.append("")
        lines.append(f"{book.library_book.title}")
        lines.append(f"{book.library_book.author}")
        lines.append(f"{book.library_book.url}")

        lines.append("")

        libraries = book.library_book.libraries

        if not libraries:
            lines.append("No copies available anywhere.")

        for library in libraries:
            location = library.location
            total_available = library.available_count

            lines.append(f"{location}")

            for status, count in library.status.items():
                lines.append(f"\t-{status}: {count}")

            lines.append(f"Total available at {location}: {total_available}")
            lines.append("")

        lines.append("\n")

    return "\n".join(lines)



def format_by_location(books: list[Book]) -> str:
    lines = []

    for target_location in TARGET_LIBRARIES:
        lines.append(f"{target_location}:")
        lines.append("-"*50)

        for book in books:

            if not book.library_book: 
                continue

            libraries = book.library_book.libraries

            if not libraries:
                continue

            if book.total_available:
                for library in libraries:
                    if library.location == target_location:
                        match_type = ""

                        if book.library_book.match_type == "close":
                            match_type = "≈"

                        elif book.library_book.match_type == "exact":
                            match_type = "✅"

                        lines.append(f"• {book.title} - {library.available_count} {match_type}")
                    

        lines.append("")
    return "\n".join(lines)


def format_by_book(books: list[Book]) -> str:
    lines = []

    for book in books:
        title = book.title
        author = book.author

        lines.append(f"📚 {title} ({author})")

        if not book.library_book: 
            lines.append("Book not found in catalog. ❌")
            continue

        match_type = ""

        if book.library_book.match_type == "close":
            match_type = "☑️"

        elif book.library_book.match_type == "exact":
            match_type = "✅"

        libraries = book.library_book.libraries


        found = False
        for library in libraries: 
            if library.available:
                found = True
                loc = library.location
                count = library.available_count

                lines.append(f"{loc}: {count} {match_type}")

        if not found:
            lines.append("No copies available. 🚫")

        lines.append("")

    return "\n".join(lines)

        
        

            
        