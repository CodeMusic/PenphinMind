"""
Neurological Function:
    Primary auditory area (A1) processes basic sound characteristics.

Project Function:
    Core audio processing from AudioManager functionality
"""

from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import CommandType, AudioCommand, VADCommand
from config import CONFIG, AudioOutputType
import logging
from typing import Optional, Dict, Any
import subprocess
from pathlib import Path

class PrimaryArea:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vad_active: bool = False
        self.current_stream: Optional[bytes] = None
        self._setup_auditory_pathway()
        self.is_active = False
        self.audio_threshold = 0.1
        
    def _setup_auditory_pathway(self) -> None:
        if CONFIG.audio_output_type == AudioOutputType.WAVESHARE:
            try:
                subprocess.run(["amixer", "-c", "0", "sset", "Speaker", f"{CONFIG.audio_volume}%"], check=True)
                subprocess.run(["amixer", "-c", "0", "sset", "Playback", f"{CONFIG.audio_volume}%"], check=True)
                subprocess.run(["amixer", "-c", "0", "sset", "Headphone", f"{CONFIG.audio_volume}%"], check=True)
                subprocess.run(["amixer", "-c", "0", "sset", "PCM", f"{CONFIG.audio_volume}%"], check=True)
                self.logger.info("WaveShare audio HAT configured")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error configuring WaveShare audio HAT: {e}")
                raise AudioProcessingError("Failed to configure audio device")

    async def process_audio(self, audio_data: bytes, operation: str = "normalize") -> bytes:
        try:
            response = await SynapticPathways.transmit_command(
                AudioCommand(
                    command_type=CommandType.AUDIO,
                    operation=operation,
                    audio_data=audio_data,
                    sample_rate=CONFIG.audio_sample_rate,
                    channels=CONFIG.audio_channels
                )
            )
            return response.get("processed_audio", b'')
        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
            return audio_data 

    async def process_raw_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process basic audio features like frequency and amplitude
        """
        try:
            response = await SynapticPathways.transmit_json({
                "type": "audio_analysis",
                "audio_data": audio_data,
                "features": ["frequency", "amplitude", "pitch"]
            })
            
            self.logger.info("Processed raw audio features")
            return response

        except Exception as e:
            self.logger.error(f"Raw audio processing error: {e}")
            return {}

    async def detect_silence(self, audio_data: bytes) -> bool:
        """
        Detect periods of silence in audio
        """
        try:
            features = await self.process_raw_audio(audio_data)
            amplitude = features.get("amplitude", 0.0)
            return amplitude < self.audio_threshold

        except Exception as e:
            self.logger.error(f"Silence detection error: {e}")
            return False

    async def filter_background_noise(self, audio_data: bytes) -> Optional[bytes]:
        """
        Filter out background noise from audio input
        """
        try:
            response = await SynapticPathways.transmit_json({
                "type": "noise_reduction",
                "audio_data": audio_data
            })
            
            filtered_audio = response.get("filtered_audio")
            self.logger.info("Filtered background noise")
            return filtered_audio

        except Exception as e:
            self.logger.error(f"Noise filtering error: {e}")
            return None 