<div align="center">

# 🤖 Hybrid LLM AI Assistant

### _Your Intelligent Desktop Companion_

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)]()

**A production-ready, locally hosted AI assistant that bridges the gap between powerful Cloud LLMs and local system control.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#-configuration) • [Architecture](#-architecture)

</div>

---

## Overview

The **Hybrid LLM AI Assistant** is a sophisticated desktop application designed to emulate the capabilities of advanced assistants like JARVIS. Unlike standard chatbots, this system integrates deeply with your operating system, allowing it to perform real-world tasks, browse the web, and generate multimedia content.

It leverages a **Hybrid Architecture**:

1.  **Cloud Intelligence**: Uses Google Gemini and Cohere APIs for complex decision-making, real-time reasoning, and general conversation.
2.  **Local Privacy**: Support for local LLMs (via LM Studio) for private content generation (emails, code, etc.).
3.  **System Automation**: Direct control over Windows applications, system settings, and media playback.

---

## Features

### Intelligent Core

- **Dual-Mode Logic**:
  - **Local Mode (Default)**: Runs entirely on your machine using Llama 3 or Mistral (via LM Studio). No data leaves your network.
  - **Cloud Mode (Optional)**: Can be configured to use Google Gemini or Cohere for complex tasks requiring massive world knowledge.
- **Multimodal Routing**: Intelligently switches between General Chat, Real-Time Web Search, and Automation based on user intent.
- **Emotion Detection**: Detects user sentiment (e.g., Happy, Curious, Urgent) to adjust the assistant's personality dynamically.

### Natural Interaction

- **Voice-First Interface**: High-accuracy **Speech-to-Text** (using Chrome Web Speech API) and natural **Text-to-Speech** (Microsoft Edge Neural Voices).
- **Wake Word Detection**: Always-listening capability (optional).
- **Universal Translation**: Automatically translates all voice inputs to English for consistent processing.

### Automation & Tools

| Feature          | Description                                                                                              |
| :--------------- | :------------------------------------------------------------------------------------------------------- |
| **App Control**  | "Open specific apps" (e.g. "Open File Explorer", "Open Chrome") using strict Windows naming conventions. |
| **System Ops**   | "Mute volume", "Lock screen", "Shutdown PC", "Brightness Control"                                        |
| **Web Browsing** | Automates Google & YouTube searches. Scrapes live data for questions like "Stock price of Apple".        |
| **Image Gen**    | Create AI art instantly using Pollinations.ai (Free) or Stable Diffusion.                                |
| **Content Gen**  | Write emails, code, and essays privately using your Local LLM.                                           |

### Modern GUI

- **Futuristic UI**: Built with **PyQt5**, featuring a dynamic listening interface and chat bubbles.
- **Visual Feedback**: Real-time status indicators ("Listening", "Thinking", "Processing").

---

## Installation

### Prerequisites

- **OS**: Windows 10/11
- **Python**: v3.10 or newer
- **Browser**: Google Chrome (Required for Speech Recognition backend)
- **LM Studio**: Required for Local LLM operations.

### 1. Clone Repository

```bash
git clone https://github.com/your-username/Hybrid-LLM-Assistant.git
cd Hybrid-LLM-Assistant
```

### 2. Set Up Virtual Environment

It is recommended to use a virtual environment to handle dependencies cleanly.

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Local LLM (Default & Recommended)

The project requires a local LLM running via **LM Studio** by default for tasks like content generation and privacy-focused operations.

