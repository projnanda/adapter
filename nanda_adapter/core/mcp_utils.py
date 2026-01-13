from typing import Optional
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.stdio import stdio_client
#from custom_transport import insecure_sse_client
from mcp.client.sse import sse_client
import os
import mcp
from mcp.client.streamable_http import streamablehttp_client
import json
import base64

# Handle different import contexts
try:
    from .llm_providers import get_provider
except ImportError:
    from llm_providers import get_provider


import sys
sys.stdout.reconfigure(line_buffering=True)


def parse_jsonrpc_response(response):
    """Helper function to parse JSON-RPC responses from MCP server"""
    if isinstance(response, str):
        try:
            response_json = json.loads(response)
            if isinstance(response_json, dict) and "result" in response_json:
                # Extract text from JSON-RPC structure
                artifacts = response_json["result"].get("artifacts", [])
                if artifacts and len(artifacts) > 0:
                    parts = artifacts[0].get("parts", [])
                    if parts and len(parts) > 0:
                        return parts[0].get("text", str(response))
        except json.JSONDecodeError:
            pass
    return str(response)

class MCPClient:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.provider = get_provider()

    async def connect_to_mcp_and_get_tools(self, mcp_server_url, transport_type="http"):
        """Connect to MCP server and return available tools
        
        Args:
            mcp_server_url: URL of the MCP server
            transport_type: Either 'http' or 'sse' for transport protocol
        """
        try:
            # Create new connection based on transport type
            if transport_type.lower() == "sse":
                transport = await self.exit_stack.enter_async_context(sse_client(mcp_server_url))
                # SSE client returns only 2 values: read_stream, write_stream
                read_stream, write_stream = transport
            else:
                transport = await self.exit_stack.enter_async_context(streamablehttp_client(mcp_server_url))
                # HTTP client returns 3 values: read_stream, write_stream, session
                read_stream, write_stream, _ = transport
            
            # Create new session
            self.session = await self.exit_stack.enter_async_context(
                mcp.ClientSession(read_stream, write_stream)
            )
            await self.session.initialize()
            
            # Get tools
            tools_result = await self.session.list_tools()
            return tools_result.tools
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")
            return None

    async def process_query(self, query, mcp_server_url, transport_type="http"):
        try:
            print(f"In MCP_utils process query: {query} on {mcp_server_url} using {transport_type}")
            # Connect and get tools
            tools = await self.connect_to_mcp_and_get_tools(mcp_server_url, transport_type)
            if not tools:
                return "Failed to connect to MCP server"

            available_tools = [{
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            } for tool in tools]

            # Initialize message history
            messages = [{"role": "user", "content": query}]
            
            # Use the provider abstraction for tool calling
            provider = self.provider
            print(f"Using LLM provider: {provider.name}")
            
            response = provider.complete_with_tools(messages, available_tools, max_tokens=1024)
            
            if "error" in response:
                return f"LLM Error: {response['error']}"
            
            # Keep processing until we get a final response without tool calls
            while True:
                has_tool_calls = False
                content = response.get("content", [])
                
                # Handle different content formats (Anthropic raw vs unified)
                if hasattr(content, '__iter__') and not isinstance(content, (str, dict)):
                    blocks = content
                else:
                    blocks = [content] if content else []
                
                # Process each block in the response
                for block in blocks:
                    # Handle both dict format and object format
                    if isinstance(block, dict):
                        block_type = block.get("type", "text")
                        block_id = block.get("id", "")
                        block_name = block.get("name", "")
                        block_input = block.get("input", {})
                        block_text = block.get("text", "")
                    else:
                        block_type = getattr(block, "type", "text")
                        block_id = getattr(block, "id", "")
                        block_name = getattr(block, "name", "")
                        block_input = getattr(block, "input", {})
                        block_text = getattr(block, "text", "")
                    
                    print(f"Block type: {block_type}")
                    
                    if block_type == "tool_use":
                        has_tool_calls = True
                        tool_name = block_name
                        tool_args = block_input
                        
                        # Call the tool
                        result = await self.session.call_tool(tool_name, tool_args)
                        print("Raw tool result: ", result)
                        
                        # Parse the result
                        processed_result = parse_jsonrpc_response(result)
                        print("Processed tool result: ", str(processed_result)[:100])
                        
                        # Add the assistant's message with tool use
                        messages.append({
                            "role": "assistant",
                            "content": [{
                                "type": "tool_use",
                                "id": block_id,
                                "name": tool_name,
                                "input": tool_args
                            }]
                        })
                        
                        # Add the tool result
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block_id,
                                "content": str(processed_result)
                            }]
                        })
                
                # If no tool calls were made, we have our final response
                if not has_tool_calls:
                    break
                    
                print(f"Getting next response from {provider.name}...")
                response = provider.complete_with_tools(messages, available_tools, max_tokens=1024)
                
                if "error" in response:
                    return f"LLM Error: {response['error']}"
                
                print(f"Response: {response}")
            
            # Return the final response
            final_response = ""
            content = response.get("content", [])
            
            if hasattr(content, '__iter__') and not isinstance(content, (str, dict)):
                blocks = content
            else:
                blocks = [content] if content else []
            
            for block in blocks:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        final_response += block.get("text", "") + "\n"
                else:
                    if getattr(block, "type", "") == "text":
                        final_response += getattr(block, "text", "") + "\n"
            
            return parse_jsonrpc_response(final_response.strip()) if final_response else "No response generated"
            
        except Exception as e:
            print(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exit_stack.aclose()
        self.session = None

# Example usage