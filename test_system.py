"""Test script to verify system functionality."""

import os
import json
import asyncio
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

async def test_system():
    """Test the BuildSystem server."""
    print("\nTesting BuildSystem...")
    print("=" * 60)
    
    url = "http://localhost:3000/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-DQppd0KyYa4yWIgsFsVRxotAK3b9AWxbsb3OOsf1WjT3BlbkFJRpXkZZW851KA65"
    }
    data = {
        "model": "agent-system",
        "messages": [
            {
                "role": "user",
                "content": "Write a simple hello world function in Python."
            }
        ],
        "stream": True
    }
    
    try:
        print("Request:")
        print("-" * 40)
        print(f"URL: {url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                url,
                headers=headers,
                json=data,
                timeout=30.0
            ) as response:
                print("\nResponse:")
                print("-" * 40)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("\nStreaming response:")
                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith("data: "):
                                try:
                                    chunk = json.loads(line[6:])
                                    if chunk == "[DONE]":
                                        continue
                                    if "choices" in chunk and chunk["choices"]:
                                        if "delta" in chunk["choices"][0]:
                                            delta = chunk["choices"][0]["delta"]
                                            if "content" in delta:
                                                print(delta["content"], end="", flush=True)
                                except json.JSONDecodeError:
                                    print(f"Error parsing chunk: {line}")
                    print("\n\n✅ Test successful!")
                else:
                    print(f"Error: {response.text}")
                    print("\n❌ Test failed!")
                    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_system())
