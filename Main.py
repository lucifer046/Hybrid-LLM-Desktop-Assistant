# ===========================================================================================================
#                                         Main.py (Application Orchestrator)
# ===========================================================================================================
# This is the central hub of the AI Assistant. It manages:
# 1. Initialization of the GUI and Status files.
# 2. Multithreading: One thread for the GUI, another for the core Logic.
# 3. Decision Making: Routes user queries to the correct backend (Automation, Search, Chat, etc.).
# 4. Inter-process Communication: Uses shared files in 'Frontend/Files' + Subprocesses for image gen.

# -------------------------------------------------------------------------------------------------------
#                                         Imports & Dependencies
# -------------------------------------------------------------------------------------------------------

# Frontend Control Functions (Imported from GUI.py for status management)
from Frontend.GUI import (
    GraphicalUserInterface, # The main PyQT5 GUI loop
    SetAssistantStatus,     # Sets status in 'Status.data' (e.g., "Thinking...", "Listening...")
    ShowTextToScreen,       # Writes text to 'Responses.data' for GUI to display
    TempDirectoryPath,      # Helper to get paths in 'Frontend/Files'
    SetMicrophoneStatus,    # Controls 'Mic.data' (True=On, False=Off)
    AnswerModifier,         # Formats answers for display
    QueryModifier,          # Formats queries (capitalization, punctuation)
    GetMicrophoneStatus,    # Reads 'Mic.data' to see if User clicked Mic button
    GetAssistantStatus,     # Reads current AI status
)

# Backend Modules (The "Brain" and "Tools" of the AI)
# from Backend.Cohere_Model import FirstLayerDMM          # Decision Making: Classifies query (General, Realtime, Automation, etc.)
# from Backend.Gemini_Model import FirstLayerDMM          # Decision Making: Classifies query (General, Realtime, Automation, etc.)
from Backend.brain_model import FirstLayerDMM          # Decision Making: Classifies query (General, Realtime, Automation, etc.)
# There are 3 models for decision making, choose one and comment the rest. I have chosen brain_model as it is completely loclly hosted and does not require any api key.

from Backend.RealTimeSearchEngine import RealTimeSearchEngine # DuckDuckGo Search integration
from Backend.Automation import Automation               # OS Automation (Opening apps, etc.)
from Backend.SpeechToText import SpeechRecognition      # STT (Google/Selenium based)
from Backend.Chatbot import Chatbot                     # Conversational AI (LLM Wrapper)
from Backend.TextToSpeech import TTS as TextToSpeech    # TTS (EdgeTTS)

# Standard Libraries
from dotenv import dotenv_values # Security: Loads API keys
from asyncio import run          # Async support for automation tasks
from time import sleep           # Delays for loops
import subprocess                # To launch external scripts (ImageGeneration)
import threading                 # For multitasking (GUI + Logic running at once)
import json                      # JSON handling for chat logs
import os                        # Filesystem operations

# -------------------------------------------------------------------------------------------------------
#                                         Initialization
# -------------------------------------------------------------------------------------------------------

# Load Configuration
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("AssistantName", "Assistant")

# Default conversation starter if history is empty
DefaultMessage = f"""{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well. How may I help you?"""

# Keyword list for automation decisions
functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

# Track subprocesses (like Image Generation)
subprocess_list = []

# -------------------------------------------------------------------------------------------------------
#                                         Helper Functions
# -------------------------------------------------------------------------------------------------------

def ShowDefaultChatIfNoChats():
    """
    Checks if 'ChatLog.json' exists. If not (or empty), creates it with default values.
    Also ensures the 'Data' directory exists.
    """
    try:
        with open(r'Data\ChatLog.json', "r", encoding='utf-8') as file:
            content = file.read()
            if len(content) < 5:
                pass 
    except FileNotFoundError:
        print("ChatLog.json file not found. Creating default response.")
        os.makedirs("Data", exist_ok=True)
        with open(r'Data\ChatLog.json', "w", encoding='utf-8') as file:
            file.write("[]")
        
        # Write default welcome message to GUI response file
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
            response_file.write(DefaultMessage)

def ReadChatLogJson():
    """Reads the chat history from JSON file."""
    try:
        with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except (FileNotFoundError, json.JSONDecodeError):
        print("ChatLog.json not found or invalid. Returning empty list.")
        return []

def ChatLogIntegration():
    """
    Reads the JSON chat log and reformats it into a plain text format.
    The formatted text is saved to 'Database.data' for the LLM context or GUI display.
    """
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    
    # Parse JSON if it's a string, or use directly if it's a list (logic depends on ReadChatLogJson return)
    # Assuming ReadChatLogJson returns a string, we load it here:
    try:
        entries = json.loads(json_data) if isinstance(json_data, str) else json_data
    except:
        entries = []

    for entry in entries:
        if entry["role"] == "user":
            formatted_chatlog += f"{Username}: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"{Assistantname}: {entry['content']}\n"

    # Ensure Temp directory exists
    temp_dir_path = TempDirectoryPath('') 
    if not os.path.exists(temp_dir_path):
        os.makedirs(temp_dir_path)

    # Write processed log
    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatOnGUI():
    """
    Reads the formatted chat log from 'Database.data' and pushes it to 'Responses.data'.
    The GUI periodically reads 'Responses.data' to update the visual chat history.
    """
    try:
        with open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8') as file:
            data = file.read()
        if len(str(data)) > 0:
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as response_file:
                response_file.write(data)
    except FileNotFoundError:
        print("Database.data file not found.")

