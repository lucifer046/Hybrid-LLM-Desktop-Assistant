from openai import OpenAI 
from rich import print
import time

# Define recognized function keywords
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search", 
    "youtube search", "reminder"
]

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
)

# --- YOUR OPTIMIZED PREAMBLE ---
# Changes: Removed conversational filler. Used strict mapping structure. 
# Explicit instruction on 'General' vs 'Realtime' logic to fit 4B model capabilities.
preamble = """
You are a Decision-Making Model. specific user queries into commands.
Output format: command (query)
Join multiple commands with a comma. Do not explain.

COMMAND RULES:
1. 'general': Static knowledge, math, coding, greetings, time/date, or vague questions (e.g., "who is he?").
2. 'realtime': News, weather, stock prices, or specific famous people/entities (e.g., "Who is Elon Musk?", "news about PVC").
3. 'open' / 'close': Launch or exit apps/websites (e.g., "open chrome").
4. 'play': Play music/media (e.g., "play believer").
5. 'generate image': Image creation requests.
6. 'reminder': Set reminders (Format: reminder [time] [date] [topic]).
7. 'system': Hardware control (volume, mute, brightness).
8. 'content': Content writing requests (emails, code, essays).
9. 'google search' / 'youtube search': Explicit search requests.
10. 'exit': User says goodbye.

EDGE CASES:
- "what is the time?" -> 'general'
- "who is the pm of india?" -> 'realtime'
- "open spotify and play jazz" -> 'open spotify, play jazz'
- If unsure, default to 'general'.
"""

# --- YOUR OPTIMIZED HISTORY ---
# Changes: Reduced to high-impact examples that teach the model the comma separation and the General/Realtime distinction.
ChatHistory = [
    {"role": "user", "content": "hello there"},
    {"role": "assistant", "content": "general hello there"},
    {"role": "user", "content": "who is shah rukh khan?"},
    {"role": "assistant", "content": "realtime who is shah rukh khan?"},
    {"role": "user", "content": "solve 2+2 and open calculator"},
    {"role": "assistant", "content": "general solve 2+2, open calculator"},
    {"role": "user", "content": "remind me to gym at 6pm tomorrow"},
    {"role": "assistant", "content": "reminder 6pm tomorrow gym"},
    {"role": "user", "content": "write a python script for sorting"},
    {"role": "assistant", "content": "content write a python script for sorting"},
    {"role": "user", "content": "bye jarvis"},
    {"role": "assistant", "content": "exit"}
]

def FirstLayerDMM(prompt: str = "test", retries: int = 0):
    if retries > 2:
        return ["general " + prompt] 

    current_messages = [{"role": "system", "content": preamble}]
    current_messages.extend(ChatHistory)
    current_messages.append({"role": "user", "content": prompt})

    try:
        start_time = time.time() 

        completion = client.chat.completions.create(
            model="local-model",
            messages=current_messages,
            temperature=0.1, 
            max_tokens=100, # Increased to 100 to prevent cutting off multi-step commands
            stream=False,
            stop=["\n", "User", "***"] 
        )

        response = completion.choices[0].message.content
        
        elapsed = time.time() - start_time
        print(f"[grey50][Debug] Speed: {elapsed:.2f}s[/grey50]") 

        # Data cleaning
        response = response.replace("\n", "")
        response = response.split(",")
        response = [i.strip() for i in response]

        temp = []
        for task in response:
            for func in funcs:
                # Relaxed check: matches if function appears at start of string
                if task.startswith(func):
                    temp.append(task)
        
        response = temp

        if len(response) == 0:
            return FirstLayerDMM(prompt=prompt, retries=retries + 1)
        else:
            return response
            
    except Exception as e:
        print(f"[bold red]Error:[/bold red] {e}")
        return ["general " + prompt]

if __name__ == "__main__":
    print("[green]Jarvis Decision Core Online (4B Optimized)[/green]")
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        result = FirstLayerDMM(user_input)
        print(result)
        
        if "exit" in result:
            break