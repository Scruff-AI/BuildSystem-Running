"""OpenAI-compatible server integrating multi-agent system."""

import os
import json
import asyncio
import socket
from typing import Dict, Optional, List, AsyncGenerator, Tuple, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from utils.logging_config import server_logger as logger
from src.web_search import search
from src.memory_manager import MemoryManager
from src.models import (
    DeepSeekChatCompletionClient,
    ClaudeChatCompletionClient,
    LiquidChatCompletionClient,
    HermesChatCompletionClient
)
from src.core.models import SystemMessage, UserMessage

# Load environment variables
load_dotenv()

# Constants
API_KEY = os.getenv('LOCAL_API_KEY')
DEFAULT_PORT = int(os.getenv('PORT', 3000))
GPT_MODEL = "gpt-4-turbo"
MODEL_DEEPSEEK = os.getenv('DEEPSEEK_MODEL', 'deepseek-coder')
MODEL_CLAUDE = os.getenv('CLAUDE_MODEL', 'claude-3-haiku-20240307')
MODEL_LIQUID = os.getenv('LIQUID_MODEL', 'liquid/lfm-40b')
MODEL_HERMES = os.getenv('HERMES_MODEL', 'nousresearch/hermes-3-llama-3.1-405b:free')

# SSE constants
SSE_DATA_PREFIX = b"data: "
SSE_NEWLINE = b"\n\n"
SSE_DONE = b"data: [DONE]\n\n"

def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return port
            except socket.error:
                continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

# Find available port
PORT = find_available_port(DEFAULT_PORT)

# Initialize Claude client
claude_client = ClaudeChatCompletionClient(
    model="Claude 3.5 Sonnet",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

class RequestHandler:
    """Handles API request processing and validation."""
    
    @staticmethod
    def validate_request(request: Request, data: Dict) -> None:
        """Validate request headers and data."""
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {API_KEY}":
            raise HTTPException(status_code=401, detail="Invalid API key")
            
        if "messages" not in data:
            raise HTTPException(status_code=422, detail="Missing required field: messages")
    
    @staticmethod
    def process_message_content(messages: List[Dict]) -> List[Dict]:
        """Process and validate message content."""
        processed = []
        for msg in messages:
            if isinstance(msg["content"], list):
                # Handle structured content
                content = " ".join(item.get("text", "") 
                                 for item in msg["content"] 
                                 if item.get("type") == "text")
            else:
                content = msg["content"]
            processed.append({"role": msg["role"], "content": content})
        return processed
    
    @staticmethod
    async def handle_agent_system(messages: List[Dict], stream: bool) -> Any:
        """Handle agent-system model requests."""
        response_gen = agent_system.process_task(messages)
        
        if stream:
            logger.info("Initiating streaming response")
            return StreamingResponse(
                stream_generator(response_gen),
                media_type="text/event-stream"
            )
        
        # Collect responses for non-streaming requests
        responses = []
        async for response in response_gen:
            responses.append(response)
        
        return JSONResponse(content={
            "id": "agent-" + os.urandom(12).hex(),
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "".join(responses)
                }
            }]
        })
    
    @staticmethod
    async def handle_claude(messages: List[Dict], stream: bool) -> Any:
        """Handle Claude model requests."""
        msg_objects = [
            SystemMessage(content=msg["content"]) if msg["role"] == "system"
            else UserMessage(content=msg["content"], source="user")
            for msg in messages
        ]
        
        result = await claude_client.create(msg_objects)
        
        if stream:
            return StreamingResponse(
                stream_generator(result),
                media_type="text/event-stream"
            )
        
        return JSONResponse(content={
            "id": "claude-" + os.urandom(12).hex(),
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": result.content
                }
            }]
        })

