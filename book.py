from dataclasses import dataclass, field
import hashlib
from typing import Literal
from _helpers import _normalize_title, _normalize_author
from enum import Enum


class BookStatus(Enum):
    CHECKED_OUT = "checked out"
    ON_HOLD = "on hold"
    ON_HOLDSHELF = "on holdshelf"
    ON_SHELF = "on shelf"
    ON_SHELF_HYPHEN = "on-shelf"
    RECENTLY_RETURNED = "recently returned"


@dataclass
class LibraryLocation:
    location: str
    status: dict[str, int] = field(default_factory=dict)

    @property
    def available_count(self) -> int:
        available_filter: list[int] = [
            self.status.get(state.value, 0)
            for state in (
                BookStatus.ON_SHELF,
                BookStatus.ON_SHELF_HYPHEN,
                BookStatus.RECENTLY_RETURNED,
            )
        ]
        return sum(available_filter)

    @property
    def available(self) -> bool:
        return self.available_count > 0


@dataclass
class LibraryBook:
    title: str
    author: str
    normalized_title: str = field(init=False)
    normalized_author: str = field(init=False)

    match_type: Literal["exact", "close"] | None = None
    url: str | None = None
    libraries: list[LibraryLocation] = field(default_factory=list)

    def __post_init__(self):
        self.normalized_title = _normalize_title(self.title)
        self.normalized_author = _normalize_author(self.author)


@dataclass
class Book:
    id: str = field(init=False)
    title: str
    author: str
    normalized_title: str = field(init=False)
    normalized_author: str = field(init=False)
    goodreads_url: str | None = None
    library_book: LibraryBook | None = None

    def __post_init__(self):
        self.normalized_title = _normalize_title(self.title)
        self.normalized_author = _normalize_author(self.author)
        self.id = self._generate_id()

    @property
    def total_available(self) -> int:
        if not self.library_book:
            return 0

        return sum(library.available_count for library in self.library_book.libraries)

    def _generate_id(self) -> str:
        value = f"{self.normalized_title}:{self.normalized_author}"
        print(f"Generating ID for: {value}")
        x = hashlib.sha256(value.encode())
        h = x.hexdigest()[:12]
        print(f"Hash: {h}")
        return h
