import os
from dotenv import load_dotenv
from moorcheh_sdk import MoorchehClient

load_dotenv()

api = os.getenv("api_key")
client = MoorchehClient(api_key=api)
    
def get_actions(extractions, error="", attempt="", attempt_number=0):
    print(f"Calling Moorcheh... attempt {attempt_number}")

    system_instruction = (
        "You are an expert Selenium Automation Engineer specializing in autonomous job applications. "
        "Your goal is to navigate web forms, handle dynamic DOM elements, and submit applications robustly."
        "Please take your time and think through this problem step by step. \n\n"
        "### OPERATIONAL RULES:\n"
        "1. **Safety First:** Never click directly. Use `safe_click(driver, element)`.\n"
        "2. **State Management:** If an input is pre-filled, overwrite it only if necessary. If a file is uploaded, do not re-upload.\n"
        "3. **Distraction Removal:** Prioritize closing cookie banners or modals before interacting with form fields.\n"
        "4. **File Uploads:** Use `upload_file(element, file_type)` on `input[type='file']` elements specifically.\n"
        "5. **Error Handling:** If an 'element not clickable' error occurred previously, retry by interacting with the parent container or using JavaScript execution.\n"
        "6. **Pacing:** Add `time.sleep(0.5)` between every distinct action.\n"
        "7. **Unknown Data:** Use generic placeholder data if personal info is missing.\n"
        "8. **Completion:** Return exactly \"DONE\" if the application is submitted or the workflow is finished.\n\n"
        "### OUTPUT FORMAT:\n"
        "YOU MUST ONLY OUTPUT SELENIUM CODE!!! No comments, no explaination, no import statements, anything of that sort is an automatic fail."
    )

    context_data = f"### CURRENT DOM CONTEXT (Cleaned HTML):\n{extractions}\n"

    error_context = ""
    if error:
        error_context = (
            f"\n### PREVIOUS ERROR:\n{error}\n"
            "CRITICAL: The previous attempt failed. Analyze the error above. "
            "If the error was 'element not clickable', do not repeat the exact same selector/interaction. "
            "Try scrolling the element into view or selecting a different unique attribute.\n"
        )

    retry_context = ""
    if attempt:
        # Dynamic pacing adjustment based on failure count
        pacing_instruction = "Maintain normal execution speed."
        if attempt_number >= 1:
            pacing_instruction = "REDUCE BATCH SIZE: Send fewer instructions to isolate the failure."
        if attempt_number >= 3:
            pacing_instruction = "SINGLE STEP MODE: Send only ONE instruction to ensure stability."

        retry_context = (
            f"\n### PREVIOUS ATTEMPT (Failed):\n{attempt}\n"
            f"### RETRY STRATEGY ({attempt_number} failures):\n"
            f"{pacing_instruction}\n"
        )

    # Combine components
    full_prompt = (
        f"{system_instruction}\n"
        f"{context_data}\n"
        f"{error_context}\n"
        f"{retry_context}\n"
        "### GENERATE RESPONSE:"
    )

    response = client.answer.generate(
        namespace="autojob", 
        query=full_prompt,
        ai_model="anthropic.claude-opus-4-5-20251101-v1:0"
    )
    return response["answer"]