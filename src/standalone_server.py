"""OpenAI-compatible server integrating multi-agent system."""

import os
import json
import asyncio
from typing import Dict, Optional, List, AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from utils.logging_config import server_logger as logger
from models import (
    DeepSeekChatCompletionClient,
    ClaudeChatCompletionClient,
    HermesChatCompletionClient,
    LiquidChatCompletionClient,
    SystemMessage,
    UserMessage
)
import web_search

# Load environment variables
load_dotenv()

# Constants
API_KEY = "sk-DQppd0KyYa4yWIgsFsVRxotAK3b9AWxbsb3OOsf1WjT3BlbkFJRpXkZZW851KA65"
PORT = 3000

# Model names
MODEL_DEEPSEEK = os.getenv("DEEPSEEK_MODEL", "deepseek-coder")
MODEL_CLAUDE = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
MODEL_HERMES = os.getenv("HERMES_MODEL", "nousresearch/hermes-3-llama-3.1-405b:free")
MODEL_LIQUID = os.getenv("LIQUID_MODEL", "liquid/lfm-40b")

# Agent names
AGENT_DEEPSEEK = "DeepSeek"
AGENT_CLAUDE = "Claude"
AGENT_HERMES = "Hermes"
AGENT_LIQUID = "Liquid"

# SSE constants
SSE_DATA_PREFIX = b"data: "
SSE_NEWLINE = b"\n\n"
SSE_DONE = b"data: [DONE]\n\n"

class AgentSystem:
    """Coordinates multiple AI models for collaborative task solving."""
    
    def __init__(self):
        """Initialize agent system with model clients."""
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Initialize other model clients
        self.models = {
            AGENT_DEEPSEEK: DeepSeekChatCompletionClient(
                model=MODEL_DEEPSEEK,
                api_key=os.getenv("DEEPSEEK_API_KEY")
            ),
            AGENT_CLAUDE: ClaudeChatCompletionClient(
                model=MODEL_CLAUDE,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ),
            AGENT_HERMES: HermesChatCompletionClient(
                model=MODEL_HERMES,
                api_key=os.getenv("OPENROUTER_API_KEY")
            ),
            AGENT_LIQUID: LiquidChatCompletionClient(
                model=MODEL_LIQUID,
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
        }
        
    async def process_task(self, task: str) -> List[str]:
        """Process task using multiple models collaboratively."""
        responses = []
        solutions = {}
        
        try:
            # Get coordinator's plan
            plan = await self._get_coordinator_plan(task)
            responses.append(f"Coordinator's Plan:\n{plan}")
            
            # Process each model in sequence to maintain order
            for model_name, client in self.models.items():
                # Get solution
                solution = await self._get_model_solution(client, task, plan)
                responses.append(f"{model_name}'s Solution:\n{solution}")
                solutions[model_name] = solution
                
                # Get review
                review = await self._get_solution_review(solution)
                responses.append(f"Review of {model_name}'s Solution:\n{review}")
            
            # Generate final review with best solution
            final_review = await self._get_final_review(responses, solutions)
            responses.append(final_review)  # Already includes "Final Review:" prefix
            
            return responses
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            raise
            
    async def _get_coordinator_plan(self, task: str) -> str:
        """Get task execution plan from coordinator."""
        messages = [
            {
                "role": "system",
                "content": "You are a coding task coordinator. Create a plan to solve the given task."
            },
            {
                "role": "user",
                "content": task
            }
        ]
        response = await self._get_completion(messages)
        return response
        
    async def _get_model_solution(self, client, task: str, plan: str) -> str:
        """Get solution from specific model."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert programmer. Implement a solution based on the given task and plan.\n"
                    "Your solution MUST include:\n"
                    '1. A docstring using triple quotes (""")\n'
                    "2. Clear comments explaining the code\n"
                    "3. A complete implementation\n"
                    "4. Example usage\n\n"
                    "Format your solution like this:\n\n"
                    "```python\n"
                    'def function_name(params):\n'
                    '    """Your docstring here."""\n'
                    "    # Your code here\n"
                    "    return result\n"
                    "```"
                )
            },
            {
                "role": "user",
                "content": f"Task: {task}\nPlan: {plan}"
            }
        ]
        response = await self._get_completion(messages, client)
        return response
        
    async def _get_solution_review(self, solution: str) -> str:
        """Get review of a model's solution."""
        messages = [
            {
                "role": "system",
                "content": "You are a code reviewer. Review the given solution for correctness and quality."
            },
            {
                "role": "user",
                "content": solution
            }
        ]
        response = await self._get_completion(messages)
        return response
        
    async def _get_final_review(self, responses: List[str], solutions: Dict[str, str]) -> str:
        """Generate final review of all solutions."""
        # Extract code from DeepSeek's solution
        deepseek_solution = solutions[AGENT_DEEPSEEK]
        code_start = deepseek_solution.find("```python")
        code_end = deepseek_solution.find("```", code_start + 8)
        if code_start >= 0 and code_end >= 0:
            code = deepseek_solution[code_start + 8:code_end].strip()
        else:
            code = deepseek_solution
            
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a technical lead. Review all solutions and provide a final assessment.\n"
                    "Include the best solution's code with docstrings and comments."
                )
            },
            {
                "role": "user",
                "content": "\n".join(responses)
            }
        ]
        review = await self._get_completion(messages)
        
        # Return review with code
        return f"Final Review:\n{review}\n\nRecommended Implementation:\n\n```python\n{code}\n```"
        
    async def _get_completion(self, messages: List[Dict], client=None) -> str:
        """Get completion from specified client or default OpenAI client."""
        try:
            if client is None:
                # Run OpenAI completion in a thread pool since it's not async
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages
                    )
                )
                return response.choices[0].message.content
            else:
                # Convert dict messages to proper Message objects
                msg_objects = []
                for msg in messages:
                    if msg["role"] == "system":
                        msg_objects.append(SystemMessage(content=msg["content"]))
                    elif msg["role"] == "user":
                        msg_objects.append(UserMessage(content=msg["content"], source="user"))
                result = await client.create(msg_objects)
                return result.content
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}")
            raise

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize agent system
agent_system = AgentSystem()

