# NANDA Adapter Agent SDK - Project Overview

## Purpose
The NANDA Adapter Agent SDK is a Python framework that enables developers to create AI agents and make them **persistent**, **discoverable**, and **interoperable** on the global internet. It's part of building an "Open and Vibrant Internet of Agents."

## Key Features
- **Multiple AI Frameworks**: Supports LangChain, CrewAI, and custom logic
- **Multi-protocol Communication**: Built-in universal communication protocol
- **Global Index**: Automatic agent discovery via MIT NANDA Index
- **SSL Support**: Production-ready with Let's Encrypt certificates
- **Agent-to-Agent Communication**: Agents can communicate using @agent_id syntax

## Architecture Components
1. **AgentBridge**: Core communication handler
2. **Message Improvement System**: Pluggable improvement logic for transforming messages
3. **Registry System**: Agent discovery and registration
4. **A2A Communication**: Agent-to-agent messaging protocol
5. **Flask API**: External communication interface

## How It Works
1. Developers create custom improvement logic (functions that transform messages)
2. NANDA wraps this logic into an agent with communication capabilities
3. Agents are registered in a global registry for discovery
4. Agents can communicate with each other through the NANDA protocol
5. Messages are improved/transformed using the custom logic before being sent

## Example Use Cases
- Pirate translator agent (transforms messages to pirate English)
- Professional message improver
- Sarcastic response generator
- Any custom message transformation logic