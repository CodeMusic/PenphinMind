"""
Main entry point for PenphinOS
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import signal
from datetime import datetime
import time

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

from Mind.mind import Mind
from Mind.config import CONFIG

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
        self.mind = Mind()
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
        await self.mind.stop_listening()
        # Exit immediately after cleanup
        os._exit(0)
            
    async def initialize(self):
        """Initialize all neural subsystems"""
        try:
            # Initialize mind first
            await self.mind.initialize()
            
            # Show splash screen
            self.logger.info("Showing splash screen...")
            await self.mind.occipital_lobe["visual"].show_splash_screen()
            
            self.running = True
            self.logger.info("PenphinOS initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise
            
    async def start_audio_automation(self):
        """Start audio detection and automation"""
        try:
            await self.mind.start_listening()
        except Exception as e:
            self.logger.error(f"Error starting audio automation: {e}")
            raise
                
    def stop_audio_automation(self):
        """Stop audio detection and automation"""
        self.mind.stop_listening()
            
    async def demo_capabilities(self):
        """Demonstrate various neural capabilities"""
        try:
            # Test speech generation
            self.logger.info("Testing Text-to-Speech...")
            audio_data = await self.mind.generate_speech(
                "Hello, I am PenphinOS, your neural operating system."
            )
            self.logger.info("Speech generated successfully")
            
            # Test speech understanding
            self.logger.info("Testing Speech Understanding...")
            text = await self.mind.understand_speech(audio_data)
            self.logger.info(f"Understood text: {text}")
            
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

async def main():
    """Main entry point"""
    try:
        mind = Mind()
        await mind.initialize()
        
        # Start the system
        await mind.process_input({"type": "start", "content": "PenphinOS"})
        
    except Exception as e:
        logger.error(f"System error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
