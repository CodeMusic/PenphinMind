"""
Chat History Management for PenphinMind

This module manages conversation state and history for chat interfaces.
"""

from typing import Dict, Any, List, Optional
import time
import json
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ConversationState:
    """
    Represents the state of a conversation, including message history
    and metadata about the conversation context.
    """
    messages: List[Dict[str, str]] = field(default_factory=list)
    system_message: Optional[str] = None
    model_name: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    conversation_id: Optional[str] = None
    
    def add_user_message(self, message: str) -> None:
        """
        Add a user message to the conversation
        
        Args:
            message: The user message content
        """
        self.messages.append({
            "role": "user",
            "content": message,
            "timestamp": time.time()
        })
        self.last_activity = time.time()
        
    def add_assistant_message(self, message: str) -> None:
        """
        Add an assistant message to the conversation
        
        Args:
            message: The assistant message content
        """
        self.messages.append({
            "role": "assistant",
            "content": message,
            "timestamp": time.time()
        })
        self.last_activity = time.time()
    
    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        Get the conversation messages in the format needed for LLM API
        
        Args:
            include_system: Whether to include the system message
            
        Returns:
            List of message dictionaries
        """
        # Start with system message if available and requested
        result = []
        if include_system and self.system_message:
            result.append({
                "role": "system",
                "content": self.system_message
            })
            
        # Add conversation messages without timestamps 
        # (since LLM APIs typically don't expect them)
        for msg in self.messages:
            result.append({
                "role": msg["role"],
                "content": msg["content"]
            })
            
        return result
    
    def clear_history(self) -> None:
        """Clear the conversation history but keep system message"""
        self.messages = []
        self.last_activity = time.time()
    
    def save_to_file(self, file_path: Optional[str] = None) -> str:
        """
        Save conversation history to a JSON file
        
        Args:
            file_path: Path to save the file, or None to use auto-generated name
            
        Returns:
            Path to the saved file
        """
        # Create a conversation snapshot
        snapshot = {
            "system_message": self.system_message,
            "model": self.model_name,
            "started_at": self.started_at,
            "last_activity": self.last_activity,
            "conversation_id": self.conversation_id,
            "messages": self.messages
        }
        
        # Generate file path if not provided
        if not file_path:
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(self.started_at))
            file_path = f"chat_history_{timestamp}.json"
            
        # Create directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2)
            
        return file_path
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'ConversationState':
        """
        Load conversation history from a JSON file
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            ConversationState object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Create conversation state from loaded data
        conv = cls(
            messages=data.get("messages", []),
            system_message=data.get("system_message"),
            model_name=data.get("model"),
            started_at=data.get("started_at", time.time()),
            last_activity=data.get("last_activity", time.time()),
            conversation_id=data.get("conversation_id")
        )
        
        return conv 