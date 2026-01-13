#!/usr/bin/env python3
"""
LLM Provider Abstraction for NANDA Agent Framework

Supports multiple LLM backends:
- Anthropic Claude (default)
- Hugging Face Inference API
"""

import os
import json
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

import sys
sys.stdout.reconfigure(line_buffering=True)


class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def complete(self, prompt: str, system: str = None, max_tokens: int = 512) -> Optional[str]:
        """Generate a completion for the given prompt"""
        raise NotImplementedError
    
    @abstractmethod
    def complete_with_tools(
        self, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]], 
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Generate a completion with tool/function calling support"""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        if not self.api_key:
            print("WARNING: ANTHROPIC_API_KEY not set")
            self.client = None
        else:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    def complete(self, prompt: str, system: str = None, max_tokens: int = 512) -> Optional[str]:
        """Generate a completion using Claude"""
        if not self.client:
            print("Anthropic client not initialized - API key missing")
            return None
        
        try:
            from anthropic import APIStatusError
            
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system:
                kwargs["system"] = system
            
            resp = self.client.messages.create(**kwargs)
            return resp.content[0].text
            
        except APIStatusError as e:
            print(f"Anthropic API error: {e.status_code} {e.message}")
            if "credit balance is too low" in str(e):
                return f"(API credit limit reached): {prompt[:100]}"
            return None
        except Exception as e:
            print(f"Anthropic SDK error: {e}")
            return None
    
    def complete_with_tools(
        self, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]], 
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Generate a completion with tool calling using Claude"""
        if not self.client:
            return {"error": "Anthropic client not initialized"}
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                tools=tools
            )
            return {
                "content": response.content,
                "stop_reason": response.stop_reason,
                "raw": response
            }
        except Exception as e:
            print(f"Anthropic tool call error: {e}")
            return {"error": str(e)}


class HuggingFaceProvider(LLMProvider):
    """Hugging Face Inference API provider"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.model = model or os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
        
        if not self.api_key:
            print("WARNING: HUGGINGFACE_API_KEY not set")
            self.client = None
        else:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(api_key=self.api_key)
    
    @property
    def name(self) -> str:
        return "huggingface"
    
    def complete(self, prompt: str, system: str = None, max_tokens: int = 512) -> Optional[str]:
        """Generate a completion using Hugging Face Inference API"""
        if not self.client:
            print("HuggingFace client not initialized - API key missing")
            return None
        
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"HuggingFace API error: {e}")
            return None
    
    def complete_with_tools(
        self, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]], 
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Generate a completion with tool calling using HuggingFace"""
        if not self.client:
            return {"error": "HuggingFace client not initialized"}
        
        try:
            # Convert Anthropic-style tools to OpenAI-style for HuggingFace
            hf_tools = []
            for tool in tools:
                hf_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {})
                    }
                })
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=hf_tools if hf_tools else None,
                max_tokens=max_tokens
            )
            
            # Convert HuggingFace response to unified format
            content = []
            choice = response.choices[0]
            
            if choice.message.content:
                content.append({
                    "type": "text",
                    "text": choice.message.content
                })
            
            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "input": json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                    })
            
            return {
                "content": content,
                "stop_reason": choice.finish_reason,
                "raw": response
            }
            
        except Exception as e:
            print(f"HuggingFace tool call error: {e}")
            return {"error": str(e)}


# Global provider instance
_current_provider: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    """Get the current LLM provider instance"""
    global _current_provider
    if _current_provider is None:
        # Default to Anthropic
        _current_provider = create_provider("anthropic")
    return _current_provider


def set_provider(provider: LLMProvider):
    """Set the current LLM provider instance"""
    global _current_provider
    _current_provider = provider
    print(f"🔧 LLM Provider set to: {provider.name} (model: {provider.model})")


def create_provider(
    provider_name: str = "anthropic",
    api_key: str = None,
    model: str = None
) -> LLMProvider:
    """
    Create an LLM provider instance
    
    Args:
        provider_name: "anthropic" or "huggingface"
        api_key: API key for the provider
        model: Model name/ID to use
    
    Returns:
        LLMProvider instance
    """
    provider_name = provider_name.lower() if provider_name else "anthropic"
    
    if provider_name == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model)
    elif provider_name in ("huggingface", "hf"):
        return HuggingFaceProvider(api_key=api_key, model=model)
    else:
        print(f"Unknown provider '{provider_name}', defaulting to Anthropic")
        return AnthropicProvider(api_key=api_key, model=model)


def init_provider(
    provider_name: str = None,
    api_key: str = None,
    model: str = None
):
    """
    Initialize and set the global LLM provider
    
    Args:
        provider_name: "anthropic" or "huggingface" (defaults to env LLM_PROVIDER or "anthropic")
        api_key: API key for the provider
        model: Model name/ID to use
    """
    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER", "anthropic")
    
    provider = create_provider(provider_name, api_key, model)
    set_provider(provider)
    return provider
