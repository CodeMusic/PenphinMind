from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import asyncio
import time
from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask
from Mind.Subcortex.BasalGanglia.commands.system_command import SystemCommand
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge

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
        try:
            command = SystemCommand.create_command(
                action=self.command,
                data=self.data,
                request_id=f"sys_{int(time.time())}"
            )
            return await NeurocorticalBridge.execute(command)
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] System command failed: {e}")
            return {"status": "error", "message": str(e)}
        
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
            # Special handling for reset command
            elif self.command == "reset":
                self.result = await self._reset_system()
            
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
        """Send ping command using proper architectural patterns."""
        try:
            # Use NeurocorticalBridge instead of direct access
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Log command
            journaling_manager.recordInfo("[SystemCommandTask] 🐬 Sending ping command via NeurocorticalBridge")
            
            # Use the bridge for proper architectural layering
            ping_result = await NeurocorticalBridge.execute_operation("ping", use_task=False)
            journaling_manager.recordInfo(f"[SystemCommandTask] 🐬 Ping response received through bridge")
            
            # Process result from bridge's standardized response format  
            if ping_result and ping_result.get("status") == "ok":
                return {
                    "success": True,
                    "response": ping_result.get("response", {}),
                    "timestamp": time.time()
                }
            else:
                error_msg = ping_result.get("message", "Unknown error") if ping_result else "No response from bridge"
                journaling_manager.recordError(f"[SystemCommandTask] 🐧 Ping failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
        except Exception as e:
            journaling_manager.recordError(f"[SystemCommandTask] ❌ Error in ping: {e}")
            import traceback
            journaling_manager.recordError(f"[SystemCommandTask] Stack trace: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
            
    async def _reset_system(self):
        """Send reset command to reset the LLM system."""
        try:
            reset_command = SystemCommand.create_reset_command(
                target="llm",
                request_id=f"reset_{int(time.time())}"
            )
            
            reset_result = await NeurocorticalBridge.execute(reset_command)
            
            if reset_result["status"] == "ok":
                return {
                    "success": True,
                    "message": "Reset completed successfully",
                    "timestamp": time.time()
                }
            else:
                return {"success": False, "error": reset_result.get("message", "Unknown error")}
                
        except Exception as e:
            journaling_manager.recordError(f"[SystemCommandTask] Reset error: {e}")
            return {"success": False, "error": str(e)}
