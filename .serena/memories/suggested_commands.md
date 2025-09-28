# Development Commands

## Installation Commands
```bash
# Install the package
pip install nanda-adapter

# Install from source (development)
pip install -e .

# Install with optional dependencies
pip install nanda-adapter[langchain]  # For LangChain support
pip install nanda-adapter[crewai]     # For CrewAI support
pip install nanda-adapter[all]        # For all frameworks
```

## Running Agents
```bash
# Run example agents
nanda-pirate              # Simple pirate agent
nanda-pirate-langchain    # LangChain pirate agent
nanda-sarcastic           # CrewAI sarcastic agent

# Run custom agent (example from README)
nohup python3 langchain_pirate.py > out.log 2>&1 &

# Check agent logs
cat out.log
```

## Environment Setup
```bash
# Required environment variables
export ANTHROPIC_API_KEY="your-api-key-here"
export DOMAIN_NAME="your-domain.com"

# Optional variables
export AGENT_ID="custom-agent-id"
export PORT="6000"
export IMPROVE_MESSAGES="true"
```

## SSL Certificate Setup (Production)
```bash
# Generate Let's Encrypt certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to working directory
sudo cp -L /etc/letsencrypt/live/your-domain.com/fullchain.pem .
sudo cp -L /etc/letsencrypt/live/your-domain.com/privkey.pem .
sudo chown $USER:$USER fullchain.pem privkey.pem
chmod 600 fullchain.pem privkey.pem
```

## Development Tools
```bash
# Show help
nanda-adapter --help

# List available examples
nanda-adapter --list-examples
```

## System Commands (macOS/Darwin)
```bash
# Process management
ps aux | grep python        # Find running Python processes
kill -9 <PID>              # Stop a process
lsof -i :6000              # Check what's using port 6000

# File operations
ls -la                     # List files with permissions
find . -name "*.py"        # Find Python files
grep -r "pattern" .        # Search for patterns
```