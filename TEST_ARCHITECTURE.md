# System Automation Assistant - Test Architecture

## Overview
This document defines the testing architecture and conventions for the System Automation Assistant project following the comprehensive Day 10 refactor. The test suite has been heavily optimized for speed, clarity, and modularity by removing duplicate boilerplate and converting all historical classes to standard `pytest` fixtures.

## Directory Structure

```text
tests/
├── automation/       # Tests for core routing, pipeline, and execution systems
├── context/          # Tests for state management and context preservation
├── filesystem/       # Tests for deterministic file and folder operations
├── regression/       # Critical bug fixes and regression prevention
├── tools/            # Unit tests for individual system tools (desktop, web)
├── voice/            # Tests for Whisper transcription and voice integration
├── manual/           # (Ignored by CI) Scripts requiring human interaction/APIs
└── conftest.py       # Centralized test fixtures and application mocks
```

## Core Principles

1. **Feature-Based Ownership**: Tests are organized by feature area (e.g., `automation`, `tools`), not by historical "Day" milestones. Legacy names like `TestDay8Part4` have been eliminated.
2. **Pytest First**: All tests utilize pure `pytest`. Legacy `unittest.TestCase` classes and `setUp()` boilerplate have been fully migrated to use `@pytest.fixture`.
3. **Aggressive Deduplication**: 
   - `AutomationEngine` initialization and component mocking are centralized in `conftest.py`.
   - `ApplicationFinder` global state is strictly managed and injected automatically into every test class via `autouse=True` fixtures to eliminate the 50+ lines of duplicated mock dictionaries found in historical files.
4. **Manual Tests Segmented**: Tests requiring live microphone input (Vosk), physical browser interactions (open_url), or expensive API dependencies (Ollama LLM Planner) are sequestered in `tests/manual/` and ignored by default `pytest` discovery via `pytest.ini`.

## Test Execution

To run the entire automated test suite:

```bash
pytest tests/
```

To run a specific module:

```bash
pytest tests/automation/
```

## Centralized Fixtures (`conftest.py`)

The `conftest.py` file automatically injects standard MagicMocks into any test class:

- `engine`: fully instantiated `AutomationEngine` with mocked internals
- `parser_mock`, `resolver_mock`, `task_planner_mock`, `executor_mock`, `history_manager_mock`
- `_mock_find_app`: Global fallback for `ApplicationFinder` capturing synthetic application definitions (`notepad`, `calculator`, `github`, `vscode`, `steam`, `discord`, `whatsapp`, `lively wallpaper`).

## Regression Tracking

The `tests/regression/` folder contains specific edge cases encountered during development:
- `test_router_regressions.py`: Covers deterministic routing bypass anomalies.
- `test_search_regressions.py`: Covers multi-application classification failures and planner fallbacks.

## Future Coverage Goals

While the current suite achieves 75 passing tests in ~1.04s, the following areas should be targeted for enhanced coverage:
- Error handling integration inside the new `DesktopTools` layer.
- Expanded testing of deeply nested/complex application sequence normalization (`close a and b and open c`).
