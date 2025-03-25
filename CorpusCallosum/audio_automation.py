from enum import Enum
import asyncio
import logging
import sounddevice as sd
import numpy as np
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from pathlib import Path

from .neural_commands import CommandType, BaseCommand, LLMCommand
from .synaptic_pathways import SynapticPathways

logger = logging.getLogger(__name__)

class AudioState(Enum):
    """Audio processing states"""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    PLAYING = "playing"

@dataclass
class AudioConfig:
    """Audio configuration parameters"""
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "float32"
    device: Optional[str] = None
    buffer_size: int = 1024
    silence_threshold: float = 0.01
    silence_duration: float = 1.0

class AudioAutomation:
    """Manages audio detection, processing, and automation"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.state = AudioState.IDLE
        self.audio_buffer: List[np.ndarray] = []
        self.silence_counter = 0
        self._setup_audio_device()
        
    def _setup_audio_device(self) -> None:
        """Set up audio device with error handling"""
        try:
            devices = sd.query_devices()
            logger.info(f"Available audio devices: {devices}")
            
            if self.config.device:
                device_id = None
                for i, device in enumerate(devices):
                    if self.config.device in device['name']:
                        device_id = i
                        break
                if device_id is None:
                    raise ValueError(f"Device {self.config.device} not found")
            else:
                device_id = sd.default.device[0]
                
            self.device_id = device_id
            logger.info(f"Using audio device: {devices[device_id]['name']}")
            
        except Exception as e:
            logger.error(f"Error setting up audio device: {e}")
            raise
            
    async def start_detection(self) -> None:
        """Start audio detection loop"""
        self.state = AudioState.RECORDING
        
        try:
            with sd.InputStream(
                device=self.device_id,
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=self.config.dtype,
                blocksize=self.config.buffer_size,
                callback=self._audio_callback
            ):
                while self.state == AudioState.RECORDING:
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error in audio detection: {e}")
            self.state = AudioState.IDLE
            raise
            
    def _audio_callback(self, indata: np.ndarray, frames: int, time: Any, status: Any) -> None:
        """Process incoming audio data"""
        if status:
            logger.warning(f"Audio callback status: {status}")
            
        # Check for silence
        if np.max(np.abs(indata)) < self.config.silence_threshold:
            self.silence_counter += frames / self.config.sample_rate
            if self.silence_counter >= self.config.silence_duration:
                asyncio.create_task(self._process_audio())
                self.silence_counter = 0
        else:
            self.silence_counter = 0
            self.audio_buffer.append(indata.copy())
            
    async def _process_audio(self) -> None:
        """Process collected audio data"""
        if not self.audio_buffer:
            return
            
        self.state = AudioState.PROCESSING
        try:
            # Combine audio buffer
            audio_data = np.concatenate(self.audio_buffer)
            self.audio_buffer.clear()
            
            # Convert to text using Whisper
            command = BaseCommand(
                command_type=CommandType.WHISPER,
                data={"audio": audio_data.tolist()}
            )
            response = await SynapticPathways.transmit_json(command)
            
            if response.get("status") == "ok" and response.get("text"):
                # Process with LLM
                llm_command = LLMCommand(
                    command_type=CommandType.LLM,
                    prompt=response["text"],
                    max_tokens=150,
                    temperature=0.7
                )
                llm_response = await SynapticPathways.transmit_json(llm_command)
                
                if llm_response.get("status") == "ok":
                    # Convert response to speech
                    tts_command = BaseCommand(
                        command_type=CommandType.TTS,
                        data={"text": llm_response["response"]}
                    )
                    await SynapticPathways.transmit_json(tts_command)
                    
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
        finally:
            self.state = AudioState.IDLE
            
    def stop_detection(self) -> None:
        """Stop audio detection"""
        self.state = AudioState.IDLE
        self.audio_buffer.clear()
        self.silence_counter = 0 