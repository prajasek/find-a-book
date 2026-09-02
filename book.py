from dataclasses import dataclass, field
from helpers import _normalize_title, _normalize_author


@dataclass
class Book:
    title: str
    author: str
    normalized_title: str = field(init=False)
    normalized_author: str = field(init=False)
    available: bool = False
    count: int = 0

    def __post_init__(self):
        self.normalized_title = _normalize_title(self.title)
        self.normalized_author = _normalize_author(self.author)