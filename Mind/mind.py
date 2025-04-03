"""
Main Mind class that coordinates all brain regions
"""

import logging
import platform
from typing import Dict, Any, Optional
from .CorpusCallosum.synaptic_pathways import SynapticPathways
from .TemporalLobe.SuperiorTemporalGyrus.HeschlGyrus.primary_acoustic_area import PrimaryAcousticArea
from .OccipitalLobe.VisualCortex.associative_visual_area import AssociativeVisualArea
from .ParietalLobe.SomatosensoryCortex.primary_area import PrimaryArea
from .FrontalLobe.PrefrontalCortex.language_processor import LanguageProcessor
from .FrontalLobe.MotorCortex.motor import Motor
from .TemporalLobe.SuperiorTemporalGyrus.AuditoryCortex.integration_area import IntegrationArea
from .ParietalLobe.SomatosensoryCortex.integration_area import IntegrationArea as SomatosensoryIntegration
from .OccipitalLobe.VisualCortex.integration_area import IntegrationArea as VisualProcessor
from .FrontalLobe.MotorCortex.integration_area import IntegrationArea as MotorIntegration
from .FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from .config import CONFIG
from .Subcortex.neurocortical_bridge import NeurocorticalBridge
from ..config import get_mind_config
from .ChatManager import ChatManager
from .Subcortex.BasalGanglia.commands import LLMCommand, SystemCommand
# Add other lobe imports as needed

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

logger = logging.getLogger(__name__)

