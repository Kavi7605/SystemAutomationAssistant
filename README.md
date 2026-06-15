# System Automation Assistant

An AI-powered desktop automation assistant built using Python, Ollama, and Agentic AI concepts.

---

# Project Overview

System Automation Assistant (SAA) is an intelligent desktop automation framework that converts natural language commands into executable system actions.

The project combines deterministic automation with local LLM reasoning to create a reliable and extensible AI assistant capable of controlling applications, interacting with the filesystem, performing web actions, and automating desktop workflows.

The long-term goal is to evolve SAA into a fully context-aware AI Agent capable of voice interaction, workflow automation, memory-based reasoning, and autonomous task execution.

---

# Current Features

## Application Automation

* Open applications
* Close applications
* Application alias resolution
* Application discovery using PATH and Start Menu indexing
* Graceful fallback handling

### Example Commands

```text
open vscode

open visual studio

open calculator

close calculator

open github
```

---

## Website Automation

* Open websites directly
* Open search results directly on supported websites
* Deterministic URL routing
* Website registry architecture
* URL Builder engine

### Example Commands

```text
open github website

open github website python projects

open youtube website ghost of yotei

open github.com

open linkedin website software engineer jobs
```

---

## Filesystem Automation

* Create folders
* Open folders
* Create files
* Open files
* Natural language path resolution
* Desktop, Downloads, Documents support
* Nested directory traversal

### Example Commands

```text
create report.docx in desktop

create folder Internship in desktop

open report.docx in desktop

open folder downloads

create notes.txt in C drive Kavi Work Degree Charusat SEM 7 Internship Reports
```

---

## Desktop Automation

* Take screenshots
* Delayed execution (Wait Action)

### Example Commands

```text
take screenshot

wait 5 seconds

open calculator and wait 5 seconds
```

---

## AI Planning & Reasoning

For complex or multi-step commands, the assistant uses local LLM reasoning through Ollama.

### Example Commands

```text
open steam and discord

open calculator and close it after 10 seconds

search python projects on github and open vscode
```

---

# Architecture

## Deterministic Routing Layer

The first layer of the system intercepts predictable commands and executes them without invoking the LLM.

Examples:

```text
open github website

open github.com

create report.docx in desktop

open notes.txt
```

Benefits:

* Faster execution
* Reduced hallucinations
* Consistent behavior
* Lower LLM dependency

---

## LLM Planning Layer

Used only for commands requiring reasoning, decomposition, or interpretation.

Components:

* Task Planner
* Command Parser
* Ollama Client

Responsibilities:

* Multi-step planning
* Complex command understanding
* Workflow decomposition

---

## Execution Layer

Components:

* Automation Engine
* Executor
* Tool Registry
* System Tools

Responsibilities:

* Command execution
* Validation
* Error handling
* Tool invocation
* Fallback management

---

## Filesystem Layer

Components:

* Path Resolver
* CreateFileTool
* OpenFileTool
* CreateFolderTool
* OpenFolderTool

Responsibilities:

* Natural language path interpretation
* Deterministic path matching
* Fuzzy matching
* Ambiguity detection
* Filesystem safety

Example:

```text
C drive Kavi Work Degree Charusat SEM 7 Internship Reports
```

Resolves to:

```text
C:\Kavi\Work\Degree\Charusat\SEM 7\Internship\Reports
```

---

# Technology Stack

## Core Technologies

* Python 3.13
* Ollama

## AI Models

* Gemma 3 (Primary)
* Llama 3 (Testing & Evaluation)

## Libraries

* subprocess
* pathlib
* os
* shutil
* webbrowser
* pyautogui

## Testing

* pytest

---

# Project Structure

```text
SystemAutomationAssistant/

├── data/
│   └── history.json
│
├── logs/
│   └── system.log
│
├── screenshots/
│
├── generated_files/
│
├── src/
│   ├── automation/
│   │   ├── engine.py
│   │   └── executor.py
│   │
│   ├── core/
│   │   ├── command_parser.py
│   │   ├── history_manager.py
│   │   ├── url_builder.py
│   │   └── website_registry.py
│   │
│   ├── llm/
│   │
│   ├── planner/
│   │
│   ├── tools/
│   │
│   └── utils/
│
├── tests/
│
├── requirements.txt
├── README.md
└── main.py
```

---

# Supported Actions

Current supported actions include:

* open_application
* close_application
* open_url
* search_web
* create_file
* open_file
* create_folder
* open_folder
* take_screenshot
* wait

---

# Testing

Install dependencies:

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
python -m pytest tests
```

Run a specific test:

```bash
python -m pytest tests/test_path_resolver.py
```

---

# Current Project Status

## Day 7 Complete

Completed:

* Application Automation
* Website Automation
* Deterministic Routing Engine
* URL Builder
* Website Registry
* Executor Fallback Logic
* Path Resolver Engine
* File Creation
* File Opening
* Folder Creation
* Folder Opening
* Screenshot Support
* Wait Action Support
* Logging Framework
* Automated Testing Framework

Estimated Completion:

```text
65% – 70%
```

Current Milestone:

```text
Production-Hardened Desktop Automation Assistant
```

---

# Day 8 Roadmap

## Environment Awareness

Examples:

```text
close it

open it again

switch to vscode
```

---

## Context Memory

Examples:

```text
open github

close it

open it again
```

---

## Browser Automation

Examples:

```text
open youtube and search ghost of yotei

open gmail and compose email
```

---

## Voice Interface

Features:

* Speech-to-Text
* Text-to-Speech
* Continuous Listening Mode
* Conversational Interaction

---

# Author

**Kavya Chavda**

B.Tech Information Technology
CSPIT, CHARUSAT

Softwingz Infotech Internship Project

---

# Version

Current Release:

```text
v0.7.0
```

Codename:

```text
Semantic Determinism & Architecture Hardening
```
