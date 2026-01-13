#!/usr/bin/env python3
"""
NANDA - Custom Message Improvement for Agent Bridge
- Accepts any custom improvement logic function
- Creates agent_bridge server with custom improve_message_direct
"""

import os
import sys
import subprocess
import time
import signal
import requests
import random
import threading

# Handle different import contexts
try:
    from .agent_bridge import *
    from . import run_ui_agent_https
    from .llm_providers import init_provider
except ImportError:
    # If running from parent directory, add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from agent_bridge import *
    import run_ui_agent_https
    from llm_providers import init_provider

class NANDA:
    """NANDA class to create agent_bridge with custom improvement logic"""
    
    def __init__(self, improvement_logic):
        """
        Initialize NANDA with custom improvement logic
        
        Args:
            improvement_logic: Function that takes (message_text: str) -> str
        """
        self.improvement_logic = improvement_logic
        self.bridge = None
        print(f"🤖 NANDA initialized with custom improvement logic: {improvement_logic.__name__}")
        
        # Register the custom improvement logic
        self.register_custom_improver()
        
        # Create agent bridge with custom logic
        self.create_agent_bridge()
    
    def register_custom_improver(self):
        """Register the custom improvement logic with agent_bridge"""
        register_message_improver("nanda_custom", self.improvement_logic)
        print(f"🔧 Custom improvement logic '{self.improvement_logic.__name__}' registered")
    
    def create_agent_bridge(self):
        """Create AgentBridge with custom improvement logic"""
        # Create standard AgentBridge
        self.bridge = AgentBridge()
        
        # Set custom improver as active (replaces improve_message_direct)
        self.bridge.set_message_improver("nanda_custom")
        print(f"✅ AgentBridge created with custom improve_message_direct: {self.improvement_logic.__name__}")
    
    def start_server(self):
        """Start the agent_bridge server with custom improvement logic"""
        print("🚀 NANDA starting agent_bridge server with custom logic...")
        
        # Register with the registry if PUBLIC_URL is set
        public_url = os.getenv("PUBLIC_URL")
        api_url = os.getenv("API_URL")
        agent_id = os.getenv("AGENT_ID")

        ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") 
        AGENT_ID = os.getenv("AGENT_ID", "default")  # Default to 'default' if not specified
        PORT = int(os.getenv("PORT", "6000"))
        TERMINAL_PORT = int(os.getenv("TERMINAL_PORT", "6010"))


        UI_MODE = os.getenv("UI_MODE", "true").lower() in ("true", "1", "yes", "y")
        UI_CLIENT_URL = os.getenv("UI_CLIENT_URL", "")
        print(f"🔧 UI_CLIENT_URL: {UI_CLIENT_URL}")

        # os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
        # os.environ["AGENT_ID"] = AGENT_ID
        # os.environ["PORT"] = str(PORT)
        # os.environ["PUBLIC_URL"] = public_url
        # os.environ['API_URL'] = api_url
        # os.environ["REGISTRY_URL"] = run_ui_agent_https.get_registry_url()
        # os.environ["UI_MODE"] = "true"
        # os.environ["UI_CLIENT_URL"] = f"{api_url}/api/receive_message"

        if public_url:
            register_with_registry(agent_id, public_url, api_url)
        else:
            print("WARNING: PUBLIC_URL environment variable not set. Agent will not be registered.")
        

        # Start the server
        IMPROVE_MESSAGES = os.getenv("IMPROVE_MESSAGES", "true").lower() in ("true", "1", "yes", "y")
        
        print(f"\n🚀 Starting Agent {AGENT_ID} bridge on port {PORT}")
        print(f"Agent terminal port: {TERMINAL_PORT}")
        print(f"Message improvement feature is {'ENABLED' if IMPROVE_MESSAGES else 'DISABLED'}")
        print(f"Logging conversations to {os.path.abspath(LOG_DIR)}")
        print(f"🔧 Using custom improvement logic: {self.improvement_logic.__name__}")
        
        # Run the agent bridge server
        run_server(self.bridge, host="0.0.0.0", port=PORT) 

    def start_server_api(self, anthropic_key=None, domain=None, agent_id=None, port=6000, api_port=6001, 
                        registry=None, public_url=None, api_url=None, cert=None, key=None, ssl=True,
                        llm_provider=None, llm_model=None, llm_api_key=None):
        """
        Start NANDA API server using run_ui_agent_https module
        
        Args:
            anthropic_key (str): Anthropic API key (used if llm_provider is 'anthropic' or None)
            domain (str): Domain name for the server
            agent_id (str): Agent ID (default: auto-generated based on domain)
            port (int): Agent bridge port (default: 6000)
            api_port (int): Flask API port (default: 6001)
            registry (str): Registry URL (optional)
            public_url (str): Public URL for the Agent Bridge (optional)
            api_url (str): API URL for the User Client (optional)
            cert (str): Path to SSL certificate file (optional, defaults to Let's Encrypt path)
            key (str): Path to SSL key file (optional, defaults to Let's Encrypt path)
            ssl (bool): Enable SSL (default: True, uses Let's Encrypt certificates)
            llm_provider (str): LLM provider to use - 'anthropic' (default) or 'huggingface'
            llm_model (str): Model name/ID to use (optional, uses provider default)
            llm_api_key (str): API key for the LLM provider (optional, overrides anthropic_key for non-anthropic providers)
        """
        # Initialize the LLM provider
        effective_provider = llm_provider or "anthropic"
        effective_api_key = llm_api_key if llm_api_key else anthropic_key
        
        print(f"🔧 Initializing LLM provider: {effective_provider}")
        if llm_model:
            print(f"🔧 Using model: {llm_model}")
        
        init_provider(
            provider_name=effective_provider,
            api_key=effective_api_key,
            model=llm_model
        )
        # Get the server IP address (assumes a public IP)
        def get_server_ip():
            """Get the public IP address of the server"""
            try:
                print("🌐 Detecting server IP address...")
                # Try first method
                response = requests.get("http://checkip.amazonaws.com", timeout=10)
                if response.status_code == 200:
                    server_ip = response.text.strip()
                    print(f"✅ Detected server IP: {server_ip}")
                    return server_ip
            except Exception as e:
                print(f"⚠️ First IP detection method failed: {e}")
            
            try:
                # Try second method
                response = requests.get("http://ifconfig.me", timeout=10)
                if response.status_code == 200:
                    server_ip = response.text.strip()
                    print(f"✅ Detected server IP (fallback): {server_ip}")
                    return server_ip
            except Exception as e:
                print(f"⚠️ Second IP detection method failed: {e}")
            
            # If both methods fail, use localhost
            server_ip = "localhost"
            print(f"⚠️ Could not determine IP automatically, using default: {server_ip}")
            return server_ip
        
        # Set up signal handlers for cleanup
        def cleanup(signum=None, frame=None):
            """Clean up processes on exit"""
            print("Cleaning up processes...")
            if hasattr(run_ui_agent_https, 'bridge_process') and run_ui_agent_https.bridge_process:
                run_ui_agent_https.bridge_process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)
        
        # Get server IP
        server_ip = get_server_ip()
        
        # Set default agent ID if not provided
        if not agent_id:
            # Generate 6-digit random number
            random_number = random.randint(100000, 999999)
            
            # Check domain pattern for agent naming
            if "nanda-registry.com" in domain:
                agent_id = f"agentm{random_number}"
            else:
                agent_id = f"agents{random_number}"
            
            print(f"🤖 Auto-generated agent ID: {agent_id}")
        
        # Set global variables in run_ui_agent_https module
        run_ui_agent_https.agent_id = agent_id
        run_ui_agent_https.agent_port = port
        run_ui_agent_https.registry_url = registry
        
        # Set default URLs if not provided
        if not public_url:
            public_url = f"http://{server_ip}:{port}"
            print(f"🔗 Auto-generated public URL: {public_url}")
        
        if not api_url:
            protocol = "https" if ssl else "http"
            api_url = f"{protocol}://{domain}:{api_port}"
        
        # Set environment variables for the agent bridge (same as run_ui_agent_https main())
        # Only set ANTHROPIC_API_KEY if it's provided (not needed for other providers)
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        os.environ["AGENT_ID"] = agent_id
        os.environ["PORT"] = str(port)
        os.environ["PUBLIC_URL"] = public_url
        os.environ['API_URL'] = api_url
        os.environ["REGISTRY_URL"] = run_ui_agent_https.get_registry_url()
        os.environ["UI_MODE"] = "true"
        os.environ["UI_CLIENT_URL"] = f"{api_url}/api/receive_message"
        
        # Create unique log directories for each agent
        log_dir = f"logs_{agent_id}"
        os.makedirs(log_dir, exist_ok=True)
        os.environ["LOG_DIR"] = log_dir
        
        # Open log file
        log_file = open(f"{log_dir}/bridge_run.txt", "a")
        
        # Start the agent bridge using the start_server method in a separate thread
        def start_bridge_server():
            """Start the bridge server in a separate thread"""
            print(f"🚀 Starting agent bridge for {agent_id} on port {port}...")
            self.start_server()
        
        # Start the bridge server in a non-daemon thread
        bridge_thread = threading.Thread(target=start_bridge_server, daemon=False)
        bridge_thread.start()
        
        # Give the bridge a moment to start
        time.sleep(2)
        
        # Print server information
        print("\n" + "="*50)
        print(f"🤖 Agent {agent_id} is running")
        print(f"🌐 Server IP: {server_ip}")
        print(f"Agent Bridge URL: http://localhost:{port}/a2a")
        print(f"Public Client API URL: {public_url}")
        print("="*50)
        print("\n📡 API Endpoints:")
        print(f"  GET  {api_url}/api/health - Health check")
        print(f"  POST {api_url}/api/send - Send a message to the client")
        print(f"  GET  {api_url}/api/agents/list - List all registered agents")
        print(f"  POST {api_url}/api/receive_message - Receive a message from agent")
        print(f"  GET  {api_url}/api/render - Get the latest message")
        print("\n🛑 Press Ctrl+C to stop all processes.")
        
        # Configure SSL context if needed
        ssl_context = None
        if ssl:
            # Set default certificate paths from current folder if not provided
            if not cert or not key:
                cert = "./fullchain.pem"
                key = "./privkey.pem"
                print(f"🔒 Using certificates from current folder: cert={cert}, key={key}")
            
            if os.path.exists(cert) and os.path.exists(key):
                ssl_context = (cert, key)
                print(f"🔒 Using SSL certificates from: {cert}, {key}")
            else:
                print("❌ ERROR: Certificate files not found at specified paths")
                print(f"Certificate path: {cert}")
                print(f"Key path: {key}")
                print(f"💡 Make sure Let's Encrypt certificates exist for domain: {domain}")
                print(f"💡 You can generate them with: certbot --nginx -d {domain}")
                sys.exit(1)
        
        # Start the Flask API server in a separate thread
        def start_flask_server():
            """Start the Flask API server in a separate thread"""
            try:
                print(f"🚀 Starting Flask API server on port {api_port}...")
                run_ui_agent_https.app.run(
                    host='0.0.0.0', 
                    port=api_port, 
                    threaded=True, 
                    ssl_context=ssl_context
                )
            except Exception as e:
                print(f"❌ Error starting Flask server: {e}")
        
        # Start the Flask server in a non-daemon thread
        flask_thread = threading.Thread(target=start_flask_server, daemon=False)
        flask_thread.start()
        
        # Give the Flask server a moment to start
        time.sleep(2)
        
        print(f"✅ Both servers are now running in background threads")
        print(f"🔧 Agent Bridge: http://localhost:{port}")
        print(f"🔧 Flask API: {'https' if ssl else 'http'}://localhost:{api_port}")
        
        print("🚀 Both servers started successfully!")
        print("📝 Servers are running in background threads")
        print("💡 To run in background, use: python3 script.py &")
        

        print("******************************************************")
        print("You can assign your agent using this link")
        print(f"https://chat39.com?agentId={agent_id}")
        print("******************************************************")
        # Keep the main process alive so threads continue running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            cleanup()