class CoordinatorService:
    """Handles coordinator (GPT) interactions with persistent memory."""
    
    def __init__(self, api_key: str):
        """Initialize coordinator with OpenAI client and memory manager."""
        self.coordinator = OpenAI(api_key=api_key)
        self.memory = MemoryManager()
        
    def _prepare_messages_with_memory(self, messages: List[Dict], conversation_id: str) -> List[Dict]:
        """Prepare messages with memory context."""
        memory_context = self.memory.format_memory_for_prompt(conversation_id)
        
        # Add memory context to system message
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] = f"{memory_context}\n\n{messages[0]['content']}"
        else:
            messages.insert(0, {
                "role": "system",
                "content": memory_context
            })
            
        return messages
        
    async def get_completion(self, messages: List[Dict], conversation_id: str) -> str:
        """Get completion from coordinator with memory context."""
        messages_with_memory = self._prepare_messages_with_memory(messages, conversation_id)
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.coordinator.chat.completions.create(
                model=GPT_MODEL,
                messages=messages_with_memory
            )
        )
        
        content = response.choices[0].message.content
        self.memory.store_message(conversation_id, "assistant", content)
        return content
        
    async def analyze_task(self, task: str, conversation_id: str) -> str:
        """Get task analysis with memory context."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a task coordinator with web search capabilities and perfect memory. "
                    "You have access to the complete conversation history and code changes through the memory system. "
                    "When analyzing tasks, you can and should use web search for any queries requiring "
                    "current information, technical documentation, or specific details. "
                    "\n\nFor simple questions, respond with 'SIMPLE_QUESTION'. "
                    "For coding tasks, provide detailed analysis including requirements, constraints, and helpful context. "
                    "Reference relevant past interactions and code changes when applicable. "
                    "\n\nYou have access to Tavily and Brave search APIs - use them whenever relevant information "
                    "might be found online. Don't state that you can't perform searches - you can and should "
                    "use the search capability when appropriate."
                )
            },
            {"role": "user", "content": task}
        ]
        
        self.memory.store_message(conversation_id, "user", task)
        return await self.get_completion(messages, conversation_id)
        
    async def summarize_search(self, results: List[Dict], conversation_id: str) -> str:
        """Summarize search results with memory context."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a search results summarizer with perfect memory. "
                    "Given a list of search results, extract and summarize the most relevant information. "
                    "Focus on key facts, recent developments, and important details. "
                    "Include specific technical details when present, as they may be crucial for coding tasks. "
                    "Consider the conversation history and previous code changes when determining relevance."
                )
            },
            {"role": "user", "content": json.dumps(results, indent=2)}
        ]
        
        summary = await self.get_completion(messages, conversation_id)
        self.memory.update_context({"latest_search_summary": summary})
        return summary
        
    async def review_solution(self, solution: str, conversation_id: str) -> str:
        """Review and approve solution with memory context."""
        messages = [
            {
                "role": "system",
                "content": (
                    "Review the solution with perfect memory of all previous interactions and code changes. "
                    "Consider correctness, efficiency, and best practices. "
                    "If the solution references search results or previous code changes, verify that "
                    "the information has been properly incorporated. "
                    "Reference relevant past decisions and changes in your review."
                )
            },
            {"role": "user", "content": solution}
        ]
        
        review = await self.get_completion(messages, conversation_id)
        self.memory.store_code_change(
            file_path="solution_review",
            content=solution,
            description=review
        )
        return review

    async def write_code_to_vscode(self, code: str, filename: str = "temp_content.txt") -> None:
        """Write code directly to VSCode."""
        try:
            with open(filename, 'w') as f:
                f.write(code)
            logger.info(f"Code written to {filename}")
        except Exception as e:
            logger.error(f"Error writing code to VSCode: {str(e)}")
            raise

