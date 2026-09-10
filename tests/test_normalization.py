from _helpers import _normalize_author, _normalize_title
import pytest

@pytest.mark.parametrize("author, expected",
                                    [
                                        ("Stephen King (hello)", "king stephen"),
                                        ("King, Stephen", "king stephen"),
                                        ("King, Stephen, 1947-", "king stephen"),
                                        ("Finn, A. J.", "aj finn"),
                                        ("Finn, A.J.", "aj finn"),
                                ]
                        )
def test_author_normalization(author, expected):
    assert _normalize_author(author) == expected




@pytest.mark.parametrize("title, expected",
                                    [
                                        ("The Woman in the Window", "the woman in the window"),
                                        ("Ordinary Men: Reserve Police Battalion 101 and the Final Solution in Poland", 
                                         "ordinary men reserve police battalion 101 and the final solution in poland"),
                                        ("test title, 123", "test title 123"),
                                        ("test title2: part 2", "test title2 part 2"),
                                        ("test title 3 (1045)", "test title 3"),
                                ]
                        )
def test_title_normalization(title, expected):
    assert _normalize_title(title) == expected