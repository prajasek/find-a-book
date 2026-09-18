import requests
from dotenv import load_dotenv
import os
import pytest

load_dotenv()

def test_push():
    msg = (
               "test push notifdication from pytest"
            )
    
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": os.getenv("PUSHOVER_TOKEN"),
        "user": os.getenv("PUSHOVER_USER_KEY"),
        "message": msg
    }

    response= requests.post(url, data=data)

    assert response.status_code == 200