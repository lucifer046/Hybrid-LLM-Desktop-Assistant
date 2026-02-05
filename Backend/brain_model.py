# ===========================================================================================================
#                                         brain_model.py (Decision Making Model)
# ===========================================================================================================
# This module acts as the "Cerebral Cortex" of the AI.
# It uses a Local LLM (via LM Studio) to classify User Queries into specific categories (Intents).
#
# Intent Categories:
# - General: Conversational, Knowledge, Math (No internet needed).
# - Realtime: News, Weather, Stock Prices (Needs internet).
# - Open/Close: App management.
# - Play: Media playback.
# - Generate Image: Visual content creation.
# - System: Hardware control.
# - Content: Writing tasks.
# - Search: Explicit Google/YouTube searches.
# - Reminder: Setting scheduling alerts.

from openai import OpenAI # Import OpenAI library to interact with the LLM API.
from dotenv import dotenv_values # Import dotenv_values to load environment variables.
import time # Import time module to measure processing time or add delays.
from rich import print # Import rich's print function for colorful terminal output. 

# -------------------------------------------------------------------------------------------------------
#                                         Configuration
# -------------------------------------------------------------------------------------------------------

# Initialize Local LLM Client (LM Studio)
# Pointing to local server instead of Cohere or OpenAI's official API.
client = OpenAI(
    base_url="http://localhost:1234/v1", # Local server URL. 
    api_key="lm-studio", # Placeholder API key. 
)

# List of valid Command Keywords for parsing the output. 
# These keywords start the response string, helping the script identify the intent.
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search", 
    "youtube search", "reminder"
]

# -------------------------------------------------------------------------------------------------------
#                                         System Preamble & Few-Shot Examples
# -------------------------------------------------------------------------------------------------------

# The Preamble is the "System Prompt" for the DMM. 
# It strictly instructs the model to OUTPUT ONLY COMMANDS, not answers.
# The Preamble is the "System Prompt" for the DMM. 
# It strictly instructs the model to OUTPUT ONLY COMMANDS, not answers.
preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
*** IMPORTANT: NEVER ANSWER THE USER'S QUESTION. NEVER GENERATE ADVICE OR EXPLANATIONS. ***
*** YOUR ONLY JOB IS TO CLASSIFY THE QUERY AND REPEAT IT. ***

