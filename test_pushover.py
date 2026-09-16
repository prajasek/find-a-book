import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

msg = (
            """Chester County Library:
            --------------------------------------------------
            • The Handmaid's Tale - 3 ✅
            • Wild Dark Shore - 1 ≈
            • The Paris Apartment - 1 ≈
            • The Girl Who Played with Fire (Millennium #2) - 2 ✅

            Henrietta Hankin Library:
            --------------------------------------------------
            • The Handmaid's Tale - 1 ✅
            • The Body Keeps the Score: Brain, Mind, and Body in the Healing of Trauma - 1 ✅
            • Wild Dark Shore - 1 ≈
            • The Paris Apartment - 2 ≈
            • None of This Is True - 2 ≈
            • The Girl Who Played with Fire (Millennium #2) - 1 ✅"""
        )


url = "https://api.pushover.net/1/messages.json"
data = {
    "token": os.getenv("PUSHOVER_TOKEN"),
    "user": os.getenv("PUSHOVER_USER_KEY"),
    "message": msg
}

response=  requests.post(url, data=data)

print(response.status_code)
print(response.json())