class AgentSystem:
    """Coordinates multiple AI models for collaborative task solving."""
    
    def __init__(self):
        """Initialize agent system with model clients."""
        self.coordinator = CoordinatorService(api_key=os.getenv("OPENAI_API_KEY"))
        self.coders = self._initialize_coders()
        
    def _initialize_coders(self) -> Dict:
        """Initialize coding agents."""
        return {
            "deepseek": DeepSeekChatCompletionClient(
                model=MODEL_DEEPSEEK,
                api_key=os.getenv("DEEPSEEK_API_KEY")
            ),
            "claude": claude_client,
            "liquid": LiquidChatCompletionClient(
                model=MODEL_LIQUID,
                api_key=os.getenv("OPENROUTER_API_KEY")
            ),
            "hermes": HermesChatCompletionClient(
                model=MODEL_HERMES,
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
        }
        
    async def _get_search_info(self, task: str, conversation_id: str) -> Tuple[str, bool]:
        """Get search information if needed."""
        needs_search = any(word in task.lower() 
                        for word in ["latest", "current", "news", "recent", "search", "find", "look up", "how to", "what is", "documentation"])
        
        if not needs_search:
            return "", False
            
        try:
            search_results = await search(task)
            if not search_results:
                return "", False
                
            formatted_results = [
                {
                    "title": result.get("title", ""),
                    "content": result.get("content", "").strip(),
                    "url": result.get("url", "")
                }
                for result in search_results
            ]
            
            search_info = await self.coordinator.summarize_search(formatted_results, conversation_id)
            return search_info, True
            
        except Exception as e:
            logger.warning(f"Web search failed: {str(e)}")
            return "", False
            
    async def _get_coder_solutions(self, context_messages: List[Dict]) -> Dict[str, str]:
        """Get solutions from all coders."""
        solutions = {}
        for name, coder in self.coders.items():
            try:
                msg_objects = [
                    SystemMessage(content=msg["content"]) if msg["role"] == "system"
                    else UserMessage(content=msg["content"], source="user")
                    for msg in context_messages
                ]
                result = await coder.create(msg_objects)
                solutions[name] = result.content
                
                # Write code solution to VSCode
                if "```" in result.content:
                    code = result.content.split("```")[1].strip()
                    if code.startswith("python"):
                        code = code[6:].strip()
                    await self.coordinator.write_code_to_vscode(code)
                
                # Store code changes in memory
                self.coordinator.memory.store_code_change(
                    file_path=f"{name}_solution",
                    content=result.content,
                    description=f"Solution generated by {name}"
                )
            except Exception as e:
                logger.error(f"Error getting {name} solution: {str(e)}")
                solutions[name] = f"Error: {str(e)}"
        return solutions
        
    async def process_task(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """Process task using multiple models collaboratively."""
        try:
            task = messages[-1]["content"]
            conversation_id = f"conversation-{os.urandom(12).hex()}"
            logger.info(f"Processing task: {task}")
            
            # Store user message in memory
            self.coordinator.memory.store_message(conversation_id, "user", task)
            
            # Get task analysis
            analysis = await self.coordinator.analyze_task(task, conversation_id)
            yield f"🤖 Coordinator Analysis:\n{analysis}\n\n"
            
            if "SIMPLE_QUESTION" in analysis:
                # Get search info for simple questions too
                search_info, has_search = await self._get_search_info(task, conversation_id)
                if has_search:
                    yield f"🔍 Search Results:\n{search_info}\n\n"
                
                # Use memory-aware completion for simple questions
                answer = await self.coordinator.get_completion([
                    {
                        "role": "system",
                        "content": (
                            "You are an AI assistant with perfect memory of our conversation. "
                            "Answer questions clearly and concisely, using information from our conversation history. "
                            "If asked about preferences or previous statements, refer to the conversation history. "
                            + (f"\n\nRelevant search information:\n{search_info}" if has_search else "")
                        )
                    },
                    {"role": "user", "content": task}
                ], conversation_id)
                
                # Store assistant's response in memory
                self.coordinator.memory.store_message(conversation_id, "assistant", answer)
                yield f"🤖 Answer:\n{answer}\n\n"
                return
                
            # Get search info if needed
            search_info, has_search = await self._get_search_info(task, conversation_id)
            if has_search:
                yield f"🔍 Search Results:\n{search_info}\n\n"
                
            # Prepare context for coders
            context_messages = messages.copy()
            context_messages.append({
                "role": "system",
                "content": (
                    f"Task Analysis:\n{analysis}\n\n"
                    + (f"Search Information:\n{search_info}\n\n" if has_search else "")
                )
            })
            
            # Get solutions from coders
            solutions = await self._get_coder_solutions(context_messages)
            for name, solution in solutions.items():
                yield f"💻 {name.capitalize()}'s Solution:\n{solution}\n\n"
                
            # Get final review
            best_solution = solutions.get("claude", next(iter(solutions.values())))
            review = await self.coordinator.review_solution(best_solution, conversation_id)
            yield f"🤖 Final Review:\n{review}\n\n"
            
        except Exception as e:
            error_msg = f"Error processing task: {str(e)}"
            logger.error(error_msg)
            yield f"❌ Error: {error_msg}\n\n"
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

async def stream_generator(response_gen) -> AsyncGenerator[bytes, None]:
    """Generate streaming response in SSE format."""
    try:
        if isinstance(response_gen, AsyncGenerator):
            # Handle async generators (like from agent_system.process_task)
            async for part in response_gen:
                chunk = {
                    "id": "agent-" + os.urandom(12).hex(),
                    "choices": [{
                        "delta": {"content": part},
                        "finish_reason": None
                    }]
                }
                yield SSE_DATA_PREFIX + json.dumps(chunk).encode() + SSE_NEWLINE
        else:
            # Handle single responses (like from Claude client)
            if hasattr(response_gen, 'content'):
                # Handle CreateResult objects
                content = response_gen.content
            elif isinstance(response_gen, list):
                # Handle list responses
                content = "\n\n".join(response_gen)
            else:
                # Handle other response types
                content = str(response_gen)
                
            chunk = {
                "id": "response-" + os.urandom(12).hex(),
                "choices": [{
                    "delta": {"content": content},
                    "finish_reason": "stop"
                }]
            }
            yield SSE_DATA_PREFIX + json.dumps(chunk).encode() + SSE_NEWLINE
            yield SSE_DONE
            
    except Exception as e:
        error_msg = f"Stream error: {e}"
        logger.error(error_msg)
        yield SSE_DATA_PREFIX + json.dumps({'error': str(e)}).encode() + SSE_NEWLINE

@app.post("/chat/completions")
async def chat(request: Request):
    """Handle chat completion requests."""
    try:
        data = await request.json()
        
        # Validate request
        RequestHandler.validate_request(request, data)
        
        # Process messages
        messages = RequestHandler.process_message_content(data["messages"])
        logger.debug(f"Processed messages: {json.dumps(messages, indent=2)}")
        
        # Route request based on model
        model = data.get("model", "").strip()
        stream = data.get("stream", False)
        
        if model == "agent-system":
            return await RequestHandler.handle_agent_system(messages, stream)
        elif model == "Claude 3.5 Sonnet":
            return await RequestHandler.handle_claude(messages, stream)
            
        raise HTTPException(status_code=404, detail="Model not found")
        
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
    logger.info("- Model ID: Claude 3.5 Sonnet")
    logger.info("=" * 60)
    
    # Also print to console for convenience
    print("\nStarting server...")
    print("=" * 60)
    print("Configure Cline with:")
    print("- API Provider: OpenAI Compatible")
    print(f"- Base URL: http://localhost:{PORT}")
    print(f"- API Key: {API_KEY}")
    print("- Model ID: Claude 3.5 Sonnet")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
