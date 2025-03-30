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
import subprocess

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

from Mind.mind import Mind
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.menu_system import run_menu_system

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

async def run_menu(mind: Mind) -> None:
    """Run the interactive menu system"""
    try:
        logger.info("Starting interactive menu system...")
        
        # Ensure the connection is initialized if not done already
        if not SynapticPathways._initialized:
            logger.info("Initializing SynapticPathways for menu system...")
            await SynapticPathways.initialize()
        
        # Run the menu system with the Mind instance
        await run_menu_system(mind=mind)
        
        # Clean up after menu system exits
        logger.info("Menu system exited, cleaning up...")
        await SynapticPathways.cleanup()
        
    except Exception as e:
        logger.error(f"Menu system error: {e}")
        logger.exception("Full exception details:")
        raise

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="""PenphinMind - A Neuromorphic AI System

This system implements a bicameral mind architecture with various neural subsystems:
- Visual Cortex (vc): LED Matrix and visual processing
- Auditory Cortex (ac): Audio processing and speech
- Frontal Cortex (fc): Language processing and LLM with interactive menu
- Full Mind (full): Complete system integration

If no mode is specified, the system defaults to the interactive menu mode.
Each mode provides direct interaction with its respective subsystem.""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--mode',
        choices=['vc', 'ac', 'fc', 'full'],
        help="""Run in specific mode:
  vc  - Visual Cortex (LED Matrix)
        Test LED matrix and visual processing
        Example: python run.py --mode vc
        
  ac  - Auditory Cortex (Audio)
        Test audio processing and speech
        Example: python run.py --mode ac
        
  fc  - Frontal Cortex (LLM)
        Interactive menu system for model management and chat
        Example: python run.py --mode fc
        
  full - Full Mind
        Run the complete system
        Example: python run.py --mode full"""
    )
    
    parser.add_argument(
        '--connection',
        choices=['serial', 'adb', 'wifi'],
        help="""Select connection mode:
  serial - Direct USB connection
  adb    - Android Debug Bridge
  wifi   - WiFi connection"""
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help="""Enable debug logging for detailed system information.
This will show all debug messages and system state changes."""
    )
    
    # Check if --mode is used without a value
    if "--mode" in sys.argv and len(sys.argv) > sys.argv.index("--mode") + 1:
        if sys.argv[sys.argv.index("--mode") + 1].startswith("--"):
            print("\nError: --mode requires a brain region suffix")
            print("Available regions:")
            print("  vc  - Visual Cortex (LED Matrix)")
            print("  ac  - Auditory Cortex (Audio)")
            print("  fc  - Frontal Cortex (LLM)")
            print("  full - Full Mind (All Cortices)")
            print("\nExample: python run.py --mode fc")
            sys.exit(1)
            
    return parser.parse_args()

async def main():
    """Main entry point"""
    args = parse_args()
    
    # Initialize logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Set mode in SynapticPathways
        if args.mode:
            SynapticPathways.set_mode(args.mode)
            
        # Set connection mode if specified
        if args.connection:
            print(f"\n🔍 Setting connection mode to {args.connection}...")
            
            # Set up ADB port forwarding if ADB mode is selected
            if args.connection == "adb":
                print("Setting up ADB port forwarding...")
                try:
                    # First ensure ADB server is running
                    subprocess.run(["adb", "start-server"], capture_output=True)
                    
                    # Check for connected devices
                    device_result = subprocess.run(
                        ["adb", "devices"],
                        capture_output=True,
                        text=True
                    )
                    print(f"ADB devices found:\n{device_result.stdout}")
                    
                    # Set up port forwarding from local port 5555 to device port 5555
                    result = subprocess.run(
                        ["adb", "forward", "tcp:5555", "tcp:5555"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print(f"ADB port forwarding set up successfully: tcp:5555 -> tcp:5555")
                        print(f"Connection will use localhost:5555 via ADB")
                    else:
                        print(f"Error setting up ADB port forwarding: {result.stderr}")
                except Exception as e:
                    print(f"Failed to set up ADB port forwarding: {e}")
            
            await SynapticPathways.set_device_mode(args.connection)
            
        penphin = PenphinMind()
        
        if args.mode:
            if args.mode == 'vc':
                await run_visual_cortex_test(penphin.mind)
            elif args.mode == 'ac':
                await run_auditory_cortex_test(penphin.mind)
            elif args.mode == 'fc':
                # Use the new menu system when in frontal cortex mode
                await run_menu(penphin.mind)
            elif args.mode == 'full':
                await penphin.run()
        else:
            # Default to menu system if no mode specified
            await run_menu(penphin.mind)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 