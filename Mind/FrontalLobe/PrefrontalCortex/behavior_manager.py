#!/usr/bin/env python3
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class SystemState(Enum):
    """System states that affect behavior"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    THINKING = "thinking"
    LISTENING = "listening"
    SPEAKING = "speaking"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class BehaviorManager:
    """Manages system-wide behaviors and state transitions"""
    
    def __init__(self):
        """Initialize behavior manager"""
        self.current_state: SystemState = SystemState.INITIALIZING
        self.state_handlers: Dict[SystemState, Any] = {}
        self.is_running = False
        
    def register_state_handler(self, state: SystemState, handler: Any) -> None:
        """Register a handler for a specific state"""
        self.state_handlers[state] = handler
        
    def set_state(self, new_state: SystemState) -> None:
        """Set new system state and notify handlers"""
        if new_state != self.current_state:
            logger.info(f"State transition: {self.current_state.value} -> {new_state.value}")
            self.current_state = new_state
            
            # Notify handler if registered
            if new_state in self.state_handlers:
                handler = self.state_handlers[new_state]
                if hasattr(handler, 'on_state_change'):
                    handler.on_state_change(new_state)
                    
    def start(self) -> None:
        """Start behavior management"""
        self.is_running = True
        self.set_state(SystemState.INITIALIZING)
        
    def stop(self) -> None:
        """Stop behavior management"""
        self.is_running = False
        self.set_state(SystemState.SHUTDOWN)
        
    def get_current_state(self) -> SystemState:
        """Get current system state"""
        return self.current_state 