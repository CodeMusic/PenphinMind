from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.CorpusCallosum.transport_layer import get_transport, ConnectionError
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import json
import time
import asyncio
from typing import Dict, Any, Optional, Callable, List
import traceback

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class CommunicationTask(NeuralTask):
    """Task to manage communication with the hardware"""
    
    # Shared instance (singleton pattern)
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get or create the shared instance"""
        if cls._instance is None:
            cls._instance = CommunicationTask()
            journaling_manager.recordInfo("[BasalGanglia] Created CommunicationTask instance")
        return cls._instance
    
    def __init__(self, priority=1):
        """Initialize the communication task."""
        super().__init__("CommunicationTask", priority)
        self.connection_type = None
        self._transport = None
        self.active = True
        self.log = logging.getLogger("CommunicationTask")
        journaling_manager.recordInfo("[BasalGanglia] Initialized CommunicationTask")
        
        # Connection state
        self._initialized = False
        self._last_activity = 0
        self._connection_monitor_active = False
        
        # Request queue and callbacks
        self._request_queue = []
        self._callbacks = {}
        
    def run(self):
        """Implementation of required abstract method.
        
        In this task, operations happen asynchronously via execute()
        """
        # This synchronous method satisfies the Task abstract requirement
        # But actual work is done in the async methods
        return {"status": "ready"}
    
    async def execute(self):
        """Execute communication task operations"""
        # Just return current status - this task works on-demand
        is_connected = hasattr(self, '_transport') and self._transport is not None
        return {
            "status": "connected" if is_connected else "disconnected",
            "connection_type": self.connection_type,
            "endpoint": self._transport.endpoint if is_connected else None
        }
    
    async def initialize(self, connection_type):
        """Initialize the communication task."""
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.transport_layer import get_transport
            
            # Log initialization
            journaling_manager.recordInfo(f"[CommunicationTask] 🔌 Initializing {connection_type} connection")
            
            # Create and store transport
            self._transport = get_transport(connection_type)
            self.connection_type = connection_type
            
            # Try to connect
            journaling_manager.recordInfo(f"[CommunicationTask] 🔄 Connecting to {connection_type}...")
            connected = await self._transport.connect()
            
            if connected:
                journaling_manager.recordInfo(f"[CommunicationTask] ✅ Connected using {connection_type}")
                return True
            else:
                journaling_manager.recordError(f"[CommunicationTask] ❌ Failed to connect using {connection_type}")
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"[CommunicationTask] ❌ Error initializing: {e}")
            import traceback
            journaling_manager.recordError(f"[CommunicationTask] Stack trace: {traceback.format_exc()}")
            return False
    
    async def send_command(self, command):
        """Send command using the method that works for models."""
        if not self._transport or not hasattr(self._transport, 'transmit'):
            journaling_manager.recordError("[CommunicationTask] ❌ Transport not initialized")
            return {"error": {"code": -1, "message": "Transport not initialized"}}
        
        try:
            action = command.get("action", "unknown")
            journaling_manager.recordInfo(f"[CommunicationTask] 📤 Sending {action} command")
            
            # Send command via transport
            response = await self._transport.transmit(command)
            journaling_manager.recordInfo(f"[CommunicationTask] 📥 Received {action} response")
            
            # Return raw response without modification
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"[CommunicationTask] ❌ Error sending command: {e}")
            import traceback
            journaling_manager.recordError(f"[CommunicationTask] Stack trace: {traceback.format_exc()}")
            return {"error": {"code": -1, "message": str(e)}}
    
    async def queue_command(self, command: Dict[str, Any], callback: Callable = None) -> str:
        """Queue a command for asynchronous processing"""
        journaling_manager.recordScope("[BasalGanglia] Queuing command", command_type=command.get("action"))
        # Generate request ID if not present
        if "request_id" not in command:
            command["request_id"] = f"req_{int(time.time())}"
            
        request_id = command["request_id"]
        
        # Register callback if provided
        if callback:
            self._callbacks[request_id] = callback
            
        # Add to queue
        self._request_queue.append(command)
        journaling_manager.recordInfo(f"[BasalGanglia] Command queued with ID: {request_id}")
        
        return request_id
    
    async def shutdown(self) -> None:
        """Shutdown the communication channel"""
        journaling_manager.recordScope("[BasalGanglia] Shutting down communication channel")
        try:
            if self._transport:
                await self._transport.disconnect()
                
            self._initialized = False
            self._transport = None
            journaling_manager.recordInfo("[BasalGanglia] Communication channel shutdown complete")
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error during communication shutdown: {e}")
    
    async def _process_queue(self) -> None:
        """Process queued commands"""
        if not self._request_queue:
            return
            
        try:
            # Take first command from queue
            command = self._request_queue.pop(0)
            journaling_manager.recordInfo(f"[BasalGanglia] Processing queued command: {command.get('action')}")
            
            # Process it
            await self.send_command(command)
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error processing command queue: {e}")
    
    async def _monitor_connection(self) -> None:
        """Monitor connection health and attempt reconnection if needed"""
        self._connection_monitor_active = True
        journaling_manager.recordInfo("[BasalGanglia] Starting connection monitor")
        
        try:
            while self.active:
                # Check if connection needs refresh
                if self._initialized and time.time() - self._last_activity > 300:  # 5 minutes
                    # Do a ping to verify connection
                    try:
                        journaling_manager.recordInfo("[BasalGanglia] Checking connection with ping")
                        await self.send_command({
                            "request_id": f"ping_{int(time.time())}",
                            "work_id": "sys",
                            "action": "ping",
                            "object": "system",
                            "data": None
                        })
                    except Exception as e:
                        journaling_manager.recordWarning(f"[BasalGanglia] Connection ping failed: {e}")
                        # Try to reconnect
                        self._initialized = False
                        await self.initialize()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error in connection monitor: {e}")
        finally:
            self._connection_monitor_active = False 