# BuildSystem Running

A multi-agent code generation system that combines multiple specialized AI models to produce high-quality code solutions. The system uses a coordinator to manage independent coding agents, each bringing their own strengths to the task.

## Features

- Multiple specialized coding agents:
  - DeepSeek (deepseek-coder) - Code generation
  - Claude (claude-3-haiku) - Code analysis
  - Hermes (llama-3.1) - Solution generation
  - Liquid (lfm-40b) - Alternative approaches
- GPT-3.5-Turbo coordinator for:
  - Task planning
  - Solution review
  - Final recommendations
- Web search integration via Tavily API
- OpenAI-compatible API for easy integration
- Streaming responses for real-time feedback

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Scruff-AI/BuildSystem-Running.git
cd BuildSystem-Running
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
# Copy template
cp .env.template .env

# Add your API keys to .env:
OPENAI_API_KEY=     # For coordinator
ANTHROPIC_API_KEY=  # For Claude
DEEPSEEK_API_KEY=   # For DeepSeek
OPENROUTER_API_KEY= # For Hermes/Liquid
TAVILY_API_KEY=     # For web search
```

5. Start the server:
```bash
# Windows
.\start_server.ps1

# Linux/Mac
python src/standalone_server.py
```

## Usage with Cline

1. Configure Cline in VSCode:
- API Provider: OpenAI Compatible
- Base URL: http://localhost:3000
- API Key: sk-DQppd0KyYa4yWIgsFsVRxotAK3b9AWxbsb3OOsf1WjT3BlbkFJRpXkZZW851KA65
- Model: agent-system

2. Use Cline normally:
- The system will:
  1. Plan the solution
  2. Get implementations from each agent
  3. Review the solutions
  4. Provide the best implementation

## System Flow

1. User submits request through Cline
2. Coordinator creates execution plan
3. Each agent generates solution independently
4. Solutions are reviewed and compared
5. Best solution is selected and returned
6. Web search is used when needed for research

## Directory Structure

```
BuildSystem-Running/
├── src/
│   ├── models/          # Model implementations
│   │   ├── _deepseek/  # DeepSeek client
│   │   ├── _claude/    # Claude client
│   │   ├── _hermes/    # Hermes client
│   │   └── _liquid/    # Liquid client
│   ├── core/           # Core system classes
│   ├── utils/          # Utilities
│   └── standalone_server.py
├── .env.template       # Environment template
├── requirements.txt    # Dependencies
├── start_server.ps1    # Windows startup script
└── test_system.py     # System test script
```

## Testing

Run the test script to verify system functionality:
```bash
python test_system.py
```

## Error Handling

The system includes error handling for:
- API failures
- Rate limiting
- Network issues
- Invalid requests

## Logging

System events are logged to help with debugging:
- Request/response details
- Model interactions
- Error information
- Performance metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE for details.
