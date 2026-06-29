# 🚀 System Automation Assistant

> A deterministic AI-powered Windows automation assistant capable of understanding natural language, maintaining conversational context, and executing real system operations with high reliability.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-success)
![Tests](https://img.shields.io/badge/Tests-517%2B_Passing-brightgreen)
![Architecture](https://img.shields.io/badge/Architecture-Hybrid_AI-orange)
![Status](https://img.shields.io/badge/Status-Under_Development-blue)

---

# Overview

System Automation Assistant (SAA) is an intelligent desktop automation platform built using a **hybrid deterministic + AI architecture**.

Unlike traditional AI assistants that rely entirely on Large Language Models, SAA executes **known commands deterministically** for speed, reliability, and zero hallucinations, while using an **Ollama-powered LLM** only as a fallback planner for unknown or complex requests.

The result is an assistant that behaves like a real operating system assistant instead of a chatbot.

---

# Architecture

```
                   User Command
                         │
                         ▼
               NLP Preprocessing Layer
                         │
                         ▼
                 Parser & Multi-Intent Parser
                         │
                         ▼
             Deterministic Semantic Router
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
 Known Command                    Unknown / Complex
        │                                 │
        ▼                                 ▼
 Command Expander                  Ollama Task Planner
        │                                 │
        └──────────────┬──────────────────┘
                       ▼
                  Executor Engine
                       │
                       ▼
              Windows System Tools
```

---

# Core Features

## Deterministic Semantic Routing

Most commands completely bypass the LLM.

Examples:

- Open applications
- Close applications
- Window management
- Brightness
- Volume
- Wi-Fi
- Power management
- Filesystem operations
- Desktop automation

This provides:

- Near-instant execution
- Zero hallucinations
- Predictable behavior
- High reliability

---

## Hybrid AI Planner

When deterministic routing cannot understand a request:

```
User
   │
   ▼
Deterministic Router
   │
   ▼
No Match
   │
   ▼
Ollama (gemma3:4b)
   │
   ▼
Structured JSON Plan
   │
   ▼
Executor
```

The LLM is only responsible for planning—not execution.

---

# Natural Language Understanding

The assistant now supports conversational English instead of rigid commands.

Examples

```
Could you please open Discord?

Actually close WhatsApp.

Launch Steam.

Switch back.

Focus the other app.

Close both of them.

Open Steam then Discord.

Open Steam and wait until it opens.

Reopen the last closed app.
```

---

# NLP Pipeline

```
User Input

↓

Grammar Normalizer

↓

Reference Normalizer

↓

Number Normalizer

↓

Application Normalizer

↓

Intent Normalizer

↓

Canonicalizer

↓

Automation Engine
```

Current capabilities include:

- Grammar normalization
- Intent normalization
- Number normalization
- Application normalization
- Reference normalization
- Command canonicalization

---

# Multi-Intent Parsing

Supports long conversational commands.

Examples

```
Open Steam then Discord

Open Steam and wait until it opens

Open Discord then maximize it

Open Steam, Discord and WhatsApp

Close Steam and Discord

Open Steam then focus previous app
```

Features

- Command splitting
- Nested parsing
- Sequential execution
- Dependency handling
- Context propagation

---

# Context Intelligence

The assistant remembers context throughout the current session.

Supports:

- it
- this
- that
- previous app
- first app
- second app
- oldest app
- newest app
- both
- all apps
- other app
- last closed app
- recently focused app

Example

```
Open Steam

Open Discord

Close it

Focus Steam

Minimize it

Close both

Reopen the last closed app
```

---

# Current Automation Capabilities

## System Controls

- Shutdown
- Restart
- Sleep
- Lock
- Brightness
- Volume
- Mute
- Wi-Fi
- Power Plans

---

## Window Management

Native Win32 APIs

- Focus Window
- Minimize
- Maximize
- Restore
- Close
- List Windows
- Active Window Detection

---

## Desktop Automation

- Mouse Movement
- Mouse Clicks
- Keyboard Typing
- Hotkeys
- Scrolling

---

## Filesystem Automation

- Create Files
- Delete Files
- Rename
- Copy
- Move
- Folder Operations

---

## Web Automation

- Open Websites
- Web Search
- Browser Launch

---

## Application Automation

- Open Applications
- Close Applications
- Focus Applications
- Running Application Detection

---

# Technology Stack

- Python 3.13
- Ollama
- gemma3:4b
- PyWin32
- psutil
- ctypes
- PyAutoGUI
- Pillow
- SpeechRecognition
- Vosk
- Pytest

---

# Testing

The project contains extensive automated testing.

Current Statistics

- **517+ automated tests**
- Unit Tests
- Integration Tests
- Regression Tests
- NLP Pipeline Tests
- Context Resolution Tests
- Multi-Intent Tests
- Sequential Execution Tests

Run the test suite

```bash
pytest tests/
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/Kavi7605/SystemAutomationAssistant.git
```

```bash
cd SystemAutomationAssistant
```

Create virtual environment

```bash
python -m venv venv
```

Activate environment

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Install Ollama

```
https://ollama.com
```

Pull the required model

```bash
ollama pull gemma3:4b
```

---

# Running

```bash
python main.py
```

---

# Project Structure

```
SystemAutomationAssistant/

│

├── src/

│ ├── automation/

│ ├── context/

│ ├── core/

│ ├── llm/

│ ├── nlp/

│ ├── parser/

│ ├── planner/

│ ├── tools/

│ ├── voice/

│ └── utils/

│

├── tests/

│ ├── automation/

│ ├── context/

│ ├── nlp/

│ ├── parser/

│ └── regression/

│

├── main.py

├── requirements.txt

└── README.md
```

---

# Current Progress

Current milestone includes:

- Hybrid AI Architecture
- Deterministic Semantic Router
- NLP Preprocessing Pipeline
- Multi-Intent Parsing
- Sequential Command Execution
- Context Intelligence
- Multi-Application Context
- Temporal References
- Conversation Memory
- Native Window Management
- Filesystem Automation
- Desktop Automation
- Extensive Regression Testing

The assistant has evolved from a simple command executor into a context-aware automation platform capable of understanding natural conversational instructions while maintaining deterministic execution.

---

# Future Roadmap

- Voice Conversation Memory
- Typo Recovery
- Ambiguity Resolution
- Confidence Scoring
- Better LLM Planning
- Playwright Web Automation
- Learning New User Phrases
- Plugin Architecture
- Cross-platform Support (Linux/macOS)

---

# License

This project is currently being developed as part of the **Softwingz Infotech Internship Program**.

---

## Author

**Kavya Chavda**

B.Tech Information Technology

System Automation Assistant Project

Softwingz Infotech Internship (2026)