import asyncio
import os
import requests
import urllib.parse
from time import sleep, time
from PIL import Image
from random import randint
from dotenv import get_key

# -----------------------------------------------------------------------------
# Configuration and Setup
# -----------------------------------------------------------------------------

# Load the Hugging Face Token from the .env file.
# This is required for the fallback generation method using Hugging Face's API.
# Ensure your .env file has a valid HF_TOKEN.
HF_TOKEN = get_key(".env", "HF_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# URL for the fallback Hugging Face Model (Stable Diffusion v1.5).
# We use the standard inference API endpoint for better compatibility with legacy models.
HF_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# -----------------------------------------------------------------------------
# Image Generation Functions
# -----------------------------------------------------------------------------

async def generate_pollinations(prompt, seed):
    """
    Generates an image using Pollinations.ai.
    This service is free, requires no API key, and is generally reliable.
    
    Args:
        prompt (str): The text description for the image.
        seed (int): A random seed to ensure unique results.
        
    Returns:
        bytes: The binary content of the image if successful, None otherwise.
    """
    # 1. URL Encode the prompt
    # This ensures spaces and special characters dont break the URL.
    encoded_prompt = urllib.parse.quote(prompt)
    
    # 2. Construct the API URL
    # We explicitly request 1024x1024 resolution and disable the logo.
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=True"
    
    # 3. Retry Logic
    # Pollinations can sometimes return 502 Bad Gateway if overloaded. We retry 3 times.
    for attempt in range(3): 
        try:
            print(f"Attempt {attempt+1} (Pollinations)...")
            # Use asyncio.to_thread because requests is blocking
            response = await asyncio.to_thread(requests.get, url, timeout=30)
            
            if response.status_code == 200:
                return response.content
            elif response.status_code in [500, 502, 503, 504]:
                # Temporary server error, wait and retry
                print(f"Gateway Error {response.status_code}, retrying in 3s...")
                await asyncio.sleep(3)
            else:
                # Permanent error (e.g. 404), stop trying
                print(f"Pollinations Error: {response.status_code}")
                break
        except Exception as e:
            # Network connection error
            print(f"Connection Error: {e}")
            await asyncio.sleep(2)
            
    return None

async def generate_huggingface(prompt):
    """
    Fallback function to generate an image using Hugging Face Inference API.
    This is called if Pollinations.ai fails after all retries.
    
    Args:
        prompt (str): The text description for the image.
        
    Returns:
        bytes: Image content if successful, None otherwise.
    """
    payload = {"inputs": prompt}
    try:
        print(f"Attempting Hugging Face Fallback...")
        response = await asyncio.to_thread(requests.post, HF_URL, headers=HEADERS, json=payload)
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"HF Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"HF Exception: {e}")
        return None

async def generate_images(prompt):
    """
    Main orchestrator for image generation.
    - Runs 2 generation tasks in parallel.
    - Tries Pollinations first for each task.
    - Falls back to Hugging Face if Pollinations fails.
    - Saves successful images to the 'Data' folder.
    
    Args:
        prompt (str): The text description for the image.
    """
    tasks = []
    
    # Inner logic for a single image generation task
    async def generate_single_image(index):
        seed = randint(0, 1000000)
        
        # Priority 1: Try Pollinations
        image_data = await generate_pollinations(prompt, seed)
        
        # Priority 2: Fallback to Hugging Face
        if not image_data:
            image_data = await generate_huggingface(prompt)
            
        return image_data

    # Create 2 concurrent tasks (for 2 different images)
    for i in range(2):
        tasks.append(asyncio.create_task(generate_single_image(i)))

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)

    # Prepare file paths
    prompt_clean = prompt.replace(" ", "_")
    
    # Ensure the 'Data' directory exists
    if not os.path.exists("Data"):
        os.makedirs("Data")

    saved_count = 0
    # Save the received image data to files
    for i, result in enumerate(results):
        if result:
            file_path = fr"Data\{prompt_clean}{i+1}.jpg"
            try:
                with open(file_path, "wb") as f:
                    f.write(result)
                print(f"Saved: {file_path}")
                saved_count += 1
            except Exception as e:
                print(f"Save Error: {e}")
    
    if saved_count == 0:
        print("CRITICAL: Failed to generate any images.")

# -----------------------------------------------------------------------------
# Viewer Functions
# -----------------------------------------------------------------------------

def open_image(prompt):
    """
    Opens and displays the generated images using the system's default image viewer.
    
    Args:
        prompt (str): The prompt used to generate the filenames.
    """
    folder_path = r"Data"
    prompt_clean = prompt.replace(" ", "_")
    # Expected filenames
    files = [f"{prompt_clean}{i}.jpg" for i in range(1, 3)]
    
    for jpg_file in files:
        path = os.path.join(folder_path, jpg_file)
        
        # Only try to open if the file actually exists
        if os.path.exists(path):
            try:
                img = Image.open(path)
                print(f"Displaying image: {path}")
                img.show()
                sleep(1) # Small pause to allow viewer to launch
            except Exception as e:
                print(f"Cannot show {jpg_file}: {e}")

def GenerateImages(prompt):
    """
    Public wrapper function.
    1. Runs the async generation process.
    2. Opens the generated images.
    """
    asyncio.run(generate_images(prompt))
    open_image(prompt)

# -----------------------------------------------------------------------------
# Main Execution Loop
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    while True:
        try:
            # File used for communication between Main.py and this script
            data_path = r"Frontend\Files\ImageGeneration.data"
            
            # Check if the trigger file exists
            if os.path.exists(data_path):
                with open(data_path, "r") as f:
                    data = f.read()
                
                # Parse the file content: "Prompt,Status"
                if data and "," in data:
                    prompt, status = data.split(",", 1)
                    
                    # If status is True, start generation
                    if status.strip() == "True":
                        print(f"Generating: {prompt}")
                        GenerateImages(prompt)
                        
                        # Reset the trigger file to prevent infinite loops
                        with open(data_path, "w") as f:
                            f.write("False,False")
                        break # Exit loop after successful generation (subprocess mode)
            
            # Sleep to prevent high CPU usage while waiting
            sleep(1)
            
        except Exception as e:
            print(f"Loop Error: {e}")
            sleep(1)
