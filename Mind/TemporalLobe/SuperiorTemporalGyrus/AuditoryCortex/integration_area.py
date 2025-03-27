"""
Auditory Integration Area - Processes and integrates auditory information
"""

import logging
from typing import Dict, Any, Optional
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

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
            
    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process an auditory command"""
        if not self._initialized:
            raise RuntimeError("Integration area not initialized")
            
        if self._processing:
            raise RuntimeError("Already processing a command")
            
        try:
            self._processing = True
            
            # Process command based on type
            command_type = command.get("type")
            if command_type == "TTS":
                return await self._process_tts(command)
            elif command_type == "ASR":
                return await self._process_asr(command)
            elif command_type == "VAD":
                return await self._process_vad(command)
            else:
                raise ValueError(f"Unknown command type: {command_type}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            self._processing = False
            
    async def _process_tts(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process text-to-speech command"""
        try:
            text = command.get("text", "")
            voice_id = command.get("voice_id", "default")
            speed = command.get("speed", 1.0)
            pitch = command.get("pitch", 1.0)
            
            # Process TTS command
            response = await SynapticPathways.send_tts(
                text=text,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch
            )
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing TTS command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_asr(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process automatic speech recognition command"""
        try:
            audio_data = command.get("audio_data")
            language = command.get("language", "en")
            model_type = command.get("model_type", "base")
            
            # Process ASR command
            response = await SynapticPathways.send_asr(
                audio_data=audio_data,
                language=language,
                model_type=model_type
            )
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing ASR command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_vad(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice activity detection command"""
        try:
            audio_chunk = command.get("audio_chunk")
            threshold = command.get("threshold", 0.5)
            frame_duration = command.get("frame_duration", 30)
            
            # Process VAD command
            response = await SynapticPathways.send_vad(
                audio_chunk=audio_chunk,
                threshold=threshold,
                frame_duration=frame_duration
            )
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing VAD command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Auditory integration area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up auditory integration area: {e}")
            raise 