def InitialExecution():
    """Boot sequence: Resets Status, checks logs, and pre-loads history to GUI."""
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatOnGUI()

# -------------------------------------------------------------------------------------------------------
#                                         Main Logic Loop
# -------------------------------------------------------------------------------------------------------

def MainExecution():
    """
    The CORE LOGIC of the Assistant.
    Steps:
    1. Listen for Audio (SpeechToText).
    2. Display User Query.
    3. Analyze Intent (FirstLayerDMM).
    4. Execute Task (Automation, Image Gen, Search, or Chat).
    5. Speak Response (TextToSpeech).
    """
    try:
        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""

        # 1. INPUT PHASE
        SetAssistantStatus("Listening...")
        Query = SpeechRecognition() # Blocks until speech is detected
        ShowTextToScreen(f"{Username}: {Query}") # Show user query on GUI immediately
        
        SetAssistantStatus("Thinking...")
        
        # 2. DECISION PHASE
        # FirstLayerDMM returns a list of classifications, e.g., ["general", "play music"]
        Decision = FirstLayerDMM(Query) 
        print(f"\nDecision: {Decision}\n")

        # Parse classifications
        G = any([i for i in Decision if i.startswith("general")])   # General chat?
        R = any([i for i in Decision if i.startswith("realtime")])  # Needs live internet info?

        # Combine queries if multiple parts exist
        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        # check for Image Generation trigggers
        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True

        # 3. AUTOMATION EXECUTION
        # If the query matches automation keywords ("open", "play", etc.)
        for queries in Decision:
            if not TaskExecution:
                if any(queries.startswith(func) for func in functions):
                    # Call Automation Module (Async)
                    run(Automation(list(Decision)))
                    TaskExecution = True

        # 4. IMAGE GENERATION EXECUTION
        # If image gen was triggered, we spawn an external python process to handle it
        if ImageExecution:
            with open(r'Frontend\Files\ImageGeneration.data', "w") as file:
                file.write(f"{ImageGenerationQuery},True") # Signal the script to start

            try:
                # Launch ImageGeneration.py independently
                p1 = subprocess.Popen(
                    ['python', r"Backend\ImageGeneration.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False,
                )
                subprocess_list.append(p1)
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        # 5. RESPONSE GENERATION (Web vs General vs Exit)
        
        if G and R or R:
            # Case: Needs Realtime Info
            SetAssistantStatus("Searching...")
            # Use DuckDuckGo Search + LLM
            Answer = RealTimeSearchEngine(QueryModifier(Merged_query))
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return True
            
        else:
            # Case: General Chat or Command
            for queries in Decision:
                if "general" in queries:
                    # General Chatbot Conversation
                    SetAssistantStatus("Thinking...")
                    QueryFinal = queries.replace("general", "")
                    Answer = Chatbot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                    
                elif "realtime" in queries:
                    # (Redundant with G and R block but handles specific edge cases)
                    SetAssistantStatus("Searching...")
                    QueryFinal = queries.replace("realtime", "")
                    Answer = RealTimeSearchEngine(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    return True
                    
                elif "exit" in queries:
                    # Exit Command
                    QueryFinal = "Okay, Bye!"
                    Answer = Chatbot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname}: {Answer}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(Answer)
                    os._exit(1) # Kill the entire process
                    
    except Exception as e:
        print(f"Error in MainExecution: {e}")

# -------------------------------------------------------------------------------------------------------
#                                         Thread Management
# -------------------------------------------------------------------------------------------------------

def FirstThread():
    """
    Background Thread: Monitors the Microphone Status file ('Mic.data').
    - If 'True': The user clicked the mic button -> Trigger MainExecution.
    - If 'False': Updates status to 'Available...'.
    """
    while True:
        try:
            CurrentStatus = GetMicrophoneStatus()

            if CurrentStatus.lower() == "true":
                print("Executing MainExecution")
                MainExecution()
            elif CurrentStatus.lower() == "false":
                AIStatus = GetAssistantStatus()
                if "Available..." in AIStatus:
                    sleep(0.1)
                else:
                    SetAssistantStatus("Available...")
            else:
                pass 
        except Exception as e:
            print(f"Error in FirstThread: {e}")
            sleep(1)

def SecondThread():
    """
    Main Thread: Runs the PyQt5 GUI.
    This is blocking, which is why Logic runs in a separate thread.
    """
    try:
        GraphicalUserInterface()
    except Exception as e:
        print(f"Error in SecondThread: {e}")

# -------------------------------------------------------------------------------------------------------
#                                         Entry Point
# -------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # 1. Run Setup
    InitialExecution()
   
    # 2. Start Logic Thread (Daemon=True so it dies when GUI closes)
    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    
    # 3. Start GUI (Main Thread)
    SecondThread()
