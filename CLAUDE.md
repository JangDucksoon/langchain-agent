# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangChain-based AI agent application that provides an interactive chat interface with tool-calling capabilities. The agent can perform web searches, file operations, and time zone queries through a conversational Korean interface.

## Key Architecture Components

- **Agent Framework**: Uses LangChain's `create_tool_calling_agent` with `ChatOllama` model (`gpt-oss:20b`)
- **Memory Management**: Implements persistent chat history per session using `InMemoryChatMessageHistory`
- **Tool Integration**: Five core tools for web search, file operations, and time queries
- **Callback System**: Custom logging callback that writes conversation history to `history.txt`
- **Event Streaming**: Real-time display of agent reasoning steps when `show_think=True`

## Core Tools Available

1. **TavilySearch** - Web search with max 5 results
2. **get_current_time_by_country** - Time zone queries (timezone parameter required)
3. **find_files_in_directory** - List files in specified directory
4. **read_file** - Read file contents as list of lines
5. **write_file** - Write content to file (file_path, contents, mode parameters)
6. **delete_file** - Delete specified file

## Running the Application

```bash
python main.py
```

## Built-in Commands

The application supports several slash commands:
- `/exit` or `exit` - Exit the application
- `/clear` or `clear` - Clear console screen
- `/history` or `history` - Display conversation history
- `/reset` or `reset` - Clear session memory
- `/lang <language>` - Change response language (default: Korean)
- `/think <True|False>` - Toggle step-by-step reasoning display

## Dependencies Installation

```bash
pip install -r requirements.txt
```

Key dependencies include:
- `langchain==0.3.27`
- `langchain-ollama==0.3.6`
- `langchain-tavily==0.2.11`
- `ollama==0.5.3`

## Important Configuration Notes

- **API Key**: Tavily search requires API key (currently embedded in code at main.py:63)
- **Model**: Uses Ollama model `gpt-oss:20b` - ensure this model is available
- **Language**: Default prompt language is Korean, configurable via `/lang` command
- **Session Management**: Each session gets unique UUID for memory isolation

## Code Organization

- `main.py` - Entry point with agent setup and command loop
- `callback/` - Custom callback handlers for logging
- `command/` - Console utilities and history management
- `tools/` - Tool implementations for file system and time operations
- `util/` - Utility functions for event printing and history logging
- `history.txt` - Persistent conversation log (auto-generated)

## Development Notes

- The agent prompt includes strict rules against duplicate tool calls
- Web searches automatically get current time context
- File operations use UTF-8 encoding
- Error handling is implemented for all tool operations
- The system maintains conversation context across interactions within a session