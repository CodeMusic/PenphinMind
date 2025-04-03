from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import asyncio
import time
import logging
import json
from Mind.CorpusCallosum.api_commands import (
    BaseCommand, 
    CommandType,
    LLMCommand, 
    SystemCommand, 
    parse_response
)
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
from Mind.config import CONFIG

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ThinkTask(NeuralTask):
    """Task to perform deep thought with LLM."""
    
    def __init__(self, prompt: str, system_message: str = None, model_name: str = None, stream: bool = False):
        """Initialize the thinking task with a prompt.
        
        Args:
            prompt: The prompt to send to the model
            system_message: The system message to send to the model
            model_name: The name of the model to use
            stream: Whether to stream the response
        """
        super().__init__("ThinkTask")
        self.prompt = prompt
        # Use provided system_message or fall back to CONFIG.persona
        self.system_message = system_message or CONFIG.persona
        self.model_name = model_name
        self.stream = stream
        self.result = None
        self.active = True
        self.creation_time = time.time()  # Add creation timestamp
        
        # Use a valid task type that exists in your enum
        # This might be different based on your actual enum values
        self.task_type = TaskType.THINKING  # Or whatever value is appropriate
        
        # For debugging, log the available TaskType values
        journaling_manager.recordDebug(f"Available TaskType values: {[t.name for t in TaskType]}")
        
    async def execute(self):
        """Execute the thinking task"""
        try:
            if self.stream:
                return await self._stream_response()
            else:
                think_command = LLMCommand.create_think_command(
                    prompt=self.prompt,
                    stream=False,
                    system_message=self.system_message
                )
                return await NeurocorticalBridge.execute(think_command)
                
        except Exception as e:
            journaling_manager.recordError(f"[ThinkTask] Execution error: {e}")
            return {"status": "error", "message": str(e)}

    async def _stream_response(self):
        """Stream response from LLM"""
        try:
            setup_command = LLMCommand.create_setup_command(
                model=self.model_name,
                response_format="llm.utf-8.stream",
                input="llm.utf-8.stream",
                enoutput=True,
                enkws=True,
                max_token_len=127,
                prompt=self.system_message
            )
            
            setup_response = await NeurocorticalBridge.execute(setup_command)
            if setup_response["status"] != "ok":
                return setup_response
            
            think_command = LLMCommand.create_think_command(
                prompt=self.prompt,
                stream=True
            )
            
            return await NeurocorticalBridge.execute(think_command)
            
        except Exception as e:
            journaling_manager.recordError(f"[ThinkTask] Error in streaming: {e}")
            return {"status": "error", "message": str(e)}
    
    def run(self):
        """Run the thinking task in the main thread.
        
        Note: This method runs in the main thread and should only handle
        lightweight operations. Use execute() for actual LLM operations.
        """
        try:
            if not self.active:
                return
            
            self.status = "running"
            journaling_manager.recordInfo(f"[ThinkTask] Running task (stream={self.stream})")
            
            # Check if we have required parameters
            if not self.prompt:
                self.status = "error"
                journaling_manager.recordError("[ThinkTask] No prompt provided")
                return
            
            # Update task state
            self.last_run = time.time()
            
            # For streaming, we need to ensure setup is complete
            if self.stream and not self.model_name:
                journaling_manager.recordWarning("[ThinkTask] Stream requested but no model specified")
                self.model_name = CONFIG.minds[self.mind_id]["llm"]["default_model"]
            
            # Schedule the execute coroutine to run in the event loop
            asyncio.create_task(self.execute())
            
            journaling_manager.recordDebug(f"[ThinkTask] Task scheduled for execution with prompt: {self.prompt[:50]}...")
            
        except Exception as e:
            self.status = "error"
            journaling_manager.recordError(f"[ThinkTask] Error in run: {e}")
            self.active = False
