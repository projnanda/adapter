#!/usr/bin/env python3
"""
LLM Provider Configuration for NANDA
Supports multiple LLM providers: Anthropic, OpenAI, Google Gemini, Groq, etc.
"""

import os
import traceback
from typing import Optional

def call_llm(prompt: str, system_prompt: str = None) -> Optional[str]:
    """Call the configured LLM provider with the given prompt"""
    
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    model = os.getenv("LLM_MODEL", "")
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "512"))
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    print(f"🤖 Calling {provider.upper()} with prompt: {prompt[:50]}...")
    
    try:
        if provider == "anthropic":
            return _call_anthropic(prompt, system_prompt, model or "claude-3-5-sonnet-20241022", max_tokens, temperature)
        elif provider == "openai":
            return _call_openai(prompt, system_prompt, model or "gpt-4o-mini", max_tokens, temperature)
        elif provider == "gemini":
            return _call_gemini(prompt, system_prompt, model or "gemini-1.5-flash", max_tokens, temperature)
        elif provider == "groq":
            return _call_groq(prompt, system_prompt, model or "llama3-8b-8192", max_tokens, temperature)
        elif provider == "mistral":
            return _call_mistral(prompt, system_prompt, model or "mistral-small-latest", max_tokens, temperature)
        elif provider == "cohere":
            return _call_cohere(prompt, system_prompt, model or "command", max_tokens, temperature)
        elif provider == "grok":
            return _call_grok(prompt, system_prompt, model or "grok-beta", max_tokens, temperature)
        else:
            print(f"❌ Unknown provider: {provider}")
            print("Available providers: anthropic, openai, gemini, groq, mistral, cohere, grok")
            return None
            
    except Exception as e:
        print(f"❌ Error calling {provider}: {e}")
        traceback.print_exc()
        return None

def _call_anthropic(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Anthropic Claude"""
    try:
        from anthropic import Anthropic, APIStatusError
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found")
            return None
        
        client = Anthropic(api_key=api_key)
        system = system_prompt or "You are Claude, an AI assistant."
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            system=system
        )
        
        return response.content[0].text
        
    except APIStatusError as e:
        print(f"❌ Anthropic API error: {e.status_code} {e.message}")
        return None
    except Exception as e:
        print(f"❌ Anthropic error: {e}")
        return None

def _call_openai(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call OpenAI GPT"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return None
        
        client = OpenAI(api_key=api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        return None

def _call_gemini(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Google Gemini"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY not found")
            return None
        
        genai.configure(api_key=api_key)
        
        generation_config = {
            "temperature": temperature,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": max_tokens,
        }
        
        model_obj = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config
        )
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = model_obj.generate_content(full_prompt)
        return response.text
        
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return None

def _call_groq(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Groq"""
    try:
        from groq import Groq
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ GROQ_API_KEY not found")
            return None
        
        client = Groq(api_key=api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Groq error: {e}")
        return None

def _call_mistral(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Mistral"""
    try:
        from mistralai.client import MistralClient
        
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            print("❌ MISTRAL_API_KEY not found")
            return None
        
        client = MistralClient(api_key=api_key)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Mistral error: {e}")
        return None

def _call_cohere(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Cohere"""
    try:
        import cohere
        
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            print("❌ COHERE_API_KEY not found")
            return None
        
        client = cohere.Client(api_key=api_key)
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = client.generate(
            model=model,
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.generations[0].text
        
    except Exception as e:
        print(f"❌ Cohere error: {e}")
        return None

def _call_grok(prompt: str, system_prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Grok/XAI"""
    try:
        import requests
        
        api_key = os.getenv("GROQ_API_KEY")  # Using GROQ_API_KEY for Grok as per your .env setup
        if not api_key:
            print("❌ GROQ_API_KEY not found in environment")
            return None
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Grok API endpoint
        url = "https://api.x.ai/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            print(f"❌ Grok API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Grok error: {e}")
        return None
