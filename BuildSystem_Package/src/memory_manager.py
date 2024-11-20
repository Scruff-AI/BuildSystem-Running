"""Memory management for coordinator persistence."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class MemoryManager:
    """Manages persistent memory for the coordinator."""
    
    def __init__(self, storage_dir: str = "BuildSystem_Package/memory"):
        """Initialize memory manager with storage directory."""
        self.storage_dir = Path(storage_dir)
        self.chat_history_file = self.storage_dir / "chat_history.json"
        self.code_changes_file = self.storage_dir / "code_changes.json"
        self.context_file = self.storage_dir / "context.json"
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Create storage directory and files if they don't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize chat history file
        if not self.chat_history_file.exists():
            self._save_json(self.chat_history_file, {"conversations": {}})
            
        # Initialize code changes file
        if not self.code_changes_file.exists():
            self._save_json(self.code_changes_file, {"changes": []})
            
        # Initialize context file
        if not self.context_file.exists():
            self._save_json(self.context_file, {"current_context": {}})
    
    def _save_json(self, file_path: Path, data: Dict):
        """Save data to JSON file with proper formatting."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load data from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def store_message(self, conversation_id: str, role: str, content: str):
        """Store a new message in chat history."""
        data = self._load_json(self.chat_history_file)
        
        if conversation_id not in data["conversations"]:
            data["conversations"][conversation_id] = []
            
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content
        }
        
        data["conversations"][conversation_id].append(message)
        self._save_json(self.chat_history_file, data)
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Retrieve conversation history."""
        data = self._load_json(self.chat_history_file)
        return data["conversations"].get(conversation_id, [])
    
    def store_code_change(self, file_path: str, content: str, description: str):
        """Store a code change with metadata."""
        data = self._load_json(self.code_changes_file)
        
        change = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "content": content,
            "description": description
        }
        
        data["changes"].append(change)
        self._save_json(self.code_changes_file, data)
    
    def get_code_changes(self, file_path: Optional[str] = None) -> List[Dict]:
        """Retrieve code changes, optionally filtered by file path."""
        data = self._load_json(self.code_changes_file)
        
        if file_path:
            return [change for change in data["changes"] 
                   if change["file_path"] == file_path]
        return data["changes"]
    
    def update_context(self, context_data: Dict):
        """Update the current context."""
        data = self._load_json(self.context_file)
        data["current_context"].update(context_data)
        self._save_json(self.context_file, data)
    
    def get_context(self) -> Dict:
        """Retrieve current context."""
        data = self._load_json(self.context_file)
        return data["current_context"]
    
    def get_full_memory(self) -> Dict:
        """Get complete memory state including history, changes, and context."""
        return {
            "chat_history": self._load_json(self.chat_history_file),
            "code_changes": self._load_json(self.code_changes_file),
            "context": self._load_json(self.context_file)
        }
    
    def format_memory_for_prompt(self, conversation_id: str) -> str:
        """Format memory data for inclusion in model prompts."""
        memory = self.get_full_memory()
        conversation = memory["chat_history"]["conversations"].get(conversation_id, [])
        recent_changes = memory["code_changes"]["changes"][-5:] if memory["code_changes"]["changes"] else []
        context = memory["context"]["current_context"]
        
        prompt_parts = []
        
        # Add conversation history
        if conversation:
            prompt_parts.append("Previous Conversation:")
            for msg in conversation:
                prompt_parts.append(f"{msg['role']}: {msg['content']}")
        
        # Add recent code changes
        if recent_changes:
            prompt_parts.append("\nRecent Code Changes:")
            for change in recent_changes:
                prompt_parts.append(
                    f"File: {change['file_path']}\n"
                    f"Description: {change['description']}\n"
                    f"Timestamp: {change['timestamp']}"
                )
        
        # Add current context
        if context:
            prompt_parts.append("\nCurrent Context:")
            for key, value in context.items():
                prompt_parts.append(f"{key}: {value}")
        
        return "\n\n".join(prompt_parts)
