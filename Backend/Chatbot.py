# ===========================================================================================================
#                                         Chatbot.py
# ===========================================================================================================
# This module defines the core conversational AI logic.
# It interfaces with the Local LLM (LM Studio) to generating "General" chat responses.
#
# Key Features:
# - Permanent Memory: Saves important user data to JSON files.
# - Session Memory: Remembers context within the current conversation run.
# - System Prompting: Enforces the assistant's persona, language, and behavior.
# - Streaming Responses: Prints output token-by-token for a real-time feel.

import os
import datetime
import json
import shutil
from json import load, dump
from dotenv import dotenv_values
from rich.console import Console
from openai import OpenAI

# -------------------------------------------------------------------------------------------------------
#                                         Configuration
# -------------------------------------------------------------------------------------------------------

# Console for rich terminal output (colored text)
console = Console()

# Load environment variables
evn_vars = dotenv_values(".env")

# Retrieve user configuration
username = evn_vars.get("Username")
assistant_name = evn_vars.get("AssistantName")
language = evn_vars.get("Language")

# Initialize OpenAI client for local LM Studio server
# This points to the local API mimicking OpenAI's structure
client = OpenAI(
    base_url="http://localhost:1234/v1", 
    api_key="lm-studio"
)

# Paths for data storage
DB_FILE = r"Data\conversation.json"
BACKUP_FILE = r"Data\conversation_backup.json"

# -------------------------------------------------------------------------------------------------------
#                                         Helper Functions
# -------------------------------------------------------------------------------------------------------

def AnswerModifier(Answer):
    """
    Removes empty lines from the response to save tokens and improve formatting.
    This ensures the output on the GUI is compact.
    
    Args:
        Answer (str): The raw response string.
        
    Returns:
        str: The cleaned response string.
    """
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def load_memory():
    """
    Loads conversation history from the 'Data/conversation.json' file.
    
    Why this is needed:
    - This allows the chatbot to 'remember' past conversations even after a restart.
    - We use a primary file and a backup file to prevent data loss.
    
    Returns:
        list: A list of message dictionaries (e.g., [{'role': 'user', 'content': 'hi'}]).
    """
    # Ensure the Data directory exists to avoid FileNotFoundError
    if not os.path.exists("Data"):
        os.makedirs("Data")
    
    try:
        # Priority 1: Try loading from the primary conversation file
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Priority 2: Fallback to backup file if primary is missing or corrupted
        try:
            with open(BACKUP_FILE, "r") as f:
                data = json.load(f)
            console.print("[yellow]⚠ Main memory corrupted. Loaded from Backup safely.[/yellow]")
            return data
        except:
            # Fallback 3: Return empty list if no valid memory found (New conversation)
            return []

def save_memory(memory_list):
    """
    Saves the current conversation history to the JSON file.
    
    Safety Strategy (Write-Backup-First):
    1. Write data to 'conversation_backup.json' first.
    2. Then copy it to 'conversation.json'.
    This ensures that if the program crashes *while* writing, we still have a valid file.
    
    Args:
        memory_list (list): The complete history of messages to save.
        
    Returns:
        bool: True if save was successful, False if an error occurred.
    """
    try:
        # Step 1: Write to backup file
        with open(BACKUP_FILE, "w") as f:
            json.dump(memory_list, f, indent=4)
        
        # Step 2: Copy backup to primary file (Atomic-like operation)
        shutil.copy(BACKUP_FILE, DB_FILE)
        return True
    except Exception as e:
        console.print(f"[red]Save Failed: {e}[/red]")
        return False

# -------------------------------------------------------------------------------------------------------
#                                         Memory & Context Setup
# -------------------------------------------------------------------------------------------------------

# Initialize memory stores
permanent_memory = load_memory() # Load long-term history from disk.
session_memory = []  # Stores messages for the *current* run only (RAM). cleared on restart.

