#!/usr/bin/env python3
# Cloud LLM API Manager
# This script provides utilities for managing cloud LLM API keys and testing connections

import os
import sys
import json
import argparse
import requests
from typing import Dict, Optional

# Configure paths
CONFIG_DIR = "/app/config"
API_KEYS_FILE = os.path.join(CONFIG_DIR, "api_keys.json")

def load_api_keys() -> Dict[str, str]:
    """Load API keys from config file"""
    if not os.path.exists(API_KEYS_FILE):
        return {"openai": "", "anthropic": ""}
    
    try:
        with open(API_KEYS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading API keys: {e}")
        return {"openai": "", "anthropic": ""}

def save_api_keys(api_keys: Dict[str, str]) -> bool:
    """Save API keys to config file"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(API_KEYS_FILE, "w") as f:
            json.dump(api_keys, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving API keys: {e}")
        return False

def set_api_key(provider: str, api_key: str) -> bool:
    """Set an API key for a specific provider"""
    if provider not in ["openai", "anthropic"]:
        print(f"Invalid provider: {provider}")
        return False
    
    api_keys = load_api_keys()
    api_keys[provider] = api_key
    return save_api_keys(api_keys)

def clear_api_key(provider: str) -> bool:
    """Clear an API key for a specific provider"""
    if provider not in ["openai", "anthropic"]:
        print(f"Invalid provider: {provider}")
        return False
    
    api_keys = load_api_keys()
    api_keys[provider] = ""
    return save_api_keys(api_keys)

def test_openai_api(api_key: Optional[str] = None) -> bool:
    """Test OpenAI API connection"""
    if not api_key:
        api_keys = load_api_keys()
        api_key = api_keys.get("openai", "")
    
    if not api_key:
        print("OpenAI API key not configured")
        return False
    
    try:
        import openai
        openai.api_key = api_key
        
        # Test with a simple completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        print("OpenAI API test successful")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"OpenAI API test failed: {e}")
        return False

def test_anthropic_api(api_key: Optional[str] = None) -> bool:
    """Test Anthropic API connection"""
    if not api_key:
        api_keys = load_api_keys()
        api_key = api_keys.get("anthropic", "")
    
    if not api_key:
        print("Anthropic API key not configured")
        return False
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test with a simple completion
        response = client.completions.create(
            prompt="\n\nHuman: Hello, this is a test.\n\nAssistant:",
            model="claude-instant-1",
            max_tokens_to_sample=10
        )
        
        print("Anthropic API test successful")
        print(f"Response: {response.completion}")
        return True
    except Exception as e:
        print(f"Anthropic API test failed: {e}")
        return False

def test_local_llm_api() -> bool:
    """Test local LLM API connection"""
    try:
        response = requests.post(
            "http://localhost:8080/generate",
            json={
                "prompt": "Hello, this is a test.",
                "max_tokens": 10,
                "model_preference": "local"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Local LLM API test successful")
            print(f"Response: {data['text']}")
            return True
        else:
            print(f"Local LLM API test failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Local LLM API test failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Cloud LLM API Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Set API key command
    set_parser = subparsers.add_parser("set", help="Set an API key")
    set_parser.add_argument("provider", choices=["openai", "anthropic"], help="Provider name")
    set_parser.add_argument("api_key", help="API key")
    
    # Clear API key command
    clear_parser = subparsers.add_parser("clear", help="Clear an API key")
    clear_parser.add_argument("provider", choices=["openai", "anthropic"], help="Provider name")
    
    # Test API connection command
    test_parser = subparsers.add_parser("test", help="Test API connection")
    test_parser.add_argument("provider", choices=["openai", "anthropic", "local", "all"], help="Provider to test")
    
    # List API keys command
    subparsers.add_parser("list", help="List configured API keys")
    
    args = parser.parse_args()
    
    if args.command == "set":
        if set_api_key(args.provider, args.api_key):
            print(f"{args.provider} API key set successfully")
        else:
            print(f"Failed to set {args.provider} API key")
    
    elif args.command == "clear":
        if clear_api_key(args.provider):
            print(f"{args.provider} API key cleared successfully")
        else:
            print(f"Failed to clear {args.provider} API key")
    
    elif args.command == "test":
        if args.provider == "openai":
            test_openai_api()
        elif args.provider == "anthropic":
            test_anthropic_api()
        elif args.provider == "local":
            test_local_llm_api()
        elif args.provider == "all":
            test_openai_api()
            test_anthropic_api()
            test_local_llm_api()
    
    elif args.command == "list":
        api_keys = load_api_keys()
        print("Configured API keys:")
        for provider, key in api_keys.items():
            if key:
                print(f"  {provider}: {key[:4]}...{key[-4:] if len(key) > 8 else ''}")
            else:
                print(f"  {provider}: Not configured")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
