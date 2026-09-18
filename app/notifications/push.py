import requests
from dotenv import load_dotenv
import os

load_dotenv()

def push_message(message, title="FindABook"):
    url = "https://api.pushover.net/1/messages.json"

    data = {
        "token": os.getenv("PUSHOVER_TOKEN"),
        "user": os.getenv("PUSHOVER_USER_KEY"),
        "message": message,
        "title": title
    }

    response = requests.post(url, data=data)

    return response.ok
     
