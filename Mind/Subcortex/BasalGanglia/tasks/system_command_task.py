from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import asyncio
import time
from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class SystemCommandTask(NeuralTask):
    """Task to handle system command operations"""
    
    def __init__(self, priority=3, command_type=None):
        """Initialize the system command task.
        
        Args:
            priority: Task priority (lower numbers = higher priority)
            command_type: Type of system command (can be set later)
        """
        super().__init__("SystemCommandTask", priority)
        self.command = command_type  # Store command_type as command
        self.data = None
        self.result = None
        self.completed = False
        self.active = False  # Start as inactive
        self.task_type = TaskType.SYSTEM_COMMAND
        self.log = logging.getLogger("SystemCommandTask")
        journaling_manager.recordInfo(f"[BasalGanglia] Created SystemCommandTask: {command_type}")
        
    async def _execute_command(self):
        """Execute the system command asynchronously"""
        journaling_manager.recordScope("[BasalGanglia] Executing system command", 
                                    command_type=self.command, 
                                    data=self.data)
        try:
            # Import SynapticPathways at runtime when needed, not at module level
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Create appropriate command format
            command = {
                "request_id": f"{self.command}_{int(time.time())}",
                "work_id": "sys",
                "action": self.command,
                "object": "system", 
                "data": self.data
            }
            
            # Use SynapticPathways to send the command
            response = await SynapticPathways.transmit_json(command)
            
            journaling_manager.recordInfo(f"[BasalGanglia] System command completed: {self.command}")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] System command failed: {e}")
            return {"error": str(e)}
        
    def run(self):
        """Run the system command task"""
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running SystemCommandTask", command_type=self.command)
        
        try:
            # Create an event loop if there isn't one already
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Execute the command and get the result
            self.result = loop.run_until_complete(self._execute_command())
            journaling_manager.recordDebug(f"[BasalGanglia] System command result: {str(self.result)[:100]}...")
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] System command task failed: {e}")
            self.result = {"error": str(e)}
            
        self.stop()  # Task completes after execution

    async def execute(self):
        """Execute system command with better error handling."""
        if not self.command:
            return None
            
        try:
            journaling_manager.recordInfo(f"[SystemCommandTask] Running command: {self.command}")
            
            # Special handling for ping command
            if self.command == "ping":
                self.result = await self._ping_system()
            # Handle other commands...
            # ...
            
            # Mark as completed
            self.completed = True
            self.active = False  # Auto-deactivate after completion
            
            return self.result
            
        except Exception as e:
            journaling_manager.recordError(f"[SystemCommandTask] Execution error: {e}")
            import traceback
            journaling_manager.recordError(f"[SystemCommandTask] Traceback: {traceback.format_exc()}")
            self.result = {"error": str(e), "success": False}
            self.completed = True
            self.active = False
            return self.result
            
    async def _ping_system(self):
        """Send ping command using same pattern as working model call."""
        try:
            # Get communication task
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            bg = SynapticPathways.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[SystemCommandTask] ❌ Communication task not found")
                return {"success": False, "error": "Communication task not found"}
            
            # Use EXACT format that works for model calls
            ping_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "ping"
            }
            
            # Log command
            journaling_manager.recordInfo("[SystemCommandTask] 📤 Sending ping command")
            
            # Send command using same method that works for models
            response = await comm_task.send_command(ping_command)
            journaling_manager.recordInfo(f"[SystemCommandTask] 📥 Ping response received")
            journaling_manager.recordDebug(f"[SystemCommandTask] 📥 Response: {response}")
            
            # Check response - EXACT format from your shared example
            if response and "error" in response:
                error_code = response["error"].get("code", -1)
                success = (error_code == 0)
                
                return {
                    "success": success,
                    "response": response,
                    "timestamp": time.time()
                }
            else:
                journaling_manager.recordError(f"[SystemCommandTask] ❌ Invalid ping response")
                return {"success": False, "error": "Invalid response"}
            
        except Exception as e:
            journaling_manager.recordError(f"[SystemCommandTask] ❌ Error in ping: {e}")
            import traceback
            journaling_manager.recordError(f"[SystemCommandTask] Stack trace: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
