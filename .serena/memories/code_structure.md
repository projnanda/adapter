# Codebase Structure

## Directory Layout
```
/
├── nanda_adapter/              # Main package
│   ├── __init__.py            # Package exports
│   ├── cli.py                 # Command-line interface
│   ├── core/                  # Core functionality
│   │   ├── nanda.py           # Main NANDA class
│   │   ├── agent_bridge.py    # Communication handling
│   │   ├── mcp_utils.py       # MCP utilities
│   │   └── run_ui_agent_https.py # HTTPS server
│   └── examples/              # Example agents
│       ├── langchain_pirate.py    # LangChain pirate example
│       └── crewai_sarcastic.py    # CrewAI sarcastic example
├── setup.py                   # Package configuration
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

## Core Classes
- **NANDA**: Main class that wraps custom improvement logic
- **AgentBridge**: Handles agent communication and message routing
- **Message Improvers**: Pluggable functions for message transformation

## Entry Points
- Console script: `nanda-adapter` (from CLI)
- Package import: `from nanda_adapter import NANDA`

## Examples Location
- `nanda_adapter/examples/` contains working examples
- `langchain_pirate.py` - Example using LangChain
- `crewai_sarcastic.py` - Example using CrewAI