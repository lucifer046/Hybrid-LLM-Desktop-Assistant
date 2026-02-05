# Changelog

All notable changes to this project will be documented in this file.

## [v1.0.1] - 2026-02-05

### 🚀 New Features

- **Local-First Architecture**: The system now runs 100% locally by default using LM Studio for both the "Brain" (decision making) and Content Generation. This increases privacy and removes dependency on paid Cloud APIs.
- **Cloud-Optional Mode**: Added configuration support in `.env` to seamlessly switch the backend to Google Gemini or Cohere if cloud processing is preferred.
- **Emotion Detection**: The core `brain_model.py` now analyzes user sentiment (e.g., Happy, Curious, Urgent) and tags queries accordingly to adjust the assistant's personality.
- **Strict Automation Rules**: Implemented strict naming conventions for Windows applications (e.g., "Open File Explorer" instead of "Open My PC") to ensure reliable app launching.
- **Universal Translation**: `SpeechToText.py` now automatically translates all non-English voice inputs to English before processing, ensuring consistent command execution.

### 🐛 Bug Fixes

- **Automation Logic**: Fixed `Automation.py` to reliably identify and close specific application windows.
- **Browser Tab Management**: Resolved an issue where asking to "Close YouTube" would kill the entire Chrome process. Now, it intelligently scans for the specific tab and closes it using `Ctrl+W` simulation.
- **App Opening Fallback**: Fixed the logic where uninstalled applications would cause silent failures. The system now reliably falls back to performing a Google Search for the app name.

### 📚 Documentation & Code Quality

- **Codebase Commenting**: Added comprehensive, beginner-friendly line-by-line comments to all key Backend files (`Automation.py`, `Chatbot.py`, `SpeechToText.py`, `RealTimeSearchEngine.py`, `brain_model.py`) to improve maintainability and educational value.
- **README Overhaul**: Completely updated `README.md` to document the new `Local-First, Cloud-Optional` philosophy, revised the Installation guide for LM Studio, and clarified the Configuration steps for API keys.