class Mind:
    """Main interface for interacting with PenphinMind"""
    
    def __init__(self, mind_id: str = None):
        # Load config for this mind
        self._config = get_mind_config(mind_id)
        self._initialized = False
        self._name = self._config["name"]
        # Use the mind-specific persona from llm config
        self._persona = self._config["llm"]["persona"].format(name=self._name)
        self._device_id = self._config["device_id"]
        self._connection = self._config["connection"]
        
        # Initialize connection settings
        self._connection_type = self._connection["type"]
        self._ip = self._connection["ip"]
        self._port = self._connection["port"]
        
        # LLM settings
        self._llm_config = self._config["llm"]
        self._default_model = self._llm_config["default_model"]
        
        self.chat_manager = None
        journaling_manager.recordInfo(f"[Mind] Initialized with persona: {self._persona[:50]}...")
        
    @property
    def name(self) -> str:
        """Get the mind's name"""
        return self._name
        
    @property
    def identity(self) -> Dict[str, Any]:
        """Get mind's identity information"""
        return {
            "name": self._name,
            "persona": self._persona,
            "device_id": self._device_id,
            "connection": self._connection_type,
            "initialized": self._initialized
        }
    
    def format_identity(self) -> str:
        """Format mind's identity for display"""
        status = "🟢 Connected" if self._initialized else "🔴 Disconnected"
        return f"🐧🐬 {self._name} [{self._device_id}] - {status}"

    def __init__(self):
        # Initialize instance variables
        self._occipital_lobe = {}
        self._temporal_lobe = {}
        self._parietal_lobe = {}
        self._motor_cortex = {}
        self.primary_acoustic = None
        self._initialized = False
        self._processing = False
        self._language_processor = None  # Language processor instance
        self._system_journeling_manager = SystemJournelingManager()
        
        # Initialize all lobes
        self._temporal_lobe = {
            "auditory": IntegrationArea()
        }
        self._parietal_lobe = {
            "somatosensory": SomatosensoryIntegration()
        }
        self._occipital_lobe = {
            "visual": VisualProcessor()
        }
        self._motor_cortex = {
            "motor": MotorIntegration()
        }
        
        journaling_manager.recordScope("Mind.__init__")
        
    @property
    def temporal_lobe(self) -> Dict[str, Any]:
        """Get temporal lobe components"""
        journaling_manager.recordScope("Mind.temporal_lobe.getter")
        return self._temporal_lobe
        
    @temporal_lobe.setter
    def temporal_lobe(self, value: Dict[str, Any]):
        """Set temporal lobe components"""
        journaling_manager.recordScope("Mind.temporal_lobe.setter", value=value)
        self._temporal_lobe = value
        
    @property
    def parietal_lobe(self) -> Dict[str, Any]:
        """Get parietal lobe components"""
        journaling_manager.recordScope("Mind.parietal_lobe.getter")
        return self._parietal_lobe
        
    @parietal_lobe.setter
    def parietal_lobe(self, value: Dict[str, Any]):
        """Set parietal lobe components"""
        journaling_manager.recordScope("Mind.parietal_lobe.setter", value=value)
        self._parietal_lobe = value
        
    @property
    def occipital_lobe(self) -> Dict[str, Any]:
        """Get occipital lobe components"""
        journaling_manager.recordScope("Mind.occipital_lobe.getter")
        return self._occipital_lobe
        
    @occipital_lobe.setter
    def occipital_lobe(self, value: Dict[str, Any]):
        """Set occipital lobe components"""
        journaling_manager.recordScope("Mind.occipital_lobe.setter", value=value)
        self._occipital_lobe = value
        
    @property
    def motor_cortex(self) -> Dict[str, Any]:
        """Get motor cortex components"""
        journaling_manager.recordScope("Mind.motor_cortex.getter")
        return self._motor_cortex
        
    @motor_cortex.setter
    def motor_cortex(self, value: Dict[str, Any]):
        """Set motor cortex components"""
        journaling_manager.recordScope("Mind.motor_cortex.setter", value=value)
        self._motor_cortex = value
        
    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """High-level audio processing"""
        journaling_manager.recordScope("Mind.process_audio", audio_data=audio_data)
        return await self.temporal_lobe["auditory"].process_auditory_input(audio_data)
        
    async def generate_speech(self, text: str) -> bytes:
        """High-level speech generation"""
        journaling_manager.recordScope("Mind.generate_speech", text=text)
        return await self.temporal_lobe["auditory"].process_text(text)
        
    async def understand_speech(self, audio_data: bytes) -> str:
        """High-level speech understanding"""
        journaling_manager.recordScope("Mind.understand_speech", audio_data=audio_data)
        result = await self.temporal_lobe["auditory"].process_auditory_input(audio_data)
        return result.get("text", "")

    async def start_listening(self) -> None:
        """Start audio input processing"""
        journaling_manager.recordScope("Mind.start_listening")
        if not self.primary_acoustic:
            # Initialize primary acoustic area if needed
            self.primary_acoustic = PrimaryAcousticArea()
        await self.primary_acoustic.start_vad()

    async def stop_listening(self) -> None:
        """Stop audio input processing"""
        journaling_manager.recordScope("Mind.stop_listening")
        if self.primary_acoustic:
            await self.primary_acoustic.stop_vad()

    def _is_raspberry_pi(self) -> bool:
        """Check if running on a Raspberry Pi"""
        journaling_manager.recordScope("Mind._is_raspberry_pi")
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False
            
    async def initialize(self, connection_type: str = None, model_name: str = None) -> bool:
        """Initialize the Mind system"""
        try:
            # Initialize base connection
            success = await NeurocorticalBridge.initialize_system(connection_type)
            if not success:
                return False

            # Initialize chat manager with persona from config
            self.chat_manager = ChatManager()
            success = await self.chat_manager.initialize(
                model_name=model_name,
                system_message=self._persona
            )

            self._initialized = success
            self._connection_type = connection_type if success else None
            return success

        except Exception as e:
            journaling_manager.recordError(f"[Mind] Initialization error: {e}")
            return False

    async def cleanup(self) -> None:
        """Clean up all brain regions"""
        journaling_manager.recordScope("Mind.cleanup")
        try:
            # Clean up all integration areas
            for area in self.temporal_lobe.values():
                await area.cleanup()
            for area in self.parietal_lobe.values():
                await area.cleanup()
            for area in self.occipital_lobe.values():
                await area.cleanup()
            for area in self.motor_cortex.values():
                await area.cleanup()
                
            # Clean up primary acoustic area
            if self.primary_acoustic:
                await self.primary_acoustic.cleanup()
                
            # Clean up language processor
            if self._language_processor:
                await self._language_processor.cleanup()
                
            self._initialized = False
            journaling_manager.recordInfo("Mind cleaned up successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up mind: {e}")
            raise
            
    async def execute_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """High-level movement execution"""
        journaling_manager.recordScope("Mind.execute_movement", movement_data=movement_data)
        return await self.motor_cortex["motor"].execute_movement(movement_data)
        
    async def stop_movement(self) -> None:
        """Stop all current movements"""
        journaling_manager.recordScope("Mind.stop_movement")
        await self.motor_cortex["motor"].stop_movement()
        
    async def process_visual_input(self, image_data: bytes) -> Dict[str, Any]:
        """
        Process visual input through visual cortex
        
        Args:
            image_data: Raw image data to process
            
        Returns:
            Dict[str, Any]: Processing result containing visual analysis
        """
        journaling_manager.recordScope("Mind.process_visual_input", image_data=image_data)
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            journaling_manager.recordDebug("Processing visual input through occipital lobe")
            result = await self.occipital_lobe["visual"].process_visual_input(image_data)
            
            journaling_manager.recordInfo("Successfully processed visual input")
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing visual input: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
    async def set_background(self, r: int, g: int, b: int) -> None:
        """
        Set the LED matrix background color
        
        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        journaling_manager.recordScope("Mind.set_background", r=r, g=g, b=b)
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            journaling_manager.recordDebug(f"Setting background color to RGB({r}, {g}, {b})")
            await self.occipital_lobe["visual"].set_background(r, g, b)
            
            journaling_manager.recordInfo("Successfully set background color")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting background color: {e}")
            raise
            
    async def clear_matrix(self) -> None:
        """Clear the LED matrix display"""
        journaling_manager.recordScope("Mind.clear_matrix")
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            journaling_manager.recordDebug("Clearing LED matrix")
            await self.occipital_lobe["visual"].clear()
            
            journaling_manager.recordInfo("Successfully cleared LED matrix")
            
        except Exception as e:
            journaling_manager.recordError(f"Error clearing LED matrix: {e}")
            raise

    async def process_input(self, input_text: str) -> Dict[str, Any]:
        """
        Process text input and generate a response
        
        Args:
            input_text: The text input to process
            
        Returns:
            Dict[str, Any]: Response with status and generated text
        """
        journaling_manager.recordScope("Mind.process_input", input_text=input_text)
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            journaling_manager.recordInfo("Processing input text through language processor")
            
            # Use self.execute_operation instead of direct NeurocorticalBridge access
            return await self.execute_operation(
                "think", 
                {"prompt": input_text},
                stream=True
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing input: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def execute_operation(self, operation: str, data=None, use_task=None, stream=False):
        """
        Execute a cognitive operation
        
        This is the public interface to the NeurocorticalBridge, respecting architectural boundaries.
        External components must use this method instead of accessing the bridge directly.
        
        Args:
            operation: The operation to perform
            data: Optional data for the operation
            use_task: Whether to use the task system
            stream: Whether to stream results
            
        Returns:
            Result of the operation
        """
        # Import here to avoid circular imports
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        journaling_manager.recordInfo(f"[Mind] Executing operation: {operation}")
        
        # Execute via NeurocorticalBridge using standardized operation format
        return await NeurocorticalBridge.execute_operation(operation, data, use_task, stream)
    
    async def think(self, prompt: str, stream: bool = False):
        """Perform thinking operation with the LLM"""
        journaling_manager.recordInfo(f"[Mind] Thinking: {prompt[:50]}...")
        
        think_command = LLMCommand.create_think_command(
            prompt=prompt,
            stream=stream,
            system_message=self._persona
        )
        return await NeurocorticalBridge.execute(think_command)

    async def reset_system(self):
        """Reset the LLM system"""
        journaling_manager.recordInfo("[Mind] Resetting system")
        
        reset_command = SystemCommand.create_reset_command(
            target="llm",
            request_id=f"reset_{int(time.time())}"
        )
        return await NeurocorticalBridge.execute(reset_command)
    
    async def get_hardware_info(self) -> Dict[str, Any]:
        """Get formatted hardware information"""
        try:
            # Use NeurocorticalBridge for hardware info
            result = await self.execute_operation("hardware_info")
            if result.get("status") == "ok":
                # Format the hardware info for display
                hw = result.get("data", {})
                formatted = self._format_hardware_info(hw)
                return {"status": "ok", "hardware_info": formatted}
            return {"status": "error", "message": result.get("message", "Failed to get hardware info")}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _format_hardware_info(self, hw: Dict[str, Any]) -> str:
        """Internal method to format hardware info"""
        cpu = hw.get("cpu_loadavg", "N/A")
        mem = hw.get("mem", "N/A")
        temp_raw = hw.get("temperature", "N/A")
        
        # Format temperature
        temp = f"{temp_raw/1000:.1f}" if isinstance(temp_raw, (int, float)) and temp_raw > 1000 else str(temp_raw)
        
        # Format network info
        net_info = ""
        if "eth_info" in hw and isinstance(hw["eth_info"], list) and len(hw["eth_info"]) > 0:
            ip = hw["eth_info"][0].get("ip", "N/A")
            net_info = f" | IP: {ip}"
        
        return f"🐧🐬 Hardware: CPU: {cpu}% | Memory: {mem}% | Temp: {temp}°C{net_info}"
    
    async def ping_system(self):
        """Ping the system to check connectivity"""
        return await self.execute_operation("ping")
    
    async def list_models(self):
        """List available models"""
        return await self.execute_operation("list_models")
    
    async def set_model(self, model_name: str):
        """Set the active model"""
        journaling_manager.recordInfo(f"[Mind] Setting model: {model_name}")
        return await self.execute_operation("set_model", {"model": model_name})
        
    async def reboot_device(self):
        """Reboot the connected device"""
        journaling_manager.recordInfo("[Mind] Rebooting device")
        return await self.execute_operation("reboot_device")
    
    async def connect(self, connection_type=None):
        """Connect to hardware using the specified connection type"""
        journaling_manager.recordInfo(f"[Mind] Connecting with type: {connection_type}")
        self._connection_type = connection_type
        result = await self.execute_operation("initialize_connection", {"connection_type": connection_type})
        return result.get("status") == "ok"
    
    def get_system_info(self):
        """Get system information"""
        return {
            "initialized": self._initialized,
            "connection_type": self._connection_type
        }
        
    def format_hardware_info(self):
        """Format hardware info in a human-readable format"""
        from .CorpusCallosum.synaptic_pathways import SynapticPathways
        return SynapticPathways.format_hw_info()
        
    def get_task_status(self):
        """
        Get status information about all active and inactive tasks
        
        This method provides a higher-level abstraction over BasalGanglia's task system
        without exposing the implementation details.
        
        Returns:
            Dict with task information including active and inactive tasks
        """
        journaling_manager.recordInfo("[Mind] Getting task status information")
        
        # Access BasalGanglia through NeurocorticalBridge only
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        
        # Structure the response to avoid exposing BasalGanglia internals
        result = {
            "active_tasks": [],
            "inactive_tasks": [],
            "total_count": 0
        }
        
        try:
            # Get task information through NeurocorticalBridge
            bg_result = NeurocorticalBridge.get_basal_ganglia()
            
            if bg_result and hasattr(bg_result, "_tasks"):
                # BasalGangliaIntegration has _tasks dict
                tasks = list(bg_result._tasks.values())
                result["total_count"] = len(tasks)
                
                # Group tasks by active status
                for task in tasks:
                    task_info = {
                        "name": getattr(task, "name", "Unknown"),
                        "type": getattr(task, "task_type", "Unknown"),
                        "priority": getattr(task, "priority", 0),
                        "created_at": getattr(task, "creation_time", 0)
                    }
                    
                    if hasattr(task, "active") and task.active:
                        result["active_tasks"].append(task_info)
                    else:
                        result["inactive_tasks"].append(task_info)
                        
            elif bg_result and hasattr(bg_result, "task_queue"):
                # Original BasalGanglia has task_queue list
                tasks = getattr(bg_result, "task_queue", [])
                result["total_count"] = len(tasks)
                
                # Group tasks by active status
                for task in tasks:
                    task_info = {
                        "name": getattr(task, "name", "Unknown"),
                        "priority": getattr(task, "priority", 0),
                        "created_at": getattr(task, "creation_time", 0)
                    }
                    
                    if hasattr(task, "active") and task.active:
                        result["active_tasks"].append(task_info)
                    else:
                        result["inactive_tasks"].append(task_info)
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Error getting task status: {e}")
            
        return result
        
    def get_default_model(self):
        """Get the currently selected default model"""
        from .CorpusCallosum.synaptic_pathways import SynapticPathways
        return SynapticPathways.default_llm_model
        
    def set_default_model(self, model_name: str):
        """Set the default model name in memory"""
        from .CorpusCallosum.synaptic_pathways import SynapticPathways
        SynapticPathways.default_llm_model = model_name
        journaling_manager.recordInfo(f"[Mind] Set default model to: {model_name}")
        
    async def get_model(self):
        """Get the currently active model from the device"""
        journaling_manager.recordInfo("[Mind] Getting active model")
        return await self.execute_operation("get_model")

    async def complete_cleanup(self):
        """
        Complete cleanup of all resources
        
        This method combines brain region cleanup with connection cleanup
        to ensure proper shutdown of all systems.
        """
        journaling_manager.recordInfo("[Mind] Performing complete cleanup")
        
        try:
            # Clean up brain regions first
            await self.cleanup()
            
            # Then clean up connection resources
            from .CorpusCallosum.synaptic_pathways import SynapticPathways
            await SynapticPathways.cleanup()
            
            journaling_manager.recordInfo("[Mind] Complete cleanup successful")
            return True
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Error during complete cleanup: {e}")
            import traceback
            journaling_manager.recordError(f"[Mind] Cleanup error trace: {traceback.format_exc()}")
            return False

    async def check_connection(self) -> Dict[str, Any]:
        """Check system connectivity"""
        try:
            # Use NeurocorticalBridge for all operations
            result = await self.execute_operation("ping")
            if result.get("status") == "ok":
                return {"status": "ok"}
            return {"status": "error", "message": result.get("message", "Connection check failed")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @property
    def connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "type": self._connection_type,
            "ip": self._ip if self._ip != "auto" else "auto-discovery",
            "port": self._port,
            "initialized": self._initialized
        }

    async def set_persona(self, new_persona: str):
        """Update the Mind's persona in config
        
        Args:
            new_persona: New system message defining the AI's personality/role
        """
        self._persona = new_persona
        if self.chat_manager:
            await self.chat_manager.set_system_message(new_persona)
        journaling_manager.recordInfo(f"[Mind] Updated persona in config: {new_persona[:50]}...")

async def setup_connection(connection_type=None):
    """
    Set up the connection to the hardware
    
    Args:
        connection_type: Type of connection to use (serial, adb, tcp)
    """
    from .FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
    from .Subcortex.neurocortical_bridge import NeurocorticalBridge
    journaling_manager = SystemJournelingManager()
    
    journaling_manager.recordScope("setup_connection", connection_type=connection_type)
    
    # Use the NeurocorticalBridge with standardized response format
    result = await NeurocorticalBridge.execute_operation(
        "initialize_connection", 
        {"connection_type": connection_type}
    )
    
    # Return true if status is ok
    return result.get("status") == "ok" 