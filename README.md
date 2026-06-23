# System Automation Assistant

An AI-powered desktop automation assistant built using Python, Ollama, and Agentic AI concepts.

---

# Project Overview

System Automation Assistant (SAA) is an intelligent desktop automation framework that converts natural language commands into executable system actions.

The project combines deterministic automation with local LLM reasoning to create a reliable, extensible, and context-aware AI assistant capable of:

* Controlling desktop applications
* Managing files and folders
* Automating web interactions
* Understanding conversational references
* Maintaining execution context
* Resolving ambiguous user requests
* Executing multi-step workflows

The long-term vision is to evolve SAA into a fully autonomous AI Agent capable of voice interaction, memory-based reasoning, workflow orchestration, and intelligent task execution.

---

# Current Features

## Application Automation

### Capabilities

* Open applications
* Close applications
* Application alias resolution
* Application discovery
* Start Menu lookup
* PATH lookup
* State tracking

### Example Commands

```text
open vscode

open visual studio

open calculator

close calculator

open github desktop
```

---

## Website Automation

### Capabilities

* Open websites directly
* Search supported websites
* Deterministic URL routing
* Website registry architecture
* Dynamic URL building

### Example Commands

```text
open github website

open github website python projects

open youtube website ghost of yotei

open linkedin website software engineer jobs

open github.com
```

---

## Filesystem Automation

### Capabilities

* Create files
* Open files
* Create folders
* Open folders
* Smart file discovery
* Natural language path resolution
* Fuzzy path matching
* Interactive disambiguation
* Context-aware file resolution

### Example Commands

```text
create report.docx in desktop

create folder Internship in documents

open report.docx

open internship folder

create notes.txt in C drive Kavi Work Degree Charusat SEM 7 Internship Reports
```

---

## Context Intelligence

### Capabilities

* Session memory
* Reference resolution
* Context synchronization
* Previous action tracking
* Active application awareness

### Example Commands

```text
open github

close it

open it again

focus previous app

show current context
```

---

## Interactive Disambiguation

The assistant can safely handle ambiguous requests by asking for clarification.

### Example

```text
delete report

Found multiple matches:

1. report.docx
2. report.pdf
3. report.txt

Select a file:
```

---

## Desktop Automation

### Capabilities

* Screenshot capture
* Delayed execution
* Timed automation

### Example Commands

```text
take screenshot

wait 5 seconds

open calculator and wait 5 seconds
```

---

## AI Planning & Reasoning

Complex tasks are delegated to local LLMs through Ollama.

### Example Commands

```text
open steam and discord

open calculator and close it after 10 seconds

search python projects on github and open vscode
```

---

# Architecture

## Deterministic Routing Layer

The first layer intercepts predictable commands and executes them without invoking the LLM.

### Examples

```text
open github website

open github.com

create report.docx

open report.docx
```

### Benefits

* Faster execution
* Reduced hallucinations
* Lower latency
* Lower LLM dependency
* More predictable behavior

---

## Context Layer

### Components

* Context Manager
* Session State
* Reference Resolver
* Context Synchronization Engine

### Responsibilities

* Track previous actions
* Maintain active entities
* Resolve references
* Support conversational commands

---

## Filesystem Layer

### Components

* Path Resolver
* Smart Discovery Engine
* Disambiguation Manager
* Filesystem Tools

### Responsibilities

* Natural language path interpretation
* Fuzzy matching
* Smart discovery
* Ambiguity detection
* Safe filesystem operations

### Example

```text
C drive Kavi Work Degree Charusat SEM 7 Internship Reports
```

Resolves to:

```text
C:\Kavi\Work\Degree\Charusat\SEM 7\Internship\Reports
```

---

## LLM Planning Layer

### Components

* Command Parser
* Ollama Client
* Planner

### Responsibilities

* Multi-step reasoning
* Task decomposition
* Workflow planning
* Intent understanding

---

## Execution Layer

### Components

* Automation Engine
* Executor
* Tool Registry
* System Tools

### Responsibilities

* Execute actions
* Validate inputs
* Invoke tools
* Handle failures
* Synchronize context

---

# Technology Stack

## Core Technologies

* Python 3.13
* Ollama

## AI Models

* Gemma 3 (Primary)
* Llama 3 (Testing & Evaluation)

## Libraries

* pathlib
* subprocess
* os
* shutil
* webbrowser
* pyautogui
* pytest

---

# Project Structure

```text
SystemAutomationAssistant/

├── data/
├── generated_files/
├── logs/
├── screenshots/
│
├── src/
│   ├── automation/
│   │   ├── engine.py
│   │   └── executor.py
│   │
│   ├── context/
│   │   └── context_manager.py
│   │
│   ├── core/
│   │   ├── command_parser.py
│   │   ├── history_manager.py
│   │   ├── url_builder.py
│   │   └── website_registry.py
│   │
│   ├── llm/
│   ├── planner/
│   ├── tools/
│   └── utils/
│
├── tests/
│   ├── automation/
│   ├── context/
│   ├── filesystem/
│   ├── regression/
│   └── tools/
│
├── requirements.txt
├── README.md
└── main.py
```

---

# Supported Actions

Current supported actions include:

```text
open_application
close_application
open_url
search_web

create_file
open_file
create_folder
open_folder

take_screenshot
wait

show_context
resolve_reference
discover_files
disambiguate_selection
```

---

# Testing

Install dependencies:

```bash
pip install -r requirements.txt
```

Run all tests:

```bash
pytest tests -v
```

Run a specific test suite:

```bash
pytest tests/filesystem -v
```

Run regression tests:

```bash
pytest tests/regression -v
```

---

# Current Project Status

## Day 15 Complete

### Completed Features

* Application Automation
* Website Automation
* Deterministic Routing
* URL Builder
* Website Registry
* Executor Framework
* Filesystem Automation
* Path Resolver
* Smart Discovery
* Interactive Disambiguation
* Context Management
* Context Synchronization
* Reference Resolution
* Screenshot Support
* Wait Actions
* Logging Framework
* Automated Testing Framework
* Regression Testing Suite

### Estimated Completion

```text
85%+
```

### Current Milestone

```text
Context-Aware Desktop Automation Assistant
```

---

# Upcoming Roadmap

## Feature 10

Application Macros

```text
open vscode
open github
open terminal
```

Saved as:

```text
start development workspace
```

---

## Feature 11

Window Management

```text
minimize chrome

maximize vscode

restore calculator
```

---

## Feature 12

System Controls

```text
increase volume

decrease brightness

turn wifi off
```

---

## Feature 13

Voice Assistant Layer

* Speech-to-Text
* Text-to-Speech
* Wake Word Detection
* Continuous Listening

---

## Feature 14

Advanced Agent Workflows

* Task Chaining
* Autonomous Planning
* Workflow Execution
* Memory-Based Reasoning

---

# Author

**Kavya Chavda**

B.Tech Information Technology
CSPIT, CHARUSAT

Softwingz Infotech Internship Project

---

# Version

Current Release

```text
v1.5.0
```

Codename

```text
Filesystem Intelligence & Context Awareness
```
