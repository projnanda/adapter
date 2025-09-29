# run_agent_ui.py - with Flask API wrapper for multiple HTTPS servers
import os
import subprocess
import time
import requests
import sys
import signal
import argparse
import threading
import json
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from python_a2a import A2AClient, Message, TextContent, MessageRole, Metadata
from queue import Queue
from threading import Event
import ssl
import datetime

sys.stdout.reconfigure(line_buffering=True)

# Global variables
bridge_process = None
registry_url = None
agent_id = None
agent_port = None
app = Flask(__name__)

# Enable CORS with support for credentials
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
    return response

# Message queues for SSE (Server-Sent Events)
# This allows us to push messages to the UI when they arrive
client_queues = {}

def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    global bridge_process
    
    print("Cleaning up processes...")
    if bridge_process:
        bridge_process.terminate()
    
    sys.exit(0)

def get_registry_url():
    """Get the registry URL from file or use default"""
    global registry_url
    
    if registry_url:
        return registry_url
        
    try:
        if os.path.exists("registry_url.txt"):
            with open("registry_url.txt", "r") as f:
                url = f.read().strip()
                print(f"Using registry URL from file: {url}")
                return url
    except Exception as e:
        print(f"Error reading registry URL: {e}")
    
    # Default if file doesn't exist
    print("Registry URL file not found. Using default: https://chat.nanda-registry.com:6900")
    return "https://chat.nanda-registry.com:6900"

def register_agent(agent_id, public_url):
    """Register the agent with the registry"""
    reg_url = get_registry_url()
    try:
        print(f"Registering agent {agent_id} at {public_url}")
        response = requests.post(
            f"{reg_url}/register", 
            json={"agent_id": agent_id, "agent_url": public_url},
            verify=False  # For development with self-signed certs
        )
        if response.status_code == 200:
            print(f"Agent {agent_id} registered successfully")
            return True
        else:
            print(f"Failed to register agent: {response.text}")
            return False
    except Exception as e:
        print(f"Error registering agent: {e}")
        return False

def lookup_agent(agent_id):
    """Look up an agent's URL in the registry"""
    reg_url = get_registry_url()
    try:
        print(f"Looking up agent {agent_id} in registry...")
        response = requests.get(
            f"{reg_url}/lookup/{agent_id}",
            verify=False  # For development with self-signed certs
        )
        if response.status_code == 200:
            agent_url = response.json().get("agent_url")
            print(f"Found agent {agent_id} at URL: {agent_url}")
            return agent_url
        print(f"Agent {agent_id} not found in registry")
        return None
    except Exception as e:
        print(f"Error looking up agent {agent_id}: {e}")
        return None

def add_message_to_queue(client_id, message):
    """Add a message to a client's queue for SSE streaming"""
    if client_id in client_queues:
        client_queues[client_id]['queue'].put(message)
        client_queues[client_id]['event'].set()

# Message handling endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "agent_id": agent_id})

