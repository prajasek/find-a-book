from dataclasses import dataclass

@dataclass
class Book:
    title: str
    author: str
    normalized_title: str = "" 
    normalized_author: str = ""
    available: bool = False
    count: int = 0