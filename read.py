import os
from dotenv import load_dotenv
from moorcheh_sdk import MoorchehClient

load_dotenv()

api = os.getenv("api_key")
client = MoorchehClient(api_key=api)

response = client.answer.generate(
    namespace="autojob", 
    query="What is Moorcheh?",
    ai_model="anthropic.claude-opus-4-5-20251101-v1:0"
)

print(response["answer"])
