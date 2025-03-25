import asyncio
from typing import Optional, Dict, Any
import logging
from pathlib import Path
import subprocess

from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import (
    CommandType, AudioCommand, VADCommand
)
from config import CONFIG, AudioOutputType

logger = logging.getLogger(__name__)

class AudioPlaybackError(Exception):
    """Audio playback related errors"""
    pass

class AudioManager:
    """Manages audio processing and playback"""
    
    def __init__(self):
        self.logger = logger
        self.vad_active: bool = False
        self.current_stream: Optional[bytes] = None
        self._setup_audio_device()
        
    def _setup_audio_device(self) -> None:
        """Configure audio device based on config"""
        if CONFIG.audio_output_type == AudioOutputType.WAVESHARE:
            try:
                # Set up WaveShare audio HAT
                subprocess.run(["amixer", "-c", "0", "sset", "Speaker", f"{CONFIG.audio_volume}%"], check=True)
                subprocess.run(["amixer", "-c", "0", "sset", "Playback", f"{CONFIG.audio_volume}%"], check=True)
                subprocess.run(["amixer", "-c", "0", "sset", "Headphone", f"{CONFIG.audio_volume}%"], check=True)
                subprocess.run(["amixer", "-c", "0", "sset", "PCM", f"{CONFIG.audio_volume}%"], check=True)
                self.logger.info("WaveShare audio HAT configured")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error configuring WaveShare audio HAT: {e}")
                raise AudioPlaybackError("Failed to configure audio device")
        
    async def start_vad(self) -> None:
        """Start Voice Activity Detection"""
        if self.vad_active:
            return
            
        try:
            self.vad_active = True
            await SynapticPathways.transmit_json(
                VADCommand(
                    command_type=CommandType.VAD,
                    audio_chunk=b'',  # Initial empty chunk
                    threshold=0.5,
                    frame_duration=30
                )
            )
            self.logger.info("VAD started")
        except Exception as e:
            self.logger.error(f"VAD start error: {e}")  
            self.vad_active = False
            raise
            
    async def stop_vad(self) -> None:
        """Stop Voice Activity Detection"""
        if not self.vad_active:
            return
            
        self.vad_active = False
        self.logger.info("VAD stopped")
        
    async def process_audio(self, audio_data: bytes, operation: str = "normalize") -> bytes:
        """
        Process audio data with specified operation
        
        Args:
            audio_data: Raw audio data
            operation: Processing operation to perform
            
        Returns:
            bytes: Processed audio data
        """
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
            
    async def play_sound(self, audio_data: bytes) -> None:
        """
        Play audio data through the system
        
        Args:
            audio_data: Audio data to play
        """
        try:
            if CONFIG.audio_output_type == AudioOutputType.LLM:
                # Use LLM audio system
                await SynapticPathways.transmit_command(
                    AudioCommand(
                        command_type=CommandType.AUDIO,
                        operation="play",
                        audio_data=audio_data,
                        sample_rate=CONFIG.audio_sample_rate,
                        channels=CONFIG.audio_channels
                    )
                )
            else:
                # Use WaveShare audio system
                # Save audio data to temporary file
                temp_file = Path("temp_audio.wav")
                temp_file.write_bytes(audio_data)
                
                try:
                    # Play using aplay
                    subprocess.run(
                        ['aplay', '-D', CONFIG.audio_device, str(temp_file)],
                        check=True,
                        capture_output=True
                    )
                finally:
                    # Cleanup temp file
                    if temp_file.exists():
                        temp_file.unlink()
                        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"WaveShare playback error: {e}")
            raise AudioPlaybackError(f"Failed to play audio: {e}")
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
            raise AudioPlaybackError(f"Failed to play audio: {e}")
            
    def set_volume(self, volume: int) -> None:
        """
        Set audio volume
        
        Args:
            volume: Volume level (0-100)
        """
        volume = max(0, min(100, volume))
        
        if CONFIG.audio_output_type == AudioOutputType.WAVESHARE:
            try:
                for control in ["Speaker", "Playback", "Headphone", "PCM"]:
                    subprocess.run(
                        ['amixer', '-c', '0', 'sset', control, f'{volume}%'],
                        check=True,
                        capture_output=True
                    )
                self.logger.info(f"WaveShare volume set to {volume}%")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error setting WaveShare volume: {e}")
                raise AudioPlaybackError(f"Failed to set volume: {e}")
            
    async def start_stream(self) -> None:
        """Start audio streaming"""
        self.current_stream = b''
        self.logger.info("Audio stream started")
        
    async def stop_stream(self) -> bytes:
        """
        Stop audio streaming and return collected data
        
        Returns:
            bytes: Collected audio data
        """
        data = self.current_stream
        self.current_stream = None
        self.logger.info("Audio stream stopped")
        return data
        
    async def add_to_stream(self, chunk: bytes) -> None:
        """Add chunk to current audio stream"""
        if self.current_stream is not None:
            self.current_stream += chunk 