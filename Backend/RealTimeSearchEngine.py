# ===========================================================================================================
#                                         RealTimeSearchEngine.py
# ===========================================================================================================
# This module combines the Power of the Local LLM with Real-Time Internet Data.
# When the DMM classifies a query as "Realtime" (e.g., "News", "System Specs"), this module is triggered.
#
# Workflow:
# 1. GoogleSearch: Uses DuckDuckGo (via `ddgs` library) to fetch top web results.
# 2. Prompt Injection: Injects these results into the LLM's system prompt context.
# 3. LLM Response: The Local LLM synthesizes the search results into a coherent natural language answer.

import os
import datetime
import json
import shutil
from json import load, dump
from dotenv import dotenv_values
from rich.console import Console
from openai import OpenAI
from ddgs import DDGS  # Library for DuckDuckGo Search

# -------------------------------------------------------------------------------------------------------
#                                         Configuration
# -------------------------------------------------------------------------------------------------------

# Console for rich terminal output
console = Console()

# Load environment variables
evn_vars = dotenv_values(".env")

# Retrieve user configuration
username = evn_vars.get("Username")
assistant_name = evn_vars.get("AssistantName")
language = evn_vars.get("Language")

# Initialize OpenAI client for local LM Studio server
client = OpenAI(
    base_url="http://localhost:1234/v1", 
    api_key="lm-studio"
)

# Paths for data storage
DB_FILE = r"Data\conversation.json"
BACKUP_FILE = r"Data\conversation_backup.json"

# -------------------------------------------------------------------------------------------------------
#                                         Search Logic
# -------------------------------------------------------------------------------------------------------

def GoogleSearch(query):
    """
    Performs a real-time web search using the DuckDuckGo API.
    
    Why:
    - LLMs have a "knowledge cutoff" and don't know recent events (like today's news).
    - We search the web to get raw text snippets about the user's query.
    - These snippets are then fed to the LLM to summarize.
    
    Args:
        query (str): The user's search term (e.g., "price of bitcoin").
        
    Returns:
        str: A structured string of search results (Title + Description + Link), or None.
    """
    try:
        # Perform search using ddgs library, limiting to top 5 results to save tokens.
        results = DDGS().text(query, max_results=5)
        
        if not results:
            return None

        # Format results into a single string for the Prompt.
        # We use [start] and [end] tags to help the LLM distinguish search data from instructions.
        Answer = f"The search results for '{query}' are:\n[start]\n"
        for i in results:
            Answer += f"Title: {i['title']}\nDescription: {i['body']}\nLink: {i['href']}\n\n"
        Answer += "[end]"
        return Answer
        
    except Exception as e:
        console.print(f"[dim red]Search skipped due to error: {e}[/dim red]")
        return None

# -------------------------------------------------------------------------------------------------------
#                                         Helper Functions
# -------------------------------------------------------------------------------------------------------

def AnswerModifier(Answer):
    """
    Removes empty lines from the response to save tokens and improve formatting.
    """
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def load_memory():
    """
    Loads conversation history from the primary JSON file.
    Falls back to the backup file if needed.
    """
    # Ensure the Data directory exists
    if not os.path.exists("Data"):
        os.makedirs("Data")
    try:
        # Try loading from the primary file
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to backup if primary fails
        try:
            with open(BACKUP_FILE, "r") as f:
                data = json.load(f)
            console.print("[yellow]⚠ Main memory corrupted. Loaded from Backup.[/yellow]")
            return data
        except:
            return []

def save_memory(memory_list):
    """
    Saves the conversation history to the JSON file safely.
    """
    try:
        # Write to backup file first
        with open(BACKUP_FILE, "w") as f:
            json.dump(memory_list, f, indent=4)
        
        # Copy backup to primary file
        shutil.copy(BACKUP_FILE, DB_FILE)
        return True
    except Exception as e:
        console.print(f"[red]Save Failed: {e}[/red]")
        return False

# Initialize memory stores
permanent_memory = load_memory()
session_memory = []  # Stores messages for the current session only

# System prompt definition
# Specific instruction to use "Search Results" if provided.
system_message = f"""Hello, I am {username}. You are a very accurate and advanced AI chatbot named {assistant_name}.
*** ROLE ***
You may receive "Search Results" along with the user's query. Use these results to provide accurate, up-to-date answers.
*** GUIDELINES ***
1. **Time:** Do not tell time unless asked.
2. **Language:** Reply ONLY in {language}. Translate if necessary.
3. **Tone:** Respectful, professional, and polite. (Use 'Aap/Apne' in Hindi).
4. **No Notes:** Do not mention your training data or internal tools.
"""

def RealTimeInformation():
    """Returns current date strings for context."""
    current_date_time = datetime.datetime.now()
    data = f"Current Time: {current_date_time.strftime('%I:%M %p')}\n"
    data += f"Day: {current_date_time.strftime('%A')}, Date: {current_date_time.strftime('%d %B %Y')}"
    return data

# -------------------------------------------------------------------------------------------------------
#                                         Main Logic
# -------------------------------------------------------------------------------------------------------

def RealTimeSearchEngine(query):
    """
    Manages the chat interaction loop with real-time search integration.
    
    Logic:
    1. Search the web for the query.
    2. Prompt Engineering: Combine Search Results + User Query.
    3. Call Local LLM to synthesize answer.
    4. Update Memory.
    
    Args:
        query (str): The user's input message.
    """
    global permanent_memory, session_memory

    try:
        # 1. Perform Web Search
        console.print(f"[dim cyan]Searching web for: {query}...[/dim cyan]")
        search_context = GoogleSearch(query)
        
        # 2. Build Prompt with Search Context
        # If search found data, inject it into the prompt structure.
        if search_context:
            prompt_content = f"""
            [Context from Web Search]
            {search_context}

            [User Query]
            {query}
            """
        else:
            prompt_content = query

        # 3. Construct API Messages
        # Start with system message and current time
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

        # Add the current user query (with injected search context)
        api_messages.append({"role": "user", "content": prompt_content})

        # 4. Call the API (Streaming Mode)
        stream = client.chat.completions.create(
            model="local-model", 
            messages=api_messages,
            temperature=0.7,
            stream=True,
        )

        response_text = ""
        console.print("")  # Add spacing before output

        # 5. Stream and Display Response
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                console.print(content, end="")  # Print in real-time
                response_text += content

        console.print("\n")

        # 6. Post-process Response
        response_text = AnswerModifier(response_text)

        # 7. Update Session Memory
        # IMPORTANT: We save the ORIGINAL `query` to memory, NOT the huge prompt with search results.
        # This keeps the context clean for future turns.
        session_memory.append({"role": "user", "content": query})
        session_memory.append({"role": "assistant", "content": response_text})

        # 8. Check for Save Triggers
        triggers = ["store this", "remember this", "save this", "memorize this", "note this"]
        
        if any(trigger in query.lower() for trigger in triggers):
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
    console.print(f"[green]System Ready ({assistant_name}). Local + Web Search Active.[/green]")
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
            RealTimeSearchEngine(user_query)

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            console.print("\n[bold red]Forced Exit.[/bold red]")
            break