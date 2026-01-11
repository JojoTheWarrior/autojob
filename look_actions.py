import os
from dotenv import load_dotenv
from moorcheh_sdk import MoorchehClient
import base64
from openai import OpenAI

load_dotenv()

api = os.getenv("OPENAI_API_KEY")
moor_api = os.getenv("api_key")
client = OpenAI()
moor_client = MoorchehClient(api_key=moor_api)

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

    prompt = """You are going to use JavaScript to help me progress through this job application. 
    Below, I've sent a screenshot with all the important parts of this website. 
    Decide on what the next action should be; an example of one action is to click on the Apply button or fill in my email, for example.
    To be safe, with a probability of 0.5, consider entering information in into two steps. For example, for one action, just click on the Country box. For the next, select your country, for example.
    Especially for Country, School, Graduation Date, Military related questions, Disability related questions, Sex related questions, and other drop downs selects, these are finnicky because you have to first click on them, then the drop down will appear. 
    If the drop down is already visible, that means you have already clicked on the drop down. In that case, type in enough relevant search such that our desired country or school or graduation date (often a range) is first (this would be one action).
    If you see that the drop down is already full, don't interact with it.
    If you see that our desired dropdown result is already visible and first, you can just desire the next action to be something as simple as "hit Enter" such that the first result is selected (another singular action).
    Your action description can also be something like "Click on the US Work Eligibility input, type in No, then click Enter". If you know that's what you need.
    Your action description can also be something like "Hit the downward arrow a few times". This could be useful for traversing dropdowns that you don't know the full answer to.
    Your action description could also include to not have driver click into an element, and to simply have driver blindly send a few keys. This could be helpful if you see that you're already in the right dropdown.
    Sometimes, with a probability of around 0.5, you should consider clicking into a dropdown (like Degree) and start typing out your degree (Bachelor's) in one action.
    If you see a popup or a cookies banner that you'd like to get rid of, you should do that first.
    The first line of your output should be one sentence describing what you would like this action to be.
    You should look at the screenshot and return a single word or phrase on the second line (your output should only be two lines, separated by a newline character), which is the inner text of the element that you would like to act on next. For instance, if you see a date select and the inner text which is visible in the image says Date, just return the word Date.
    The point of these keywords are to allow the HTML pruner to get only relevant tags that are ancestors of nodes or nodes themselves that contain these visible text. 
    If you're uploading a resume v.s. cover letter, specifiy which it is you want to upload.
    If you deem that the job application is complete, just return the word Done (only one line in this case).
    If you deem that the current page has nothing to interact with, or all the fields have already been filled, just return the word Scroll (only one line in this case).
    If you're trying to close a popup or cookies, let the keyword be Cookies (still two lines in this case).
    If a field is filled but the form still does not seem to acknowledge it, do not refill it. Some forms do not update unless you resubmit them.
    Even if a field is filled incorrectly, do not refill it. Only interact with unfilled elements."""

    if past_wants != []:
        prompt += "By the way, here's a list of your past 10 wants. If you seem to be stuck on a task such as inputting a Visa status or whether you will require sponsorization in the future, try different goals. \
            Instead of just asking to click on the input, you might consider asking to click on the input AND typing, or asking to click on the input AND typing AND pressing Enter in sequence." + '\n'.join(past_wants)

    max_info = open("./test_info.json", "r", encoding="utf-8").read()

    prompt += "Also, here's all the applicant information about me you could need. If you're still missing some info, fill it with a random and generic guess: " + max_info

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

    prompt = f"You are going to use Selenium to help me progress through this job application. \
    You are going to write lines of Selenium to accomplish just the following objective on this page: \
    {past_command} \
    Do not include any leading or trailing preamble or header or footer; just lines of Selenium. \
    Only have runnable Selenium in your answer. Do not include any imports (assume that all relevant Selenium functions have been imported). The driver is called driver. \
    Make sure to separate each Selenium line with a time.sleep(0.1). \
    To be safe, when trying to send input into a box, clear contents inside first by doing control + A, then hitting delete. \
    After filling an input, unless specified to ONLY do one thing by the action, you may consider with a 50% likelihood to hit Enter after the input. \
    If you'd like to upload a resume or cover letter, call my custom function upload_file(upload element (not the button but the input itself), one of 'resume' or 'cv') \
    Attached below is a simplified subset of the HTML webpage, and it should contain enough context for you to reference objects in Selenium. \
    {html_body}"

    max_info = open("./test_info.json", "r", encoding="utf-8").read()

    prompt += "Also, here's all the applicant information about me you could need. If you're still missing some info, fill it with a random and generic guess: " + max_info

    response = moor_client.answer.generate(
        namespace="autojob", 
        query=prompt,
        ai_model="anthropic.claude-opus-4-5-20251101-v1:0"
    )
    return response["answer"]