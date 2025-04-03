from enum import Enum
import asyncio
import logging
import sounddevice as sd
import numpy as np
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from pathlib import Path

from .api_commands import CommandType, BaseCommand, LLMCommand
from .synaptic_pathways import SynapticPathways
from Mind.CorpusCallosum.api_commands import create_command, parse_response
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge

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
            
            # Convert to text using ASR
            asr_response = await NeurocorticalBridge.execute("asr_inference", {
                "audio_data": audio_data.tolist()
            })
            
            if asr_response.get("status") == "ok" and asr_response.get("data", {}).get("text"):
                # Process with LLM
                llm_response = await NeurocorticalBridge.execute("think", {
                    "prompt": asr_response["data"]["text"]
                }, stream=True)
                
                if llm_response.get("status") == "ok":
                    # Convert response to speech
                    await NeurocorticalBridge.execute("tts_inference", {
                        "text": llm_response["data"]["delta"]
                    })
                    
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
        finally:
            self.state = AudioState.IDLE
            
    def stop_detection(self) -> None:
        """Stop audio detection"""
        self.state = AudioState.IDLE
        self.audio_buffer.clear()
        self.silence_counter = 0

    async def setup_audio(self) -> Dict[str, Any]:
        """Initialize audio system"""
        return await NeurocorticalBridge.execute("setup_audio", {
            "capcard": 0,
            "capdevice": 0,
            "capVolume": 0.5,
            "playcard": 0,
            "playdevice": 1,
            "playVolume": 0.5
        })
    
    async def setup_asr(self) -> Dict[str, Any]:
        """Initialize ASR system"""
        command = create_command("asr", "setup", data={
            "model": "sherpa-ncnn-streaming-zipformer-20M-2023-02-17",
            "response_format": "asr.utf-8",
            "input": "sys.pcm",
            "enoutput": True,
            "enkws": True,
            "rule1": 2.4,
            "rule2": 1.2,
            "rule3": 30
        })
        return await SynapticPathways.send_command(command) 