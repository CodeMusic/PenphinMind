"""
Auditory Integration Area - Processes and integrates auditory information
"""

import logging
from typing import Dict, Any, Optional
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.Subcortex.api_commands import BaseCommand, AudioCommand, CommandType

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class IntegrationArea:
    """Processes and integrates auditory information"""
    
    def __init__(self):
        """Initialize the integration area"""
        journaling_manager.recordScope("AuditoryIntegrationArea.__init__")
        self._initialized = False
        self._processing = False
        
        # Register with SynapticPathways
        SynapticPathways.register_integration_area("auditory", self)
        
    async def initialize(self) -> None:
        """Initialize the integration area"""
        if self._initialized:
            return
            
        try:
            # Initialize audio processing components
            self._initialized = True
            journaling_manager.recordInfo("Auditory integration area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize auditory integration area: {e}")
            raise
            
    async def process_command(self, command: BaseCommand) -> Dict[str, Any]:
        """Process an auditory command"""
        if not self._initialized:
            raise RuntimeError("Integration area not initialized")
            
        if self._processing:
            raise RuntimeError("Already processing a command")
            
        try:
            self._processing = True
            
            if not isinstance(command, AudioCommand):
                raise ValueError(f"Expected AudioCommand, got {type(command)}")
            
            # Process command based on action
            if command.action == "tts":
                return await self._process_tts(command)
            elif command.action == "asr":
                return await self._process_asr(command)
            elif command.action == "vad":
                return await self._process_vad(command)
            elif command.action == "whisper":
                return await self._process_whisper(command)
            else:
                raise ValueError(f"Unknown audio action: {command.action}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            self._processing = False
            
    async def _process_tts(self, command: AudioCommand) -> Dict[str, Any]:
        """Process text-to-speech command"""
        try:
            response = await SynapticPathways.send_tts(
                text=command.data["text"],
                voice_id=command.data.get("voice", "default"),
                speed=command.data.get("speed", 1.0),
                pitch=command.data.get("pitch", 1.0)
            )
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing TTS command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_asr(self, command: AudioCommand) -> Dict[str, Any]:
        """Process automatic speech recognition command"""
        try:
            response = await SynapticPathways.send_asr(
                audio_data=command.data["audio_data"],
                language=command.data.get("language", "en"),
                model_type=command.data.get("model_type", "base")
            )
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing ASR command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_vad(self, command: AudioCommand) -> Dict[str, Any]:
        """Process voice activity detection command"""
        try:
            response = await SynapticPathways.send_vad(
                audio_chunk=command.data["audio_chunk"],
                threshold=command.data.get("threshold", 0.5),
                frame_duration=command.data.get("frame_duration", 30)
            )
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing VAD command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_whisper(self, command: AudioCommand) -> Dict[str, Any]:
        """Process whisper command"""
        try:
            response = await SynapticPathways.send_whisper(
                audio_data=command.data["audio_data"],
                language=command.data.get("language", "en"),
                model_type=command.data.get("model_type", "base")
            )
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing whisper command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Auditory integration area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up auditory integration area: {e}")
            raise 