@app.route('/api/send', methods=['POST', 'OPTIONS'])
def send_message():
    """Send a message to the agent bridge and return the response"""

    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        
        # Add required CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        
        for key, value in headers.items():
            response.headers[key] = value
            
        return response

    try:
        data = request.json
        print(f"Incoming Data from FE {data}")
        if not data or 'message' not in data:
            return jsonify({"error": "Missing message in request"}), 400
        
        message_text = data['message']
        conversation_id = data.get('conversation_id')
        client_id = data.get('client_id', 'ui_client')
        comm_mode=data.get("comm_mode","frontend")
        chat_history=data.get("chat_history",[])
        partner_capabilities = data.get("partner_capabilities",[])
        agent_capabilities = data.get("agent_capabilities",[])
        
        # Create metadata for the message
        metadata = {
            'source': 'ui_client',
            'client_id': client_id,
            'comm_mode': comm_mode,
            'chat_history':chat_history,
            'partner_capabilities':partner_capabilities,
            'agent_capabilities':agent_capabilities
        }

        # Create an A2A client to talk to the agent bridge
        # Use HTTP for local communication

        bridge_url = f"http://localhost:{agent_port}/a2a"  # Remove /a2a since A2AClient adds it
        client = A2AClient(bridge_url, timeout=60)
        

        # Send the message to the bridge WITHOUT preprocessing
        # Let the bridge handle "@" commands and "/query" commands
        response = client.send_message(
            Message(
                role=MessageRole.USER,
                content=TextContent(text=message_text),
                conversation_id=conversation_id,
                metadata=Metadata(custom_fields=metadata)
            )
        )
        print(f"Response: {response}")
        # Extract the response from the agent
        if hasattr(response.content, 'text'):
            # Return the response with conversation ID
            return jsonify({
                "response": response.content.text,
                "conversation_id": response.conversation_id,
                "agent_id": agent_id
            })
        else:
            return jsonify({"error": "Received non-text response"}), 500
            
    except Exception as e:
        print(f"Error in /api/send: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agents/list', methods=['GET'])
def list_agents():
    """List all registered clients"""
    reg_url = get_registry_url()
    try:
        # Use clients endpoint if available
        try:
            response = requests.get(
                f"{reg_url}/clients",
                verify=False  # For development with self-signed certs
            )
        except:
            # Fall back to list endpoint
            response = requests.get(
                f"{reg_url}/list",
                verify=False  # For development with self-signed certs
            )
            
        if response.status_code == 200:
            return jsonify(response.json())
        return jsonify({"error": f"Failed to get agent list: {response.text}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/receive_message', methods=['POST'])
def receive_message():
    """Receive a message from the agent bridge and display it"""
    try:
        data = request.json
        message = data.get('message', '')
        from_agent = data.get('from_agent', '')
        conversation_id = data.get('conversation_id', '')
        timestamp = data.get('timestamp', '')
       
        reg_url = get_registry_url()
        sender_name = requests.get(
                f"{reg_url}/sender/{from_agent}",
                verify=False  # For development with self-signed certs
            )
        sender_name = sender_name.json().get("sender_name")

        print("\n--- New message received ---")
        print(f"From: {from_agent}")
        print(f"Message: {message}")
        print(f"Conversation ID: {conversation_id}")
        print(f"Timestamp: {timestamp}")
        print(f"Sender Name: {sender_name}")
        print("----------------------------\n")
        
        # Create a unique file for each agent to avoid conflicts when running multiple agents
        message_file = f"latest_message.json"
        
        # Create a JavaScript snippet that the client can use to display this
        with open(message_file, "w") as f:
            json.dump({
                "message": message,
                "from_agent": from_agent,
                "sender_name": sender_name,
                "conversation_id": conversation_id,
                "timestamp": timestamp
            }, f)
        
        return jsonify({"status": "received"})
    except Exception as e:
        print(f"Error processing received message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/render', methods=['GET'])
def render_on_ui():
    try:
        # Use agent-specific message file
        message_file = f"latest_message.json"
        
        if not os.path.exists(message_file):
            return jsonify({})
        else:
            latest_message = json.load(open(message_file))
            # Remove the original file
            os.remove(message_file)
            return jsonify(latest_message)
    except Exception as e:
        print(f"No latest message found")
        return jsonify({"error": str(e)}), 500


@app.route('/api/messages/stream', methods=['GET'])
def stream_messages():
    """SSE endpoint for streaming messages to UI clients"""
    client_id = request.args.get('client_id')
    if not client_id or client_id not in client_queues:
        return jsonify({"error": "Client not registered"}), 400
    
    def generate():
        client_data = client_queues[client_id]
        queue = client_data['queue']
        event = client_data['event']
        
        # Send any queued messages
        while True:
            # Wait for new messages
            event.wait()
            
            # Get all queued messages
            while not queue.empty():
                message = queue.get()
                yield f"data: {json.dumps(message)}\n\n"
            
            # Reset event
            event.clear()
    
    response = Response(
        stream_with_context(generate()), 
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache', 
            'X-Accel-Buffering': 'no',
            'Content-Type': 'text/event-stream',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )
    return response

def main():
    global bridge_process, registry_url, agent_id, agent_port
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    parser = argparse.ArgumentParser(description="Run an agent with Flask API wrapper")
    parser.add_argument("--id", required=True, help="Agent ID")
    parser.add_argument("--port", type=int, default=6000, help="Agent bridge port (default: 6000)")
    parser.add_argument("--api-port", type=int, default=5000, help="Flask API port (default: 5000)")
    parser.add_argument("--registry", help="Registry URL")
    parser.add_argument("--public-url", help="Public URL for the Agent Bridge")
    parser.add_argument("--api-url", help="Api URL for the User Client")
    parser.add_argument("--cert", help="Path to SSL certificate file")
    parser.add_argument("--key", help="Path to SSL key file")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL with default certificates")
    
    args = parser.parse_args()
    
    # Set global variables
    agent_id = args.id
    agent_port = args.port
    api_port = args.api_port
    registry_url = args.registry
    
    # Determine public URL for registration
    public_url = args.public_url
    api_url = args.api_url
    #if not public_url:
        # Default to the chat domain with the specific API port
        #public_url = f"http://localhost:{port}" 
    
    # Set environment variables for the agent bridge
    os.environ["AGENT_ID"] = agent_id
    os.environ["PORT"] = str(agent_port)
    os.environ["PUBLIC_URL"] = public_url
    os.environ['API_URL'] = api_url
    os.environ["REGISTRY_URL"] = get_registry_url()
    os.environ["UI_MODE"] = "true"
    # Use HTTP for local communication
    os.environ["UI_CLIENT_URL"] = f"{api_url}/api/receive_message" #f"https://chat2.nanda-registry.com:{api_port}/api/receive_message"
    
    # Create unique log directories for each agent
    log_dir = f"logs_{agent_id}"
    os.makedirs(log_dir, exist_ok=True)
    os.environ["LOG_DIR"] = log_dir
    

    log_file = open(f"{log_dir}/bridge_run.txt","a")

    # . the agent bridge
    print(f"Starting agent bridge for {agent_id} on port {agent_port}...")
    bridge_process = subprocess.Popen(["python3", "agent_bridge.py"],stdout=log_file, stderr=log_file)
    
    # Give the bridge a moment to start
    time.sleep(2)

    #api_url = "https://chat2.nanda-registry.com:{api_port}"
    
    # Register the agent (with API URL)
    #register_agent(agent_id, public_url)
    
    print("\n" + "="*50)
    print(f"Agent {agent_id} is running")
    print(f"Agent Bridge URL: http://localhost:{agent_port}/a2a")
    print(f"Public Client API URL: {public_url}")
    print("="*50)
    print("\nAPI Endpoints:")
    print(f"  GET  {api_url}/api/health - Health check")
    print(f"  POST {api_url}/api/send - Send a message to the client")
    print(f"  GET  {api_url}/api/agents/list - List all registered agents")
    print(f"  POST {api_url}/api/receive_message - Receive a message from agent")
    print(f"  GET  {api_url}/api/render - Get the latest message")
    print("\nPress Ctrl+C to stop all processes.")
    
    # Configure SSL context if needed
    ssl_context = None
    if args.ssl:
        if args.cert and args.key:
            # Use provided certificate paths
            if os.path.exists(args.cert) and os.path.exists(args.key):
                ssl_context = (args.cert, args.key)
                print(f"Using SSL certificates from: {args.cert}, {args.key}")
            else:
                print("ERROR: Certificate files not found at specified paths")
                print(f"Certificate path: {args.cert}")
                print(f"Key path: {args.key}")
                sys.exit(1)
        else:
            print("ERROR: SSL enabled but certificate paths not provided")
            print("Please provide --cert and --key arguments")
            sys.exit(1)

    # Start the Flask API server
    app.run(host='0.0.0.0', port=api_port, threaded=True, ssl_context=ssl_context)

if __name__ == "__main__":
    main()
