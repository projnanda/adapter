# API Endpoints and Communication

## Flask API Endpoints
When running with `start_server_api()`, these endpoints are available:

### Health and Status
- `GET /api/health` - Health check endpoint
- `GET /api/render` - Get the latest message

### Agent Communication
- `POST /api/send` - Send a message to the agent
- `POST /api/receive_message` - Receive a message from agent
- `GET /api/agents/list` - List all registered agents

### Agent Bridge
- Agent Bridge runs on port 6000 (default)
- Flask API runs on port 6001 (default)
- Agent Bridge URL: `http://localhost:6000/a2a`

## Message Flow
1. Messages sent to agent are processed by improvement logic
2. Improved messages can be sent to other agents using @agent_id syntax
3. Registry system enables agent discovery
4. A2A protocol handles inter-agent communication

## Registration
- Agents automatically register with global registry on startup
- Registration URL: Gets determined from registry_url.txt
- Enrollment link provided in logs for manual registration

## Environment Configuration
- `PUBLIC_URL`: Agent bridge public URL
- `API_URL`: Flask API public URL  
- `UI_CLIENT_URL`: Client callback URL
- `REGISTRY_URL`: Global registry endpoint

## SSL Configuration
- Production mode uses HTTPS with Let's Encrypt certificates
- Development mode uses HTTP on localhost
- Certificate files: `fullchain.pem` and `privkey.pem` in current directory