# System prompt definition
# This is the "Persona" of the AI. It tells the LLM who it is and how to behave.
system_message = f"""Hello, I am {username}. You are a very accurate and advanced AI chatbot named {assistant_name} which has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply ONLY in {language}. Even if the question is in another language, translate and reply in {language}.***
*** Always be respectful, professional, and polite. ***
*** If replying in Hindi, ALWAYS use formal 'Aap' and 'Apne'. NEVER use 'Tum', 'Tu', or 'Tumne'. ***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

def RealTimeInformation():
    """
    Generates a string containing the current dynamic time and date.
    
    Why:
    - LLMs are static (trained on old data). They don't know "today's date".
    - We inject this string into the System Prompt so the AI knows exactly when it is.
    """
    current_date_time = datetime.datetime.now()
    data = f"Current Time: {current_date_time.strftime('%I:%M %p')}\n"
    data += f"Day: {current_date_time.strftime('%A')}, Date: {current_date_time.strftime('%d %B %Y')}"
    return data

# -------------------------------------------------------------------------------------------------------
#                                         Main Chatbot Logic
# -------------------------------------------------------------------------------------------------------

def Chatbot(query):
    """
    Manages the chat interaction loop.
    
    - Builds context from system instructions, permanent memory, and session history.
    - Sends the query to the local LLM and streams the response.
    - Updates session memory and optionally saves to permanent memory.
    
    Args:
        query (str): The user's input message.
    """
    global permanent_memory, session_memory

    try:
        # 1. Build the API message context
        # Start with the system message and current time
        api_messages = [
            {"role": "system", "content": system_message + "\n\n" + RealTimeInformation()}
        ]

        # Add permanent memory (long-term context)
        if len(permanent_memory) > 0:
            for msg in permanent_memory:
                api_messages.append(msg)

        # Add recent session memory (short-term context, last 6 messages)
        recent_session = session_memory[-6:]
        for msg in recent_session:
            api_messages.append(msg)

        # Add the current user query
        api_messages.append({"role": "user", "content": query})

        # 2. Call the API (Streaming Mode)
        # This sends the prompt to LM Studio
        stream = client.chat.completions.create(
            model="local-model", 
            messages=api_messages,
            temperature=0.7,
            stream=True,
        )

        response_text = ""
        console.print("")  # Add spacing before output

        # 3. Stream and display the response
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                console.print(content, end="")  # Print in real-time
                response_text += content

        console.print("\n")

        # 4. Post-process the response
        # Remove extra newlines to keep memory clean
        response_text = AnswerModifier(response_text)

        # 5. Update Session Memory
        session_memory.append({"role": "user", "content": query})
        session_memory.append({"role": "assistant", "content": response_text})

        # 6. Check for Save Triggers
        # If the user asks to "remember" or "store", save the context to permanent memory
        triggers = ["store this", "remember this", "save this", "memorize this", "note this"]
        
        if any(trigger in query.lower() for trigger in triggers):
            # Add to permanent memory list
            permanent_memory.append({"role": "user", "content": query})
            permanent_memory.append({"role": "assistant", "content": response_text})
            
            # Persist to disk
            if save_memory(permanent_memory):
                console.print(f"[dim green]✔ Securely stored in {assistant_name}'s permanent memory.[/dim green]")
        
        return response_text

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        console.print("[yellow]Ensure LM Studio server is running on port 1234.[/yellow]")
        return ""

# -------------------------------------------------------------------------------------------------------
#                                         Main Execution (Test Node)
# -------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    console.print(f"[green]System Ready (Local). Safe-Memory Active.[/green]")
    console.print(f"[dim]Permanent Memory Items Loaded: {len(permanent_memory)}[/dim]")
    
    # Start the interactive loop
    while True:
        try:
            user_query = input("User: ")
            
            # Skip empty inputs
            if not user_query.strip():
                continue

            # Check for exit commands
            if user_query.lower() in ["exit", "quit", "bye"]:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            # Process the query
            Chatbot(user_query)

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            console.print("\n[bold red]Forced Exit.[/bold red]")
            break