A GUI-based automation system for managing Notion databases using natural language instructions and AI (Gemini/OpenAI). Features include scheduled tasks, manual commands, and AI-to-API translation for Notion operations—all wrapped in a secure, user-friendly desktop interface.

## Features

- 🔧 Natural language to Notion API translation using Gemini or OpenAI
- 🧠 AI-powered task creation and execution
- ⏰ Schedule recurring tasks with frequency control
- 🔐 Secure token-based Notion access and RSA-based communication
- 🖥️ Tkinter GUI with tabs for configuration, tasks, manual input, and logs
- 📁 Persistent task and config storage via JSON files

## Installation

```bash
pip install -r requirements.txt
python notion.py
```
Requirements
Python 3.8+
Notion Integration Token
Gemini API Key (or OpenAI Key for future support)

Usage
Enter your Notion token and API key under the Configuration tab.
Create automation tasks using natural instructions like:
"Create a task for reviewing design documents every Monday."
Click Start Task to begin automated execution.
View logs or manually run commands from the respective tabs.
