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

from AppOpener import close, open as appopen # Import AppOpener to control desktop applications (Open/Close).
from webbrowser import open as webopen # Import webbrowser to open URLs in the default browser.
from pywhatkit import search, playonyt # Import pywhatkit for performing Google Searches and playing YouTube videos.
from dotenv import dotenv_values # Import dotenv_values to securely load sensitive variables from the .env file.
from bs4 import BeautifulSoup # Import BeautifulSoup for parsing HTML content (Web Scraping).
from rich import print # Import rich's print function for beautiful, colored terminal output.
from openai import OpenAI # Import OpenAI client to interact with the Local LLM (LM Studio).
import webbrowser # Standard library for web browsing.
import subprocess # Standard library for executing system commands (like 'shutdown', 'taskkill').
import requests # Standard library for making HTTP requests (GET/POST).
import keyboard # Library to simulate keyboard key presses (shortcuts).
import asyncio # Standard library for writing concurrent code using the async/await syntax.
import tempfile # Standard library to create temporary files (used for LLM content generation).
import os # Standard library for Operating System interactions (file paths, system checks).
import ctypes # Standard library to call low-level Windows API functions (e.g., locking the screen).
import platform # Standard library to detect the underlying OS (Windows, Linux, Mac).

# -------------------------------------------------------------------------------------------------------
#                                         Configuration
# -------------------------------------------------------------------------------------------------------

# Load environment variables from the .env file (e.g., API keys, settings).
env_vars = dotenv_values(".env")

# Initialize the OpenAI Client for the Local LLM (LM Studio).
# This client is used primarily for the 'Content' generation feature,
# where the AI writes essays, emails, or code for the user.
client = OpenAI(
    base_url="http://localhost:1234/v1", # The local URL where LM Studio is running.
    api_key="lm-studio" # A placeholder key since we are running locally.
)

# List of CSS classes used to scrape Google Search results.
# These classes are specific to Google's HTML structure and are used to extract
# the "Quick Answer" or "Featured Snippet" text from the search results page.
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
        # Explicit handling for File Explorer (AppOpener often misses this)
        if app in ["file explorer", "file manager", "my computer", "this pc", "explorer"]:
            os.startfile("explorer")
            return True

        appopen(app, match_closest=True, output=True, throw_error=True) # Attempt to open the app. 
        return True # Indicate successful execution. 
    
    except:
        # Fallback: Web Search logic to open via Chrome
        
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
        
        # Helper to open URL in Chrome safely using exact paths
        def open_in_chrome(url):
            try:
                system = platform.system()
                if system == "Windows":
                    # Common Chrome paths on Windows
                    chrome_paths = [
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                    ]
                    for path in chrome_paths:
                        if os.path.exists(path):
                            subprocess.run([path, url])
                            return True
                    # Fallback to 'start chrome'
                    subprocess.run(f'start chrome "{url}"', shell=True)
                    return True
                else:
                    webbrowser.open(url)
                    return True
            except Exception as e:
                print(f"Error opening Chrome: {e}")
                webbrowser.open(url)
                return True

        html = google_search(app) # Perform Google Search and retrieve HTML. 

        if html:
            link = extract_link(html) # Extract links from the HTML content. 
            if link:
                open_in_chrome(link[0]) # Open the link in Chrome. 
                return True 
            else:
                open_in_chrome(f"https://www.google.com/search?q={app}")
                return True
        else:
            open_in_chrome(f"https://www.google.com/search?q={app}")
            return True 
    
