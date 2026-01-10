import os
from dotenv import load_dotenv
from moorcheh_sdk import MoorchehClient

load_dotenv()

api = os.getenv("api_key")
client = MoorchehClient(api_key=api)
    
def get_actions(extractions_json):
    print("Calling Moorcheh...")
    
    prompt = "You are going to use Selenium to help me progress through this job application. \
    Below, I've sent an extracted JSON with all the important parts of this website. \
    For every input field that should be filled in on the current page, fill it using the information you know about me. \
    If you don't know a piece of information, fill it with generic placeholder data \
    If you need to upload a resume, you can find it with the relative path at ./resumes/resume.pdf \
    Send your response as a single string, with newlines separating each Selenium command. \
    Make sure to add a small 0.5 second sleep between each action.\
    If you deem that the application is complete and that the window can be closed, just return the string \"DONE\" \
    Otherwise, send Selenium instructions without any preamble or explanation (just send lines of Selenium) \
    Here is the summary of the website:\
    " + extractions_json

    response = client.answer.generate(
        namespace="autojob", 
        query=prompt,
        ai_model="anthropic.claude-opus-4-5-20251101-v1:0"
    )
    return response["answer"]