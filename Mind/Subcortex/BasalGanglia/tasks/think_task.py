from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import asyncio
import time
import logging
import json

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ThinkTask(NeuralTask):
    """Task to perform deep thought with LLM."""
    
    def __init__(self, prompt, priority=5, stream=False):
        """Initialize the thinking task with a prompt.
        
        Args:
            prompt: The prompt to send to the model
            priority: Task priority (lower is higher)
            stream: Whether to stream the response
        """
        super().__init__("ThinkTask", priority)
        self.prompt = prompt
        self.result = None
        self.active = True
        self.stream = stream
        self.task_type = TaskType.THINKING
        
    async def execute(self):
        """Execute the thinking task asynchronously."""
        journaling_manager.recordInfo(f"[BasalGanglia] Executing thinking task: {self.prompt[:50]}...")
        
        try:
            # Only import SynapticPathways here when needed
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Create thinking command
            inference_command = {
                "request_id": f"inference_{int(time.time())}",
                "work_id": f"think_{int(time.time())}",
                "action": "inference",
                "object": "llm.utf-8",
                "data": {
                    "delta": self.prompt,
                    "index": 0,
                    "finish": True
                }
            }
            
            # Send command and get response
            if self.stream:
                journaling_manager.recordInfo("[ThinkTask] Using streaming mode")
                response = await self._stream_response(inference_command)
            else:
                journaling_manager.recordInfo("[ThinkTask] Using non-streaming mode")
                response = await SynapticPathways.transmit_json(inference_command)
                
                # Extract the response
                if "data" in response:
                    data = response["data"]
                    if isinstance(data, dict) and "delta" in data:
                        self.result = data.get("delta", "")
                    elif isinstance(data, str):
                        self.result = data
                    else:
                        self.result = str(data)
                else:
                    error_code = response.get("error", {}).get("code", -1)
                    error_msg = response.get("error", {}).get("message", "Unknown error")
                    self.result = f"Error {error_code}: {error_msg}"
            
            # Task is complete
            self.active = False
            journaling_manager.recordInfo(f"[BasalGanglia] Thinking task completed: {self.result[:50]}...")
            
            return self.result
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error in thinking task: {e}")
            import traceback
            journaling_manager.recordError(f"[BasalGanglia] Stack trace: {traceback.format_exc()}")
            self.result = f"Error: {str(e)}"
            self.active = False
            return self.result
    
    async def _stream_response(self, command):
        """Stream response from LLM and update result as it arrives."""
        # Import here to avoid circular dependency
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Initialize the LLM
            setup_command = {
                "request_id": f"setup_{int(time.time())}",
                "work_id": command["work_id"],
                "action": "setup",
                "object": "llm.setup",
                "data": {
                    "model": SynapticPathways.default_llm_model,
                    "response_format": "llm.utf-8.stream", 
                    "input": "llm.utf-8", 
                    "enoutput": True,
                    "enkws": False,
                    "max_token_len": 127
                }
            }
            
            # Send setup command
            await SynapticPathways.transmit_json(setup_command)
            
            # Send inference command
            response = await SynapticPathways.transmit_json(command)
            
            if not response or "data" not in response:
                error_code = response.get("error", {}).get("code", -1)
                error_msg = response.get("error", {}).get("message", "Unknown error")
                self.result = f"Error {error_code}: {error_msg}"
                return response
            
            # Initialize streaming result
            self.result = ""
            
            # Extract initial response
            if isinstance(response["data"], dict) and "delta" in response["data"]:
                delta = response["data"]["delta"]
                self.result += delta
                
                # Keep getting streaming responses until finished
                finish = response["data"].get("finish", False)
                
                while not finish:
                    # Create streaming request
                    stream_command = {
                        "request_id": f"stream_{int(time.time())}",
                        "work_id": command["work_id"],
                        "action": "inference.stream",
                        "object": "llm.utf-8.stream"
                    }
                    
                    # Send stream command
                    stream_response = await SynapticPathways.transmit_json(stream_command)
                    
                    # Process response
                    if not stream_response or "data" not in stream_response:
                        break
                        
                    data = stream_response["data"]
                    if isinstance(data, dict):
                        delta = data.get("delta", "")
                        self.result += delta
                        finish = data.get("finish", False)
                    else:
                        break
                    
                    # Don't overwhelm the device with requests
                    await asyncio.sleep(0.1)
            
            elif isinstance(response["data"], str):
                # Handle direct string response
                self.result = response["data"]
            
            # Clean up LLM resources
            exit_command = {
                "request_id": f"exit_{int(time.time())}",
                "work_id": command["work_id"],
                "action": "exit"
            }
            await SynapticPathways.transmit_json(exit_command)
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"[ThinkTask] Error in streaming: {e}")
            self.result = f"Error: {str(e)}"
            return {"error": {"code": -1, "message": str(e)}}
    
    def run(self):
        """Implementation of abstract method from Task base class.
        
        Note: This runs in the main thread, so it's not suitable for long-running operations.
        Use execute() for async operations.
        """
        journaling_manager.recordInfo(f"[BasalGanglia] ThinkTask.run() called")
        return {"status": "running", "message": "Use execute() for async operations"}