-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require any up to date information like if the query is 'who was akbar?' respond with 'general who was akbar?', if the query is 'how can i study more effectively?' respond with 'general how can i study more effectively?', if the query is 'can you help me with this math problem?' respond with 'general can you help me with this math problem?', if the query is 'Thanks, i really liked it.' respond with 'general thanks, i really liked it.' , if the query is 'what is python programming language?' respond with 'general what is python programming language?', etc. Respond with 'general (query)' if a query doesn't have a proper noun or is incomplete like if the query is 'who is he?' respond with 'general who is he?', if the query is 'what's his networth?' respond with 'general what's his networth?', if the query is 'tell me more about him.' respond with 'general tell me more about him.', and so on even if it require up-to-date information to answer. Respond with 'general (query)' if the query is asking about time, day, date, month, year, etc like if the query is 'what's the time?' respond with 'general what's the time?'.
-> Respond with 'realtime ( query )' if a query can not be answered by a llm model (because they don't have realtime data) and requires up to date information like if the query is 'who is indian prime minister' respond with 'realtime who is indian prime minister', if the query is 'tell me about facebook's recent update.' respond with 'realtime tell me about facebook's recent update.', if the query is 'tell me news about coronavirus.' respond with 'realtime tell me news about coronavirus.', etc and if the query is asking about any individual or thing like if the query is 'who is akshay kumar' respond with 'realtime who is akshay kumar', if the query is 'what is today's news?' respond with 'realtime what is today's news?', if the query is 'what is today's headline?' respond with 'realtime what is today's headline?', etc.
-> Respond with 'open (application name or website name)' if a query is asking to open any application like 'open facebook', 'open telegram', etc. but if the query is asking to open multiple applications, respond with 'open 1st application name, open 2nd application name' and so on.

*** SUPER CRITICAL for 'open' commands: ALWAYS use the exact Windows system name for apps.
- 'camera' -> 'open camera'
- 'calculator' -> 'open calculator'
- 'file explorer' or 'files' -> 'open file explorer'
- 'settings' -> 'open settings'
- 'notepad' -> 'open notepad'
- 'command prompt' or 'terminal' -> 'open cmd' or 'open terminal'
- 'task manager' -> 'open task manager'
- 'brave' -> 'open brave'
- 'chrome' -> 'open google chrome'
- 'edge' -> 'open microsoft edge'
***

-> Respond with 'close (application name)' if a query is asking to close any application like 'close notepad', 'close facebook', etc. but if the query is asking to close multiple applications or websites, respond with 'close 1st application name, close 2nd application name' and so on.
-> Respond with 'play (song name)' if a query is asking to play any song like 'play afsanay by ys', 'play let her go', etc. but if the query is asking to play multiple songs, respond with 'play 1st song name, play 2nd song name' and so on.
-> Respond with 'generate image (image prompt)' if a query is requesting to generate a image with given prompt like 'generate image of a lion', 'generate image of a cat', etc. but if the query is asking to generate multiple images, respond with 'generate image 1st image prompt, generate image 2nd image prompt' and so on.
-> Respond with 'reminder (datetime with message)' if a query is requesting to set a reminder like 'set a reminder at 9:00pm on 25th june for my business meeting.' respond with 'reminder 9:00pm 25th june business meeting'.
-> Respond with 'system (task name)' if a query is asking to control system hardware like 'mute volume', 'volume up', 'volume down', 'brightness up', 'brightness down', 'shutdown', 'restart', 'lock screen', 'turn off'. example: 'system mute', 'system volume up', 'system brightness down'. if asking for multiple system tasks: 'system volume up, system brightness down'.
-> Respond with 'content (topic)' if a query is asking to write any type of content like application, codes, emails or anything else about a specific topic but if the query is asking to write multiple types of content, respond with 'content 1st topic, content 2nd topic' and so on.
-> Respond with 'google search (topic)' if a query is asking to search a specific topic on google but if the query is asking to search multiple topics on google, respond with 'google search 1st topic, google search 2nd topic' and so on.
-> Respond with 'youtube search (topic)' if a query is asking to search a specific topic on youtube but if the query is asking to search a specific topic on youtube, respond with 'youtube search 1st topic, youtube search 2nd topic' and so on.
*** If the query is asking to perform multiple tasks like 'open facebook, telegram and close whatsapp' respond with 'open facebook, open telegram, close whatsapp' ***
*** If the user is saying goodbye or wants to end the conversation like 'bye jarvis.' respond with 'exit'.***
*** Respond with 'general (query)' if you can't decide the kind of query or if a query is asking to perform a task which is not mentioned above. ***
"""

# Few-Shot Learning History: Adapted to OpenAI Format
ChatHistory = [
    {"role": "user", "content": "how are you?"},
    {"role": "assistant", "content": "general how are you?"},
    {"role": "user", "content": "do you like pizza?"},
    {"role": "assistant", "content": "general do you like pizza?"},
    {"role": "user", "content": "open chrome and tell me about mahatma gandhi."},
    {"role": "assistant", "content": "open chrome, general tell me about mahatma gandhi."},
    {"role": "user", "content": "open chrome and firefox."},
    {"role": "assistant", "content": "open chrome, open firefox"},
    {"role": "user", "content": "what is todays date by the way remind me that i have a dancing performance on 5th aug 11:00pm"},
    {"role": "assistant", "content": "general what is today's date, reminder 11:00pm 5 aug dancing performance"},
    {"role": "user", "content": "chat with me."},
    {"role": "assistant", "content": "general chat with me."},
    {"role": "user", "content": "what are your capabilities"},
    {"role": "assistant", "content": "general what are your capabilities"},
    {"role": "user", "content": "who are you"},
    {"role": "assistant", "content": "general who are you"},
    {"role": "user", "content": "increase volume and brightness"},
    {"role": "assistant", "content": "system volume up, system brightness up"},
    {"role": "user", "content": "mute the laptop"},
    {"role": "assistant", "content": "system mute"},
    {"role": "user", "content": "shutdown the system"},
    {"role": "assistant", "content": "system shutdown"},
    {"role": "user", "content": "write an application for sick leave"},
    {"role": "assistant", "content": "content application for sick leave"},
    {"role": "user", "content": "write a python script for sorting"},
    {"role": "assistant", "content": "content write a python script for sorting"}
]

# -------------------------------------------------------------------------------------------------------
#                                         First Layer DMM Logic
# -------------------------------------------------------------------------------------------------------

def FirstLayerDMM(prompt: str = "test", retries: int = 0):
    """
    The main Classification Function.
    1. Sends user query + Preamble + ChatHistory to Local LLM.
    2. Receives a comma-separated list of commands (e.g., "open chrome, general hello").
    3. Parses and validates these commands against the 'funcs' list.
    """
    # Construct the messages list for the API call
    messages = [{"role": "system", "content": preamble}]
    messages.extend(ChatHistory)
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="local-model", # Model name usually ignored by LM Studio, but good to have
            messages=messages,
            temperature=0.7,
            max_tokens=100, # Limit output token count for speed
            stream=False 
        )

        response_text = response.choices[0].message.content

        # Clean up response
        response_text = response_text.replace("\n", "")
        response_list = response_text.split(",")
        response_list = [i.strip() for i in response_list]

        # Filter: Only accept commands starting with known keywords
        temp = []
        for task in response_list:
            for func in funcs:
                if task.startswith(func):
                    temp.append(task)

        clean_response = temp

        # Fallback Logic for empty responses
        if len(clean_response) == 0:
            if retries < 3:
                 print(f"[yellow]Empty response. Retry #{retries + 1}...[/yellow]") 
                 return FirstLayerDMM(prompt=prompt, retries=retries + 1)
            else:
                 # Default to 'general' if DMM fails repeatedly
                 return ["general " + prompt]
        else:
            return clean_response

    except Exception as e:
        print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
        # In case of connection error or other issues, fallback to general
        return ["general " + prompt]

# -------------------------------------------------------------------------------------------------------
#                                         Main Execution (Test Node)
# -------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    print("[green]Jarvis Decision Core Online (Local LLM)[/green]")
    while True:
        user_query = input("User: ")
        
        # Check for local exit
        if user_query.lower() in ["exit", "quit", "bye"]:
            print("Exiting...")
            break

        start_time = time.time() 
        result = FirstLayerDMM(user_query)
        end_time = time.time()
        
        execution_time = end_time - start_time

        print(result)
        print(f"[bold black] Debug [/bold black] [dim]Processing Time: {execution_time:.4f} seconds[/dim]")