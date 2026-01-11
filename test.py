import json
from moorcheh_sdk import MoorchehClient
from dotenv import load_dotenv
import os

load_dotenv()

profile = ""
with open("info.json", "r") as r:
    profile = r.read()

documents = [
    {
        "id": "full_user_profile",
        "text": profile,
        "category": "json"
    }
]

print("Uploading profile to Moorcheh...")
api_key = os.getenv("api_key") 
with MoorchehClient(api_key=api_key) as client:
    status = client.documents.upload(
        namespace_name="autojob",
        documents=documents
    )
    
    print(status)