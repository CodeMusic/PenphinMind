"""
Main Mind class that coordinates all brain regions
"""

import logging
import platform
import json
import time
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
from config import CONFIG  # Use absolute import instead of relative
from .mind_config import get_mind_by_id  # Use mind_config directly for mind-specific configs
from .Subcortex.neurocortical_bridge import NeurocorticalBridge
# Don't import ChatManager here to avoid circular import
from .Subcortex.api_commands import LLMCommand, SystemCommand
# Add other lobe imports as needed

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

logger = logging.getLogger(__name__)

class Mind:
    """Main interface for interacting with PenphinMind"""
    
    def __init__(self, mind_id: str = None):
        # Load config for this mind
        self._config = get_mind_by_id(mind_id)  # Use get_mind_by_id directly
        self._initialized = False
        self._name = self._config["name"]
        # Use the mind-specific persona from llm config
        self._persona = self._config["llm"]["persona"].format(name=self._name)
        self._device_id = self._config["device_id"]
        self._connection = self._config["connection"]
        self._mind_id = self._config.get("mind_id", "auto")  # Get the mind_id from config
        
        # Initialize connection settings
        self._connection_type = self._connection["type"]
        self._ip = self._connection["ip"]
        self._port = self._connection["port"]
        
        # LLM settings
        self._llm_config = self._config["llm"]
        self._default_model = self._llm_config["default_model"]
        
        # Initialize chat_manager as None - will be created when needed
        # We don't import ChatManager here to avoid circular imports
        self.chat_manager = None
        journaling_manager.recordInfo(f"[Mind] Initialized with persona: {self._persona[:50]}...")
        
        # Initialize instance variables
        self._occipital_lobe = {}
        self._temporal_lobe = {}
        self._parietal_lobe = {}
        self._motor_cortex = {}
        self.primary_acoustic = None
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
    def name(self) -> str:
        """Get the mind's name"""
        return self._name
    
    @property
    def mind_id(self) -> str:
        """Get the mind's ID"""
        return self._mind_id
        
    @property
    def identity(self) -> Dict[str, Any]:
        """Get mind's identity information"""
        return {
            "name": self._name,
            "mind_id": self._mind_id,
            "persona": self._persona,
            "device_id": self._device_id,
            "connection": self._connection_type,
            "initialized": self._initialized
        }
    
    def format_identity(self) -> str:
        """Format mind's identity for display"""
        status = "🟢 Connected" if self._initialized else "🔴 Disconnected"
        return f"🐧🐬 {self._name} [ID: {self._mind_id}] [{self._device_id}] - {status}"

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
            # Use the connection type from the mind config if not specified
            if connection_type is None:
                connection_type = self._connection_type
            
            journaling_manager.recordInfo(f"[Mind] Initializing with connection type: {connection_type}")
            journaling_manager.recordInfo(f"[Mind] Using connection settings from mind ID: {self._mind_id}")
            
            # Get connection settings from the mind configuration
            connection_details = self._connection.copy()
            journaling_manager.recordInfo(f"[Mind] Connection details: {connection_details}")
            
            # Initialize base connection through NeurocorticalBridge
            # Pass the connection details from the mind configuration
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            success = await NeurocorticalBridge.initialize_system(connection_type)
            
            if not success:
                journaling_manager.recordError("[Mind] Failed to initialize bridge")
                return False

            # Don't initialize ChatManager yet, we'll create it only when entering chat
            # ChatManager will be initialized in the start_chat function instead
            self._initialized = success
            self._connection_type = connection_type if success else None
            return success
            
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Initialization error: {e}")
            import traceback
            journaling_manager.recordError(f"[Mind] Initialization error trace: {traceback.format_exc()}")
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
    
    async def think(self, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """
        Send a thought prompt to the LLM
        
        Args:
            prompt: The thought prompt
            stream: Whether to stream results
            
        Returns:
            Dict with response from LLM
        """
        try:
            # Create the think command
            think_command = {
                "request_id": f"think_{int(time.time())}",
                "work_id": "llm",
                "action": "inference",
                "data": {
                    "prompt": prompt,
                    "stream": stream
                }
            }
            
            # Execute via bridge
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            result = await NeurocorticalBridge.execute(think_command)
            
            # Return standardized result format
            if isinstance(result, dict) and result.get("status") == "ok":
                return {
                    "status": "ok",
                    "response": result.get("response", ""),
                    "raw_response": result
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "Thinking failed"),
                    "raw_response": result
                }
        except Exception as e:
            journaling_manager.recordError(f"⚠️ Error: {e}")
            import traceback
            journaling_manager.recordError(f"❌ Stack trace: {traceback.format_exc()}")
            return {
                "status": "error", 
                "message": str(e)
            }

    async def reset_system(self):
        """Reset the LLM system"""
        journaling_manager.recordDebug(f"[Mind.reset_system] 🔄 Resetting LLM system...")
        journaling_manager.recordDebug(f"[Mind.reset_system] 🔄 Connection type: {self._connection_type}")
        journaling_manager.recordDebug(f"[Mind.reset_system] 🔄 Initialized: {self._initialized}")
        
        journaling_manager.recordInfo("[Mind] Resetting system")
        
        try:
            # Import NeurocorticalBridge here to avoid circular imports
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Use direct reset method 
            result = await NeurocorticalBridge._direct_reset_system()
            
            # Log the result
            journaling_manager.recordDebug(f"[Mind.reset_system] 📊 Reset result: {json.dumps(result, indent=2)}")
            
            # Return standardized format
            if result.get("status") == "ok":
                return {
                    "status": "ok",
                    "message": result.get("message", "Reset successful"),
                    "response": result.get("response", {})
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "Reset failed"),
                    "response": result.get("response", {})
                }
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Reset error: {e}")
            import traceback
            journaling_manager.recordDebug(f"[Mind] Reset error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
    
    async def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information using hwinfo API command with direct transport"""
        try:
            # Import NeurocorticalBridge here to avoid circular imports
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Create hardware info command
            hw_command = NeurocorticalBridge.create_sys_command("hwinfo")
            
            journaling_manager.recordDebug(f"[Mind.get_hardware_info] Getting hardware info...")
            journaling_manager.recordDebug(f"[Mind.get_hardware_info] Command: {json.dumps(hw_command, indent=2)}")
            
            # Send directly through transport
            result = await NeurocorticalBridge._send_to_hardware(hw_command)
            
            journaling_manager.recordDebug(f"[Mind.get_hardware_info] 📊 Result: {json.dumps(result, indent=2)}")
            
            # Check if we got data from the API
            if isinstance(result, dict) and "error" in result and isinstance(result["error"], dict) and result["error"].get("code") == 0:
                # Extract the hardware data field
                if "data" in result:
                    hw_data = result["data"]
                    
                    # Temperature might be in millicelsius (as per API, temperature: 46350 means 46.35°C)
                    if "temperature" in hw_data and isinstance(hw_data["temperature"], (int, float)):
                        if hw_data["temperature"] > 1000:  # Likely in millicelsius
                            hw_data["temperature"] = hw_data["temperature"] / 1000.0
                    
                    # Update the hardware info in SynapticPathways
                    from .CorpusCallosum.synaptic_pathways import SynapticPathways
                    SynapticPathways.update_hardware_info(hw_data)
                    
                    # Format the hardware info for display
                    formatted = SynapticPathways.format_hw_info()
                    return {"status": "ok", "hardware_info": formatted, "data": hw_data}
            
            return {"status": "error", "message": "Failed to get hardware info", "raw_response": result}
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Hardware info error: {e}")
            import traceback
            journaling_manager.recordDebug(f"Hardware info error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
    
    async def ping_system(self):
        """Ping the system to check connectivity using direct transport"""
        journaling_manager.recordDebug(f"[Mind.ping_system] 🔍 Pinging system...")
        journaling_manager.recordDebug(f"[Mind.ping_system] 🔄 Connection type: {self._connection_type}")
        journaling_manager.recordDebug(f"[Mind.ping_system] 🔄 Initialized: {self._initialized}")
        
        try:
            # Import NeurocorticalBridge here to avoid circular imports
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Use the direct ping method which doesn't depend on BasalGanglia
            result = await NeurocorticalBridge._direct_ping()
            
            journaling_manager.recordDebug(f"[Mind.ping_system] 📊 Raw result: {json.dumps(result, indent=2) if result else 'None'}")
            
            # Check if NeurocorticalBridge already standardized the response
            if isinstance(result, dict) and result.get("status") == "ok":
                journaling_manager.recordDebug(f"[Mind.ping_system] ✅ Connection successful (standardized response)")
                return result
            
            # Check if result contains an error section with code 0 (success)
            if isinstance(result, dict):
                # Try to get direct response from API
                response = result.get("response", {})
                if isinstance(response, dict) and "error" in response:
                    error = response.get("error", {})
                    if isinstance(error, dict) and error.get("code") == 0:
                        journaling_manager.recordDebug(f"[Mind.ping_system] ✅ Connection successful (API response)")
                        # Success - API returned error code 0
                        return {
                            "status": "ok",
                            "raw_response": response
                        }
                
                # Try original format as well (sometimes _direct_ping returns the unwrapped API response)
                if "error" in result and isinstance(result["error"], dict) and result["error"].get("code") == 0:
                    journaling_manager.recordDebug(f"[Mind.ping_system] ✅ Connection successful (unwrapped API response)")
                    return {
                        "status": "ok",
                        "raw_response": result
                    }
            
            # Format as standardized error response
            journaling_manager.recordDebug(f"[Mind.ping_system] ❌ Connection failed")
            return {
                "status": "error", 
                "message": result.get("message", "Ping failed"),
                "raw_response": result
            }
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Ping error: {e}")
            import traceback
            journaling_manager.recordDebug(f"[Mind] Ping error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
    
    async def list_models(self):
        """List available models using lsmode API command with direct transport"""
        journaling_manager.recordDebug(f"[Mind.list_models] 🔍 Listing models...")
        
        try:
            # Import NeurocorticalBridge here to avoid circular imports
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Create lsmode command
            lsmode_command = NeurocorticalBridge.create_sys_command("lsmode")
            
            journaling_manager.recordDebug(f"[Mind.list_models] Command: {json.dumps(lsmode_command, indent=2)}")
            
            # Send directly through transport
            result = await NeurocorticalBridge._send_to_hardware(lsmode_command)
            
            journaling_manager.recordDebug(f"[Mind.list_models] 📊 Raw result: {json.dumps(result, indent=2)}")
            
            # Check if we got data from the API
            if isinstance(result, dict) and "error" in result and isinstance(result["error"], dict) and result["error"].get("code") == 0:
                # If we got data in the format we expect
                if "data" in result and isinstance(result["data"], list):
                    # Format the response for consistency
                    models_data = result["data"]
                    
                    # Cache the models in SynapticPathways for later use
                    try:
                        from .CorpusCallosum.synaptic_pathways import SynapticPathways
                        SynapticPathways.available_models = models_data
                    except ImportError:
                        pass  # It's ok if we can't cache it
                    
                    # Debug info about models
                    models_count = len(models_data)
                    journaling_manager.recordDebug(f"[Mind.list_models] ✅ Found {models_count} models")
                    
                    # Return standardized response
                    return {
                        "status": "ok",
                        "response": models_data
                    }
            
            # If we didn't get expected data from API or it failed
            return {
                "status": "error",
                "message": "Failed to get models list or invalid format",
                "raw_response": result
            }
        except Exception as e:
            journaling_manager.recordError(f"[Mind] List models error: {e}")
            import traceback
            journaling_manager.recordDebug(f"List models error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
        
    async def set_model(self, model_name: str):
        """Set the active model using LLM module's setup API"""
        journaling_manager.recordDebug(f"[Mind.set_model] 🔄 Setting model: {model_name}")
        journaling_manager.recordDebug(f"[Mind.set_model] 🔄 Connection type: {self._connection_type}")
        journaling_manager.recordDebug(f"[Mind.set_model] 🔄 Initialized: {self._initialized}")
        
        # Create command using llm setup format as per API spec
        command_data = {
            "model": model_name,
            "response_format": "llm.utf-8",  # Standard output
            "input": "llm.utf-8",            # UART input
            "enoutput": True,                # Enable UART output
            "enkws": False,                  # No KWS interruption
            "max_token_len": 127,            # Recommended token length
            "prompt": self._persona          # System message/persona
        }
        
        journaling_manager.recordDebug(f"[Mind.set_model] 📋 Command data prepared with LLM setup format")
        
        try:
            # Try direct transport method first
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            from Mind.Subcortex.api_commands import CommandFactory
            
            # Create proper LLM setup command per API spec
            setup_command = CommandFactory.create_llm_setup_command(
                model_name=model_name,
                persona=self._persona
            )
            
            journaling_manager.recordDebug(f"[Mind.set_model] 🔌 Using direct transport method")
            journaling_manager.recordDebug(f"[Mind.set_model] 📦 Command: {json.dumps(setup_command, indent=2)}")
            
            # Send directly through hardware transport
            direct_result = await NeurocorticalBridge._send_to_hardware(setup_command)
            
            journaling_manager.recordDebug(f"[Mind.set_model] 📊 Direct result: {json.dumps(direct_result, indent=2)}")
            
            # Process result
            if isinstance(direct_result, dict) and "error" in direct_result:
                error = direct_result.get("error", {})
                if isinstance(error, dict) and error.get("code") == 0:
                    # Success according to API
                    journaling_manager.recordDebug(f"[Mind.set_model] ✅ Successfully set model: {model_name}")
                    
                    # Update the default model
                    self.set_default_model(model_name)
                    
                    return {
                        "status": "ok",
                        "model": model_name,
                        "raw_response": direct_result
                    }
                else:
                    # API error
                    error_message = error.get("message", "Unknown error")
                    journaling_manager.recordDebug(f"[Mind.set_model] ❌ Error setting model: {error_message}")
                    
                    return {
                        "status": "error",
                        "message": error_message,
                        "raw_response": direct_result
                    }
            
            # Unexpected format
            journaling_manager.recordDebug(f"[Mind.set_model] ❌ Unexpected response format")
            return {
                "status": "error",
                "message": "Invalid response format from hardware",
                "raw_response": direct_result
            }
            
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Error setting model: {e}")
            import traceback
            journaling_manager.recordDebug(f"Set model error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
        
    async def reboot_device(self):
        """Reboot the connected device"""
        journaling_manager.recordDebug(f"[Mind.reboot_device] 🔄 Rebooting device...")
        journaling_manager.recordDebug(f"[Mind.reboot_device] 🔄 Connection type: {self._connection_type}")
        journaling_manager.recordDebug(f"[Mind.reboot_device] 🔄 Initialized: {self._initialized}")
        
        journaling_manager.recordInfo("[Mind] Rebooting device")
        
        try:
            # Import NeurocorticalBridge here to avoid circular imports
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Use direct reboot method
            result = await NeurocorticalBridge._direct_reboot()
            
            journaling_manager.recordDebug(f"[Mind.reboot_device] 📊 Result: {json.dumps(result, indent=2)}")
            
            # Return standardized format
            if result.get("status") == "ok":
                return {
                    "status": "ok",
                    "message": result.get("message", "Rebooting..."),
                    "response": result.get("response", {})
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "Reboot command failed"),
                    "response": result.get("response", {})
                }
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Reboot error: {e}")
            import traceback
            journaling_manager.recordDebug(f"[Mind] Reboot error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
    
    async def connect(self, connection_type=None):
        """Connect to hardware using the specified connection type"""
        journaling_manager.recordInfo(f"[Mind] Connecting with type: {connection_type or self._connection_type}")
        
        # Use the connection type from the mind config if not specified
        if connection_type is None:
            connection_type = self._connection_type
        
        # Get connection details from the mind configuration
        connection_details = self._connection.copy()
        journaling_manager.recordInfo(f"[Mind] Using connection settings: {connection_details}")
        
        # Use initialize method which uses NeurocorticalBridge.initialize_system
        return await self.initialize(connection_type)
    
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
        """Get the currently active model from memory (not directly from device)"""
        journaling_manager.recordInfo("[Mind] Getting active model information")
        journaling_manager.recordDebug("[Mind] Note: Device doesn't support direct model query, using cached model info")
        
        try:
            # Get the model from SynapticPathways
            from .CorpusCallosum.synaptic_pathways import SynapticPathways
            model_name = SynapticPathways.default_llm_model
            
            if model_name:
                journaling_manager.recordDebug(f"[Mind.get_model] Current model (from cache): {model_name}")
                return {
                    "status": "ok",
                    "response": model_name
                }
            else:
                # If no model is set in memory, we don't know the current model
                journaling_manager.recordDebug("[Mind.get_model] No model is currently set in memory")
                return {
                    "status": "unknown",
                    "message": "No model currently set in memory"
                }
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Error getting model info: {e}")
            return {
                "status": "error",
                "message": f"Error retrieving model info: {str(e)}"
            }
        
    async def process_thought(self, input_text: str) -> Dict[str, Any]:
        """
        Process a thought/message and generate a response
        Used by the chat interface
        
        Args:
            input_text: The user input to process
            
        Returns:
            Dict with status and response
        """
        journaling_manager.recordInfo(f"[Mind] Processing thought: {input_text[:50]}...")
        
        try:
            # Use the think method
            result = await self.think(input_text)
            
            # Format the response in a standard way
            if isinstance(result, dict) and result.get("status") == "ok":
                return {
                    "status": "ok",
                    "response": result.get("response", "")
                }
            elif isinstance(result, str):
                return {
                    "status": "ok",
                    "response": result
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "Unknown error")
                }
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Error processing thought: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

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
            
            # Then clean up connection resources through NeurocorticalBridge
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            await NeurocorticalBridge.cleanup()
            
            journaling_manager.recordInfo("[Mind] Complete cleanup successful")
            return True
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Error during complete cleanup: {e}")
            import traceback
            journaling_manager.recordError(f"[Mind] Cleanup error trace: {traceback.format_exc()}")
            return False

    async def check_connection(self) -> Dict[str, Any]:
        """Check system connectivity"""
        journaling_manager.recordDebug(f"[Mind.check_connection] 🔍 Checking connection...")
        journaling_manager.recordDebug(f"[Mind.check_connection] 🔄 Connection type: {self._connection_type}")
        journaling_manager.recordDebug(f"[Mind.check_connection] 🔄 Initialized: {self._initialized}")
        
        try:
            # Use ping operation to check connection
            result = await self.ping_system()
            
            # Log the result
            journaling_manager.recordDebug(f"[Mind.check_connection] 📊 Ping result: {json.dumps(result, indent=2)}")
            
            # Use the standardized result from ping_system
            if result.get("status") == "ok":
                journaling_manager.recordDebug(f"[Mind.check_connection] ✅ Connection successful")
                return {"status": "ok"}
            else:
                journaling_manager.recordDebug(f"[Mind.check_connection] ❌ Connection failed: {result.get('message', 'Unknown error')}")
                return {"status": "error", "message": result.get("message", "Connection check failed")}
        except Exception as e:
            journaling_manager.recordDebug(f"[Mind.check_connection] ❌ Connection error: {e}")
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

    def get_chat_manager(self):
        """
        Get or lazily create the chat manager instance
        
        Returns:
            ChatManager instance
        """
        if self.chat_manager is None:
            # Import here to avoid circular import
            from Interaction.chat_manager import ChatManager
            self.chat_manager = ChatManager(self)
            
        return self.chat_manager

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
    
    # Use NeurocorticalBridge's initialize_system method directly
    return await NeurocorticalBridge.initialize_system(connection_type) 