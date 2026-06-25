# System Automation Assistant

The System Automation Assistant is a deterministic, AI-powered system orchestrator. It uses an Ollama-backed LLM (`gemma3:4b`) as a fallback task planner, but prioritizes a completely deterministic semantic routing engine for 100% reliable system control. 

This hybrid architecture guarantees fast, predictable execution for known capabilities while retaining the flexibility of an LLM for complex or unknown tasks.

## Architecture Overview

The project is split into the following modular layers:

- **Command Parser**: Captures user input, classifies intent, and extracts arguments using heuristics and NLP techniques.
- **Automation Engine**: The deterministic routing layer. Maps natural language and intent classifications directly to tools via regex and semantic matching.
- **Task Planner (LLM)**: An Ollama fallback layer. If the Automation Engine cannot route a request deterministically, it generates a multi-step task plan using `gemma3:4b`.
- **Executor**: Executes steps synchronously, handling context synchronization and tool invocation.
- **Context Manager & Application State Manager**: Real-time state trackers that know exactly what apps are running, focused, and open on screen.
- **Tool Registry**: Modularized suite of system tools across various categories (System Controls, Window Management, Filesystem, Desktop, Web).

## Features

### Deterministic Routing
All core commands bypass the LLM and map directly to native Python implementations (Win32 APIs, psutil) ensuring near-instantaneous execution without hallucinations.

### System Controls
- **Power Management**: Shutdown, Restart, Sleep, Lock Screen, Power Modes (Best Battery, Balanced, Best Performance)
- **Display & Audio**: Brightness controls, Volume controls (Mute, Unmute, Adjust)
- **Network**: Wi-Fi toggle and status, Mobile Hotspot status

### Window Management
Native Windows Window Management (bypassing PyAutoGUI).
- List Open Windows
- Get Active Window
- Focus, Minimize, Maximize, Restore, and Close windows

### Filesystem Automation
- Create, Rename, Delete, Copy, Move files and folders
- Open specific Workspaces

### Website & Application Automation
- Search Web
- Open URLs
- Open / Close Applications natively

### Desktop Automation
- Mouse movements, clicking, scrolling
- Type text, Hotkey execution

## Technology Stack

- **Python 3.13**
- **Ollama (`gemma3:4b`)**: Local LLM inference.
- **PyWin32 & ctypes**: Native deterministic system controls.
- **psutil**: Process management and Application State Tracking.
- **Pytest**: Over 440 unit and regression tests ensuring 0 regressions.
- **PyAutoGUI**: Legacy desktop interactions (mouse/keyboard).

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Kavi7605/SystemAutomationAssistant.git
   cd SystemAutomationAssistant
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and Configure Ollama:**
   - Download and install [Ollama](https://ollama.com/)
   - Pull the required model:
     ```bash
     ollama pull gemma3:4b
     ```

5. **Set up Environment Variables:**
   - Create a `.env` file in the root directory and add any necessary configuration keys.

## Usage

Start the interactive assistant:
```bash
python main.py
```

### Example Commands:
- "Mute the volume"
- "Set brightness to 50%"
- "Open Discord and focus it"
- "Turn on the mobile hotspot"
- "Put the PC to sleep"

## Testing

The project is fully covered by Pytest, including unit, integration, and regression tests.

To run the complete test suite:
```bash
pytest tests/
```

## Project Structure

```
SystemAutomationAssistant/
├── main.py                 # Application entry point
├── requirements.txt        # Project dependencies
├── src/
│   ├── automation/         # Deterministic routing and execution (engine, executor, router)
│   ├── context/            # Application state and context memory tracking
│   ├── core/               # Command parser, NLP classification, history management
│   ├── llm/                # Ollama client and LLM abstraction
│   ├── planner/            # Task planning and entity resolution
│   ├── tools/              # Core tool definitions and dynamic registry
│   │   ├── system_control/ # Native Windows API implementations for hardware/window control
│   │   └── ...             # Desktop, filesystem, and basic tools
│   ├── utils/              # Helper utilities, logger, browser integration
│   └── voice/              # Speech-to-text components (Whisper, Vosk)
└── tests/                  # Over 440 pytest unit, integration, and regression tests
```

## Current Status

The System Automation Assistant is currently in a stable milestone (Day 17 completion). All core semantic routing, deterministic pipelines, application tracking, and native Window management features have been fully implemented, stabilized, and heavily tested.

## Roadmap

- [ ] Further optimizations to context retention
- [ ] Improved multi-step NLP interpretations
- [ ] Expanded Voice Assistant capability enhancements
- [ ] Web Automation stabilization using Playwright
