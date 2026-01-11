import os
from dotenv import load_dotenv
from moorcheh_sdk import MoorchehClient
import base64
from openai import OpenAI
import random

load_dotenv()

moor_client = MoorchehClient(api_key=os.getenv("api_key"))
relenvant_context = ""
search_res = moor_client.similarity_search.query(
    namespaces=["autojob"],
    query="first name",
    top_k=10 # Get top 3 most relevant pieces of data
)
search_res.get
for res in search_res.get('results', []):
    relenvant_context += res['text'] + "\n"
    
print(relenvant_context)