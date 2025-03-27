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
from .FrontalLobe.PrefrontalCortex.llm import LLM
from .FrontalLobe.MotorCortex.motor import Motor
from .TemporalLobe.SuperiorTemporalGyrus.AuditoryCortex.integration_area import IntegrationArea
from .ParietalLobe.SomatosensoryCortex.integration_area import IntegrationArea as SomatosensoryIntegration
from .OccipitalLobe.VisualCortex.integration_area import IntegrationArea as VisualProcessor
from .FrontalLobe.MotorCortex.integration_area import IntegrationArea as MotorIntegration
from .FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from .config import CONFIG
# Add other lobe imports as needed

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

logger = logging.getLogger(__name__)

class Mind:
    """
    High-level coordinator for all brain regions
    """
    def __init__(self):
        # Initialize instance variables
        self._occipital_lobe = {}
        self._temporal_lobe = {}
        self._parietal_lobe = {}
        self._motor_cortex = {}
        self.primary_acoustic = None
        self._initialized = False
        self._processing = False
        self._llm = None  # LLM instance
        
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
            
    async def initialize(self) -> None:
        """Initialize all brain regions"""
        journaling_manager.recordScope("Mind.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Mind already initialized")
            return
            
        try:
            # Initialize synaptic pathways with appropriate test mode
            is_raspberry_pi = self._is_raspberry_pi()
            test_mode = not is_raspberry_pi
            journaling_manager.recordInfo(f"Running on {'Raspberry Pi' if is_raspberry_pi else 'non-Raspberry Pi'}, test_mode={test_mode}")
            await SynapticPathways.initialize(test_mode=test_mode)
            
            # Initialize all integration areas
            for area in self.temporal_lobe.values():
                await area.initialize()
            for area in self.parietal_lobe.values():
                await area.initialize()
            for area in self.occipital_lobe.values():
                await area.initialize()
            for area in self.motor_cortex.values():
                await area.initialize()
            
            # Initialize primary acoustic area if needed
            if not self.primary_acoustic:
                self.primary_acoustic = PrimaryAcousticArea()
                await self.primary_acoustic.initialize()
                
            # Initialize LLM
            self._llm = LLM()
            await self._llm.initialize()
                
            self._initialized = True
            journaling_manager.recordInfo("Mind initialized successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize mind: {e}")
            raise
            
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
                
            # Clean up LLM
            if self._llm:
                await self._llm.cleanup()
                
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
        Process text input through LLM
        
        Args:
            input_text: Text to process
            
        Returns:
            Dict[str, Any]: Processing result containing response and status
        """
        journaling_manager.recordScope("Mind.process_input", input_text=input_text)
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            if not self._llm:
                journaling_manager.recordError("LLM not initialized")
                raise RuntimeError("LLM not initialized")
                
            journaling_manager.recordDebug("Processing input through LLM")
            # Process through LLM
            response = await self._llm.process_input(input_text)
            
            journaling_manager.recordInfo("Successfully processed input")
            return {
                "status": "ok",
                "response": response.get("response", ""),
                "message": response.get("message", "")
            }
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing input: {e}")
            return {
                "status": "error",
                "message": str(e)
            } 