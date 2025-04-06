"""
Main Mind class that coordinates all brain regions
"""

import logging
import platform
import json
import time
import asyncio
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

# Initialize journaling manager with config log level
journaling_manager = SystemJournelingManager(CONFIG.log_level)

logger = logging.getLogger(__name__)

class Mind:
    """Main interface for interacting with PenphinMind"""
    
    # Class variables
    _current_llm_work_id = None  # Store the current LLM work_id
    
    def __init__(self, mind_id: str = None, persona: str = "You are a helpful assistant."):
        """Initialize Mind with optional configuration ID from minds_config.json"""
        journaling_manager.recordScope("Mind.__init__")
        
        # Ensure persona is provided
        if not persona:
            raise ValueError("Persona cannot be empty")
            
        # Initialize basic attributes
        self._mind_id = None
        self._config = {}
        self._name = "PenphinMind"
        self._connection_type = None
        self._initialized = False
        self._ip = None
        self._port = None
        self._persona = persona
        self._device_id = ""
        
        # Set mind_id and load configuration if provided
        self.mind_id = mind_id
        if mind_id:
            self._load_config(mind_id)
            
            # Now initialize connection settings from loaded config
            if "connection" in self._config:
                self._connection_type = self._config["connection"].get("type", "tcp")
                self._ip = self._config["connection"].get("ip", "auto")
                self._port = self._config["connection"].get("port", "auto")
            else:
                journaling_manager.recordWarning(f"No connection configuration found for mind: {mind_id}")
                self._connection_type = "tcp"  # Default
                self._ip = "auto"
                self._port = "auto"
        
        # Default system prompts
        self._llm_config = {
            "persona": self._persona,
            "stream": True,  # Default to streaming mode for better UX
            "model": None
        }
        
        # If there's an llm config in the mind config, update with our settings
        if "llm" in self._config:
            # Start with the config llm settings
            llm_settings = self._config["llm"].copy()
            # But always use our persona
            llm_settings["persona"] = self._persona
            self._llm_config.update(llm_settings)
        
        # Initialize the default model from config if available
        if "llm" in self._config and "default_model" in self._config["llm"]:
            self._default_model = self._config["llm"]["default_model"]
        else:
            self._default_model = "qwen2.5-0.5b"  # Default fallback
        
        # Initialize chat_manager as None - will be created when needed
        # We don't import ChatManager here to avoid circular imports
        self.chat_manager = None
        
        if hasattr(self, '_persona'):
            journaling_manager.recordInfo(f"[Mind] Initialized with persona: {self._persona[:50]}...")
        
        # Initialize instance variables
        self._occipital_lobe = {}
        self._temporal_lobe = {}
        self._parietal_lobe = {}
        self._motor_cortex = {}
        self.primary_acoustic = None
        self._processing = False
        self._language_processor = None  # Language processor instance
        self._system_journeling_manager = SystemJournelingManager(CONFIG.log_level)
        
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
        
    @mind_id.setter
    def mind_id(self, value: str):
        """Set the mind's ID"""
        self._mind_id = value
        
    def _load_config(self, mind_id: str) -> None:
        """
        Load mind-specific configuration from mind_config.py
        
        Args:
            mind_id: ID of the mind to load configuration for
        """
        journaling_manager.recordScope("Mind._load_config", mind_id=mind_id)
        journaling_manager.recordInfo(f"[Mind] Loading configuration for mind: {mind_id}")
        
        # Get mind configuration using the mind_config module
        mind_config = get_mind_by_id(mind_id)
        
        # Store the configuration
        self._config = mind_config
        
        # Store key properties from the configuration
        self._name = mind_config.get("name", "PenphinMind")
        self._device_id = mind_config.get("device_id", "")
        
        # Ensure connection settings are properly initialized
        connection_settings = mind_config.get("connection", {})
        if connection_settings:
            self._connection = connection_settings
            # Also set individual connection properties for direct access
            self._connection_type = connection_settings.get("type", "tcp")
            self._ip = connection_settings.get("ip", "auto")
            self._port = connection_settings.get("port", "auto")
        else:
            # Default connection settings if not in config
            self._connection = {
                "type": "tcp", 
                "ip": "auto", 
                "port": "auto"
            }
            self._connection_type = "tcp"
            self._ip = "auto"
            self._port = "auto"
            journaling_manager.recordWarning(f"[Mind] No connection settings in mind config, using defaults")
        
        # Store LLM configuration
        self._llm_config = mind_config.get("llm", {
            "default_model": "qwen2.5-0.5b",
            "persona": self._persona,
            "stream": True
        })
        
        # Ensure the persona is always from initialization
        self._llm_config["persona"] = self._persona
        
        # Set the default model from LLM config
        self._default_model = self._llm_config.get("default_model", "qwen2.5-0.5b")
        
        # Update SynapticPathways with the default model for cross-component access
        try:
            from .CorpusCallosum.synaptic_pathways import SynapticPathways
            SynapticPathways.default_llm_model = self._default_model
            journaling_manager.recordDebug(f"[Mind] Updated SynapticPathways with default model: {self._default_model}")
        except ImportError:
            journaling_manager.recordWarning("[Mind] Could not update SynapticPathways with default model")
        
        # Process additional configuration sections if available
        if "hardware" in mind_config:
            hardware_config = mind_config.get("hardware", {})
            try:
                from .CorpusCallosum.synaptic_pathways import SynapticPathways
                SynapticPathways.update_hardware_info(hardware_config)
                journaling_manager.recordDebug(f"[Mind] Updated hardware info from config")
            except ImportError:
                journaling_manager.recordWarning("[Mind] Could not update hardware info from config")
        
        # Populate any additional capabilities from the config
        for capability_name, capability_config in mind_config.items():
            if capability_name not in ["name", "device_id", "connection", "llm", "hardware"]:
                # Store the capability config in a standardized location
                if not hasattr(self, "_capabilities"):
                    self._capabilities = {}
                self._capabilities[capability_name] = capability_config
                journaling_manager.recordDebug(f"[Mind] Registered capability: {capability_name}")
        
        journaling_manager.recordInfo(f"[Mind] Configuration loaded for {self._name} (ID: {mind_id})")
        
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
            
    async def initialize(self, connection_type: str = None, model_name: str = None, visual_only: bool = False, auditory_only: bool = False, complete: bool = False) -> bool:
        """
        Initialize the Mind system
        
        Args:
            connection_type: Type of connection to use
            model_name: Optional LLM model to use
            visual_only: If True, only initialize visual components for splash screen
            auditory_only: If True, only initialize auditory components for sound test
            complete: If True, complete the initialization after a partial initialization
            
        Returns:
            bool: True if initialization was successful
        """
        try:
            # If already fully initialized and not forced to complete, return success
            if self._initialized and not complete:
                return True
                
            # Use the connection type from the mind config if not specified
            if connection_type is None:
                connection_type = self._connection_type
            
            journaling_manager.recordInfo(f"[Mind] Initializing with connection type: {connection_type}")
            journaling_manager.recordInfo(f"[Mind] Using connection settings from mind ID: {self._mind_id}")
            
            # Get connection settings from the mind configuration if available
            connection_details = {}
            if hasattr(self, '_connection'):
                connection_details = self._connection.copy()
            else:
                journaling_manager.recordWarning("[Mind] No connection details available in mind configuration")
            
            journaling_manager.recordInfo(f"[Mind] Connection details: {connection_details}")
            
            # Initialize SynapticPathways and NeurocorticalBridge
            from .CorpusCallosum.synaptic_pathways import SynapticPathways
            from .Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Skip actual connection if we're just initializing visual or auditory
            connection_result = True
            
            if not visual_only and not auditory_only:
                # Initialize NeurocorticalBridge for connection to hardware
                connection_result = await NeurocorticalBridge.initialize_system(connection_type)
                journaling_manager.recordInfo(f"[Mind] Connection result: {connection_result}")
                
                # If connection failed and this is a complete initialization, return failure
                if not connection_result and complete:
                    journaling_manager.recordError("[Mind] Connection failed during complete initialization")
                    return False
            
            # Initialize specific brain regions if requested
            success = True
            
            # Visual-only initialization for splash screen
            if visual_only or not auditory_only:
                try:
                    # Initialize visual processing components
                    if "visual" in self._occipital_lobe:
                        journaling_manager.recordInfo("[Mind] Initializing visual cortex...")
                        self._occipital_lobe["visual"].initialize()
                        journaling_manager.recordInfo("[Mind] Visual cortex initialized")
                except Exception as e:
                    journaling_manager.recordError(f"[Mind] Visual cortex initialization error: {e}")
                    if not auditory_only:  # Only fail if this wasn't just a temporary visual init for splash
                        success = False
                
            # Auditory-only initialization for audio testing
            if auditory_only or not visual_only:
                try:
                    # Initialize auditory processing components
                    if "auditory" in self._temporal_lobe:
                        journaling_manager.recordInfo("[Mind] Initializing auditory cortex...")
                        self._temporal_lobe["auditory"].initialize()
                        journaling_manager.recordInfo("[Mind] Auditory cortex initialized")
                except Exception as e:
                    journaling_manager.recordError(f"[Mind] Auditory cortex initialization error: {e}")
                    if not visual_only:  # Only fail if this wasn't just a temporary auditory init for test
                        success = False
            
            # If this is a complete initialization or not partial, initialize all remaining components
            if complete or (not visual_only and not auditory_only):
                # Initialize the remaining brain regions
                try:
                    # Motor & Somatosensory
                    if "motor" in self._motor_cortex:
                        journaling_manager.recordInfo("[Mind] Initializing motor cortex...")
                        self._motor_cortex["motor"].initialize()
                        journaling_manager.recordInfo("[Mind] Motor cortex initialized")
                        
                    if "somatosensory" in self._parietal_lobe:
                        journaling_manager.recordInfo("[Mind] Initializing somatosensory cortex...")
                        self._parietal_lobe["somatosensory"].initialize()
                        journaling_manager.recordInfo("[Mind] Somatosensory cortex initialized")
                except Exception as e:
                    journaling_manager.recordError(f"[Mind] Brain region initialization error: {e}")
                    success = False
            
            # Store model name for later (used when chat is initialized, not setting model here)
            # This prevents the model loading during initialization
            if model_name:
                self._default_model = model_name
                journaling_manager.recordInfo(f"[Mind] Stored model name for later use: {model_name}")
            elif complete and self._default_model:
                journaling_manager.recordInfo(f"[Mind] Using default model from config: {self._default_model}")
            
            # Only set the model when explicitly completing initialization AND not in auditory_only mode
            if complete and not auditory_only and success and self._default_model and connection_result:
                journaling_manager.recordInfo(f"[Mind] Setting default model from config during completion: {self._default_model}")
                model_result = await self.set_model(self._default_model)
                if model_result.get("status") != "ok":
                    journaling_manager.recordWarning(f"[Mind] Failed to set default model: {model_result.get('message', 'Unknown error')}")
                    # Continue despite model loading error - this is non-critical
            
            # Initialize any capabilities defined in the config
            if success and hasattr(self, "_capabilities"):
                journaling_manager.recordInfo(f"[Mind] Initializing {len(self._capabilities)} capabilities from config")
                for capability_name, capability_config in self._capabilities.items():
                    try:
                        journaling_manager.recordDebug(f"[Mind] Initializing capability: {capability_name}")
                        # Here you would initialize specific capabilities based on config
                        # This is extensibility point for future capabilities
                    except Exception as e:
                        journaling_manager.recordError(f"[Mind] Error initializing capability {capability_name}: {e}")
            
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
            # Use NeurocorticalBridge.create_llm_inference_command instead of creating manually
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Get the work_id from instance or class storage
            work_id = self._current_llm_work_id or Mind._current_llm_work_id
            
            # Verify we have a valid work_id in llm.XXXX format
            if not work_id or not work_id.startswith("llm."):
                journaling_manager.recordWarning(f"[Mind.think] ⚠️ Invalid work_id format: {work_id}")
                journaling_manager.recordWarning("[Mind.think] ⚠️ Falling back to default 'llm'")
                work_id = "llm"
            else:
                journaling_manager.recordInfo(f"[Mind.think] ✅ Using work_id: {work_id}")
            
            # Create the think command
            think_command = NeurocorticalBridge.create_llm_inference_command(
                prompt=prompt,
                stream=stream,
                work_id=work_id
            )
            
            # Debug log the command
            journaling_manager.recordDebug(f"[Mind.think] Command: {json.dumps(think_command)}")
            
            # Execute via bridge
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
            journaling_manager.recordError(f"[Mind.think] Error: {e}")
            import traceback
            journaling_manager.recordError(f"[Mind.think] Stack trace: {traceback.format_exc()}")
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
        """
        Set the LLM model to use
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            Dict with status and response
        """
        try:
            journaling_manager.recordInfo(f"Setting LLM model to: {model_name}")
            
            # Create command data
            data = {
                "model": model_name,
                "persona": self._llm_config.get("persona", "You are a helpful assistant.")
            }
            
            # Debug log before executing
            journaling_manager.recordDebug(f"[Mind.set_model] Set model request data: {json.dumps(data)}")
            
            # Execute command
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            result = await NeurocorticalBridge.execute_operation(
                operation="set_model",
                data=data
            )
            
            # Debug log the complete response
            journaling_manager.recordDebug(f"[Mind.set_model] Complete response: {json.dumps(result)}")
            
            # If successful, store the model name
            if result.get("status") == "ok":
                self._llm_config["model"] = model_name
                journaling_manager.recordInfo(f"Model set to {model_name}")
                
                # Extract and store the work_id - we know it's in result.response.work_id 
                response = result.get("response", {})
                if isinstance(response, dict) and "work_id" in response:
                    work_id = response["work_id"]
                    self._current_llm_work_id = work_id
                    Mind._current_llm_work_id = work_id
                    journaling_manager.recordInfo(f"✅ Work ID set: {work_id}")
                else:
                    journaling_manager.recordWarning(f"⚠️ Expected work_id not found in response")
                    
                    # If not found, try fallback methods
                    if not self._current_llm_work_id:
                        # Regex fallback for llm.XXXX format
                        import re
                        response_str = str(result)
                        work_id_match = re.search(r'llm\.\d+', response_str)
                        if work_id_match:
                            work_id = work_id_match.group(0)
                            self._current_llm_work_id = work_id
                            Mind._current_llm_work_id = work_id
                            journaling_manager.recordInfo(f"✅ Found work_id via regex: {work_id}")
            
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"Set model error: {e}")
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
        
        # Get connection details from the mind configuration if available
        if hasattr(self, '_connection'):
            connection_details = self._connection.copy()
            journaling_manager.recordInfo(f"[Mind] Using connection settings: {connection_details}")
        else:
            journaling_manager.recordInfo("[Mind] No connection details available, using defaults")
        
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

    async def set_persona(self, persona: str) -> None:
        """
        Set the mind's persona
        
        Args:
            persona: The new persona to use
        """
        if not persona:
            raise ValueError("Persona cannot be empty")
            
        # Update the persona
        self._persona = persona
        
        # Also update it in the llm_config
        if hasattr(self, '_llm_config') and isinstance(self._llm_config, dict):
            self._llm_config["persona"] = persona
            
        journaling_manager.recordInfo(f"[Mind] Updated persona: {persona[:50]}...")
        return None

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

    async def llm_inference(self, prompt, stream=None, callback=None, work_id=None):
        """
        Perform LLM inference with the given prompt
        
        Args:
            prompt: Text prompt for the LLM
            stream: Whether to use streaming mode
            callback: For streaming mode, function to handle streaming chunks
            work_id: Specific work_id to use (if None, uses the stored work_id from setup)
            
        Returns:
            str: LLM response
        """
        try:
            # Get streaming mode from config if not provided
            if stream is None:
                stream = self._llm_config.get("stream", True)
            
            # Use provided work_id or get from instance/class
            effective_work_id = work_id
            if not effective_work_id:
                effective_work_id = self._current_llm_work_id or Mind._current_llm_work_id
                
                # Verify proper format
                if not effective_work_id or not effective_work_id.startswith("llm."):
                    journaling_manager.recordWarning(f"[Mind.llm_inference] ⚠️ Invalid work_id: {effective_work_id}")
                    journaling_manager.recordWarning("[Mind.llm_inference] ⚠️ Falling back to default 'llm'")
                    effective_work_id = "llm"
                else:
                    journaling_manager.recordInfo(f"[Mind.llm_inference] ✅ Using work_id: {effective_work_id}")
            
            # Log the inference request
            journaling_manager.recordInfo(f"[Mind.llm_inference] Request: stream={stream}, work_id={effective_work_id}")
            journaling_manager.recordDebug(f"[Mind.llm_inference] Prompt (first 100 chars): {prompt[:100]}...")
            
            # Create data object with explicit work_id
            data = {
                "prompt": prompt,
                "stream": stream,
                "work_id": effective_work_id
            }
            
            # Debug log the inference request data
            journaling_manager.recordDebug(f"[Mind.llm_inference] Data: {json.dumps(data)}")
            
            # Create and execute command
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            result = await NeurocorticalBridge.execute_operation(
                operation="think",
                data=data,
                stream=stream
            )
            
            # Log completion
            journaling_manager.recordInfo(f"[Mind.llm_inference] Completed: {result.get('status', 'unknown')}")
            
            # Return the response for non-streaming mode
            if not stream:
                return result.get("response", "")
            
            # For streaming mode with callback
            if stream and callback:
                import asyncio
                
                # Log callback activation
                journaling_manager.recordDebug(f"[Mind.llm_inference] Starting streaming task")
                
                # Start streaming task
                streaming_task = asyncio.create_task(
                    NeurocorticalBridge.execute_operation(
                        operation="think",
                        data={
                            "prompt": prompt,
                            "stream": True,
                            "work_id": effective_work_id
                        },
                        stream=True,
                        use_task=False
                    )
                )
                
                # Return empty string for streaming mode (callback will handle the response)
                return ""
            
            # Fallback for streaming without callback
            return result.get("response", "")
            
        except Exception as e:
            journaling_manager.recordError(f"[Mind.llm_inference] Error: {e}")
            import traceback
            journaling_manager.recordError(f"[Mind.llm_inference] Stack trace: {traceback.format_exc()}")
            return f"Error: {str(e)}"

    @property
    def capabilities(self) -> Dict[str, Any]:
        """
        Get available capabilities loaded from configuration
        
        Returns:
            Dict mapping capability names to their configurations
        """
        if not hasattr(self, "_capabilities"):
            self._capabilities = {}
        return self._capabilities
    
    def has_capability(self, capability_name: str) -> bool:
        """
        Check if a specific capability is available
        
        Args:
            capability_name: Name of the capability to check
            
        Returns:
            bool: True if the capability is available
        """
        return capability_name in self.capabilities
    
    def get_capability_config(self, capability_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific capability
        
        Args:
            capability_name: Name of the capability
            
        Returns:
            Optional[Dict]: Configuration for the capability or None if not available
        """
        return self.capabilities.get(capability_name)
    
    async def execute_capability(self, capability_name: str, operation: str = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an operation on a specific capability
        
        Args:
            capability_name: Name of the capability
            operation: Operation to execute
            data: Additional data for the operation
            
        Returns:
            Dict with operation result
        """
        journaling_manager.recordInfo(f"[Mind] Executing capability: {capability_name}.{operation}")
        
        # Check if capability exists
        if not self.has_capability(capability_name):
            journaling_manager.recordError(f"[Mind] Capability not available: {capability_name}")
            return {
                "status": "error",
                "message": f"Capability '{capability_name}' not available"
            }
        
        try:
            # Get the capability config
            capability_config = self.get_capability_config(capability_name)
            
            # Log the request
            journaling_manager.recordDebug(f"[Mind.execute_capability] Request: {capability_name}.{operation}")
            journaling_manager.recordDebug(f"[Mind.execute_capability] Config: {json.dumps(capability_config)}")
            journaling_manager.recordDebug(f"[Mind.execute_capability] Data: {json.dumps(data) if data else 'None'}")
            
            # Here we would dispatch to the appropriate handler based on capability_name
            # This is a placeholder for future implementation of specific capabilities
            
            # For now, log that this is unimplemented
            journaling_manager.recordWarning(f"[Mind] Capability '{capability_name}' execution not implemented yet")
            return {
                "status": "error",
                "message": f"Capability '{capability_name}' execution not implemented"
            }
            
        except Exception as e:
            journaling_manager.recordError(f"[Mind] Error executing capability {capability_name}: {e}")
            import traceback
            journaling_manager.recordError(f"[Mind] Capability execution error trace: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error executing capability: {str(e)}"
            }

    def _setup_components(self):
        """
        Set up components for the Mind
        
        This method is called after the base connection is established
        and is intended to be overridden by subclasses to set up additional components
        """
        pass

async def setup_connection(connection_type=None):
    """
    Set up the connection to the hardware
    
    Args:
        connection_type: Type of connection to use (serial, adb, tcp)
    """
    from .FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
    from .Subcortex.neurocortical_bridge import NeurocorticalBridge
    from config import CONFIG
    journaling_manager = SystemJournelingManager(CONFIG.log_level)
    
    journaling_manager.recordScope("setup_connection", connection_type=connection_type)
    
    # Use NeurocorticalBridge's initialize_system method directly
    return await NeurocorticalBridge.initialize_system(connection_type) 