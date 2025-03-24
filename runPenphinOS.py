#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any
import signal
from datetime import datetime

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from CorpusCallosum.synaptic_pathways import SynapticPathways, SerialConnectionError
from CorpusCallosum.neural_commands import (
    CommandType,
    BaseCommand,
    TTSCommand,
    ASRCommand,
    LLMCommand,
    CommandFactory,
    CommandSerializer,
    SystemCommand
)
from config import CONFIG
from CorpusCallosum.redmine_manager import RedmineManager
from SomatosensoryCortex.button_manager import ButtonManager
from AuditoryCortex.speech_manager import SpeechManager
from AuditoryCortex.audio_manager import AudioManager
from BicameralCortex.perspective_thinking_manager import PerspectiveThinkingManager

# Create logs directory if it doesn't exist
log_dir = Path(CONFIG.log_file).parent
log_dir.mkdir(parents=True, exist_ok=True)
log_dir.chmod(0o777)  # Give full permissions

# Configure logging (after CONFIG import to ensure directories exist)
logging.basicConfig(
    level=getattr(logging, CONFIG.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(CONFIG.log_file)
    ]
)
logger = logging.getLogger("PenphinOS")

class PenphinOS:
    """Main OS class that manages all neural subsystems"""
    
    def __init__(self):
        self.logger = logger
        self.running = True
        self.command_handlers = {}
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Shutdown signal received...")
        self.running = False
        # Force exit after cleanup
        sys.exit(0)
        
    async def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up resources...")
        if hasattr(self, 'button_manager'):
            self.button_manager.cleanup()
        await SynapticPathways.close_connections()
        # Exit immediately after cleanup
        os._exit(0)
        
    async def handle_tts_command(self, command: TTSCommand) -> Dict[str, Any]:
        """Handle Text-to-Speech commands"""
        self.logger.info(f"Processing TTS command: {command.text}")
        return await SynapticPathways.send_tts(
            text=command.text,
            voice_id=command.voice_id,
            speed=command.speed,
            pitch=command.pitch
        )
        
    async def handle_asr_command(self, command: ASRCommand) -> Dict[str, Any]:
        """Handle Automatic Speech Recognition commands"""
        self.logger.info("Processing ASR command")
        return await SynapticPathways.send_asr(
            audio_data=command.input_audio,
            language=command.language,
            model_type=command.model_type
        )
        
    async def handle_llm_command(self, command: LLMCommand) -> Dict[str, Any]:
        """Handle Large Language Model commands"""
        self.logger.info(f"Processing LLM command: {command.prompt[:50]}...")
        return await SynapticPathways.send_llm(
            prompt=command.prompt,
            max_tokens=command.max_tokens,
            temperature=command.temperature
        )
        
    def register_command_handlers(self):
        """Register handlers for different command types"""
        self.command_handlers = {
            CommandType.TTS: self.handle_tts_command,
            CommandType.ASR: self.handle_asr_command,
            CommandType.LLM: self.handle_llm_command,
            # Add more handlers as needed
        }
        
        # Register handlers with SynapticPathways
        for command_type, handler in self.command_handlers.items():
            SynapticPathways.register_command_handler(command_type, handler)
            
    async def _play_startup_sequence(self):
        """Play startup audio sequence"""
        try:
            # Remove duration parameter
            await SynapticPathways.send_tts(
                text="System initializing",
                voice_id="en-US-1"
            )
        except Exception as e:
            self.logger.error(f"Startup sequence error: {e}")
            raise
            
    async def initialize(self):
        """Initialize all subsystems"""
        try:
            # Initialize neural pathways
            self.logger.info("Initializing neural pathways...")
            await SynapticPathways.initialize()
            
            # Initialize audio manager first
            self.audio_manager = AudioManager()
            
            # Initialize speech manager with audio manager
            self.speech_manager = SpeechManager(self.audio_manager)
            
            # Initialize button manager
            self.button_manager = ButtonManager()
            self.button_manager.register_press_callback(self.handle_button_press)
            self.button_manager.register_release_callback(self.handle_button_release)
            
            # Register command handlers
            self.register_command_handlers()
            
            # Play startup sequence
            await self._play_startup_sequence()
            
            # Welcome message
            await SynapticPathways.send_tts(
                text=SynapticPathways.welcome_message,
                voice_id="en-US-1"
            )
            
            self.logger.info("PenphinOS initialization complete")
            
        except SerialConnectionError as e:
            self.logger.error(f"Failed to initialize neural pathways: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise
            
    async def demo_capabilities(self):
        """Demonstrate various neural capabilities"""
        try:
            # Test TTS
            self.logger.info("Testing Text-to-Speech...")
            tts_response = await self.handle_tts_command(
                TTSCommand(
                    command_type=CommandType.TTS,
                    text="Hello, I am PenphinOS, your neural operating system.",
                    voice_id="en-US-1"
                )
            )
            self.logger.info(f"TTS Response: {tts_response}")
            
            # Test LLM
            self.logger.info("Testing Language Model...")
            llm_response = await self.handle_llm_command(
                LLMCommand(
                    command_type=CommandType.LLM,
                    prompt="What can you tell me about neural networks?",
                    max_tokens=100
                )
            )
            self.logger.info(f"LLM Response: {llm_response}")
            
        except Exception as e:
            self.logger.error(f"Demo error: {e}")
            raise
            
    async def run(self):
        """Main run loop"""
        try:
            await self.initialize()
            
            # Run demo if requested
            if "--demo" in sys.argv:
                await self.demo_capabilities()
            
            # Main event loop
            while self.running:
                try:
                    # Process commands from neural pathways
                    await asyncio.sleep(0.1)  # Prevent CPU spinning
                except asyncio.CancelledError:
                    break
                
        except Exception as e:
            self.logger.error(f"Runtime error: {e}")
        finally:
            await self.cleanup()

    async def handle_button_press(self):
        """Handle button press events"""
        self.logger.info("Button pressed")
        try:
            await SynapticPathways.send_system_command("button_press")
            # Start recording when button is pressed
            await self.speech_manager.start_recording()
        except Exception as e:
            self.logger.error(f"Button press handler error: {e}")

    async def handle_button_release(self):
        """Handle button release events"""
        self.logger.info("Button released")
        try:
            await SynapticPathways.send_system_command("button_release")
            # Stop recording and process audio when button is released
            text = await self.speech_manager.stop_recording()
            if text:
                await SynapticPathways.process_assistant_interaction(text_input=text)
        except Exception as e:
            self.logger.error(f"Button release handler error: {e}")

async def main():
    """Main entry point"""
    try:
        # Initialize configuration
        # CONFIG is already an instance, no need to call it
        logger.info("Starting PenphinOS...")
        
        # Initialize audio components
        audio_manager = AudioManager()
        speech_manager = SpeechManager(audio_manager)
        
        # Start the system
        logger.info("Starting PenphinOS...")
        
        # Main event loop
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down PenphinOS...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Cleanup
        if 'audio_manager' in locals():
            await audio_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
