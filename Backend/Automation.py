# ===========================================================================================================
#                                         Automation.py
# ===========================================================================================================
# This module handles all system-level automation tasks and online application interactions.
# It acts as the "Hands" of the AI, executing commands like opening apps, playing music,
# searching the web, and controlling system volume/power.
#
# Key Features:
# - App Management: Open/Close applications (using AppOpener).
# - Web Automation: Google Search, YouTube Search/Play (using pywhatkit & webbrowser).
# - System Control: Volume, Shutdown, Sleep (using keyboard shortcuts).
# - Content Generation: Writing text to files (using Local LLM).
# - Async Execution: Capable of running multiple commands in parallel.

from AppOpener import close, open as appopen # Import AppOpener module to open/close applications. 
from webbrowser import open as webopen # Import webbrowser module to open web pages. 
from pywhatkit import search, playonyt # Import pywhatkit module to search and play YouTube videos. 
from dotenv import dotenv_values # Import dotenv module to load environment variables. 
from bs4 import BeautifulSoup # Import BeautifulSoup module to parse HTML content. 
from rich import print # Import rich module to print formatted text. 
from openai import OpenAI # Import OpenAI module to interact with OpenAI API or Local LM Studio server. 
import webbrowser # Import webbrowser module to open web pages. 
import subprocess # Import subprocess module to run system commands. 
import requests # Import requests module to make HTTP requests. 
import keyboard # Import keyboard module to simulate keyboard events. 
import asyncio # Import asyncio module to handle asynchronous operations. 
import tempfile # Import tempfile module to create temporary files. 
import os # Import os module to interact with the operating system. 

# -------------------------------------------------------------------------------------------------------
#                                         Configuration
# -------------------------------------------------------------------------------------------------------

# Load environment variables from .env file. 
env_vars = dotenv_values(".env")

# Initialize OpenAI client for local LM Studio server
# This is used specifically for the 'Content' generation command.
client = OpenAI(
    base_url="http://localhost:1234/v1", 
    api_key="lm-studio"
)

# CSS classes used for parsing Google Search results (HTML scraping).
CSS_CLASSES = [
    "ZCubwf",
    "hgKElc",
    "LTKOO sY7ric",
    "Z0lcw",
    "gsrt vk_bk FzvWSb YwPhnf",
    "pclqee",
    "tw-Data-text tw-text-small tw-ta",
    "U6rdf",
    "5uO5Gd LTKOO",
    "vlzY6d",
    "webanswers-webanswers_table__webanswers-table",
    "dDoNo ikb4Bb gsrt",
    "sXLaOe",
    "LwkFke",
    "VQF4g",
    "qv3Wpe",
    "kno-rdesc",
    "SPZz6b",
]

# User-Agent string to mimic a real browser for HTTP requests.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/100.0.4896.75 Safari/537.36"
)

# Professional responses for chat interactions (currently unused in logic but defined).
professional_response = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with."
    "I'm at your service for additional assistance or support, you may need don't hesitate to ask me."
    "I'm here to assist you with any questions or tasks you may have."
    "Please let me know if you need any further assistance or have any questions."
]

# List to store chatbox messages for the Content Generation LLM context.
messages = []

# System message for the Content Writer persona.
SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username', 'User')}. You're a content writer. You have to write content like letters, codes, applications, essays, notes, songs, poems, summaries, etc. for the user."}]

# -------------------------------------------------------------------------------------------------------
#                                         Automation Functions
# -------------------------------------------------------------------------------------------------------

def WebSearch(query):
    """
    Performs a Google search using pywhatkit.
    """
    search(query)
    return True

def Content(Topic):
    """
    Generates text content (essays, code, etc.) using the Local LLM.
    1. Generates content based on 'Topic'.
    2. Saves it to a temporary text file.
    3. Opens the file in Notepad for the user.
    """

    # Nested function to open a file in notepad. 
    def open_notepad(File):
        default_text_editor = "notepad.exe"
        subprocess.Popen([default_text_editor, File]) # Open the file in notepad. 

    # Nested function to generate content using LLM. 
    def ContentGeneration(Topic):
        messages.append({"role": "user", "content": f"{Topic}"}) # Append the prompt to the messages list. 
        
        completion = client.chat.completions.create(
            model="local-model", 
            messages= SystemChatBot + messages,
            temperature=0.7,
            stream=True,
        )

        Answer = "" # Initialize the answer in an empty string for the response.
        
        # Process streamed response chunks. 
        for chunk in completion:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content # Check for the content in current chunk. 
                Answer += content # Append the content to answer. 
                #print(content, end="") # Print the content in real-time.
        Answer = Answer.replace("/s", "") # Remove unwanted tokens from the answer. 
        messages.append({"role": "assistant", "content": f"{Answer}"}) # Append the answer to the messages list. 
        return Answer

    Topic_Clean: str = Topic.replace("Content", "") # Remove "Content" keyword from the topic.
    ContentByLLM = ContentGeneration(Topic) # Generate content using LLM. 

    # Create a temporary file path. 
    temp_dir = tempfile.gettempdir()
    file_name = f"LLM_Output_{Topic_Clean[:10].replace(' ', '_')}.txt"
    temp_file_path = os.path.join(temp_dir, file_name)

    # Write the content to the temporary file. 
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(ContentByLLM)
        f.close()
        
    open_notepad(temp_file_path) # Open the file in notepad. 
    return True # Indicate successful execution. 

def YoutubeSearch(Topic):
    """
    Opens YouTube search results for a specific topic in the browser.
    """
    search_url = f"https://www.youtube.com/results?search_query={Topic}" # Create the search URL. 
    webbrowser.open(search_url) # Open the search URL in the default browser. 
    return True # Indicate successful execution. 

