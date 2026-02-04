# ===========================================================================================================
#                                         TextToSpeech.py
# ===========================================================================================================
# This module converts text responses into audio using Microsoft Edge's TTS API.
# It provides a high-quality, natural-sounding voice for free (unlike paid APIs).
#
# Key Features:
# - EdgeTTS: Uses the `edge-tts` python library to fetch audio.
# - Asynchronous Generation: Generates audio files without blocking the main thread significantly.
# - Long Text Handling: Splits long responses into chunks to avoid boring the user.
# - Pygame Mixer: Plays the generated MP3 file smoothly.

import pygame # Audio playback
import random # For randomizing transitional phrases
import asyncio # For async TTS generation
import edge_tts # The core TTS engine
import os # File management
from rich.console import Console
from dotenv import dotenv_values

# -------------------------------------------------------------------------------------------------------
#                                         Configuration
# -------------------------------------------------------------------------------------------------------

# Console for rich terminal output
console = Console()

# Load environment variables
env_vars = dotenv_values(".env")

# Get usage settings
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural") # Default to Aria if not set

# File path for the temporary audio file
file_path = r"Data\speech.mp3"

# -------------------------------------------------------------------------------------------------------
#                                         Core Functions
# -------------------------------------------------------------------------------------------------------

async def TextToSpeech(text):
    """
    Generates an MP3 file from the given text using Edge TTS.
    
    Args:
        text (str): The text to speak.
    """
    # Clean up previous file
    if os.path.exists(file_path):
        os.remove(file_path)

    # Create the communicate object
    # Pitch and Rate adjustments make the voice sound more conversational/robotic depending on preference
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+22%')
    
    # Save to disk
    await communicate.save(file_path)

def TTS(text, func=lambda r=None: True):
    """
    Synchronous wrapper to Play the generated audio.
    
    Args:
        text (str): The text to speak.
        func (function): A callback function to check if playback should continue (e.g., check for stop signal).
    """
    while True:
        try:
            # 1. Generate Audio (Async call wrapped in Sync)
            asyncio.run(TextToSpeech(text))
            
            # 2. Initialize Audio Mixer
            pygame.mixer.init()

            # 3. Load and Play
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            # 4. Block until finished (but allow interruption via `func`)
            while pygame.mixer.music.get_busy():
                if func() == False: # Check external stop signal
                    break
                pygame.time.Clock().tick(10) # Efficient polling
            
            return True
        
        except Exception as e:
            print(f"Error in TTS: {e}")
        
        finally:
            # Cleanup
            try:
                func(False) # Signal end
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except Exception as e:
                print(f"Error in final block: {e}")

# -------------------------------------------------------------------------------------------------------
#                                         Long Text Handling
# -------------------------------------------------------------------------------------------------------

def TTSLongText(Text, func=lambda r=None: True):
    """
    Handles very long responses by speaking only the first few sentences
    and directing the user to read the rest on the screen.
    This improves UX by not making the user wait for 2 minutes of speech.
    
    Args:
        Text (str): The full response text.
        func (function): Stop signal callback.
    """
    Data = str(Text).split(".") # Split into sentences
    
    # List of "Read the rest" phrases
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]

    # Logic: If text > 400 chars and > 5 sentences, truncate it.
    if len(Data) > 5 and len(Text) >= 400:
        # Speak first 5 sentences + random transition phrase
        TTS(" ".join(Data[0:5]) + ". " + random.choice(responses), func)

    # Otherwise just speak the whole text.
    else:
        TTS(Text, func)

# -------------------------------------------------------------------------------------------------------
#                                         Main Execution (Test Node)
# -------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    while True:
        try:
            text_in = input("Enter the text: ")
            TTSLongText(text_in)
        except KeyboardInterrupt:
            console.print("\n[bold red]Forced Exit.[/bold red]")
            break
