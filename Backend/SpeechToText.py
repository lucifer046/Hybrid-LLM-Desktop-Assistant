# ===========================================================================================================
#                                         SpeechToText.py
# ===========================================================================================================
# This module implements a robust, free Speech Recognition system using the Web Speech API.
#
# How it works:
# 1. Creates a local HTML file containing JavaScript for the Web Speech API (supported by Chrome).
# 2. Uses Selenium to open this HTML file in a HEADLESS Chrome browser.
# 3. Reads the recognized text from the DOM in real-time.
# 4. Supports auto-translation via `mtranslate` if the input isn't English.
#
# Why this approach?
# - It's free (unlike Google Cloud STT).
# - It's more accurate than offline libraries like `SpeechRecognition` (CMU Sphinx).
# - It supports many languages out of the box.

from dotenv import dotenv_values # Import dotenv_values to load environment variables.
from selenium import webdriver # Import webdriver to control the browser.
from selenium.webdriver.common.by import By # Import By to locate elements in the DOM.
from selenium.webdriver.chrome.options import Options # Import Options to configure Chrome settings.
from selenium.webdriver.support.ui import WebDriverWait # Import WebDriverWait to wait for elements.
from selenium.webdriver.support import expected_conditions as EC # Import expected_conditions to check element states.
from rich.console import Console # Import Console for rich terminal output.
import os # Import os for file path operations.   
import mtranslate as mt # Import mtranslate for language translation.
import time # Import time for delays.

# -------------------------------------------------------------------------------------------------------
#                                         Configuration
# -------------------------------------------------------------------------------------------------------

# Console for rich terminal output
console = Console()

# Load environment variables
env_vars = dotenv_values(".env")

# Get the input language settings (e.g., 'en-US', 'hi-IN')
input_language = env_vars.get("INPUT_LANGUAGE")

# -------------------------------------------------------------------------------------------------------
#                                         Web Speech API Setup
# -------------------------------------------------------------------------------------------------------

# Define the HTML/JS that runs inside the hidden browser.
html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;
            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };

            recognition.start();
        }
        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
        
    </script>
</body>
</html>'''

# Inject the user's preferred language into the JS code
html_code = str(html_code).replace("recognition.lang = '';", f"recognition.lang = '{input_language}';")

# Save detailed HTML file to disk
with open("Data/Voice.html", "w") as f:
    f.write(html_code) 

# Construct the file URL for Selenium
current_dir = os.getcwd()
file_url = f"file:///{current_dir}/Data/Voice.html"  

# -------------------------------------------------------------------------------------------------------
#                                         Selenium Driver Setup
# -------------------------------------------------------------------------------------------------------

# Set Chrome Options to allow microphone access without UI
chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3" 
chrome_options.add_argument("--headless=new") # Run in background
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument("--use-fake-ui-for-media-stream") # Auto-allow mic permission
chrome_options.add_argument("--use-fake-device-for-media-stream")

# Initialize the webdriver
# NOTE: You must have the correct ChromeDriver installed for your Chrome version
driver = webdriver.Chrome(options=chrome_options)

# Define path for status communication with GUI
temp_dir_path = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(temp_dir_path, exist_ok=True)

# -------------------------------------------------------------------------------------------------------
#                                         Helper Functions
# -------------------------------------------------------------------------------------------------------

def SetAssistantStatus(status):
    """Updates the status file so the GUI can show 'Listening...' or errors."""
    with open(rf"{temp_dir_path}/status.data", "w", encoding="utf-8") as f:
        f.write(status)

def QueryModifier(query):
    """
    Format the raw speech text:
    - Lowercase start.
    - Add question marks to questions.
    - Add periods to statements.
    - Capitalize the first letter.
    """
    new_query = query.lower().strip()
    query_words = new_query.split()
    question_words = [
        "what", "where", "when", "why", "how", "who", "which", "whom", "whose", "whatsoever", "wherever", 
        "whenever", "whichever", "whichever", "whichever", "can you", "what's", "where's", "when's", "why's", "how's", 
        "who's", "which's", "whom's", "whose's", "whatsoever's", "wherever's", "whenever's", "whichever's", "whichever's"
    ]

    # Check if the query is empty.
    if not query_words: return ""
    
    # Check if the query is a question and add question mark if necessary.
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query += "?"
        else:
            new_query += "?"
    else:
        # Add a period if the query is not a question.
        if query_words[-1][-1] in ['.','?', '!']:
            new_query += "."
        else:
            new_query += "."
    return new_query.capitalize()

def UniversalTranslator(query):
    """
    Translates non-English input to English using mtranslate.
    This allows the logic in Main.py to always work with English commands.
    """
    english_query = mt.translate(query, "en", "auto")
    return english_query.capitalize()

# -------------------------------------------------------------------------------------------------------
#                                         Main Logic
# -------------------------------------------------------------------------------------------------------

def SpeechRecognition():
    """
    The main blocking function that waits for speech.
    
    Flow:
    1. Opens the HTML file in Selenium.
    2. Clicks 'Start Recognition'.
    3. Loops and checks the 'output' P-tag for text.
    4. If text is found, stops recognition, formats/translates it, and returns provided string.
    """
    # Open the file in the hidden browser
    driver.get(file_url)
    
    # Start speech recognition by clicking the start button via JS
    start_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "start")))
    start_btn.click()
    
    while True:
        try:
            # Polling mechanism: Get text from the HTML output element
            Text = driver.find_element(By.ID, "output").text

            if Text:
                # Stop speech recognition
                driver.find_element(By.ID, "end").click()
                
                # Always translate to English
                SetAssistantStatus("Translating...")
                return QueryModifier(UniversalTranslator(Text))
            
            time.sleep(0.2) # Prevent CPU spiking

        except Exception as e:
            print(f"Error: {e}")
            SetAssistantStatus("Error: " + str(e))
            return None

# -------------------------------------------------------------------------------------------------------
#                                         Main Execution (Test Node)
# -------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    while True:
        try:
            print("Listening...")
            query = SpeechRecognition()
            print(f"Recognized: {query}")
        except KeyboardInterrupt:
            console.print("\n[bold red]Forced Exit.[/bold red]")
            break