def PlayYoutube(query):
    """
    Plays the first video result for a query on YouTube.
    """
    playonyt(query) # Use pywhatkit's playonyt to play the video on youtube. 
    return True # Indicate successful execution. 

def OpenApp(app, sess=requests.Session()):
    """
    Attempts to open a desktop application or a website.
    - First logic: Uses AppOpener to find installed apps.
    - Fallback logic: If app not found, searches Google for a link and opens it.
    """
    try: 
        appopen(app, match_closest=True, output=True, throw_error=True) # Attempt to open the app. 
        return True # Indicate successful execution. 
    
    except:
        # Fallback: Web Search logic
        
        # Nested function to extract links from the HTML content. 
        def extract_link(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, "html.parser") # Parse the HTML content. 
            links = soup.find_all("a", {'jsname': 'UWckNb'}) # Find all the links in the HTML content. 
            for link in links: # Iterate over the links. 
                return [link.get("href")] # Return the list of links.

        # Nested function to perform Google Search and retrive HTML. 
        def google_search(query):
            search_url = f"https://www.google.com/search?q={query}" # Create the search URL. 
            headers = {
                "User-Agent": USER_AGENT
            }
            response = sess.get(search_url, headers=headers) # Send a GET request to the search URL. 
            
            if response.status_code == 200:
                return response.text # Return the HTML content. 
            else:
                print(f"Failed to retrieve HTML content. Status code: {response.status_code}") # Print the status code. 
                return None # Return None if the request failed. 
                
        html = google_search(app) # Perform Google Search and retrieve HTML. 

        if html:
            link = extract_link(html) # Extract links from the HTML content. 
            if link:
                webbrowser.open(link[0]) # Open the link in the default browser. 
                return True # Indicate successful execution. 
            else:
                print("No links found in the HTML content.") # Print a message if no links are found. 
                return False # Indicate failure. 
    
def CloseApp(app):
    """
    Closes a running application.
    """
    if "chrome" in app:
        pass # skip if the app is chrome (safety measure). 
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True) # Attempt to close the app. 
            return True # Indicate successful execution. 
        except:
            print(f"Failed to close {app}") # Print a message if the app fails to close. 
            return False # Indicate failure. 

def ExecuteCommand(command):
    """
    Executes system-level commands using keyboard shortcuts.
    Supports: Volume controls, Mute, Shutdown, Restart, Lock.
    """
    
    # Nested functions for specific actions
    def mute():
        keyboard.press_and_release(" volume mute")

    def unmute():
        keyboard.press_and_release(" volume mute")
    
    def increase_volume():
        keyboard.press_and_release(" volume up")
    
    def decrease_volume():
        keyboard.press_and_release(" volume down")
    
    def turn_off():
        keyboard.press_and_release(" sleep")
    
    def turn_on():
        keyboard.press_and_release(" sleep")

    def lock():
        keyboard.press_and_release(" lock")

    def shutdown():
        keyboard.press_and_release(" shutdown")

    def restart():
        keyboard.press_and_release(" restart")

    # Command Router
    if "mute" in command:
        mute()
    elif "unmute" in command:
        unmute()
    elif "increase volume" in command:
        increase_volume()
    elif "decrease volume" in command:
        decrease_volume()
    elif "turn off" in command:
        turn_off()
    elif "turn on" in command:
        turn_on()
    elif "lock" in command:
        lock()
    elif "shutdown" in command:
        shutdown()
    elif "restart" in command:
        restart()
    else:
        print(f"Unknown command: {command}") # Print a message if the command is unknown. 

    return True # Indicate successful execution. 

# -------------------------------------------------------------------------------------------------------
#                                         Orchestrator Functions
# -------------------------------------------------------------------------------------------------------

async def translate_and_execute(commands: list[str]):
    """
    Parses a list of commands and schedules their execution asynchronously.
    Each command type ('open', 'play', 'system', etc.) maps to a specific function.
    """
    funcs = [] # List to store asynchronous tasks.

    for command in commands:
        if command.startswith("open "): # Handle "open" command.
            if "open it" in command:
                pass # Skip context-dependent "it" commands. 
            if "open file " in command:
                 pass # Skip file opening commands (handled differently). 
            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open ")) # Schedule app opening in a separate thread. 
                funcs.append(fun) # Add the function to the list. 
        
        elif command.startswith("general "):
            pass # Skip "general" chat commands (handled by Chatbot.py, not Automation). 

        elif command.startswith("close "):
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close ")) 
            funcs.append(fun) 
        
        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play ")) 
            funcs.append(fun) 
        
        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content ")) 
            funcs.append(fun) 
            
        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YoutubeSearch, command.removeprefix("youtube search ")) 
            funcs.append(fun) 
            
        elif command.startswith("google search "):
            fun = asyncio.to_thread(WebSearch, command.removeprefix("google search ")) # Use WebSearch instead of local definition
            funcs.append(fun) 

        elif command.startswith("system "):
            fun = asyncio.to_thread(ExecuteCommand, command.removeprefix("system ")) # Use ExecuteCommand
            funcs.append(fun) 

        else:
            print(f"Unknown command: {command}") 
            
    # Execute all scheduled tasks concurrently
    results = await asyncio.gather(*funcs) 

    for result in results: 
        if isinstance(result, str):
            yield result 
        else:
            yield result 

async def Automation(commands: list[str]):
    """
    Public wrapper to run the automation logic.
    Main.py calls this function.
    """
    async for result in translate_and_execute(commands): 
        pass
    return True # Indicate successful execution.   

# -------------------------------------------------------------------------------------------------------
#                                         Main Execution (Test Node)
# -------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio
    while True:
        command = input("Enter command: ")
        asyncio.run(Automation([command]))
