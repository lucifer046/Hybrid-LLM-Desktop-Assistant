from google import genai
from google.genai import types
import time
from rich import print
from dotenv import dotenv_values

# Load environment variables from the .env file
env_vars = dotenv_values(".env")
GeminiAPIKey = env_vars.get("GeminiAPIKey")
gemini_model = env_vars.get("GeminiModel")

# Configure the Gemini API with the retrieved key
client = genai.Client(api_key=GeminiAPIKey)

# List of valid function keywords for classification
# These keywords match the categories defined in the system instructions
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search", 
    "youtube search", "reminder"
]

# System instructions for the Gemini model
# Defines the persona, rules, and categories for query classification
sys_instruction = """
You are a fast and accurate Decision-Making Model. Classify the user's query into one or more of the following categories.
*** Output ONLY the category and content. Do not engage in conversation. ***

CRITICAL RULE (VERBATIM CONTENT): 
When outputting the content part, you MUST preserve the user's EXACT phrasing, punctuation (?!.), and casing.
- Input: "Hello!!" -> Output: "general Hello!!" (NOT "general Hello")
- Input: "what??" -> Output: "general what??" (NOT "general what")

CATEGORIES:
1. 'general (query)': Chat, static knowledge, or ambiguous questions.
2. 'realtime (query)': News, weather, stock prices, live scores.
3. 'open (app_name)': Launching apps.
4. 'close (app_name)': Closing apps.
5. 'play (media_name)': Playing music/video.
6. 'generate image (prompt)': Creating images.
7. 'reminder (time/date message)': Setting reminders.
8. 'system (command)': Device control.
9. 'content (topic)': Writing code/emails.
10. 'google search (query)': Explicit search.
11. 'youtube search (query)': Explicit YouTube search.
12. 'exit': User says goodbye.

If multiple actions, separate with commas.
"""

# Few-shot learning examples to guide the model's behavior
# Includes examples for punctuation, ambiguity, multi-tasking, and edge cases
ChatHistory = [
    # 1. PUNCTUATION & EXACTNESS TRAINING (The Fix)
    {"role": "user", "parts": [{"text": "whats going on sir?"}]}, 
    {"role": "model", "parts": [{"text": "general whats going on sir?"}]}, 
    {"role": "user", "parts": [{"text": "Hello!!"}]}, 
    {"role": "model", "parts": [{"text": "general Hello!!"}]}, 
    {"role": "user", "parts": [{"text": "REALLY???"}]}, 
    {"role": "model", "parts": [{"text": "general REALLY???"}]},

    # 2. REALTIME & AMBIGUITY
    {"role": "user", "parts": [{"text": "who is he?"}]}, 
    {"role": "model", "parts": [{"text": "general who is he?"}]}, 
    {"role": "user", "parts": [{"text": "who is the president of usa?"}]}, 
    {"role": "model", "parts": [{"text": "realtime who is the president of usa?"}]}, 

    # 3. MULTI-TASKING
    {"role": "user", "parts": [{"text": "open spotify and play starboy."}]}, 
    {"role": "model", "parts": [{"text": "open spotify, play starboy"}]}, 

    # 4. EDGE CASES
    {"role": "user", "parts": [{"text": "search for cute cats on youtube."}]}, 
    {"role": "model", "parts": [{"text": "youtube search cute cats"}]}, 
    
    # 5. EXIT
    {"role": "user", "parts": [{"text": "bye jarvis."}]}, 
    {"role": "model", "parts": [{"text": "exit"}]}
]

def FirstLayerDMM(prompt: str = "test", retries: int = 0):
    """
    Classifies the user's query into specific categories using the Gemini model.
    
    Args:
        prompt (str): The user's input query.
        retries (int): Current retry count for the recursive call.

    Returns:
        list: A list of classified tasks/actions.
    """
    try:
        # Start a chat session with the pre-defined history
        # Using the new google-genai SDK format
        chat = client.chats.create(
            model=gemini_model,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=60,
                response_mime_type="text/plain",
                system_instruction=sys_instruction
            ),
            history=ChatHistory
        )

        # Send the user's prompt to the model
        response_obj = chat.send_message(prompt)
        response_text = response_obj.text

        # Clean up the response: remove newlines and split by comma
        response_text = response_text.replace("\n", "")
        response_list = response_text.split(",")
        response_list = [i.strip() for i in response_list]

        # Filter the response to ensure it contains valid function keywords
        temp = []
        for task in response_list:
            for func in funcs:
                if task.startswith(func):
                    temp.append(task)

        # Retry logic: If no valid tasks are found, retry up to 2 times
        # Fallback to 'general' category if retries fail
        if len(temp) == 0:
            if retries < 2:
                 return FirstLayerDMM(prompt=prompt, retries=retries + 1)
            else:
                 return ["general " + prompt]
        else:
            return temp

    except Exception as e:
        print(f"[bold red]Error in FirstLayerDMM:[/bold red] {e}")
        # Return a safe default in case of error
        return ["general " + prompt]

if __name__ == "__main__":
    # Main loop for testing the classification logic interactively
    while True:
        try:
            # Get user input
            user_query = input("User: ")
            
            # Skip empty inputs
            if not user_query.strip():
                continue

            # Check for exit commands
            if user_query.lower() in ["exit", "quit", "bye"]:
                print("[yellow]Goodbye![/yellow]")
                break

            # Measure execution time for performance monitoring
            start_time = time.time()
            result = FirstLayerDMM(user_query) 
            end_time = time.time()

            # Display the result and execution time
            print(result)
            print(f"[bold black] Debug [/bold black] [dim]Time: {end_time - start_time:.4f}s[/dim]")

        except KeyboardInterrupt:
            # Handle manual interruption (Ctrl+C)
            print("\n[bold red]Forced Exit (Ctrl+C) detected. Shutting down...[/bold red]")
            break
            
        except EOFError:
            # Handle end of file (Ctrl+D)
            print("\n[bold red]Exiting...[/bold red]")
            break
            
        except Exception as e:
            # Catch-all for unexpected errors to prevent crash
            print(f"[bold red]An error occurred:[/bold red] {e}")
            break