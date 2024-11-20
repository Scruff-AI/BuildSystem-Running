# BuildSystem_Package

An AI-powered code generation system that combines multiple language models with web search capabilities and persistent memory.

## Features

- **Multi-Model Integration**
  - OpenAI GPT (Coordinator)
  - Claude 3 Haiku (via Anthropic API)
  - DeepSeek Coder
  - OpenRouter Models:
    * Primary: Gemini Pro, Llama 2 70B
    * Automatic fallback system

- **Web Search Integration**
  - Primary: Tavily API for real-time information
  - Failover: Brave Search API
  - Parallel search capabilities
  - Search result summarization

- **Persistent Memory System**
  - 5GB storage limit with automatic recycling
  - Chat history tracking by conversation ID
  - Code change monitoring with metadata
  - Context preservation across sessions
  - Memory-aware model prompting

- **Advanced Logging**
  - Comprehensive logging system
  - Model interaction tracking
  - Error handling and fallback logging
  - Log rotation and cleanup

## Setup

1. Create and activate virtual environment:
```powershell
python -m venv ai_code_gen_env
.\ai_code_gen_env\Scripts\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r BuildSystem_Package/requirements.txt
```

3. Configure environment variables:
```
# Copy template and fill in your API keys
cp BuildSystem_Package/.env.template BuildSystem_Package/.env
```

4. Start the server:
```powershell
.\BuildSystem_Package\start_standalone.ps1
```

## Usage

Connect to the server using Cline with:
- API Provider: OpenAI Compatible
- Base URL: http://localhost:3000
- Model Options:
  * "agent-system": Full multi-model system with memory
  * "Claude 3 Haiku": Direct Claude access

The system will:
- Analyze tasks using the coordinator
- Search for relevant information if needed
- Get solutions from multiple models
- Write code directly to VSCode
- Maintain context across sessions
- Automatically handle model fallbacks

## Architecture

- **Coordinator Service**: 
  * Task analysis and decomposition
  * Model selection and orchestration
  * Solution review and integration
  * Memory-aware completions

- **Memory Manager**:
  * 5GB storage with automatic cleanup
  * JSON-based persistence
  * Conversation tracking
  * Code change history
  * Context preservation

- **Search Manager**: 
  * Real-time web search
  * Automatic failover
  * Result summarization
  * Memory integration

- **Model Clients**: 
  * Specialized implementations
  * Error handling
  * Automatic retries
  * Fallback mechanisms

## Directory Structure

```
BuildSystem_Package/
├── src/
│   ├── core/           # Core model types and interfaces
│   ├── models/         # Model-specific implementations
│   │   ├── _claude/    # Claude 3 Haiku client
│   │   ├── _deepseek/  # DeepSeek Coder client
│   │   ├── _liquid/    # OpenRouter Liquid client
│   │   └── _hermes/    # OpenRouter Hermes client
│   ├── web_search.py   # Search functionality
│   └── memory_manager.py # Persistent memory system
├── utils/
│   └── logging_config.py # Logging configuration
├── logs/               # Log files (gitignored)
├── memory/            # Persistent storage (gitignored)
└── start_standalone.ps1 # Server startup script
```

## Memory System Details

The memory system maintains three main components:
1. **Chat History** (chat_history.json):
   - Conversations tracked by unique IDs
   - Message history with timestamps
   - Role-based organization (user/assistant)

2. **Code Changes** (code_changes.json):
   - File-based change tracking
   - Change descriptions and timestamps
   - Last 5 changes per file preserved

3. **Context** (context.json):
   - Current session context
   - Search result summaries
   - Cross-conversation references

Memory is automatically recycled when approaching the 5GB limit, preserving:
- Most recent conversations
- Current session code changes
- Essential context information

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details
