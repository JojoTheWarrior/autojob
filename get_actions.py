

prompt = "You are going to use Selenium to help me progress through this job application. \
    Below, I've sent an extracted JSON with all the important parts of this website. \
    For every input field that should be filled in on the current page, fill it using the information you know about me. \
    If you don't know a piece of information, fill it with generic placeholder data \
    Send your response as a single string, with newlines separating each Selenium command. \
    Make sure to add a small 0.5 second sleep between each action. \
    Here is the summary of the website:"