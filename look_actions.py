import os
from dotenv import load_dotenv
from moorcheh_sdk import MoorchehClient
import base64
from openai import OpenAI
import random

load_dotenv()

api = os.getenv("OPENAI_API_KEY")
moor_api = os.getenv("api_key")
client = OpenAI()
moor_client = MoorchehClient(api_key=moor_api)
profile = open("info.json", "r", encoding="utf-8").read()

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
    
def sanitize(text: str) -> str:
    return (
        text
        .encode("utf-8", errors="ignore")
        .decode("utf-8", errors="ignore")
    )

# alternate between wanting and executing

def want_actions(screenshot, past_wants=[]):
    print(f"Calling for want")

    image_b64 = encode_image(screenshot)

    prompt = """You are the critic, an clever agent that finds the next best action to navigate a job application website.
    Take a deep breath and think about this problem step by step. 
    Below, I've sent a screenshot with all the important parts of this website. 
    YOUR TASK: determine the next action; an example of one action is to click on the Apply button or fill in my email, for example.
    The first thing you should always look to do is to clear any distractions or popups such as cookie banners.
    One of the biggest challenges for you is to deal with dropdowns, so pay special attention to them.
    Most of the time with dropdowns, your ONLY ACTION should be to first click the dropdown and open it.
    This is the best course of action, as you could then see the options available to you.
    After opening the dropdown, in the NEXT action, you can then type in your desired option or hit the down arrow to navigate to it.
    Most importantly, input shows the correct option, but the dropdown is still open, just hit Enter to select it.
    If the drop down is already visible, that means you have already clicked on it. In that case, type in enough relevant search such that our desired country or school or graduation date (often a range) is first (this would be one action).
    If you see that the drop down is already full, don't interact with it.
    If you see that our desired dropdown result is already visible and first, you can just desire the next action to be something as simple as "hit Enter" such that the first result is selected (another singular action).
    If a field is filled but the form still does not seem to acknowledge it, DO NOT REFILL IT. Some forms do not update unless you resubmit them.
    
    Another big challenge is make sure text fields are only filled once. IF THE TEXT FIELD IS ALREADY FILLED, DO NOT FILL IT AGAIN AT ALL COSTS.
    #IMPORTANT: IF A FIELD IS ALREADY FILLED, DO NOT FILL IT AGAIN. THIS WILL OFTEN CAUSE THE FORM TO BREAK.
      - If everything is filled, and there is nothing else currently to do, just return the word \"Scroll\" (in a single line).
      - If the application is complete, just return the word \"Done\" (in a single line).
    
    ACTION FORMATTING:
    An action description is just a sentence, something like, something like "Click on the US Work Eligibility input, type in No, then click Enter". If you know that's what you need.
    It can also be something like "Hit the downward arrow a 2 times". This could be useful for traversing dropdowns that you don't know the full answer to.
    Your action description could also include to not have the driver click into an element, and to simply have driver blindly send a few keys. This could be helpful if you see that you're already in the right dropdown.
    50% of the time, you should consider something like clicking into the dropdown then typing the desired option, all in one action.
    The first line of your output should be one sentence describing what you would like this action to be.
    You should look at the screenshot and return a single keyword or phrase on the second line (your output should only be two lines, separated by a newline character), which is the inner text of the element that you would like to act on next. For instance, if you see a date select and the inner text which is visible in the image says Date, just return the word Date.
    If you're uploading a resume v.s. cover letter, specifiy which it is you want to upload.
    If you deem that the job application is complete, just return the word Done (only one line in this case).
    If you deem that the current page has nothing to interact with, or all the fields have already been filled, just return the word Scroll (only one line in this case).
    If you're trying to close a popup or cookies, let the KEYWORD be Cookies (still two lines in this case).
    """

    if past_wants != []:
        prompt += "Here is a list of the past 10 actions you wanted to do. If you ever seem to be trying to do the same action over and over again, try something else. \
            Instead of just asking to click on the input, you might consider asking to click on the input AND typing, or asking to click on the input AND typing AND pressing Enter in sequence." + '\n'.join(past_wants)

    prompt += "This is the profile of the applicant. Be sure to be constantly refer back to the profile while filling the form. If there is any missing information, fill it with a generic educated guess." + profile

    if random.randint(1, 2) == 2:
        prompt += "This time, make sure to ask specifically to press Enter at the end of your action."

    if random.randint(1, 10) == 10:
        prompt += "If you look at your past actions and realize that you've been trying the same thing for a while, try scrolling down."

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{image_b64}"
                }
            ]
        }]
    )

    print("Want response generated")

    return response.output_text


    
# takes a screenshot path
def execute_actions(html_body, past_command=""):
    print(f"Calling Moorcheh...")
    html_body = sanitize(html_body)

    prompt = f"You are the actor, a clever agent that is best at writing Selenium code to progress through job application websites. \
    Take a deep breath and think about this problem step by step. \
    YOUR TASK: Given the past command I wanted to do, write Selenium code to accomplish the task \
    You are going to write lines of Selenium to accomplish just the following objective on this page: \
    {past_command} \
    NEVER include anything extra, please just write the lines of code. \
    Only have runnable Selenium in your answer. Do not include any imports (assume that all relevant Selenium functions have been imported). The driver is called driver. \
    Make sure to separate each Selenium line with a time.sleep(0.1). \
    When trying to send input into a box, clear contents inside first by doing control + A, then hitting delete. \
    When uploading a resume or cover letter, use the custom function  **upload_file(input_element, str)**) \
        - Where input_element is the actual <input> element, and **str is either \"resume\" or \"cover_letter\"**. \
    Attached below is a simplified subset of the HTML webpage, and it should contain enough context for you to reference objects in Selenium. \
    {html_body}"

    max_info = open("./test_info.json", "r", encoding="utf-8").read()

    prompt += "This is the profile of the applicant. Be sure to be constantly refer back to the profile while filling the form. If there is any missing information, fill it with a generic educated guess." + profile

    response = moor_client.answer.generate(
        namespace="autojob", 
        query=prompt,
        ai_model="anthropic.claude-opus-4-5-20251101-v1:0"
    )
    return response["answer"]