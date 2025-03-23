import asyncio
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neuro_commands import (
    CommandType, TTSCommand, ASRCommand, WhisperCommand
)

logger = logging.getLogger(__name__)

class SpeechManager:
    """Manages speech recognition and synthesis"""
    
    def __init__(self):
        self.recording: bool = False
        self.current_audio: Optional[bytes] = None
        self.logger = logger
        
    async def start_recording(self) -> None:
        """Start recording audio"""
        if self.recording:
            return
            
        self.recording = True
        self.current_audio = b''
        self.logger.info("Started recording")
        
    async def stop_recording(self) -> str:
        """
        Stop recording and transcribe the audio
        
        Returns:
            str: Transcribed text from the audio
        """
        if not self.recording:
            return ""
            
        self.recording = False
        self.logger.info("Stopped recording, transcribing...")
        
        try:
            # Use Whisper for high-quality transcription
            response = await SynapticPathways.transmit_command(
                WhisperCommand(
                    command_type=CommandType.WHISPER,
                    audio_data=self.current_audio,
                    language="en",
                    task="transcribe"
                )
            )
            
            transcribed_text = response.get("text", "")
            self.logger.info(f"Transcribed: {transcribed_text}")
            return transcribed_text
            
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return ""
        finally:
            self.current_audio = None
            
    async def process_audio_chunk(self, chunk: bytes) -> None:
        """Process an incoming chunk of audio data"""
        if self.recording and chunk:
            self.current_audio += chunk
            
    async def speak_text(self, text: str, voice_id: str = "default") -> None:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            voice_id: Voice ID to use
        """
        try:
            await SynapticPathways.transmit_command(
                TTSCommand(
                    command_type=CommandType.TTS,
                    text=text,
                    voice_id=voice_id,
                    speed=1.0,
                    pitch=1.0
                )
            )
        except Exception as e:
            self.logger.error(f"TTS error: {e}")