async def stream_generator(response) -> AsyncGenerator[bytes, None]:
    """Generate streaming response in SSE format."""
    try:
        # For agent system responses, stream each part
        if isinstance(response, list):
            for part in response:
                chunk = {
                    "id": "agent-" + os.urandom(12).hex(),
                    "choices": [{
                        "delta": {"content": part + "\n\n"},
                        "finish_reason": None
                    }]
                }
                yield SSE_DATA_PREFIX + json.dumps(chunk).encode() + SSE_NEWLINE
            
            # Send final chunk
            yield SSE_DATA_PREFIX + json.dumps({'choices': [{'finish_reason': 'stop'}]}).encode() + SSE_NEWLINE
            yield SSE_DONE
            return
            
        # For OpenAI responses, stream chunks directly
        for chunk in response:
            chunk_data = chunk.model_dump()
            logger.debug(f"Streaming chunk: {json.dumps(chunk_data)}")
            yield SSE_DATA_PREFIX + json.dumps(chunk_data).encode() + SSE_NEWLINE
        
        # Send final [DONE] marker
        logger.debug("Stream completed")
        yield SSE_DONE
    except Exception as e:
        error_msg = f"Stream error: {e}"
        logger.error(error_msg)
        yield SSE_DATA_PREFIX + json.dumps({'error': str(e)}).encode() + SSE_NEWLINE

@app.post("/chat/completions")
async def chat(request: Request):
    """Handle chat completion requests."""
    try:
        # Check authorization first
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {API_KEY}":
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get request data
        data = await request.json()
        logger.info(f"Received chat request: {json.dumps(data, indent=2)}")
        
        # Check for required fields
        if "messages" not in data:
            raise HTTPException(status_code=422, detail="Missing required field: messages")
        
        # Extract messages and handle content
        messages = []
        for msg in data["messages"]:
            if isinstance(msg["content"], list):
                # Handle structured content
                content = " ".join(item.get("text", "") for item in msg["content"] if item.get("type") == "text")
            else:
                # Handle string content
                content = msg["content"]
            messages.append({
                "role": msg["role"],
                "content": content
            })
        
        logger.debug(f"Processed messages: {json.dumps(messages, indent=2)}")
        
        # Check if using agent system
        if data.get("model") == "agent-system":
            # Process with agent system
            responses = await agent_system.process_task(messages[-1]["content"])
            
            # Handle streaming
            if data.get("stream", False):
                logger.info("Initiating streaming response")
                return StreamingResponse(
                    stream_generator(responses),
                    media_type="text/event-stream"
                )
            
            # Handle non-streaming
            result = {
                "id": "agent-" + os.urandom(12).hex(),
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "\n\n".join(responses)
                    }
                }]
            }
            return JSONResponse(content=result)
        
        # Get response from OpenAI for other models
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai_client.chat.completions.create(
                model=data.get("model", "gpt-3.5-turbo").strip(),
                messages=messages,
                stream=data.get("stream", False)
            )
        )

        # Handle streaming
        if data.get("stream", False):
            logger.info("Initiating streaming response")
            return StreamingResponse(
                stream_generator(response),
                media_type="text/event-stream"
            )

        # Handle non-streaming - convert response to dict
        result = response.model_dump()
        logger.info(f"Sending non-streaming response: {json.dumps(result, indent=2)}")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    logger.info("=" * 60)
    logger.info("Server configuration:")
    logger.info(f"- Base URL: http://localhost:{PORT}")
    logger.info(f"- API Key: {API_KEY}")
    logger.info("- Model ID: agent-system")
    logger.info("=" * 60)
    
    # Also print to console for convenience
    print("\nStarting server...")
    print("=" * 60)
    print("Configure Cline with:")
    print("- API Provider: OpenAI Compatible")
    print(f"- Base URL: http://localhost:{PORT}")
    print(f"- API Key: {API_KEY}")
    print("- Model ID: agent-system")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