1.  **Download & Install**: [LM Studio](https://lmstudio.ai/)
2.  **Download a Model**: Search for and download a lightweight, instruction-tuned model (e.g., `Meta-Llama-3-8B-Instruct` or `Mistral-7B`).
3.  **Start Server**:
    - Go to the "Local Server" tab (double-headed arrow icon).
    - **Load** your downloaded model.
    - Click **Start Server**.
    - Ensure the URL is `http://localhost:1234`.

### Why Local LLM? (Important)

This project uses a **Hybrid Architecture** where cloud models handle complex logic (reasoning, routing), but **Private Content Generation** is handled locally.

- **Privacy**: When you ask the assistant to write an email, code, or personal note, that data is processed **entirely on your machine**. It never leaves your network.
- **Cost**: Cloud APIs charge per token. By offloading heavy text generation tasks to your local GPU/CPU, you save significantly on API costs.
- **Offline Capability**: Essential features remain functional even without an internet connection.

> **Note**: If you cannot run a local model due to hardware limitations, you will need to modify `Backend/Automation.py` to use OpenAI/Gemini APIs for the `Content()` function instead.

---

## Configuration (Environmental Setup)

To run this assistant, you must configure a `.env` file with your API keys. This is critical for the AI "Brain" to function.

### Why do I need this?

The assistant relies on Cloud APIs (Google Gemini, Cohere) for its intelligence. These services require secure authentication via API keys. These keys are private and should **never** be shared or committed to GitHub.

### Step-by-Step Guide

**1. Create the File**

- Locate the file named `.env.example` in the root directory.
- Rename it to `.env` (or create a new file named `.env`).

**2. Configure Keys**

**A. User Preferences (Required)**
These settings customize the assistant for you.

```ini
Username=User
AssistantName=Jarvis
Language=English
INPUT_LANGUAGE=en
AssistantVoice=en-IN-PrabhatNeural
```

**B. Cloud API Keys (Optional)**
_Only fill these if you intend to switch the backend to use Cloud Models (Gemini/Cohere) instead of Local LLM._

```ini
You need to sign up for free API keys from the following providers:

- **Gemini API Key** (for Decision Making & Chat):
  - **Go to**: [Google AI Studio](https://aistudio.google.com/app/apikey)
  - **Cost**: Free tier available.
  - **Action**: Create a new API key.

- **Cohere API Key** (for Alternative Chat Models):
  - **Go to**: [Cohere Dashboard](https://dashboard.cohere.com/api-keys)
  - **Cost**: Free trial keys available.
  - **Action**: Generate a Trial Key.

- **Hugging Face Token** (for Image Generation fallback):
  - **Go to**: [Hugging Face Settings](https://huggingface.co/settings/tokens)
  - **Action**: Create a "Read" token.
```

**4. Verify**
Run the application. If you see authentication errors, double-check that you copied the entire key string without extra spaces.

---

## Usage

Run the main application entry point:

```bash
python Main.py
```

### Example Commands

- **Productivity**: _"Open Notepad and write a python script for a calculator."_
- **Information**: _"Who won the last Super Bowl?"_
- **Media**: _"Play Lo-Fi beats on YouTube."_
- **Creative**: _"Generate an image of a cyberpunk city."_
- **System**: _"Turn up the volume."_

---

## Architecture

The system operates using a multi-threaded architecture to ensure the GUI remains responsive while heavy AI processing happens in the background.

```mermaid
graph TD
    User((User)) -->|Voice Input| STT[Speech Recognition]
    STT --> Brain[Decision Logic (Gemini/Brain_Model)]

    Brain -->|Auto Command| Auto[Automation Module]
    Brain -->|General Chat| LLM[LLM Chatbot]
    Brain -->|Live Info| Search[Real-Time Search Engine]
    Brain -->|Image Gen| Img[Image Generator]

    Auto --> System[Windows OS]
    LLM --> Response[Text Response]
    Search --> Response
    Img --> Files[Saved Images]

    Response --> TTS[Text-to-Speech]
    TTS --> User
```

---

## Project Structure

```bash
├── Backend/                # 🧠 The Brain
│   ├── Automation.py       # OS interactions & AppOpener
│   ├── Chatbot.py          # LLM Conversation wrapper
│   ├── RealTimeSearch.py   # Web Scraping logic
│   ├── ImageGeneration.py  # AI Image Gen logic
│   └── SpeechToText.py     # Selenium-based STT
├── Frontend/               # 🎨 The Face
│   ├── GUI.py              # PyQt5 Application
│   └── Assets/             # Icons and Gifs
├── Data/                   # 💾 Memory
│   ├── ChatLog.json        # Conversation History
│   └── Database.data       # Temporary Context
└── Main.py                 # 🎬 Orchestrator
```

---

## Security Note

- **API Keys**: Your API keys are stored locally in `.env`. **Never** upload this file to GitHub.
- **Local Processing**: Automation scripts run with user privileges. Review the code in `Automation.py` if you intend to modify system commands.

---

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## Disclaimer

This system is designed to automate tasks and control your computer. While secure by design, **the developer is not responsible for any data loss, system damage, or unintended actions** resulting from the use of this software. Users are advised to review the code (specifically `Automation.py`) before running potentially destructive commands.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/your-username">Hybrid-LLM-Assistant</a></sub>
</div>