def CloseApp(app):
    """
    Closes a running application.
    Prioritizes closing safe windows via WM_CLOSE message.
    For browsers, it attemps to close strictly the matched tab (Ctrl+W) unless the user explicitly asks to close the browser.
    """
    app = app.lower().strip()

    # Safety Check: Handle File Explorer specifically
    if "file explorer" in app or "explorer" == app:
        try:
            # Use PowerShell to safely close only open Explorer windows
            cmd = "powershell -Command \"(New-Object -ComObject Shell.Application).Windows() | ForEach-Object { $_.Quit() }\""
            subprocess.run(cmd, shell=True)
            print("Closed all File Explorer windows.")
            return True
        except Exception as e:
            print(f"Error closing File Explorer: {e}")
            return False

    # Special handling for UWP apps that act stubborn (Settings, Store, etc.)
    if "settings" in app:
        try:
            subprocess.run("taskkill /f /im SystemSettings.exe", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            print("Closed Settings.")
            return True
        except:
             pass
             
    if "store" in app or "calculator" in app:
         # Rely on window title matching below, but ensuring they aren't blocked by critical process checks later
         pass

    # Logic: Search for visible windows matching the app name
    try:
        import time
        import keyboard
        from ctypes import windll, create_unicode_buffer
        
        WM_CLOSE = 0x0010
        found_windows = []

        def enum_windows_callback(hwnd, _):
            if windll.user32.IsWindowVisible(hwnd):
                length = windll.user32.GetWindowTextLengthW(hwnd)
                buf = create_unicode_buffer(length + 1)
                windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                
                if app in title:
                    found_windows.append(hwnd)
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        windll.user32.EnumWindows(CMPFUNC(enum_windows_callback), 0)

        if found_windows:
            print(f"Found {len(found_windows)} window(s) matching '{app}'. Closing...")
            for hwnd in found_windows:
                # 1. Identify if it's a browser window
                length = windll.user32.GetWindowTextLengthW(hwnd)
                buf = create_unicode_buffer(length + 1)
                windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                
                is_browser = any(b in title for b in ["chrome", "edge", "firefox", "brave", "opera"])
                
                # 2. Decide: Close Window vs Close Tab
                # If it is a browser AND the user did NOT explicitly ask to close the browser itself -> Close Tab
                # e.g. app="youtube", title="youtube - chrome" -> Close Tab
                # e.g. app="chrome", title="youtube - chrome" -> Close Window
                if is_browser and "chrome" not in app and "edge" not in app and "firefox" not in app and "browser" not in app:
                    print(f"Closing browser tab for: {title}")
                    try:
                        windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
                        windll.user32.SetForegroundWindow(hwnd)
                        time.sleep(0.5) # Wait for focus
                        keyboard.press_and_release("ctrl+w")
                    except Exception as e:
                        print(f"Failed to close tab: {e}")
                else:
                    # Generic Safe Close (simulates 'X' button)
                    print(f"Closing window: {title}")
                    windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            return True
        else:
            print(f"No running window found for '{app}'.")

    except Exception as e:
        print(f"Error in window closing logic: {e}")

    # Fallback: Force Kill (Last Resort) - ONLY for non-critical apps
    try:
        critical_processes = ["explorer", "winlogon", "services", "csrss", "lsass", "smss", "svchost", "dwm", "chrome", "firefox", "msedge", "lockapp", "searchui", "python", "py"]
        
        if app in critical_processes:
            print(f"Safety Protocol: Execution blocked. Cannot force kill critical/protected process '{app}'.")
            return False
        
        if app.endswith(".exe"):
             subprocess.run(f"taskkill /f /im {app}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
             return True

        return False
    except:
        return False 

def ExecuteCommand(command):
    """
    Executes system-level commands using keyboard shortcuts.
    Supports: Volume controls, Mute, Shutdown, Restart, Lock, Brightness.
    """
    
    # Nested functions for specific actions
    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")
    
    def increase_volume():
        # Press multiple times for noticeable change
        for _ in range(5):
            keyboard.press_and_release("volume up")
    
    def decrease_volume():
        for _ in range(5):
            keyboard.press_and_release("volume down")
    
    def turn_off():
        # Sleep/Hibernate command
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    
    def turn_on():
        pass # Not applicable for software command

    def lock():
        # Lock workstation
        ctypes.windll.user32.LockWorkStation()

    def shutdown():
        os.system("shutdown /s /t 0")

    def restart():
        os.system("shutdown /r /t 0")

    def adjust_brightness(change):
        """Adjusts screen brightness using PowerShell/WMI."""
        try:
            # Get current brightness
            cmd_get = 'powershell -Command "(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightness).CurrentBrightness"'
            result = subprocess.run(cmd_get, capture_output=True, text=True, shell=True)
            if not result.stdout.strip():
                print("Could not retrieve current brightness.")
                return
            
            try:
                current_brightness = int(result.stdout.strip())
            except ValueError:
                print("Invalid brightness value returned.")
                return

            # Calculate new brightness (clamped between 0 and 100)
            new_brightness = max(0, min(100, current_brightness + change))
            
            # Set new brightness
            cmd_set = f'powershell -Command "(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {new_brightness})"'
            subprocess.run(cmd_set, shell=True)
            print(f"Brightness set to {new_brightness}%")
            
        except Exception as e:
            print(f"Error adjusting brightness: {e}")

    # Command Router
    if "mute" in command:
        mute()
    elif "unmute" in command:
        unmute()
    elif "increase volume" in command or "volume up" in command:
        increase_volume()
    elif "decrease volume" in command or "volume down" in command:
        decrease_volume()
    elif "increase brightness" in command or "brightness up" in command:
        adjust_brightness(10)
    elif "decrease brightness" in command or "brightness down" in command:
        adjust_brightness(-10)
    elif "turn off" in command or "sleep" in command:
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
        command = command.lower() # Normalize command to lowercase
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

        # New: Direct handling for system commands without "system" prefix
        elif any(k in command for k in ["volume", "brightness", "mute", "unmute", "lock", "shutdown", "restart", "turn off", "sleep"]):
             fun = asyncio.to_thread(ExecuteCommand, command)
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
    async def main():
        print("Automation Script Started. Type 'exit' to quit.")
        while True:
            try:
                # Use to_thread to prevent input() from blocking the event loop entirely
                command = await asyncio.to_thread(input, "Enter command: ")
                
                if not command:
                    continue
                    
                if command.lower() in ["exit", "quit"]:
                    print("Exiting...")
                    break

                await Automation([command])
                
            except KeyboardInterrupt:
                print("\nStopping...")
                break
            except Exception as e:
                print(f"Error executing command: {e}")

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal Error: {e}")
