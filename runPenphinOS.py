#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any
import signal
from datetime import datetime
import time
from CorpusCallosum.visual_cortex import VisualCortex
from CorpusCallosum.synaptic_pathways import SynapticPathways
from PreFrontalCortex.behavior_manager import BehaviorManager
from config import CONFIG


# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

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
from CorpusCallosum.redmine_manager import RedmineManager
from SomatosensoryCortex.button_manager import ButtonManager
from AuditoryCortex.speech_manager import SpeechManager
from AuditoryCortex.audio_manager import AudioManager
from BicameralCortex.perspective_thinking_manager import PerspectiveThinkingManager
from CorpusCallosum.audio_automation import AudioAutomation, AudioConfig

# Create logs directory if it doesn't exist
log_dir = Path(CONFIG.log_file).parent
log_dir.mkdir(parents=True, exist_ok=True)
log_dir.chmod(0o777)  # Give full permissions

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Default to INFO if config not available
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PenphinOS")

class PenphinOS:
    """Main OS class that manages all neural subsystems"""
    
    def __init__(self):
        self.logger = logger
        self.running = False
        self.command_handlers = {}
        self.audio_automation = None
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
        """Initialize all neural subsystems"""
        try:
            await SynapticPathways.initialize()
            self.register_command_handlers()
            
            # Initialize audio automation
            audio_config = AudioConfig(
                sample_rate=CONFIG.audio_sample_rate,
                channels=CONFIG.audio_channels,
                device=CONFIG.audio_device
            )
            self.audio_automation = AudioAutomation(audio_config)
            
            self.running = True
            self.logger.info("PenphinOS initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise
            
    async def start_audio_automation(self):
        """Start audio detection and automation"""
        if self.audio_automation:
            try:
                await self.audio_automation.start_detection()
            except Exception as e:
                self.logger.error(f"Error starting audio automation: {e}")
                raise
                
    def stop_audio_automation(self):
        """Stop audio detection and automation"""
        if self.audio_automation:
            self.audio_automation.stop_detection()
            
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

async def get_system_info():
    """Get comprehensive system information"""
    try:
        import platform
        import psutil
        import torch
        
        system_info = {
            "System": {
                "OS": platform.system(),
                "Version": platform.version(),
                "Machine": platform.machine(),
                "Processor": platform.processor()
            },
            "Resources": {
                "CPU Cores": psutil.cpu_count(),
                "Memory Total (GB)": round(psutil.virtual_memory().total / (1024**3), 2),
                "Memory Available (GB)": round(psutil.virtual_memory().available / (1024**3), 2),
                "Disk Usage (%)": psutil.disk_usage('/').percent
            },
            "CUDA": {
                "Available": torch.cuda.is_available(),
                "Device Count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "Current Device": torch.cuda.current_device() if torch.cuda.is_available() else None,
                "Device Name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
            }
        }
        return system_info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}

async def display_system_status():
    """Display comprehensive system status"""
    try:
        # Get system information
        system_info = await get_system_info()
        
        logger.info("\n" + "="*50)
        logger.info("PenphinOS System Status")
        logger.info("="*50)
        
        # Configuration Status
        logger.info("\nConfiguration:")
        logger.info(f"Mode: {'Hardware' if CONFIG.is_raspberry_pi else 'Test'}")
        logger.info(f"Audio Output: {CONFIG.audio_output_type}")
        logger.info(f"Serial Port: {CONFIG.serial_default_port}")
        logger.info(f"Serial Baud Rate: {CONFIG.serial_baud_rate}")
        logger.info(f"Log Level: {CONFIG.log_level}")
        logger.info(f"Log File: {CONFIG.log_file}")
        
        # System Information
        if system_info:
            logger.info("\nSystem Information:")
            for category, info in system_info.items():
                logger.info(f"\n{category}:")
                for key, value in info.items():
                    logger.info(f"  {key}: {value}")
        
        # Neural Components Status
        logger.info("\nNeural Components:")
        logger.info(f"SynapticPathways Ready: {hasattr(SynapticPathways, '_instance')}")
        logger.info(f"Audio Manager Ready: {CONFIG.audio_enabled}")
        logger.info(f"Speech Recognition Model: {CONFIG.asr_model_type}")
        logger.info(f"TTS Provider: {CONFIG.tts_provider}")
        logger.info(f"LLM Provider: {CONFIG.llm_provider}")
        
        logger.info("\n" + "="*50)
    except Exception as e:
        logger.error(f"Error displaying system status: {e}")

async def main():
    """Main entry point for PenphinOS"""
    try:
        # Initialize behavior manager
        behavior_manager = BehaviorManager()
        
        # Initialize visual cortex
        visual_cortex = None
        try:
            visual_cortex = VisualCortex()
            behavior_manager.register_state_handler(SystemState.INITIALIZING, visual_cortex)
            behavior_manager.register_state_handler(SystemState.THINKING, visual_cortex)
            behavior_manager.register_state_handler(SystemState.LISTENING, visual_cortex)
            behavior_manager.register_state_handler(SystemState.SPEAKING, visual_cortex)
            behavior_manager.register_state_handler(SystemState.ERROR, visual_cortex)
            behavior_manager.register_state_handler(SystemState.SHUTDOWN, visual_cortex)
        except Exception as e:
            logger.warning(f"Failed to initialize visual cortex: {e}")
            logger.info("Continuing without LED matrix display")
        
        # Initialize synaptic pathways
        await SynapticPathways.initialize(test_mode=False)
        
        # Start behavior management
        behavior_manager.start()
        
        # Start the system
        os = PenphinOS()
        await os.run()
        
    except Exception as e:
        logger.error(f"Runtime error: {e}")
        if visual_cortex:
            visual_cortex.on_state_change(SystemState.ERROR)
    finally:
        if 'os' in locals():
            await os.cleanup()
        await SynapticPathways.close_connections()
        if visual_cortex:
            visual_cortex.cleanup()
            
if __name__ == "__main__":
    asyncio.run(main())
