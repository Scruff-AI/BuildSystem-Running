# BuildSystem_Package

An AI-powered code generation system that combines multiple language models with web search capabilities and persistent memory.

## Features

- **Multi-Model Integration**
  - OpenAI GPT (Coordinator)
  - Claude 3.5 Sonnet
  - DeepSeek Coder
  - Liquid LLM
  - Hermes

- **Web Search Integration**
  - Primary: Tavily API
  - Failover: Brave Search API
  - Parallel search capabilities

- **Persistent Memory**
  - Chat history tracking
  - Code change monitoring
  - Context preservation
  - Memory-aware responses

- **Advanced Logging**
  - Comprehensive logging system
  - Error tracking
  - Request monitoring
  - Log rotation

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
  * "Claude 3.5 Sonnet": Direct Claude access

## Architecture

- **Coordinator Service**: Orchestrates task analysis, model selection, and solution review
- **Search Manager**: Handles web searches with automatic failover
- **Memory Manager**: Maintains persistent storage of conversations and code changes
- **Model Clients**: Specialized clients for each AI model
- **Logging System**: Comprehensive logging with rotation and error tracking

## Directory Structure

```
BuildSystem_Package/
├── src/
│   ├── core/           # Core model types and interfaces
│   ├── models/         # Model-specific implementations
│   ├── web_search.py   # Search functionality
│   └── memory_manager.py # Persistent memory system
├── utils/
│   └── logging_config.py # Logging configuration
├── logs/               # Log files (gitignored)
├── memory/            # Persistent storage (gitignored)
└── start_standalone.ps1 # Server startup script
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details
