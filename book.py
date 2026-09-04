from dataclasses import dataclass, field
from typing import Literal
from helpers import _normalize_title, _normalize_author


@dataclass
class Library:
    location: str
    book_count: str


@dataclass
class LibraryBook:
    title: str
    author: str
    normalized_title: str = field(init=False)
    normalized_author: str = field(init=False)

    match_type: Literal["exact", "close"] | None = None
    url: str | None = None
    libraries: list[Library] = field(default_factory=list)

    def __post_init__(self):
        self.normalized_title = _normalize_title(self.title)
        self.normalized_author = _normalize_author(self.author)



@dataclass
class Book:
    title: str
    author: str
    normalized_title: str = field(init=False)
    normalized_author: str = field(init=False)
    goodreads_url: str | None = None
    library_book: LibraryBook | None = None


    def __post_init__(self):
        self.normalized_title = _normalize_title(self.title)
        self.normalized_author = _normalize_author(self.author)

    @property
    def total_available(self) -> int:
        return sum(library.book_count for library in self.library_book.libraries)