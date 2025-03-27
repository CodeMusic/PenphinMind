"""
Main entry point for PenphinMind system
"""

import argparse
import asyncio
import logging
import sys
import signal
import os
from typing import Optional
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

from Mind.mind import Mind
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Create logs directory if it doesn't exist
log_dir = Path(CONFIG.log_file).parent
log_dir.mkdir(parents=True, exist_ok=True)
log_dir.chmod(0o777)  # Give full permissions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class BrainRegion:
    """Enum-like class for brain regions"""
    VISUAL_CORTEX = "vc"
    AUDITORY_CORTEX = "ac"
    FRONTAL_CORTEX = "fc"
    FULL_MIND = "full"

    @classmethod
    def get_aliases(cls) -> dict:
        """Get all aliases for brain regions"""
        return {
            "vc": cls.VISUAL_CORTEX,
            "visualcortex": cls.VISUAL_CORTEX,
            "ac": cls.AUDITORY_CORTEX,
            "auditorycortex": cls.AUDITORY_CORTEX,
            "fc": cls.FRONTAL_CORTEX,
            "frontalcortex": cls.FRONTAL_CORTEX,
            "full": cls.FULL_MIND,
            "fullmind": cls.FULL_MIND
        }

class PenphinMind:
    """Main system class that manages all neural subsystems"""
    
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
            self.logger.info("PenphinMind initialized successfully")
            
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
                "Hello, I am PenphinMind, your neural operating system."
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

async def run_visual_cortex_test(mind: Mind) -> None:
    """Run visual cortex (LED matrix) unit tests"""
    try:
        await mind.initialize()
        logger.info("Running visual cortex tests...")
        
        # Show splash screen first
        await mind.occipital_lobe["visual"].show_splash_screen()
        
        # Test LED matrix
        await mind.set_background(255, 0, 0)  # Red
        await asyncio.sleep(1)
        await mind.set_background(0, 255, 0)  # Green
        await asyncio.sleep(1)
        await mind.set_background(0, 0, 255)  # Blue
        await asyncio.sleep(1)
        
        # Show gear animation to indicate unit testing mode
        await mind.occipital_lobe["visual"].show_gear_animation(duration=3.0, color=(0, 255, 0))
        
        # Clear matrix
        await mind.clear_matrix()
        
    except Exception as e:
        logger.error(f"Visual cortex test error: {e}")
        raise

async def run_auditory_cortex_test(mind: Mind) -> None:
    """Run auditory cortex (audio) unit tests"""
    try:
        await mind.initialize()
        logger.info("Running auditory cortex tests...")
        
        # Test speech generation
        logger.info("Testing Text-to-Speech...")
        audio_data = await mind.generate_speech(
            "Hello, I am testing the auditory cortex."
        )
        logger.info("Speech generated successfully")
        
        # Test speech understanding
        logger.info("Testing Speech Understanding...")
        text = await mind.understand_speech(audio_data)
        logger.info(f"Understood text: {text}")
        
    except Exception as e:
        logger.error(f"Auditory cortex test error: {e}")
        raise

async def run_frontal_cortex_test(mind: Mind) -> None:
    """Run frontal cortex (LLM) unit tests"""
    try:
        await mind.initialize()
        logger.info("Running frontal cortex tests...")
        
        # Interactive chat mode for testing
        print("\nWelcome to PenphinMind Chat!")
        print("Type 'exit' to quit")
        print("-" * 50)
        
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'exit':
                break
                
            # Process input through mind
            response = await mind.process_input(user_input)
            
            # Print response
            if response.get("status") == "ok":
                print("\nPenphinMind:", response.get("response", ""))
            else:
                print("\nError:", response.get("message", "Unknown error"))
                
    except Exception as e:
        logger.error(f"Frontal cortex test error: {e}")
        raise

def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run PenphinMind system or brain region tests")
    parser.add_argument(
        "--unit-test",
        choices=list(BrainRegion.get_aliases().keys()),
        help="Run unit tests for a specific brain region. Available regions: vc (visual cortex), ac (auditory cortex), fc (frontal cortex), full (full mind)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run system in demo mode"
    )
    
    # Check if --unit-test is used without a value
    if "--unit-test" in sys.argv and len(sys.argv) > sys.argv.index("--unit-test") + 1:
        if sys.argv[sys.argv.index("--unit-test") + 1].startswith("--"):
            print("\nError: --unit-test requires a brain region suffix")
            print("Available regions:")
            print("  vc  - Visual Cortex (LED Matrix)")
            print("  ac  - Auditory Cortex (Audio)")
            print("  fc  - Frontal Cortex (LLM)")
            print("  full - Full Mind (All Cortices)")
            print("\nExample: python run.py --unit-test fc")
            sys.exit(1)
            
    return parser.parse_args()

async def main() -> None:
    """Main entry point"""
    # Parse arguments
    args = parse_args()
    
    # Initialize mind
    mind = PenphinMind()
    
    try:
        # Determine which mode to run
        if args.unit_test:
            region = BrainRegion.get_aliases()[args.unit_test]
            
            if region == BrainRegion.VISUAL_CORTEX:
                await run_visual_cortex_test(mind.mind)
            elif region == BrainRegion.AUDITORY_CORTEX:
                await run_auditory_cortex_test(mind.mind)
            elif region == BrainRegion.FRONTAL_CORTEX:
                await run_frontal_cortex_test(mind.mind)
            else:
                await mind.run()
        else:
            await mind.run()
            
    finally:
        await mind.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 