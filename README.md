# 🤖 YouTube Auto-Commenter Bot 🎯

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![YouTube Data API](https://img.shields.io/badge/YouTube%20Data-API%20v3-red)](https://developers.google.com/youtube/v3)

> 🔮 Automate your YouTube engagement with intelligent comment sequencing and randomization

## 🚀 Overview

This bot automatically engages with YouTube videos based on category IDs using a smart commenting system. It follows a sequential pattern initially, then switches to randomization after exhausting the comment pool - keeping your engagement fresh and authentic.

## 🛠️ Prerequisites

- Python 3.8 or higher 🐍
- YouTube Data API v3 credentials 🔑
- Google Cloud Console project access 🌐

## 🔧 Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/youtube-auto-commenter.git
cd youtube-auto-commenter
```

2. Install Python:
   - Download the latest version from [Python.org](https://www.python.org/downloads/)
   - Ensure you check "Add Python to PATH" during installation

3. Install required packages:
```bash
pip install -r requirements.txt
```

## 📡 API Setup

1. Create TWO separate projects in Google Cloud Console:
   - Navigate to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "New Project" in the top-right corner
   - Name your projects (e.g., "YouTube Bot 1" and "YouTube Bot 2")

2. For EACH project:
   - Enable YouTube Data API v3:
     - Go to "APIs & Services" > "Library"
     - Search for "YouTube Data API v3"
     - Click "Enable"
   
   - Create OAuth 2.0 credentials:
     - Go to "APIs & Services" > "Credentials"
     - Click "Create Credentials" > "OAuth client ID"
     - Choose "Desktop app" as application type
     - Download the client secret file
     - Rename files to `client_secret_1.json` and `client_secret_2.json` respectively

3. Configure OAuth consent screen:
   - Set application name
   - Add authorized domains
   - Select "force-ssl" scope
   - Add `/auth/youtube.force-ssl` to required scopes

## ⚙️ Configuration

1. Place both `client_secret_1.json` and `client_secret_2.json` in the project root directory
2. Update `config.json` with your preferred:
   - Category IDs
   - Comment templates
   - Time intervals

## 🎮 Usage

Run the bot:
```bash
python main.py
```

## 🔐 Security Notes

- Never share your client secret files
- Keep your API keys secure
- Monitor your API quota usage
- Follow YouTube's terms of service

## ⚠️ Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with YouTube's terms of service and community guidelines.

## 📜 License

MIT License - feel free to modify and use this project as you wish!

---
💻 Created with 🖤 by Riddlerx1
