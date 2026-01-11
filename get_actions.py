import os
from dotenv import load_dotenv
from moorcheh_sdk import MoorchehClient

load_dotenv()

api = os.getenv("api_key")
client = MoorchehClient(api_key=api)
    
def get_actions(extractions_json, error="", attempt="", attempt_number=0):
    print(f"Calling Moorcheh... attempt {attempt_number}")

    prompt = "You are going to use Selenium to help me progress through this job application. \
    Below, I've sent an extracted JSON with all the important parts of this website. \
    First and foremost, clear all distractions from the page (like accept cookies, close any other popups) \
    For every input field that should be filled in on the current page, fill it using the information you know about me. \
    Any input fields that are already full do not have to be filled again. If you want to refill them, make sure you write over the previous value of that input box \
    If you don't know a piece of information, fill it with generic placeholder data \
    If you need to upload a resume or CV, call the function upload_file(selenium element of the <input> (important: not the button, rather the thing that looks like input[type='file']), \"resume\" or \"cv\" (so a string attribute)) \
    If the resume or CV has already been uploaded, then don't try to upload it again \
    If there was a previous error and it was something about \"element not clickable\" at a coordinate, the fix is usually not to reposition the screen but rather to perhaps not interact with that element or interact with it differently \
    Never directly click an element; instead, use the function we have defined safe_click(driver, element) \
    Send your response as a single string, with newlines separating each Selenium command. \
    Make sure to add a small 0.5 second sleep between each action.\
    If you deem that the application is complete and that the window can be closed, just return the string \"DONE\" \
    Otherwise, send Selenium instructions without any preamble or explanation (just send lines of Selenium) \
    Also don't include any imports (assume all Selenium things are there) \
    Here is the summary of the website:\
    " + extractions_json

    if error != "":
        prompt += "\n\nAdditionally, here's the error that this page threw last time. \
        See if you can fix it for next time:\n" + error
    if attempt != "":
        prompt += f"\n\nAnd the instructions you tried running last time are sent after this. \
            If you tried to send many instructions at once, you might need to slow down. \
            You've already been on this page {attempt_number} times. If this number is >= 1, consider halving the number of instructions you're sending at once. \
            If you've been on this page many, many times, try just sending one instruction at a time to navigate slowly and not rush any interactions. \n" + attempt 
        
    response = client.answer.generate(
        namespace="autojob", 
        query=prompt,
        ai_model="anthropic.claude-opus-4-5-20251101-v1:0"
    )
    return response["answer"]