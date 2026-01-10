import os
from dotenv import load_dotenv
from moorcheh_sdk import MoorchehClient

load_dotenv()

api = os.getenv("api_key")
client = MoorchehClient(api_key=api)

with open("rbc_extraction.json", "r") as r:
    json = r.read()

prompt = """You are going to use Selenium to help me progress through this job application.
Below, I've sent an extracted JSON with all the important parts of this website.
For every input field that should be filled in on the current page, fill it using the information you know about me.
If you don't know a piece of information, fill it with generic placeholder data
Send your response as a single string, with newlines separating each Selenium command.
Make sure to add a small 0.5 second sleep between each action.
When you come across a resume upload section, find the resume in the relative path resumes/resume.pdf
Make sure to only output Selenium commands, don't include imports, only code proceed through the application.
Here is the summary of the website:
""" + json
    
response = client.answer.generate(
    namespace="autojob", 
    query=prompt,
    ai_model="anthropic.claude-opus-4-5-20251101-v1:0"
)
print(prompt + "\n\n")

print(response["answer"])
