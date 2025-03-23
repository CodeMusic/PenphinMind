#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
import sys
import signal
from datetime import datetime

from CorpusCallosum.synaptic_pathways import SynapticPathways, SerialConnectionError
from CorpusCallosum.neural_commands import (
    CommandType,
    BaseCommand,
    TTSCommand,
    ASRCommand,
    LLMCommand,
    CommandFactory,
    CommandSerializer
)
from config import CONFIG

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
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup handlers for system signals"""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
    def _handle_shutdown(self, signum, frame):
        """Handle system shutdown signals"""
        self.logger.info("Shutdown signal received")
        self.running = False
        # Note: We can't await here since this is a sync callback
        # The cleanup will happen in the main loop's finally block
        
    async def cleanup(self):
        """Cleanup resources before shutdown"""
        self.logger.info("Cleaning up resources...")
        await SynapticPathways.close_connections()
        
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
            
    async def initialize(self):
        """Initialize all subsystems"""
        try:
            # Initialize neural pathways
            self.logger.info("Initializing neural pathways...")
            await SynapticPathways.initialize()
            
            # Register command handlers
            self.register_command_handlers()
            
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
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Runtime error: {e}")
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    os = PenphinOS()
    
    # Setup cleanup on shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(
            os.cleanup())
        )
    
    await os.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
