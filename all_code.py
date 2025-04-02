from PreFrontalCortex.system_journeling_manager import (
    SystemJournelingManager,
    SystemJournelingLevel
)
from PenphinMind.mind import Mind

async def launch_penphin_os():
    """Launch the main PenphinOS system"""
    mind = Mind()
    await mind.initialize()
    # Add any additional initialization or startup logic here
    return mind

async def launch_test_llm():
    """Launch the LLM test environment"""
    mind = Mind()
    await mind.initialize()
    # Add LLM-specific test logic here
    return mind

async def launch_test_led():
    """Launch the LED matrix test environment"""
    mind = Mind()
    await mind.initialize()
    # Add LED matrix-specific test logic here
    return mind

async def main():
    # Initialize the journaling manager
    journaling_manager = SystemJournelingManager(SystemJournelingLevel.INFO)
    journaling_manager.record_info("Initializing PenphinMind system")
    
    # Launch the appropriate component based on command line arguments
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-llm":
            await launch_test_llm()
        elif sys.argv[1] == "--test-led":
            await launch_test_led()
        else:
            await launch_penphin_os()
    else:
        await launch_penphin_os()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
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

from Mind.mind import Mind, setup_connection
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.menu_system import clear_screen, run_menu_system
from Mind.CorpusCallosum.transport_layer import run_adb_command, get_transport

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

async def run_menu(mind: Mind, connection_type: str) -> None:
    """Run the interactive menu system"""
    was_initialized = SynapticPathways._initialized
    
    try:
        logger.info("Starting interactive menu system...")
        
        # Ensure the connection is initialized if not done already
        if not SynapticPathways._initialized:
            logger.info("Initializing SynapticPathways for menu system...")
            await SynapticPathways.initialize(connection_type)
        
        # Run the menu system with the Mind instance
        await run_menu_system(mind=mind)
        
    except Exception as e:
        logger.error(f"Menu system error: {e}")
        logger.exception("Full exception details:")
        raise
    finally:
        # Only clean up if we initialized it in this function
        if not was_initialized and SynapticPathways._initialized:
            logger.info("Menu system exited, cleaning up...")
            await SynapticPathways.cleanup()

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
        choices=['serial', 'adb', 'tcp'],
        help="""Select connection mode:
serial - Direct USB connection
adb    - Android Debug Bridge
tcp    - TCP/IP network connection"""
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
    clear_screen()
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
            print("\n🔍 Setting connection mode to {}...".format(args.connection))
            try:
                if await setup_connection(args.connection):
                    print(f"{args.connection.capitalize()} connection established successfully")
                else:
                    print(f"Failed to establish {args.connection} connection")
            except Exception as e:
                print(f"Error setting up connection: {e}")
            
        penphin = PenphinMind()
        
        if args.mode:
            if args.mode == 'vc':
                await run_visual_cortex_test(penphin.mind)
            elif args.mode == 'ac':
                await run_auditory_cortex_test(penphin.mind)
            elif args.mode == 'fc':
                # Use the new menu system when in frontal cortex mode
                await run_menu(penphin.mind, args.connection)
            elif args.mode == 'full':
                await penphin.run()
        else:
            # Default to menu system if no mode specified
            await run_menu(penphin.mind, args.connection)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

# Add this where the program exits or in a signal handler
async def shutdown():
    """Clean up resources before shutdown"""
    try:
        # Import here to avoid circular imports
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        await SynapticPathways.final_shutdown()
        print("All connections and port forwarding cleaned up.")
    except Exception as e:
        print(f"Error during shutdown cleanup: {e}")

# Make sure this is called when the program exits
# For example, at the end of main() or in a signal handler

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
# test_llm_visualization.py - Test script for LLM visualization

import asyncio
import argparse
import sys
import os
from typing import Dict, Any

# Add the project root to the Python path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways

# ANSI escape codes for colored output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

async def setup_connection(connection_type: str) -> bool:
    """Initialize the connection to the LLM system"""
    print(f"{Colors.BLUE}[*] Initializing {connection_type} connection...{Colors.ENDC}")
    success = await SynapticPathways.initialize(connection_type)
    
    if not success:
        print(f"{Colors.RED}[!] Failed to initialize connection{Colors.ENDC}")
        return False
    
    # Get hardware info
    hw_info = await SynapticPathways.get_hardware_info()
    print(f"{Colors.GREEN}[+] Connection established{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Device status: CPU: {hw_info.get('cpu_load', 'N/A')}, "
          f"Memory: {hw_info.get('memory_usage', 'N/A')}, "
          f"Temp: {hw_info.get('temperature', 'N/A')}{Colors.ENDC}")
    
    # Get available models
    models = await SynapticPathways.get_available_models()
    if models:
        print(f"{Colors.GREEN}[+] Available models: {len(models)}{Colors.ENDC}")
        for model in models[:3]:  # Show only a few models
            print(f"    - {model.get('mode', 'Unknown')}: {model.get('type', 'Unknown')}")
        if len(models) > 3:
            print(f"    - ... and {len(models) - 3} more")
    
    return True

async def think_with_visualization(prompt: str, art_style: str, grid_size: tuple) -> Dict[str, Any]:
    """Send a prompt to the LLM with visualization"""
    width, height = grid_size
    print(f"{Colors.BLUE}[*] Thinking with {art_style} visualization ({width}x{height})...{Colors.ENDC}")
    
    # Different entry points depending on art style
    if art_style in ["wave", "matrix", "binary", "emphasis", "gradient"]:
        return await SynapticPathways.think_with_artistic_grid(
            prompt, 
            art_style=art_style,
            color_mode="color",
            width=width,
            height=height
        )
    else:
        return await SynapticPathways.think_with_pixel_grid(
            prompt,
            width=width,
            height=height,
            color_mode="color" if art_style != "grayscale" else "grayscale"
        )

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="LLM Visualization Test")
    parser.add_argument("--connection", "-c", default="tcp", choices=["tcp", "adb", "serial"],
                       help="Connection type to use (default: tcp)")
    parser.add_argument("--art-style", "-a", default="basic",
                       choices=["basic", "grayscale", "wave", "matrix", "binary", "emphasis", "gradient"],
                       help="Art style for visualization (default: basic)")
    parser.add_argument("--width", "-W", type=int, default=64,
                       help="Width of the pixel grid (default: 64)")
    parser.add_argument("--height", "-H", type=int, default=32,
                       help="Height of the pixel grid (default: 32)")
    args = parser.parse_args()
    
    # Setup connection
    if not await setup_connection(args.connection):
        print(f"{Colors.RED}[!] Exiting due to connection failure{Colors.ENDC}")
        return
    
    # Show welcome message
    print(f"\n{Colors.HEADER}{Colors.BOLD}===== LLM Visualization Test =====")
    print(f"Type your prompt and see the LLM output visualized")
    print(f"Use '/style <style>' to change visualization style")
    print(f"Use '/size <width> <height>' to change grid size")
    print(f"Use '/exit' or Ctrl+C to quit{Colors.ENDC}\n")
    
    # Initialize settings
    art_style = args.art_style
    grid_size = (args.width, args.height)
    
    # Main interaction loop
    try:
        while True:
            # Get user prompt
            try:
                user_input = input(f"{Colors.BOLD}> {Colors.ENDC}")
            except EOFError:
                break
                
            # Handle commands
            if user_input.startswith('/'):
                parts = user_input.strip().split()
                command = parts[0].lower()
                
                if command == '/exit':
                    break
                    
                elif command == '/style' and len(parts) > 1:
                    style = parts[1].lower()
                    valid_styles = ["basic", "grayscale", "wave", "matrix", "binary", "emphasis", "gradient"]
                    if style in valid_styles:
                        art_style = style
                        print(f"{Colors.GREEN}[+] Visualization style set to: {art_style}{Colors.ENDC}")
                    else:
                        print(f"{Colors.YELLOW}[!] Invalid style. Valid options: {', '.join(valid_styles)}{Colors.ENDC}")
                        
                elif command == '/size' and len(parts) > 2:
                    try:
                        width = int(parts[1])
                        height = int(parts[2])
                        if width > 0 and height > 0:
                            grid_size = (width, height)
                            print(f"{Colors.GREEN}[+] Grid size set to: {width}x{height}{Colors.ENDC}")
                        else:
                            print(f"{Colors.YELLOW}[!] Width and height must be positive{Colors.ENDC}")
                    except ValueError:
                        print(f"{Colors.YELLOW}[!] Width and height must be numbers{Colors.ENDC}")
                
                elif command == '/help':
                    print(f"{Colors.BLUE}Available commands:{Colors.ENDC}")
                    print(f"  /style <style> - Change visualization style")
                    print(f"  /size <width> <height> - Change grid size")
                    print(f"  /exit - Exit the program")
                    print(f"  /help - Show this help message")
                    
                else:
                    print(f"{Colors.YELLOW}[!] Unknown command. Type /help for available commands{Colors.ENDC}")
                    
                continue
                
            # Skip empty prompts
            if not user_input.strip():
                continue
                
            # Send the prompt to the LLM with visualization
            try:
                result = await think_with_visualization(user_input, art_style, grid_size)
                
                # Print completion message 
                print(f"\n{Colors.GREEN}[+] Thinking complete!{Colors.ENDC}")
                
                # Ask if user wants to see text result
                show_text = input(f"{Colors.BOLD}Show text result? (y/n): {Colors.ENDC}").lower().startswith('y')
                if show_text:
                    print(f"\n{Colors.BLUE}--- Result ---{Colors.ENDC}")
                    if isinstance(result, dict) and "error" in result:
                        print(f"{Colors.RED}Error: {result['error']}{Colors.ENDC}")
                    else:
                        print(result)
                    print(f"{Colors.BLUE}-------------{Colors.ENDC}\n")
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[!] Thinking interrupted{Colors.ENDC}")
                continue
            except Exception as e:
                print(f"\n{Colors.RED}[!] Error: {str(e)}{Colors.ENDC}")
                
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Program interrupted{Colors.ENDC}")
    
    # Clean up
    print(f"\n{Colors.BLUE}[*] Cleaning up...{Colors.ENDC}")
    await SynapticPathways.cleanup()
    print(f"{Colors.GREEN}[+] Done. Goodbye!{Colors.ENDC}")

if __name__ == "__main__":
    asyncio.run(main()) 
"""
PenphinMind - Neural operating system for advanced AI interaction
"""

__version__ = "0.1.0" 
"""
Mental Configuration - Manages the mental architecture of PenphinMind
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import os
from .FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Get the project root directory (where config.py is located)
PROJECT_ROOT = Path(__file__).parent
CONFIG_FILE = PROJECT_ROOT / "config.json"

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class AudioOutputType(str, Enum):
    """Audio output device types"""
    WAVESHARE = "waveshare"
    LOCAL_LLM = "local_llm"

class MentalConfiguration:
    """
    Configuration settings for the PenphinMind system
    """
    def __init__(self):
        journaling_manager.recordScope("MentalConfiguration.__init__")
        
        # Initialize default values
        self._init_defaults()
        
        # Serial settings with defaults
        self.serial_settings = {
            "port": "COM7",
            "baud_rate": 115200,
            "timeout": 1.0,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "xonxoff": False,
            "rtscts": False,
            "dsrdtr": False
        }
        
        # Load configuration from config.json
        self._load_config()
        
        # Load environment variables (these override config file settings)
        self._load_env_vars()
        
        journaling_manager.recordInfo("Mental configuration initialized")

    def _init_defaults(self):
        """Initialize default configuration values"""
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        self.audio_device_controls = {
            "volume": 100,
            "mute": False,
            "input_device": "default",
            "output_device": "default",
            "latency": 0.1,
            "buffer_size": 2048
        }
        
        # Visual settings
        self.visual_height = 32
        self.visual_width = 64
        self.visual_fps = 30
        
        # Motor settings
        self.motor_speed = 100
        self.motor_acceleration = 50
        
        # LLM settings
        self.llm_model = "gpt-3.5-turbo"
        self.llm_temperature = 0.7
        self.llm_max_tokens = 1000
        
        # LLM service settings
        self.llm_service = {
            "ip": "10.0.0.154",
            "port": 10001,
            "timeout": 5.0
        }
        
        # System settings
        self.debug_mode = False
        self.log_level = "DEBUG"
        self.log_file = str(PROJECT_ROOT / "logs" / "penphin.log")
        
        # ADB settings
        self.adb_path = "adb"  # Default to system adb

    def _load_config(self) -> None:
        """Load configuration from config.json"""
        journaling_manager.recordScope("MentalConfiguration._load_config")
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    
                # Load corpus callosum settings
                if "corpus_callosum" in config_data:
                    cc_config = config_data["corpus_callosum"]
                    
                    # Load LLM service settings
                    if "llm_service" in cc_config:
                        self.llm_service.update(cc_config["llm_service"])
                    
                    # Load ADB path
                    if "adb_path" in cc_config:
                        self.adb_path = cc_config["adb_path"]
                    
                    # Load serial settings
                    if "serial_settings" in cc_config:
                        self.serial_settings.update(cc_config["serial_settings"])
                        journaling_manager.recordInfo(f"Loaded serial settings: {self.serial_settings}")
                    
                # Load other sections as needed...
                
                journaling_manager.recordInfo(f"Configuration loaded from {CONFIG_FILE}")
            else:
                journaling_manager.recordWarning(f"Config file not found at {CONFIG_FILE}, using defaults")
                
        except Exception as e:
            journaling_manager.recordError(f"Error loading config.json: {e}")

    def save(self) -> bool:
        """Save current configuration to JSON file"""
        try:
            # Ensure the config structure matches the expected format
            config_data = {
                "corpus_callosum": {
                    "llm_service": self.llm_service,
                    "adb_path": self.adb_path,
                    "serial_settings": self.serial_settings,
                    "api_keys": {
                        "openai": "",
                        "elevenlabs": ""
                    },
                    "logging": {
                        "level": self.log_level,
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                }
                # Add other sections as needed...
            }
            
            # Ensure directory exists
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with pretty formatting
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            
            journaling_manager.recordInfo(f"Configuration saved to {CONFIG_FILE}")
            return True
        except Exception as e:
            journaling_manager.recordError(f"Error saving config: {e}")
            return False

    def _load_env_vars(self) -> None:
        """Load configuration from environment variables"""
        journaling_manager.recordScope("MentalConfiguration._load_env_vars")
        
        # Audio settings
        if "PENPHIN_SAMPLE_RATE" in os.environ:
            self.sample_rate = int(os.environ["PENPHIN_SAMPLE_RATE"])
            journaling_manager.recordDebug(f"Loaded sample rate from env: {self.sample_rate}")
        if "PENPHIN_CHANNELS" in os.environ:
            self.channels = int(os.environ["PENPHIN_CHANNELS"])
            journaling_manager.recordDebug(f"Loaded channels from env: {self.channels}")
        if "PENPHIN_CHUNK_SIZE" in os.environ:
            self.chunk_size = int(os.environ["PENPHIN_CHUNK_SIZE"])
            journaling_manager.recordDebug(f"Loaded chunk size from env: {self.chunk_size}")
            
        # Audio device controls
        if "PENPHIN_AUDIO_VOLUME" in os.environ:
            self.audio_device_controls["volume"] = int(os.environ["PENPHIN_AUDIO_VOLUME"])
            journaling_manager.recordDebug(f"Loaded audio volume from env: {self.audio_device_controls['volume']}")
        if "PENPHIN_AUDIO_MUTE" in os.environ:
            self.audio_device_controls["mute"] = os.environ["PENPHIN_AUDIO_MUTE"].lower() == "true"
            journaling_manager.recordDebug(f"Loaded audio mute from env: {self.audio_device_controls['mute']}")
        if "PENPHIN_AUDIO_INPUT" in os.environ:
            self.audio_device_controls["input_device"] = os.environ["PENPHIN_AUDIO_INPUT"]
            journaling_manager.recordDebug(f"Loaded audio input device from env: {self.audio_device_controls['input_device']}")
        if "PENPHIN_AUDIO_OUTPUT" in os.environ:
            self.audio_device_controls["output_device"] = os.environ["PENPHIN_AUDIO_OUTPUT"]
            journaling_manager.recordDebug(f"Loaded audio output device from env: {self.audio_device_controls['output_device']}")
        if "PENPHIN_AUDIO_LATENCY" in os.environ:
            self.audio_device_controls["latency"] = float(os.environ["PENPHIN_AUDIO_LATENCY"])
            journaling_manager.recordDebug(f"Loaded audio latency from env: {self.audio_device_controls['latency']}")
        if "PENPHIN_AUDIO_BUFFER" in os.environ:
            self.audio_device_controls["buffer_size"] = int(os.environ["PENPHIN_AUDIO_BUFFER"])
            journaling_manager.recordDebug(f"Loaded audio buffer size from env: {self.audio_device_controls['buffer_size']}")
            
        # Visual settings
        if "PENPHIN_VISUAL_HEIGHT" in os.environ:
            self.visual_height = int(os.environ["PENPHIN_VISUAL_HEIGHT"])
            journaling_manager.recordDebug(f"Loaded visual height from env: {self.visual_height}")
        if "PENPHIN_VISUAL_WIDTH" in os.environ:
            self.visual_width = int(os.environ["PENPHIN_VISUAL_WIDTH"])
            journaling_manager.recordDebug(f"Loaded visual width from env: {self.visual_width}")
        if "PENPHIN_VISUAL_FPS" in os.environ:
            self.visual_fps = int(os.environ["PENPHIN_VISUAL_FPS"])
            journaling_manager.recordDebug(f"Loaded visual FPS from env: {self.visual_fps}")
            
        # Motor settings
        if "PENPHIN_MOTOR_SPEED" in os.environ:
            self.motor_speed = int(os.environ["PENPHIN_MOTOR_SPEED"])
            journaling_manager.recordDebug(f"Loaded motor speed from env: {self.motor_speed}")
        if "PENPHIN_MOTOR_ACCELERATION" in os.environ:
            self.motor_acceleration = int(os.environ["PENPHIN_MOTOR_ACCELERATION"])
            journaling_manager.recordDebug(f"Loaded motor acceleration from env: {self.motor_acceleration}")
            
        # LLM settings
        if "PENPHIN_LLM_MODEL" in os.environ:
            self.llm_model = os.environ["PENPHIN_LLM_MODEL"]
            journaling_manager.recordDebug(f"Loaded LLM model from env: {self.llm_model}")
        if "PENPHIN_LLM_TEMPERATURE" in os.environ:
            self.llm_temperature = float(os.environ["PENPHIN_LLM_TEMPERATURE"])
            journaling_manager.recordDebug(f"Loaded LLM temperature from env: {self.llm_temperature}")
        if "PENPHIN_LLM_MAX_TOKENS" in os.environ:
            self.llm_max_tokens = int(os.environ["PENPHIN_LLM_MAX_TOKENS"])
            journaling_manager.recordDebug(f"Loaded LLM max tokens from env: {self.llm_max_tokens}")
            
        # LLM service settings
        if "PENPHIN_LLM_SERVICE_IP" in os.environ:
            self.llm_service["ip"] = os.environ["PENPHIN_LLM_SERVICE_IP"]
            journaling_manager.recordDebug(f"Loaded LLM service IP from env: {self.llm_service['ip']}")
        if "PENPHIN_LLM_SERVICE_PORT" in os.environ:
            self.llm_service["port"] = int(os.environ["PENPHIN_LLM_SERVICE_PORT"])
            journaling_manager.recordDebug(f"Loaded LLM service port from env: {self.llm_service['port']}")
        if "PENPHIN_LLM_SERVICE_TIMEOUT" in os.environ:
            self.llm_service["timeout"] = float(os.environ["PENPHIN_LLM_SERVICE_TIMEOUT"])
            journaling_manager.recordDebug(f"Loaded LLM service timeout from env: {self.llm_service['timeout']}")
            
        # System settings
        if "PENPHIN_DEBUG_MODE" in os.environ:
            self.debug_mode = os.environ["PENPHIN_DEBUG_MODE"].lower() == "true"
            journaling_manager.recordDebug(f"Loaded debug mode from env: {self.debug_mode}")
        if "PENPHIN_LOG_LEVEL" in os.environ:
            self.log_level = os.environ["PENPHIN_LOG_LEVEL"]
            journaling_manager.recordDebug(f"Loaded log level from env: {self.log_level}")
            
        # Serial settings from environment
        if "PENPHIN_SERIAL_PORT" in os.environ:
            self.serial_settings["port"] = os.environ["PENPHIN_SERIAL_PORT"]
        if "PENPHIN_SERIAL_BAUD" in os.environ:
            self.serial_settings["baud_rate"] = int(os.environ["PENPHIN_SERIAL_BAUD"])
        if "PENPHIN_SERIAL_TIMEOUT" in os.environ:
            self.serial_settings["timeout"] = float(os.environ["PENPHIN_SERIAL_TIMEOUT"])
            
        journaling_manager.recordInfo("Environment variables loaded successfully")

# Create global configuration instance
CONFIG = MentalConfiguration() 
"""
Menu system for PenphinMind
"""

import os
import asyncio
from typing import Dict, Any, List
import time
import json

from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.mind import setup_connection

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

def clear_screen():
    """Clear the terminal screen"""
    pass
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Unix/Linux/MacOS
        os.system('clear')

def print_header():
    """Print PenphinMind header"""
    print("=" * 60)
    print("                     PenphinMind")
    print("=" * 60)
    print()

async def get_current_model_info():
    """Get information about the current active model"""
    active_model = await SynapticPathways.get_active_model()
    
    if active_model["success"]:
        if isinstance(active_model["model"], dict):
            return active_model["model"]
        elif isinstance(active_model["model"], str):
            if "details" in active_model:
                return active_model["details"]
            return {"model": active_model["model"], "type": active_model["model"].split("-")[0] if "-" in active_model["model"] else ""}
    
    return {"model": "No model selected", "type": ""}

async def display_main_menu() -> str:
    """Display main menu and get user choice"""
    print_header()
    
    # Refresh hardware info before displaying
    await SynapticPathways.get_hardware_info()
    
    # Display hardware info
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    print()
    
    print("Main Menu:")
    print("1) Chat")
    print("2) Information")
    print("3) System")
    print("4) Exit")
    print()
    
    choice = input("Enter your choice (1-4): ")
    return choice.strip()

async def display_model_list() -> str:
    """Display list of available models and get user choice"""
    clear_screen()
    print_header()
    
    # Refresh hardware info before displaying
    await SynapticPathways.get_hardware_info()
    
    # Display hardware info
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    
    print("\nAvailable Models:")
    print("----------------")
    
    # Get and display models - use cached models when available
    models = await SynapticPathways.get_available_models()
    
    # Log the models for debugging
    using_cached = len(SynapticPathways.available_models) > 0
    journaling_manager.recordInfo(f"Retrieved models (cached: {using_cached}): {models}")
    
    if using_cached:
        print(f"[Using cached model information - {len(models)} models available]")
    
    if not models:
        print("No models available or failed to retrieve model information.")
        print("Press Enter to return to main menu...")
        input()
        return ""
    
    # Build a list of models to display
    model_dict = {}
    count = 1
    
    # Group models by type
    model_types = {}
    for model in models:
        model_type = model.get("type", "unknown")
        if model_type not in model_types:
            model_types[model_type] = []
        model_types[model_type].append(model)
    
    # Display models by type
    for model_type, type_models in model_types.items():
        print(f"\n{model_type.upper()} Models:")
        for model in type_models:
            # Get the model name from the mode field (original API field)
            model_name = model.get("mode", "Unknown")
            
            # Get capabilities and format them for display
            capabilities = model.get("capabilities", [])
            capabilities_str = ""
            if capabilities:
                capabilities_str = f" [{', '.join(capabilities)}]"
            
            # Log the individual model data for debugging
            journaling_manager.recordInfo(f"Model data: {model}")
            journaling_manager.recordInfo(f"Using model name from 'mode' field: {model_name}")
            
            model_dict[count] = model
            print(f"{count}) {model_name}{capabilities_str}")
            count += 1
    
    print("\n0) Return to main menu")
    print()
    
    choice = input("Enter model number for details (0 to return): ")
    
    if not choice or choice == "0":
        return ""
    
    try:
        model_num = int(choice)
        if 1 <= model_num < count:
            await display_model_details(model_dict[model_num])
    except (ValueError, KeyError):
        print("Invalid selection. Press Enter to continue...")
        input()
    
    return ""

async def display_model_details(model: Dict[str, Any]):
    """Display detailed information about a specific model"""
    clear_screen()
    print_header()
    
    # Refresh hardware info before displaying
    await SynapticPathways.get_hardware_info()
    
    # Display hardware info
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    print()
    
    # Log the model data for debugging
    journaling_manager.recordInfo(f"Displaying details for model: {model}")
    print("[Using cached model information]")
    print()
    
    # Get model identifier from the mode field (original API field)
    model_name = model.get('mode', "Unknown")
    
    print("Model Details:")
    print("-------------")
    print(f"Name: {model_name}")
    print(f"Type: {model.get('type', '')}")
    
    # Display capabilities
    capabilities = model.get("capabilities", [])
    if capabilities:
        print("\nCapabilities:")
        for cap in capabilities:
            print(f"- {cap}")
    
    # Display input/output types
    print("\nInput Types:")
    input_types = model.get("input_type", [])
    if isinstance(input_types, list):
        for inp in input_types:
            print(f"- {inp}")
    else:
        print(f"- {input_types}")
    
    print("\nOutput Types:")
    output_types = model.get("output_type", [])
    if isinstance(output_types, list):
        for out in output_types:
            print(f"- {out}")
    else:
        print(f"- {output_types}")
    
    # Display mode parameters if available
    mode_params = model.get("mode_param", {})
    if mode_params:
        print("\nParameters:")
        for param_name, param_value in mode_params.items():
            print(f"- {param_name}: {param_value}")
    
    print("\nPress Enter to return to model list...")
    input()

async def reboot_system():
    """Reboot the M5Stack system"""
    clear_screen()
    print_header()
    
    print("Rebooting system...")
    
    result = await SynapticPathways.reboot_device()
    
    if result["success"]:
        print("Reboot command sent successfully.")
        print("Device will restart. The application will lose connection.")
        print("You may need to restart the application after device reboot.")
        
        # Wait a moment to allow device to reboot
        print("\nWaiting for device to reboot...")
        await asyncio.sleep(5)
        
        # Try to reconnect and get hardware info
        try:
            print("Attempting to reconnect...")
            # Re-initialize the connection
            await SynapticPathways.initialize()
            
            # Get updated hardware info
            hw_info = await SynapticPathways.get_hardware_info()
            print("\nDevice reconnected successfully!")
            print(SynapticPathways.format_hw_info())
        except Exception as e:
            journaling_manager.recordError(f"Error reconnecting after reboot: {e}")
            print("\nCould not reconnect to device after reboot.")
            print("You will need to restart the application manually.")
    else:
        print(f"Reboot failed: {result.get('message', 'Unknown error')}")
    
    print("\nPress Enter to return to main menu...")
    input()

async def start_chat():
    """Start chat interface with LLM"""
    clear_screen()
    print_header()
    
    # Refresh hardware info before displaying
    await SynapticPathways.get_hardware_info()
    
    # Display hardware info at the top of chat
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    
    print("\nWelcome to PenphinMind Chat\n")
    print("Type 'exit' to return to main menu")
    print("Type 'reset' to reset the LLM\n")
    
    # Initialize LLM with setup command
    llm_work_id = f"llm.{int(time.time())}"
    setup_command = {
        "request_id": f"setup_{int(time.time())}",
        "work_id": llm_work_id,
        "action": "setup",
        "object": "llm.setup",
        "data": {
            "model": SynapticPathways.default_llm_model,
            "response_format": "llm.utf-8", 
            "input": "llm.utf-8", 
            "enoutput": True,
            "enkws": False,
            "max_token_len": 127,
            "prompt": "You are a helpful assistant."
        }
    }
    
    # Log which model we're using
    journaling_manager.recordInfo(f"Using LLM model: {SynapticPathways.default_llm_model}")
    
    # Send setup command
    print("Initializing LLM...")
    setup_response = await SynapticPathways.transmit_json(setup_command)
    journaling_manager.recordInfo(f"LLM setup response: {setup_response}")
    
    if setup_response and setup_response.get("error", {}).get("code", 1) == 0:
        print("LLM initialized successfully.\n")
    else:
        error_msg = setup_response.get("error", {}).get("message", "Unknown error")
        print(f"Error initializing LLM: {error_msg}")
        print("Press Enter to return to main menu...")
        input()
        return
    
    chat_history = []
    running = True
    
    while running:
        # Get user input
        user_input = input("You: ")
        
        # Check for exit command
        if user_input.lower() in ("exit", "quit", "menu"):
            # Clean up LLM resources before exiting
            exit_command = {
                "request_id": f"exit_{int(time.time())}",
                "work_id": llm_work_id,
                "action": "exit"
            }
            await SynapticPathways.transmit_json(exit_command)
            break
            
        # Check for reset command
        if user_input.lower() == "reset":
            print("\nResetting LLM...")
            
            # First exit current LLM session
            exit_command = {
                "request_id": f"exit_{int(time.time())}",
                "work_id": llm_work_id,
                "action": "exit"
            }
            await SynapticPathways.transmit_json(exit_command)
            
            # Reset the system
            result = await SynapticPathways.clear_and_reset()
            hw_info = SynapticPathways.format_hw_info()
            print(hw_info)
            
            # Reinitialize LLM with new work_id
            llm_work_id = f"llm.{int(time.time())}"
            setup_command["request_id"] = f"setup_{int(time.time())}"
            setup_command["work_id"] = llm_work_id
            
            # Make sure we're using the latest model (in case it changed)
            setup_command["data"]["model"] = SynapticPathways.default_llm_model
            journaling_manager.recordInfo(f"Reinitializing with LLM model: {SynapticPathways.default_llm_model}")
            
            setup_response = await SynapticPathways.transmit_json(setup_command)
            
            print("LLM has been reset.\n")
            continue
        
        if not user_input.strip():
            continue
            
        # Add user message to history
        chat_history.append({"role": "user", "content": user_input})
        
        # Generate LLM response
        print("\nAI: ", end="", flush=True)
        
        try:
            # Create LLM inference command
            inference_command = {
                "request_id": f"inference_{int(time.time())}",
                "work_id": llm_work_id,
                "action": "inference",
                "object": "llm.utf-8",
                "data": {
                    "delta": user_input,
                    "index": 0,
                    "finish": True
                }
            }
            
            # Send inference command
            response = await SynapticPathways.think_with_visualization(user_input)
            journaling_manager.recordInfo(f"LLM inference response: {response}")
            
            # Check for errors
            if response and response.get("error", {}).get("code", 1) != 0:
                error_message = response.get("error", {}).get("message", "Unknown error")
                print(f"Error generating response: {error_message}")
                continue
                
            # Extract response
            if "data" in response:
                data = response["data"]
                if isinstance(data, dict) and "delta" in data:
                    # Handle streaming format response
                    ai_response = data.get("delta", "")
                    print(ai_response)
                elif isinstance(data, str):
                    # Handle direct string response
                    ai_response = data
                    print(ai_response)
                else:
                    # Unknown format
                    print("No valid response received.")
                    continue
                
                # Add AI response to history
                chat_history.append({"role": "assistant", "content": ai_response})
            else:
                print("No data in response.")
            
        except Exception as e:
            journaling_manager.recordError(f"Error in chat: {e}")
            print(f"An error occurred: {e}")
            
        print()  # Empty line after response

async def system_menu() -> None:
    """Display and handle system menu options"""
    while True:
        clear_screen()
        print_header()
        
        # Display hardware info
        hw_info = SynapticPathways.format_hw_info()
        print(hw_info)
        print()
        
        print("System Menu:")
        print("1) Hardware Info")
        print("2) List Models")
        print("3) Ping System")
        print("4) Reboot Device")
        print("0) Back to Main Menu")
        print()
        
        choice = input("Enter your choice (0-4): ").strip()
        
        try:
            if choice == "0":
                return
            elif choice == "1":
                # Hardware Info
                hw_info = await SynapticPathways.get_hardware_info()
                print("\n=== Hardware Information ===")
                print(json.dumps(hw_info, indent=2))
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                # List Models
                models = await SynapticPathways.get_available_models()
                print("\n=== Available Models ===")
                print(json.dumps(models, indent=2))
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                # Ping System
                print("\nPinging system...")
                result = await SynapticPathways.ping_system()
                print(f"Ping {'successful' if result else 'failed'}")
                input("\nPress Enter to continue...")
                
            elif choice == "4":
                # Reboot (using existing reboot_system function)
                await reboot_system()
                
            else:
                print("\nInvalid choice. Press Enter to continue...")
                input()
                
        except Exception as e:
            print(f"\nError: {e}")
            input("\nPress Enter to continue...")

async def run_menu_system(mind=None):
    """Run the main menu system
    
    Args:
        mind: Optional Mind instance for additional functionality
    """
    while True:
        choice = await display_main_menu()
        
        if choice == "1":
            await start_chat()
        elif choice == "2":
            await display_model_list()
        elif choice == "3":
            await system_menu()
        elif choice == "4":
            print("Exiting PenphinMind...")
            break
        else:
            print("Invalid choice. Press Enter to continue...")
            input()

async def initialize_system(connection_type=None):
    """Initialize the system with the specified connection type"""
    await setup_connection(connection_type)

# Entry point
if __name__ == "__main__":
    asyncio.run(run_menu_system()) 
"""
Main Mind class that coordinates all brain regions
"""

import logging
import platform
from typing import Dict, Any, Optional
from .CorpusCallosum.synaptic_pathways import SynapticPathways
from .TemporalLobe.SuperiorTemporalGyrus.HeschlGyrus.primary_acoustic_area import PrimaryAcousticArea
from .OccipitalLobe.VisualCortex.associative_visual_area import AssociativeVisualArea
from .ParietalLobe.SomatosensoryCortex.primary_area import PrimaryArea
from .FrontalLobe.PrefrontalCortex.language_processor import LanguageProcessor
from .FrontalLobe.MotorCortex.motor import Motor
from .TemporalLobe.SuperiorTemporalGyrus.AuditoryCortex.integration_area import IntegrationArea
from .ParietalLobe.SomatosensoryCortex.integration_area import IntegrationArea as SomatosensoryIntegration
from .OccipitalLobe.VisualCortex.integration_area import IntegrationArea as VisualProcessor
from .FrontalLobe.MotorCortex.integration_area import IntegrationArea as MotorIntegration
from .FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from .config import CONFIG
# Add other lobe imports as needed

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

logger = logging.getLogger(__name__)

class Mind:
    """
    High-level coordinator for all brain regions
    """
    def __init__(self):
        # Initialize instance variables
        self._occipital_lobe = {}
        self._temporal_lobe = {}
        self._parietal_lobe = {}
        self._motor_cortex = {}
        self.primary_acoustic = None
        self._initialized = False
        self._processing = False
        self._language_processor = None  # Language processor instance
        
        # Initialize all lobes
        self._temporal_lobe = {
            "auditory": IntegrationArea()
        }
        self._parietal_lobe = {
            "somatosensory": SomatosensoryIntegration()
        }
        self._occipital_lobe = {
            "visual": VisualProcessor()
        }
        self._motor_cortex = {
            "motor": MotorIntegration()
        }
        
        journaling_manager.recordScope("Mind.__init__")
        
    @property
    def temporal_lobe(self) -> Dict[str, Any]:
        """Get temporal lobe components"""
        journaling_manager.recordScope("Mind.temporal_lobe.getter")
        return self._temporal_lobe
        
    @temporal_lobe.setter
    def temporal_lobe(self, value: Dict[str, Any]):
        """Set temporal lobe components"""
        journaling_manager.recordScope("Mind.temporal_lobe.setter", value=value)
        self._temporal_lobe = value
        
    @property
    def parietal_lobe(self) -> Dict[str, Any]:
        """Get parietal lobe components"""
        journaling_manager.recordScope("Mind.parietal_lobe.getter")
        return self._parietal_lobe
        
    @parietal_lobe.setter
    def parietal_lobe(self, value: Dict[str, Any]):
        """Set parietal lobe components"""
        journaling_manager.recordScope("Mind.parietal_lobe.setter", value=value)
        self._parietal_lobe = value
        
    @property
    def occipital_lobe(self) -> Dict[str, Any]:
        """Get occipital lobe components"""
        journaling_manager.recordScope("Mind.occipital_lobe.getter")
        return self._occipital_lobe
        
    @occipital_lobe.setter
    def occipital_lobe(self, value: Dict[str, Any]):
        """Set occipital lobe components"""
        journaling_manager.recordScope("Mind.occipital_lobe.setter", value=value)
        self._occipital_lobe = value
        
    @property
    def motor_cortex(self) -> Dict[str, Any]:
        """Get motor cortex components"""
        journaling_manager.recordScope("Mind.motor_cortex.getter")
        return self._motor_cortex
        
    @motor_cortex.setter
    def motor_cortex(self, value: Dict[str, Any]):
        """Set motor cortex components"""
        journaling_manager.recordScope("Mind.motor_cortex.setter", value=value)
        self._motor_cortex = value
        
    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """High-level audio processing"""
        journaling_manager.recordScope("Mind.process_audio", audio_data=audio_data)
        return await self.temporal_lobe["auditory"].process_auditory_input(audio_data)
        
    async def generate_speech(self, text: str) -> bytes:
        """High-level speech generation"""
        journaling_manager.recordScope("Mind.generate_speech", text=text)
        return await self.temporal_lobe["auditory"].process_text(text)
        
    async def understand_speech(self, audio_data: bytes) -> str:
        """High-level speech understanding"""
        journaling_manager.recordScope("Mind.understand_speech", audio_data=audio_data)
        result = await self.temporal_lobe["auditory"].process_auditory_input(audio_data)
        return result.get("text", "")

    async def start_listening(self) -> None:
        """Start audio input processing"""
        journaling_manager.recordScope("Mind.start_listening")
        if not self.primary_acoustic:
            # Initialize primary acoustic area if needed
            self.primary_acoustic = PrimaryAcousticArea()
        await self.primary_acoustic.start_vad()

    async def stop_listening(self) -> None:
        """Stop audio input processing"""
        journaling_manager.recordScope("Mind.stop_listening")
        if self.primary_acoustic:
            await self.primary_acoustic.stop_vad()

    def _is_raspberry_pi(self) -> bool:
        """Check if running on a Raspberry Pi"""
        journaling_manager.recordScope("Mind._is_raspberry_pi")
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False
            
    async def initialize(self) -> None:
        """Initialize all brain regions"""
        journaling_manager.recordScope("Mind.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Mind already initialized")
            return
            
        try:
            # Check if running on Raspberry Pi for logging
            is_raspberry_pi = self._is_raspberry_pi()
            journaling_manager.recordInfo(f"Running on {'Raspberry Pi' if is_raspberry_pi else 'non-Raspberry Pi'}")
            
            # Initialize synaptic pathways
            await SynapticPathways.initialize()
            
            # Initialize all integration areas
            for area in self.temporal_lobe.values():
                await area.initialize()
            for area in self.parietal_lobe.values():
                await area.initialize()
            for area in self.occipital_lobe.values():
                await area.initialize()
            for area in self.motor_cortex.values():
                await area.initialize()
            
            # Initialize primary acoustic area if needed
            if not self.primary_acoustic:
                self.primary_acoustic = PrimaryAcousticArea()
                await self.primary_acoustic.initialize()
                
            # Initialize language processor
            self._language_processor = LanguageProcessor()
            await self._language_processor.initialize()
                
            self._initialized = True
            journaling_manager.recordInfo("Mind initialized successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize mind: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up all brain regions"""
        journaling_manager.recordScope("Mind.cleanup")
        try:
            # Clean up all integration areas
            for area in self.temporal_lobe.values():
                await area.cleanup()
            for area in self.parietal_lobe.values():
                await area.cleanup()
            for area in self.occipital_lobe.values():
                await area.cleanup()
            for area in self.motor_cortex.values():
                await area.cleanup()
                
            # Clean up primary acoustic area
            if self.primary_acoustic:
                await self.primary_acoustic.cleanup()
                
            # Clean up language processor
            if self._language_processor:
                await self._language_processor.cleanup()
                
            self._initialized = False
            journaling_manager.recordInfo("Mind cleaned up successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up mind: {e}")
            raise
            
    async def execute_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """High-level movement execution"""
        journaling_manager.recordScope("Mind.execute_movement", movement_data=movement_data)
        return await self.motor_cortex["motor"].execute_movement(movement_data)
        
    async def stop_movement(self) -> None:
        """Stop all current movements"""
        journaling_manager.recordScope("Mind.stop_movement")
        await self.motor_cortex["motor"].stop_movement()
        
    async def process_visual_input(self, image_data: bytes) -> Dict[str, Any]:
        """
        Process visual input through visual cortex
        
        Args:
            image_data: Raw image data to process
            
        Returns:
            Dict[str, Any]: Processing result containing visual analysis
        """
        journaling_manager.recordScope("Mind.process_visual_input", image_data=image_data)
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            journaling_manager.recordDebug("Processing visual input through occipital lobe")
            result = await self.occipital_lobe["visual"].process_visual_input(image_data)
            
            journaling_manager.recordInfo("Successfully processed visual input")
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing visual input: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
    async def set_background(self, r: int, g: int, b: int) -> None:
        """
        Set the LED matrix background color
        
        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        journaling_manager.recordScope("Mind.set_background", r=r, g=g, b=b)
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            journaling_manager.recordDebug(f"Setting background color to RGB({r}, {g}, {b})")
            await self.occipital_lobe["visual"].set_background(r, g, b)
            
            journaling_manager.recordInfo("Successfully set background color")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting background color: {e}")
            raise
            
    async def clear_matrix(self) -> None:
        """Clear the LED matrix display"""
        journaling_manager.recordScope("Mind.clear_matrix")
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            journaling_manager.recordDebug("Clearing LED matrix")
            await self.occipital_lobe["visual"].clear()
            
            journaling_manager.recordInfo("Successfully cleared LED matrix")
            
        except Exception as e:
            journaling_manager.recordError(f"Error clearing LED matrix: {e}")
            raise

    async def process_input(self, input_text: str) -> Dict[str, Any]:
        """
        Process text input through language system
        
        Args:
            input_text: Text to process
            
        Returns:
            Dict[str, Any]: Processing result containing response and status
        """
        journaling_manager.recordScope("Mind.process_input", input_text=input_text)
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Mind not initialized, initializing now")
                await self.initialize()
                
            if not self._language_processor:
                journaling_manager.recordError("Language processor not initialized")
                raise RuntimeError("Language processor not initialized")
                
            journaling_manager.recordDebug("Processing input through language processor")
            # Process through language processor
            response = await self._language_processor.process_input(input_text)
            
            journaling_manager.recordInfo("Successfully processed input")
            return {
                "status": "ok",
                "response": response.get("response", {})
            }
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing input: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

async def setup_connection(connection_type=None):
    """Set up the connection to the device using the specified connection type"""
    from FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
    journaling_manager = SystemJournelingManager()
    
    journaling_manager.recordInfo(f"Mind setting up connection of type: {connection_type}")
    
    if connection_type:
        # Forward to SynapticPathways
        try:
            await SynapticPathways.set_device_mode(connection_type)
            return True
        except Exception as e:
            journaling_manager.recordError(f"Error setting up connection: {e}")
            return False
    else:
        journaling_manager.recordInfo("No connection type specified, using default")
        return await SynapticPathways.initialize() 
"""
Project Function:
    Handles OpenAI integration:
    OpenAI Manager System:
    - Response generation
    - Context management
    - Error handling
    - State management
    - Feedback processing
    - Learning integration
"""

import openai
import os
from typing import Dict, Any, Optional
from ..FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class OpenAIManager:
    """Manages OpenAI API integration for response generation"""
    
    def __init__(self):
        """Initialize OpenAI manager"""
        journaling_manager.recordScope("OpenAIManager.__init__")
        try:
            self.api_key = os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                journaling_manager.recordError("OpenAI API key not found in environment variables")
                raise ValueError("OpenAI API key not found in environment variables")
                
            openai.api_key = self.api_key
            self.model = "gpt-4"
            journaling_manager.recordDebug(f"OpenAI manager initialized with model: {self.model}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing OpenAI manager: {e}")
            raise

    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using OpenAI's API"""
        journaling_manager.recordScope("OpenAIManager.generate_response", prompt=prompt, context=context)
        try:
            messages = [{"role": "system", "content": "You are PenphinOS, a bicameral AI assistant."}]
            
            if context:
                messages.append({"role": "system", "content": f"Context: {str(context)}"})
                journaling_manager.recordDebug(f"Added context to messages: {context}")
                
            messages.append({"role": "user", "content": prompt})
            journaling_manager.recordDebug(f"Added user prompt to messages: {prompt}")

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages
            )
            
            result = response.choices[0].message.content
            journaling_manager.recordDebug(f"Generated response: {result}")
            return result
            
        except Exception as e:
            error_msg = f"OpenAI Error: {str(e)}"
            journaling_manager.recordError(error_msg)
            return error_msg 
"""
Bicameral Mind Perspective Manager:
    - Manages multiple thinking perspectives
    - Integrates different viewpoints
    - Handles perspective switching
    - Coordinates thought processes
"""

from typing import Dict, Any, Optional
from ...CorpusCallosum.neural_commands import CommandType, LLMCommand
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class PerspectiveThinkingManager:
    """Manages bicameral mind perspectives"""

    def __init__(self):
        """Initialize the perspective manager"""
        journaling_manager.recordScope("PerspectiveThinkingManager.__init__")
        self.perspectives = {
            "logical": self._logical_perspective,
            "creative": self._creative_perspective,
            "emotional": self._emotional_perspective,
            "intuitive": self._intuitive_perspective
        }
        self.current_perspective = "logical"
        journaling_manager.recordInfo("Perspective manager initialized")

    async def process_thought(self, input_text: str) -> str:
        """
        Process input through multiple perspectives and integrate responses
        """
        journaling_manager.recordScope("PerspectiveThinkingManager.process_thought", input_text=input_text)
        perspective_responses = {}
        
        for perspective_name, perspective_func in self.perspectives.items():
            journaling_manager.recordDebug(f"Processing through {perspective_name} perspective")
            response = await perspective_func(input_text)
            perspective_responses[perspective_name] = response
            journaling_manager.recordDebug(f"{perspective_name} perspective response: {response}")

        # Log the multi-perspective processing
        journaling_manager.recordInfo(f"Completed multi-perspective analysis for: {input_text}")

        return self._integrate_perspectives(perspective_responses)

    async def _logical_perspective(self, input_text: str) -> str:
        """
        Process input with logical, structured thinking
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._logical_perspective", input_text=input_text)
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=f"Analyze this logically: {input_text}",
            max_tokens=150,
            temperature=0.3
        )
        response = await SynapticPathways.transmit_json(command)
        return response.get("response", "")

    async def _creative_perspective(self, input_text: str) -> str:
        """
        Process input with creative, lateral thinking
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._creative_perspective", input_text=input_text)
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=f"Think creatively about: {input_text}",
            max_tokens=150,
            temperature=0.8
        )
        response = await SynapticPathways.transmit_json(command)
        return response.get("response", "")

    async def _emotional_perspective(self, input_text: str) -> str:
        """
        Process input with emotional intelligence
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._emotional_perspective", input_text=input_text)
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=f"Consider the emotional aspects of: {input_text}",
            max_tokens=150,
            temperature=0.6
        )
        response = await SynapticPathways.transmit_json(command)
        return response.get("response", "")

    async def _intuitive_perspective(self, input_text: str) -> str:
        """
        Process input with intuitive thinking
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._intuitive_perspective", input_text=input_text)
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=f"Consider this from an intuitive perspective: {input_text}",
            max_tokens=150,
            temperature=0.7
        )
        response = await SynapticPathways.transmit_json(command)
        return response.get("response", "")

    def _integrate_perspectives(self, responses: Dict[str, str]) -> str:
        """
        Integrate responses from different perspectives
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._integrate_perspectives", responses=responses)
        try:
            # Combine responses with perspective labels
            integrated = []
            for perspective, response in responses.items():
                integrated.append(f"{perspective.capitalize()} perspective: {response}")
            
            result = "\n\n".join(integrated)
            journaling_manager.recordDebug(f"Integrated perspectives result: {result}")
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"Error integrating perspectives: {e}")
            return "Error integrating different perspectives" 
"""
Neurological Function:
    Cognitive Functions of Cerebellum include:
    - Timing of cognitive processes
    - Language processing support
    - Spatial processing
    - Working memory assistance
    - Emotional processing
    - Cognitive prediction

Potential Project Implementation:
    Could handle:
    - Process timing
    - Cognitive sequencing
    - Predictive modeling
    - Error learning
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Cerebellar Learning Areas manage motor learning:
    - Procedural memory formation
    - Skill acquisition
    - Movement pattern storage
    - Adaptation to changes
    - Sequence learning
    - Performance optimization

Potential Project Implementation:
    Could handle:
    - Motor pattern learning
    - Skill optimization
    - Adaptive algorithms
    - Performance monitoring
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Motor Coordination in Cerebellum handles movement precision:
    - Fine-tunes motor movements
    - Maintains balance and posture
    - Coordinates timing of actions
    - Error correction in movements
    - Adapts motor programs
    - Learns movement sequences

Potential Project Implementation:
    Could handle:
    - Movement optimization
    - Timing control
    - Error detection/correction
    - Motion smoothing
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Vestibulocerebellum manages balance and spatial orientation:
    - Balance maintenance
    - Eye movement control
    - Spatial orientation
    - Motion processing
    - Posture adjustment
    - Equilibrium control

Potential Project Implementation:
    Could handle:
    - Balance algorithms
    - Spatial orientation
    - Motion compensation
    - Stability control
"""

# Implementation will be added when needed 
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
"""
Command loader for neural command system
"""

import json
from pathlib import Path
from typing import Dict, Any, Type
from dataclasses import dataclass, field
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from .command_types import BaseCommand, CommandType

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class CommandLoader:
    """Loader for neural command definitions"""
    
    def __init__(self):
        """Initialize the command loader"""
        journaling_manager.recordScope("CommandLoader.__init__")
        self.command_definitions = self._load_command_definitions()
        
    def _load_command_definitions(self) -> Dict[str, Any]:
        """Load command definitions from JSON file"""
        journaling_manager.recordScope("CommandLoader._load_command_definitions")
        try:
            # Get the path to raw_commands.json
            current_dir = Path(__file__).parent
            json_path = current_dir / "raw_commands.json"
            
            if not json_path.exists():
                journaling_manager.recordError(f"Command definitions file not found: {json_path}")
                raise FileNotFoundError(f"Command definitions file not found: {json_path}")
                
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            # Get command definitions from command_types key
            definitions = data.get("command_types", {})
            journaling_manager.recordDebug(f"Loaded {len(definitions)} command definitions")
            return definitions
            
        except Exception as e:
            journaling_manager.recordError(f"Error loading command definitions: {e}")
            raise
            
    def _create_command_class(self, command_type: str, definition: Dict[str, Any]) -> Type[BaseCommand]:
        """Create a command class from its definition"""
        journaling_manager.recordScope("CommandLoader._create_command_class", command_type=command_type)
        try:
            # Create class attributes
            class_attrs = {
                "__doc__": definition.get("description", f"Command for {command_type}")
            }
            
            # Add parameters from definition
            for param_name, param_def in definition.get("parameters", {}).items():
                param_type = param_def.get("type", "str")
                param_default = param_def.get("default")
                param_description = param_def.get("description", "")
                
                # Map JSON types to Python types
                type_mapping = {
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict
                }
                
                python_type = type_mapping.get(param_type, str)
                
                # Add field with default if specified
                if param_default is not None:
                    class_attrs[param_name] = field(default=param_default, metadata={"description": param_description})
                else:
                    class_attrs[param_name] = field(metadata={"description": param_description})
                    
            # Create the class
            command_class = dataclass(type(f"{command_type.title()}Command", (BaseCommand,), class_attrs))
            journaling_manager.recordDebug(f"Created command class: {command_class.__name__}")
            return command_class
            
        except Exception as e:
            journaling_manager.recordError(f"Error creating command class: {e}")
            raise
            
    def load_commands(self) -> Dict[str, Type[BaseCommand]]:
        """Load all command classes"""
        journaling_manager.recordScope("CommandLoader.load_commands")
        try:
            command_classes = {}
            for command_type, definition in self.command_definitions.items():
                if command_type in CommandType.__members__:
                    command_classes[command_type] = self._create_command_class(command_type, definition)
                else:
                    journaling_manager.recordError(f"Invalid command type in definitions: {command_type}")
                    
            journaling_manager.recordDebug(f"Loaded {len(command_classes)} command classes")
            return command_classes
            
        except Exception as e:
            journaling_manager.recordError(f"Error loading command classes: {e}")
            raise
            
    def get_command_class(self, command_type: str) -> Type[BaseCommand]:
        """Get a command class by type"""
        journaling_manager.recordScope("CommandLoader.get_command_class", command_type=command_type)
        try:
            if command_type not in self.command_definitions:
                journaling_manager.recordError(f"Unknown command type: {command_type}")
                raise ValueError(f"Unknown command type: {command_type}")
                
            if command_type not in CommandType.__members__:
                journaling_manager.recordError(f"Invalid command type: {command_type}")
                raise ValueError(f"Invalid command type: {command_type}")
                
            return self._create_command_class(command_type, self.command_definitions[command_type])
            
        except Exception as e:
            journaling_manager.recordError(f"Error getting command class: {e}")
            raise
            
    def validate_command(self, command_type: str, data: Dict[str, Any]) -> None:
        """Validate command data against its definition"""
        journaling_manager.recordScope("CommandLoader.validate_command", command_type=command_type)
        try:
            if command_type not in self.command_definitions:
                journaling_manager.recordError(f"Unknown command type: {command_type}")
                raise ValueError(f"Unknown command type: {command_type}")
                
            if command_type not in CommandType.__members__:
                journaling_manager.recordError(f"Invalid command type: {command_type}")
                raise ValueError(f"Invalid command type: {command_type}")
                
            definition = self.command_definitions[command_type]
            required_params = {
                name for name, param in definition.get("parameters", {}).items()
                if not param.get("optional", False)
            }
            
            missing_params = required_params - set(data.keys())
            if missing_params:
                journaling_manager.recordError(f"Missing required parameters: {missing_params}")
                raise ValueError(f"Missing required parameters: {missing_params}")
                
            journaling_manager.recordDebug("Command data validated successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Command validation failed: {e}")
            raise 
"""
Base command types for the neural command system
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any
import time
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class CommandType(Enum):
    """Types of neural commands supported by the system"""
    ASR = "asr"  # Automatic Speech Recognition
    TTS = "tts"  # Text to Speech
    VAD = "vad"  # Voice Activity Detection
    LLM = "llm"  # Large Language Model
    VLM = "vlm"  # Vision Language Model
    KWS = "kws"  # Keyword Spotting
    SYS = "sys"  # System Commands
    AUDIO = "audio"  # Audio Processing
    CAMERA = "camera"  # Camera Control
    YOLO = "yolo"  # Object Detection
    WHISPER = "whisper"  # Speech Recognition
    MELOTTS = "melotts"  # Neural TTS

class BaseCommand:
    """Base class for all neural commands"""
    def __init__(self, command_type: CommandType, action: str = "process"):
        """Initialize base command"""
        journaling_manager.recordScope("BaseCommand.__init__")
        try:
            if not isinstance(command_type, CommandType):
                journaling_manager.recordError(f"Invalid command type: {command_type}")
                raise ValueError("Command type must be a CommandType enum")
                
            self.command_type = command_type
            self.action = action
            self.timestamp = time.time()
            journaling_manager.recordDebug(f"Command timestamp set to: {self.timestamp}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing command: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary"""
        journaling_manager.recordScope("BaseCommand.to_dict")
        try:
            data = {
                "command_type": self.command_type.value,
                "action": self.action,
                "timestamp": self.timestamp
            }
            journaling_manager.recordDebug(f"Command converted to dict: {data}")
            return data
            
        except Exception as e:
            journaling_manager.recordError(f"Error converting command to dict: {e}")
            raise 
"""
Neural command system for PenphinMind
"""

from typing import Dict, Any, Type, Optional, List
from dataclasses import dataclass, field
import json
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from .command_types import BaseCommand, CommandType
from .command_loader import CommandLoader
from datetime import datetime
import traceback
import time

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ASRCommand(BaseCommand):
    """Automatic Speech Recognition commands"""
    def __init__(self, command_type: CommandType, input_audio: bytes, language: str = "en", model_type: str = "base"):
        journaling_manager.recordScope("ASRCommand.__init__")
        super().__init__(command_type)
        self.input_audio = input_audio
        self.language = language
        self.model_type = model_type
        journaling_manager.recordDebug(f"ASR command initialized with language: {self.language}, model: {self.model_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ASR command to dictionary"""
        journaling_manager.recordScope("ASRCommand.to_dict")
        data = super().to_dict()
        data.update({
            "input_audio": self.input_audio.hex() if self.input_audio else None,
            "language": self.language,
            "model_type": self.model_type
        })
        journaling_manager.recordDebug(f"Converted ASR command to dict: {data}")
        return data

@dataclass
class TTSCommand(BaseCommand):
    """Text-to-Speech command"""
    def __init__(self, command_type: CommandType, text: str = None, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0, **kwargs):
        journaling_manager.recordScope("TTSCommand.__init__")
        super().__init__(command_type)
        # Extract text from parameters if not directly provided
        self.text = text or kwargs.get('parameters', {}).get('text', '')
        self.voice_id = voice_id
        self.speed = speed
        self.pitch = pitch
        journaling_manager.recordDebug(f"TTS command initialized with voice: {self.voice_id}, speed: {self.speed}, pitch: {self.pitch}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary"""
        journaling_manager.recordScope("TTSCommand.to_dict")
        # Use the M5Stack API format
        return {
            "request_id": f"tts_{int(time.time())}",
            "work_id": "tts",
            "action": "process",
            "object": "tts.utf-8",
            "data": json.dumps({
                "text": self.text,
                "voice_id": self.voice_id,
                "speed": self.speed,
                "pitch": self.pitch
            })
        }

class VADCommand(BaseCommand):
    """Voice Activity Detection commands"""
    def __init__(self, command_type: CommandType, audio_chunk: bytes, threshold: float = 0.5, frame_duration: int = 30):
        journaling_manager.recordScope("VADCommand.__init__")
        super().__init__(command_type)
        self.audio_chunk = audio_chunk
        self.threshold = threshold
        self.frame_duration = frame_duration
        journaling_manager.recordDebug(f"VAD command initialized with threshold: {self.threshold}, frame_duration: {self.frame_duration}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert VAD command to dictionary"""
        journaling_manager.recordScope("VADCommand.to_dict")
        data = super().to_dict()
        data.update({
            "audio_chunk": self.audio_chunk.hex(),
            "threshold": self.threshold,
            "frame_duration": self.frame_duration
        })
        journaling_manager.recordDebug(f"Converted VAD command to dict: {data}")
        return data

class LLMCommand(BaseCommand):
    """Command for language model operations"""
    def __init__(self, command_type: CommandType, request_id: str = None, prompt: str = None, max_tokens: int = 100, 
                 temperature: float = 0.7, work_id: str = "llm", action: str = "inference", 
                 object: str = "llm.utf-8.stream", **kwargs):
        journaling_manager.recordScope("LLMCommand.__init__")
        super().__init__(command_type)
        self.request_id = request_id or f"generate_{int(time.time())}"
        self.work_id = work_id
        self.action = action
        self.object = object
        
        # Either use provided prompt or extract from data/kwargs
        if prompt:
            self.prompt = prompt
        elif "data" in kwargs and isinstance(kwargs["data"], dict):
            self.prompt = kwargs["data"].get("prompt", "")
        elif "parameters" in kwargs and isinstance(kwargs["parameters"], dict):
            self.prompt = kwargs["parameters"].get("prompt", "")
        else:
            self.prompt = ""
            
        self.max_tokens = max_tokens
        self.temperature = temperature
        journaling_manager.recordDebug(f"LLM command initialized with action: {self.action}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary format"""
        journaling_manager.recordScope("LLMCommand.to_dict")
        # Use the M5Stack LLM Module API format
        return {
            "request_id": self.request_id,
            "work_id": self.work_id,
            "action": self.action,
            "object": self.object,
            "data": {
                "delta": self.prompt,
                "index": 0,
                "finish": True
            }
        }

    def _parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the response data from the LLM API"""
        # Create a structured response object
        parsed_response = {
            "success": False,
            "error": None,
            "data": None,
            "request_id": response_data.get("request_id", "unknown")
        }
        
        # Check for error responses
        if response_data.get("error"):
            error_info = response_data.get("error", {})
            error_code = error_info.get("code", "unknown")
            error_message = error_info.get("message", "Unknown error")
            
            parsed_response["error"] = {
                "code": error_code,
                "message": error_message
            }
            return parsed_response
        
        # Process successful responses
        if "data" in response_data:
            data = response_data["data"]
            parsed_response["success"] = True
            
            # Data could be a string, dict with text field, or other dict
            if isinstance(data, dict):
                if "text" in data:
                    parsed_response["data"] = {
                        "generated_text": data.get("text", ""),
                        "finished": True
                    }
                else:
                    parsed_response["data"] = {
                        "generated_text": data.get("generated_text", str(data)),
                        "finished": data.get("finished", True)
                    }
            else:
                # Treat data as the generated text
                parsed_response["data"] = {
                    "generated_text": str(data),
                    "finished": True
                }
        
        return parsed_response

class VLMCommand(BaseCommand):
    """Vision Language Model commands"""
    def __init__(self, command_type: CommandType, image_data: bytes, prompt: Optional[str] = None, task_type: str = "classify"):
        journaling_manager.recordScope("VLMCommand.__init__")
        super().__init__(command_type)
        self.image_data = image_data
        self.prompt = prompt
        self.task_type = task_type
        journaling_manager.recordDebug(f"VLM command initialized with task_type: {self.task_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert VLM command to dictionary"""
        journaling_manager.recordScope("VLMCommand.to_dict")
        data = super().to_dict()
        data.update({
            "image_data": self.image_data.hex(),
            "prompt": self.prompt,
            "task_type": self.task_type
        })
        journaling_manager.recordDebug(f"Converted VLM command to dict: {data}")
        return data

class KWSCommand(BaseCommand):
    """Keyword Spotting commands"""
    def __init__(self, command_type: CommandType, keywords: List[str], sensitivity: float = 0.5, audio_data: Optional[bytes] = None):
        journaling_manager.recordScope("KWSCommand.__init__")
        super().__init__(command_type)
        self.keywords = keywords
        self.sensitivity = sensitivity
        self.audio_data = audio_data
        journaling_manager.recordDebug(f"KWS command initialized with keywords: {self.keywords}, sensitivity: {self.sensitivity}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert KWS command to dictionary"""
        journaling_manager.recordScope("KWSCommand.to_dict")
        data = super().to_dict()
        data.update({
            "keywords": self.keywords,
            "sensitivity": self.sensitivity,
            "audio_data": self.audio_data.hex() if self.audio_data else None
        })
        journaling_manager.recordDebug(f"Converted KWS command to dict: {data}")
        return data

class SystemCommand(BaseCommand):
    """System control commands"""
    def __init__(self, command_type: CommandType, action: str, parameters: Dict[str, Any] = None):
        journaling_manager.recordScope("SystemCommand.__init__")
        super().__init__(command_type)
        self.action = action
        self.parameters = parameters or {}
        journaling_manager.recordDebug(f"System command initialized with action: {self.action}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system command to dictionary"""
        journaling_manager.recordScope("SystemCommand.to_dict")
        
        # Create system command in proper format
        data = None  # Default to null instead of "None" string
        if self.parameters:
            if isinstance(self.parameters, dict):
                data = self.parameters
            else:
                data = {"params": self.parameters}
                
        # Set the object based on action type
        api_object = "None"
        api_action = self.action
        
        # Map standard action names to M5Stack API action names
        if self.action == "status":
            api_action = "get_status"
            api_object = "llm"
        elif self.action == "get_model_info":
            api_action = "lsmode"
            api_object = "system"
        elif self.action in ["reboot", "reset"]:
            if self.action == "reset":
                api_action = "reset"
                api_object = "llm"  # Reset the LLM specifically
            else:  # reboot
                api_action = "reboot"
                api_object = "system"  # Reboot the entire system
                
        # Return command in M5Stack API format
        return {
            "request_id": f"sys_{self.action}_{int(time.time())}",
            "work_id": "sys",
            "action": api_action,
            "object": api_object,
            "data": data
        }
        
    def validate(self) -> bool:
        """Validate system command"""
        journaling_manager.recordScope("SystemCommand.validate")
        try:
            if not self.action:
                journaling_manager.recordError("System command missing action")
                return False
                
            if not isinstance(self.parameters, dict):
                journaling_manager.recordError("System command parameters must be a dictionary")
                return False
                
            journaling_manager.recordDebug("System command validated successfully")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating system command: {e}")
            return False

class AudioCommand(BaseCommand):
    """Audio processing commands"""
    def __init__(self, command_type: CommandType, operation: str, audio_data: bytes, sample_rate: int = 16000, channels: int = 1):
        journaling_manager.recordScope("AudioCommand.__init__")
        super().__init__(command_type)
        self.operation = operation
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.channels = channels
        journaling_manager.recordDebug(f"Audio command initialized with operation: {self.operation}, sample_rate: {self.sample_rate}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Audio command to dictionary"""
        journaling_manager.recordScope("AudioCommand.to_dict")
        data = super().to_dict()
        data.update({
            "operation": self.operation,
            "audio_data": self.audio_data.hex(),
            "sample_rate": self.sample_rate,
            "channels": self.channels
        })
        journaling_manager.recordDebug(f"Converted Audio command to dict: {data}")
        return data

class CameraCommand(BaseCommand):
    """Camera control commands"""
    def __init__(self, command_type: CommandType, action: str, resolution: tuple = (640, 480), format: str = "RGB"):
        journaling_manager.recordScope("CameraCommand.__init__")
        super().__init__(command_type)
        self.action = action
        self.resolution = resolution
        self.format = format
        journaling_manager.recordDebug(f"Camera command initialized with action: {self.action}, resolution: {self.resolution}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Camera command to dictionary"""
        journaling_manager.recordScope("CameraCommand.to_dict")
        data = super().to_dict()
        data.update({
            "action": self.action,
            "resolution": list(self.resolution),
            "format": self.format
        })
        journaling_manager.recordDebug(f"Converted Camera command to dict: {data}")
        return data

class YOLOCommand(BaseCommand):
    """YOLO object detection commands"""
    def __init__(self, command_type: CommandType, image_data: bytes, confidence_threshold: float = 0.5, nms_threshold: float = 0.4):
        journaling_manager.recordScope("YOLOCommand.__init__")
        super().__init__(command_type)
        self.image_data = image_data
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        journaling_manager.recordDebug(f"YOLO command initialized with confidence: {self.confidence_threshold}, nms: {self.nms_threshold}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert YOLO command to dictionary"""
        journaling_manager.recordScope("YOLOCommand.to_dict")
        data = super().to_dict()
        data.update({
            "image_data": self.image_data.hex(),
            "confidence_threshold": self.confidence_threshold,
            "nms_threshold": self.nms_threshold
        })
        journaling_manager.recordDebug(f"Converted YOLO command to dict: {data}")
        return data

class WhisperCommand(BaseCommand):
    """Whisper speech recognition commands"""
    def __init__(self, command_type: CommandType, audio_data: bytes, language: Optional[str] = None, task: str = "transcribe"):
        journaling_manager.recordScope("WhisperCommand.__init__")
        super().__init__(command_type)
        self.audio_data = audio_data
        self.language = language
        self.task = task
        journaling_manager.recordDebug(f"Whisper command initialized with task: {self.task}, language: {self.language}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Whisper command to dictionary"""
        journaling_manager.recordScope("WhisperCommand.to_dict")
        data = super().to_dict()
        data.update({
            "audio_data": self.audio_data.hex(),
            "language": self.language,
            "task": self.task
        })
        journaling_manager.recordDebug(f"Converted Whisper command to dict: {data}")
        return data

class MeloTTSCommand(BaseCommand):
    """MeloTTS synthesis commands"""
    def __init__(self, command_type: CommandType, text: str, speaker_id: str = "default", language: str = "en", style: Optional[str] = None):
        journaling_manager.recordScope("MeloTTSCommand.__init__")
        super().__init__(command_type)
        self.text = text
        self.speaker_id = speaker_id
        self.language = language
        self.style = style
        journaling_manager.recordDebug(f"MeloTTS command initialized with speaker: {self.speaker_id}, language: {self.language}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert MeloTTS command to dictionary"""
        journaling_manager.recordScope("MeloTTSCommand.to_dict")
        data = super().to_dict()
        data.update({
            "text": self.text,
            "speaker_id": self.speaker_id,
            "language": self.language,
            "style": self.style
        })
        journaling_manager.recordDebug(f"Converted MeloTTS command to dict: {data}")
        return data

class CommandSerializer:
    """Handles command serialization/deserialization"""
    
    @staticmethod
    def serialize(command: BaseCommand) -> Dict[str, Any]:
        """Serialize command to dictionary format"""
        journaling_manager.recordScope("CommandSerializer.serialize", command=command)
        try:
            if not isinstance(command, BaseCommand):
                journaling_manager.recordError("Invalid command type")
                raise ValueError("Invalid command type")
                
            # Use the command's to_dict method if available
            if hasattr(command, 'to_dict'):
                data = command.to_dict()
                journaling_manager.recordDebug(f"Serialized command using to_dict: {data}")
                return data
                
            # Fallback to basic serialization
            data = {
                "command_type": command.command_type.value,
                **{k: v for k, v in command.__dict__.items() if not k.startswith('_')}
            }
            journaling_manager.recordDebug(f"Serialized command using fallback: {data}")
            return data
            
        except Exception as e:
            journaling_manager.recordError(f"Error serializing command: {e}")
            raise
            
    @staticmethod
    def deserialize(data: Dict[str, Any]) -> BaseCommand:
        """Deserialize command from dictionary format"""
        journaling_manager.recordScope("CommandSerializer.deserialize", data=data)
        try:
            if not isinstance(data, dict):
                journaling_manager.recordError("Invalid data type")
                raise ValueError("Invalid data type")
                
            command_type = CommandType(data["command_type"])
            command = CommandFactory.create_command(command_type, **data)
            
            journaling_manager.recordDebug(f"Deserialized command: {command_type}")
            return command
            
        except Exception as e:
            journaling_manager.recordError(f"Error deserializing command: {e}")
            raise
            
    @staticmethod
    def to_json(command: BaseCommand) -> str:
        """Serialize command to JSON string"""
        journaling_manager.recordScope("CommandSerializer.to_json", command=command)
        try:
            data = CommandSerializer.serialize(command)
            json_str = json.dumps(data)
            journaling_manager.recordDebug(f"Serialized command to JSON: {json_str}")
            return json_str
            
        except Exception as e:
            journaling_manager.recordError(f"Error serializing command to JSON: {e}")
            raise
            
    @staticmethod
    def from_json(json_str: str) -> BaseCommand:
        """Deserialize command from JSON string"""
        journaling_manager.recordScope("CommandSerializer.from_json", json_str=json_str)
        try:
            data = json.loads(json_str)
            command = CommandSerializer.deserialize(data)
            journaling_manager.recordDebug(f"Deserialized command from JSON: {command.command_type}")
            return command
            
        except Exception as e:
            journaling_manager.recordError(f"Error deserializing command from JSON: {e}")
            raise

class CommandFactory:
    """Factory for creating command instances"""
    
    _command_classes = {
        CommandType.ASR: ASRCommand,
        CommandType.TTS: TTSCommand,
        CommandType.VAD: VADCommand,
        CommandType.LLM: LLMCommand,
        CommandType.VLM: VLMCommand,
        CommandType.KWS: KWSCommand,
        CommandType.SYS: SystemCommand,
        CommandType.AUDIO: AudioCommand,
        CommandType.CAMERA: CameraCommand,
        CommandType.YOLO: YOLOCommand,
        CommandType.WHISPER: WhisperCommand,
        CommandType.MELOTTS: MeloTTSCommand
    }
    
    @classmethod
    def create_command(cls, command_type: CommandType, **kwargs) -> BaseCommand:
        """Create a command object from command type and parameters"""
        try:
            # Remove command_type from kwargs if it exists
            kwargs.pop('command_type', None)
            
            # Get the command class
            command_class = cls._command_classes.get(command_type)
            if not command_class:
                raise ValueError(f"Unknown command type: {command_type}")
                
            # Create command instance with command_type
            return command_class(command_type=command_type, **kwargs)
            
        except Exception as e:
            journaling_manager.recordError(f"Error creating command: {e}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise
            
    @classmethod
    def validate_command(cls, command_type: CommandType, data: Dict[str, Any]) -> None:
        """Validate command data"""
        journaling_manager.recordScope("CommandFactory.validate_command", command_type=command_type, data=data)
        try:
            if command_type not in cls._command_classes:
                journaling_manager.recordError(f"Unknown command type: {command_type}")
                raise ValueError(f"Unknown command type: {command_type}")
                
            command_class = cls._command_classes[command_type]
            
            # Remove command_type and timestamp from data to avoid duplicate arguments
            validation_data = data.copy()
            validation_data.pop('command_type', None)
            validation_data.pop('timestamp', None)
            
            # Create a temporary command for validation
            command = command_class(command_type=command_type, **validation_data)
            
            if hasattr(command, 'validate'):
                if not command.validate():
                    journaling_manager.recordError("Command validation failed")
                    raise ValueError("Command validation failed")
                    
            journaling_manager.recordDebug("Command data validated successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Command validation failed: {e}")
            raise

# Create global command factory
COMMAND_FACTORY = CommandFactory() 
"""
Neurological Function:
    Redmine Manager System:
    - Learning logging
    - Training logging
    - History tracking
    - Error handling
    - State management
    - Feedback processing

Project Function:
    Handles Redmine integration:
    - Learning event logging
    - Training result logging
    - History retrieval
    - Error handling
"""

from redminelib import Redmine
import os
from ..FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from typing import Any, Optional

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class RedmineManager:
    """Manages Redmine integration for learning and training logging"""
    
    def __init__(self):
        """Initialize Redmine manager"""
        journaling_manager.recordScope("RedmineManager.__init__")
        try:
            self.api_key = os.getenv('REDMINE_API_KEY')
            self.url = os.getenv('REDMINE_URL', 'http://localhost:3000')
            self.redmine = Redmine(self.url, key=self.api_key)
            self.project_id = 'penphin-os'
            journaling_manager.recordDebug(f"Redmine manager initialized with URL: {self.url}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing Redmine manager: {e}")
            raise

    def log_learning(self, title: str, description: str, category: str = "learning") -> Any:
        """Log a learning event or insight"""
        journaling_manager.recordScope("RedmineManager.log_learning", title=title, category=category)
        try:
            issue = self.redmine.issue.create(
                project_id=self.project_id,
                subject=title,
                description=description,
                tracker_id=1,  # 1 for learning
                category=category
            )
            journaling_manager.recordDebug(f"Logged learning event: {title}")
            return issue
            
        except Exception as e:
            journaling_manager.recordError(f"Error logging learning event: {e}")
            raise

    def log_training_result(self, model_name: str, accuracy: float, notes: str) -> Any:
        """Log training results"""
        journaling_manager.recordScope("RedmineManager.log_training_result", model_name=model_name, accuracy=accuracy)
        try:
            issue = self.redmine.issue.create(
                project_id=self.project_id,
                subject=f"Training Results: {model_name}",
                description=f"Accuracy: {accuracy}\nNotes: {notes}",
                tracker_id=2  # 2 for training
            )
            journaling_manager.recordDebug(f"Logged training results for {model_name}: {accuracy}")
            return issue
            
        except Exception as e:
            journaling_manager.recordError(f"Error logging training results: {e}")
            raise

    def get_learning_history(self, category: Optional[str] = None) -> Any:
        """Retrieve learning history"""
        journaling_manager.recordScope("RedmineManager.get_learning_history", category=category)
        try:
            filters = {'project_id': self.project_id}
            if category:
                filters['category'] = category
            history = self.redmine.issue.filter(**filters)
            journaling_manager.recordDebug(f"Retrieved learning history for category: {category}")
            return history
            
        except Exception as e:
            journaling_manager.recordError(f"Error retrieving learning history: {e}")
            raise 
"""
Neurological Function:
    Synaptic Pathways System:
    - Neural communication
    - Signal transmission
    - Command routing
    - Response handling
    - Error management
    - State tracking
    - Connection management

Project Function:
    Handles neural communication:
    - Command transmission
    - Response processing
    - Error handling
    - State management
"""

# Standard library imports
import asyncio
import json
import logging
import os
import platform
import stat
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable, Type
from enum import Enum
import subprocess
import re
import traceback
import threading
import socket
import paramiko

# Third-party imports
import serial
import serial.tools.list_ports

# Local imports
from Mind.CorpusCallosum.neural_commands import (
    BaseCommand, CommandType, CommandFactory, CommandSerializer,
    TTSCommand, ASRCommand, LLMCommand, SystemCommand, WhisperCommand, VADCommand
)
from Mind.CorpusCallosum.command_loader import CommandLoader
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel
from Mind.CorpusCallosum.transport_layer import get_transport, ConnectionError, CommandError, run_adb_command
from Mind.Subcortex.BasalGanglia.basal_ganglia_integration import BasalGangliaIntegration
from Mind.Subcortex.BasalGanglia.tasks.display_visual_task import DisplayVisualTask

# Initialize journaling manager
journaling_manager = SystemJournelingManager(CONFIG.log_level)
journaling_manager.recordDebug(f"Initializing SynapticPathways with {CONFIG.log_level} level logging")

class SerialConnectionError(Exception):
    """Raised when serial connection fails"""
    pass

class CommandTransmissionError(Exception):
    """Raised when command transmission fails"""
    pass

class SynapticPathways:
    """Manages neural communication pathways with hardware abstraction"""
    
    # Class variables
    _serial_connection: Optional[serial.Serial] = None
    _managers: Dict[str, Any] = {}
    _initialized = False
    _mode = None  # Set by command line argument
    _audio_cache_dir = Path("cache/audio")
    _command_handlers: Dict[CommandType, Callable] = {}
    _integration_areas: Dict[str, Any] = {}
    welcome_message = ""
    _connection_type = None
    _serial_port = None
    _response_buffer = ""
    _response_callback = None
    _response_thread = None
    _stop_thread = False
    current_hw_info = {
        "cpu_load": "N/A",
        "memory_usage": "N/A",
        "temperature": "N/A",
        "timestamp": 0
    }
    # Store available models
    available_models = []
    default_llm_model = ""
    _transport = None
    _active_operation = False  # Tracks if an operation is in progress
    _final_shutdown = False    # Indicates this is the final application shutdown
    _basal_ganglia = None
    _brain_mode = None  # Brain region mode from run.py (vc, ac, fc, full)
    _ui_mode = None     # UI mode for visualization (will be derived from brain mode)
    _cortex_communication_enabled = True  # Enable communication between cortices
    
    def __init__(self):
        """Initialize the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.__init__")
        self._initialized = False
        self._processing = False
        self.current_state = {
            "connection": None,
            "status": "idle",
            "error": None
        }
        journaling_manager.recordDebug("SynapticPathways instance initialized")
        journaling_manager.recordDebug(f"Current state: {self.current_state}")
        
    @classmethod
    def register_integration_area(cls, area_type: str, area_instance: Any) -> None:
        """Register an integration area for neural processing"""
        cls._integration_areas[area_type] = area_instance
        journaling_manager.recordInfo(f"Registered integration area: {area_type}")

    @classmethod
    def get_integration_area(cls, area_type: str) -> Any:
        """Get a registered integration area"""
        return cls._integration_areas.get(area_type)

    @classmethod
    def set_mode(cls, mode: str) -> None:
        """
        Set the brain region mode from command line arguments
        
        Args:
            mode: Brain region mode ('vc', 'ac', 'fc', 'full')
        """
        if mode not in ["vc", "ac", "fc", "full"]:
            journaling_manager.recordWarning(f"Unknown brain mode: {mode}, defaulting to 'fc'")
            mode = "fc"
        
        cls._brain_mode = mode
        journaling_manager.recordInfo(f"Operational mode set to: {mode}")
        
        # Automatically derive the UI mode based on brain mode
        if mode == "full":
            cls._ui_mode = "full"  # Full pixel visualization for full brain mode
            cls._cortex_communication_enabled = True
            journaling_manager.recordInfo("UI mode set to 'full' with cortex communication enabled")
        elif mode == "fc":
            cls._ui_mode = "fc"  # Text visualization for frontal cortex mode
            journaling_manager.recordInfo("UI mode set to 'fc' (text visualization)")
        elif mode == "vc":
            cls._ui_mode = "full"  # Visual cortex mode should use full visualization
            journaling_manager.recordInfo("UI mode set to 'full' for visual cortex tests")
        else:
            cls._ui_mode = "headless"  # Headless for other modes
            journaling_manager.recordInfo("UI mode set to 'headless' (no visualization)")

    @classmethod
    async def initialize(cls, connection_type=None):
        """Initialize the SynapticPathways system."""
        journaling_manager.recordInfo(f"Initializing SynapticPathways with connection type: {connection_type}")
        
        try:
            # Get BG integration
            bg = cls.get_basal_ganglia()
            
            # Get communication task - use get_communication_task or direct _tasks access
            if hasattr(bg, "get_communication_task"):
                comm_task = bg.get_communication_task()
            else:
                # Fallback to direct task access if method doesn't exist
                comm_task = bg._tasks.get("CommunicationTask")
                if not comm_task:
                    # Create it if needed
                    from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask
                    comm_task = CommunicationTask(priority=1)
                    bg.add_task(comm_task)
            
            # Initialize communication
            if connection_type and comm_task:
                journaling_manager.recordInfo(f"Initializing communication with {connection_type}")
                success = await comm_task.initialize(connection_type)
                cls._initialized = success
                cls._connection_type = connection_type if success else None
                
                if success:
                    journaling_manager.recordInfo(f"Successfully connected using {connection_type}")
                    return True
            
            # Try existing connection
            elif cls._connection_type and comm_task:
                return await comm_task.initialize(cls._connection_type)
            
            # No connection specified
            else:
                journaling_manager.recordError("No connection type specified and no existing connection")
                return False
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing SynapticPathways: {e}")
            import traceback
            journaling_manager.recordError(f"Traceback: {traceback.format_exc()}")
        return False

    @classmethod
    async def set_device_mode(cls, mode: str) -> None:
        """Initialize the connection in the requested mode (serial, adb, or tcp)"""
        if mode not in ["serial", "adb", "tcp", "wifi"]:
            raise ValueError("Invalid mode. Use 'serial', 'adb', or 'tcp'")
        
        # Convert 'wifi' to 'tcp' for backward compatibility
        if mode == "wifi":
            mode = "tcp"
            journaling_manager.recordInfo("Converting 'wifi' mode to 'tcp' for clarity")
        
        journaling_manager.recordInfo(f"\nInitializing {mode} connection...")
        
        # Only cleanup if we're switching modes or not initialized
        if cls._connection_type != mode or not cls._initialized:
            journaling_manager.recordInfo(f"Cleaning up existing connections before establishing new {mode} connection...")
            await cls.cleanup()
        else:
            journaling_manager.recordInfo(f"Reusing existing {mode} connection - skipping cleanup")
        
        try:
            # Get appropriate transport
            journaling_manager.recordInfo(f"Creating {mode} transport...")
            cls._transport = get_transport(mode)
            cls._connection_type = mode  # Set connection type before connect attempt
            
            # Try to connect
            connect_start = time.time()
            connection_successful = await cls._transport.connect()
            connect_time = time.time() - connect_start
            
            if connection_successful:
                journaling_manager.recordInfo(f"{mode.capitalize()} connection established in {connect_time:.2f} seconds")
                
                # Test the connection with ping_system instead of transport.test_connection
                try:
                    journaling_manager.recordInfo(f"Testing {mode} connection...")
                    test_start = time.time()
                    connection_tested = await cls.ping_system()  # Use existing ping_system method
                    test_time = time.time() - test_start
                    
                    if connection_tested:
                        journaling_manager.recordInfo(f"{mode.capitalize()} connection tested successfully in {test_time:.2f} seconds")
                    else:
                        journaling_manager.recordWarning(f"{mode.capitalize()} connection test failed, but continuing anyway")
                except Exception as e:
                    journaling_manager.recordWarning(f"Connection test failed but continuing: {e}")
                    connection_tested = True  # Assume it works anyway
                
                # Set as initialized
                cls._initialized = True
                cls._connection_type = mode
                
                # Populate initial hardware info and models
                try:
                    journaling_manager.recordInfo("Getting initial hardware info...")
                    cls.current_hw_info = await cls.get_hardware_info()
                except Exception as e:
                    journaling_manager.recordWarning(f"Failed to get hardware info: {e}")
                
                try:
                    journaling_manager.recordInfo("Getting available models...")
                    cls.available_models = await cls.get_available_models()
                except Exception as e:
                    journaling_manager.recordWarning(f"Failed to get models: {e}")
                
                journaling_manager.recordInfo(f"{mode.capitalize()} connection setup complete!")
                return
            else:
                journaling_manager.recordError(f"Failed to establish {mode} connection after {connect_time:.2f} seconds")
                
                # If TCP connection failed and it wasn't already a retry with discovered IP,
                # the WiFiTransport.connect() method already tried ADB discovery and retried TCP
                if mode == "tcp":
                    # Both the initial TCP attempt and the ADB-discovered IP attempt failed
                    # Ask the user if they want to try ADB mode
                    try:
                        print("\n=========================================")
                        print("TCP connection failed with configured IP and with ADB-discovered IP.")
                        print("Would you like to try connecting via ADB mode instead? [Y/n]")
                        choice = input("Enter choice: ").strip().lower()
                        
                        # Default to yes if empty or 'y'
                        if not choice or choice.startswith('y'):
                            journaling_manager.recordInfo("User chose to try ADB mode as fallback")
                            # Clean up failed TCP transport
                            if cls._transport:
                                await cls._transport.disconnect()
                            
                            # Try ADB mode
                            await cls.set_device_mode("adb")
                            return
                        else:
                            journaling_manager.recordInfo("User chose not to try ADB mode")
                            print("Connection failed. Please check your device and try again.")
                    except Exception as e:
                        journaling_manager.recordError(f"Error during user prompt: {e}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error initializing {mode} connection: {e}")
            
            # If TCP connection failed with an exception, ask if user wants to try ADB
            if mode == "tcp":
                try:
                    print("\n=========================================")
                    print(f"TCP connection failed with error: {str(e)}")
                    print("Would you like to try connecting via ADB mode instead? [Y/n]")
                    choice = input("Enter choice (default: Y): ").strip().lower()
                    
                    # Default to yes if empty or 'y'
                    if not choice or choice.startswith('y'):
                        journaling_manager.recordInfo("User chose to try ADB mode after TCP error")
                        # Clean up if needed
                        if cls._transport:
                            await cls._transport.disconnect()
                        
                        # Try ADB mode
                        await cls.set_device_mode("adb")
                        return
                    else:
                        journaling_manager.recordInfo("User chose not to try ADB mode")
                        print("Connection failed. Please check your device and try again.")
                except Exception as prompt_err:
                    journaling_manager.recordError(f"Error during user prompt: {prompt_err}")

    @classmethod
    async def cleanup(cls) -> None:
        """Clean up resources before establishing a new connection or shutting down"""
        if not cls._initialized or not cls._transport:
            # Nothing to clean up in terms of transport
            pass
        else:
            try:
                # Disconnect the transport
                journaling_manager.recordInfo(f"Disconnecting {cls._connection_type} transport...")
                await cls._transport.disconnect()
                journaling_manager.recordInfo("Transport disconnected successfully")
            except Exception as e:
                journaling_manager.recordError(f"Error during transport cleanup: {e}")
                    
            # Shutdown BasalGanglia if it exists
            if cls._basal_ganglia:
                journaling_manager.recordInfo("Shutting down BasalGanglia task system")
                cls._basal_ganglia.shutdown()
                cls._basal_ganglia = None
        
        # Reset state
        cls._transport = None
        cls._initialized = False
        cls._connection_type = None
        cls._mode = None
        journaling_manager.recordInfo("Synaptic pathways cleaned up")

    @classmethod
    async def transmit_json(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transmit a command as JSON and get response using CommunicationTask
        
        This method is kept for backward compatibility but uses CommunicationTask
        """
        try:
            # Get communication task
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            # Send command
            return await comm_task.send_command(command)
            
        except Exception as e:
            journaling_manager.recordError(f"Error in transmit_json: {e}")
            raise CommandTransmissionError(f"Failed to transmit command: {e}")

    @classmethod
    async def send_command(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the appropriate processor"""
        journaling_manager.recordInfo(f"\nProcessing command: {command}")
        
        command_type = command.get("type", "")
        command_action = command.get("command", "")
        
        # Handle LLM commands through BasalGanglia
        if command_type == "LLM":
            # Get a timestamp for request ID
            request_id = command.get("data", {}).get("request_id", f"llm_{int(time.time())}")
            
            # For setup commands, still use direct API as these configure the LLM system
            if command_action == "setup":
                setup_data = command.get("data", {})
                setup_command = {
                    "request_id": request_id,
                    "work_id": "llm",
                    "action": "setup",
                    "object": "llm.setup",
                    "data": {
                        "model": setup_data.get("model", "qwen2.5-0.5b"),
                        "response_format": "llm.utf-8.stream",
                        "input": "llm.utf-8.stream",
                        "enoutput": True,
                        "enkws": True,
                        "max_token_len": 127
                    }
                }
                return await cls.transmit_json(setup_command)
                
            # For actual generation, use the ThinkTask
            elif command_action == "generate":
                prompt = command.get("data", {}).get("prompt", "")
                # Use BasalGanglia for thinking tasks
                return await cls.think(prompt, stream=True)
            
            # Other LLM command types can be handled similarly
            else:
                # Continue with existing implementation for other actions
                return {
                    "error": {
                        "code": 1,
                        "message": f"Unknown LLM command: {command_action}"
                    }
                }
                
        # Handle other command types...
        # This would be implemented for other command types
        
        return {
            "error": {
                "code": 1,
                "message": f"Unknown command type: {command_type}"
            }
        }

    @classmethod
    async def send_system_command(cls, command_type: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a system command through the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.send_system_command", command_type=command_type, data=data)
        
        try:
            # Use BasalGanglia for task management
            task = cls.get_basal_ganglia().system_command(command_type, data)
            
            # Wait for task to complete (this is a blocking operation)
            while task.active or not task.has_completed():
                await asyncio.sleep(0.1)
            
            # Return task result
            return task.result if task.result is not None else {"error": "Task completed with no result"}
            
        except Exception as e:
            journaling_manager.recordError(f"Error sending system command: {e}")
            raise CommandTransmissionError(f"Failed to send system command: {e}")
            
    @classmethod
    def _validate_command(cls, command: BaseCommand) -> None:
        """Validate a command"""
        journaling_manager.recordScope("SynapticPathways._validate_command", command=command)
        try:
            # Get command data without timestamp
            command_data = command.to_dict()
            command_data.pop('timestamp', None)
            
            # Validate command data
            CommandFactory.validate_command(command.command_type, command_data)
            journaling_manager.recordDebug("Command validated successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Command validation failed: {e}")
            raise
            
    @classmethod
    async def _process_command(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a command through the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways._process_command", command=command)
        try:
            # Process command through appropriate integration area
            command_type = command.get("command_type")
            if command_type in cls._integration_areas:
                area = cls._integration_areas[command_type]
                if hasattr(area, "process_command"):
                    return await area.process_command(command)
                    
            # If no specific handler, use default processing
            response = await cls.transmit_json(command)
            journaling_manager.recordDebug(f"Command processed: {response}")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {e}")
            raise

    # Command handler registration
    @classmethod
    def register_command_handler(cls, command_type: CommandType, handler: "Callable") -> None:
        """Register a handler for a specific command type"""
        cls._command_handlers[command_type] = handler
        journaling_manager.recordInfo(f"Registered handler for {command_type}")

    @classmethod
    async def transmit_command(cls, command: BaseCommand) -> Dict[str, Any]:
        """Transmit a command object directly"""
        try:
            # If it's an LLM command, use the think task
            if command.command_type == CommandType.LLM:
                llm_command = command.to_dict()
                prompt = llm_command.get("data", {}).get("prompt", "")
                return await cls.think(prompt, stream=llm_command.get("data", {}).get("stream", False))
            
            # For other commands, use existing logic
            command_dict = CommandSerializer.serialize(command)
            return await cls.transmit_json(command_dict)
            
        except Exception as e:
            journaling_manager.recordError(f"Command transmission failed: {e}")
            raise

    @classmethod
    def get_manager(cls, manager_type: str) -> Any:
        """Get a registered manager instance"""
        return cls._managers.get(manager_type)

    @classmethod
    def register_manager(cls, manager_type: str, manager_instance: Any) -> None:
        """Register a manager instance"""
        cls._managers[manager_type] = manager_instance
        journaling_manager.recordInfo(f"Registered {manager_type} manager")

    @classmethod
    async def close_connections(cls) -> None:
        """Close all connections and clean up resources"""
        try:
            if cls._serial_connection and cls._serial_connection.is_open:
                cls._serial_connection.close()
                cls._serial_connection = None
            cls._initialized = False
            cls._mode = None
            journaling_manager.recordInfo("Neural pathways connections closed")
        except Exception as e:
            journaling_manager.recordError(f"Error closing neural pathways connections: {e}")
            raise

    @classmethod
    def _start_response_thread(cls):
        """Start thread to continuously read responses"""
        cls._stop_thread = False
        cls._response_thread = threading.Thread(target=cls._read_responses)
        cls._response_thread.daemon = True
        cls._response_thread.start()

    @classmethod
    def _stop_response_thread(cls):
        """Stop the response reading thread"""
        cls._stop_thread = True
        if cls._response_thread:
            cls._response_thread.join()

    @classmethod
    def _read_responses(cls):
        """Continuously read responses from the serial port"""
        while not cls._stop_thread:
            if cls._connection_type == "serial" and cls._serial_connection and cls._serial_connection.is_open:
                try:
                    if cls._serial_connection.in_waiting:
                        char = cls._serial_connection.read().decode('utf-8')
                        cls._response_buffer += char
                        
                        # Check for complete JSON response
                        if char == '\n' and cls._response_buffer.strip():
                            try:
                                response = json.loads(cls._response_buffer.strip())
                                if cls._response_callback:
                                    cls._response_callback(response.get('data', ''))
                            except json.JSONDecodeError:
                                journaling_manager.recordError(f"Error decoding JSON: {cls._response_buffer}")
                            finally:
                                cls._response_buffer = ""
                except Exception as e:
                    journaling_manager.recordError(f"Error reading from serial: {e}")
            elif cls._connection_type == "adb":
                try:
                    # Read one character at a time using ADB
                    read_result = subprocess.run(
                        ["adb", "shell", f"dd if={cls._serial_port} bs=1 count=1 iflag=nonblock 2>/dev/null"],
                        capture_output=True,
                        text=True
                    )
                    
                    if read_result.returncode == 0 and read_result.stdout:
                        char = read_result.stdout
                        cls._response_buffer += char
                        
                        # Check for complete JSON response
                        if char == '\n' and cls._response_buffer.strip():
                            try:
                                response = json.loads(cls._response_buffer.strip())
                                if cls._response_callback:
                                    cls._response_callback(response.get('data', ''))
                            except json.JSONDecodeError:
                                journaling_manager.recordError(f"Error decoding JSON: {cls._response_buffer}")
                            finally:
                                cls._response_buffer = ""
                except Exception as e:
                    journaling_manager.recordError(f"Error reading from ADB: {e}")
            time.sleep(0.01)

    @classmethod
    async def get_hardware_info(cls) -> Dict[str, Any]:
        """Get hardware information without forcing a refresh."""
        journaling_manager.recordDebug("[SynapticPathways] Getting hardware info")
        
        try:
            # Get hardware info task
            bg = cls.get_basal_ganglia()
            hw_task = bg.get_hardware_info_task()
            
            if not hw_task:
                journaling_manager.recordError("[SynapticPathways] ❌ Hardware info task not found")
                return cls.current_hw_info
            
            # Return current cached info without forcing refresh
            hw_info = hw_task.hardware_info
            journaling_manager.recordDebug(f"[SynapticPathways] 📊 Retrieved hardware info: {hw_info}")
            return hw_info
            
        except Exception as e:
            journaling_manager.recordError(f"[SynapticPathways] ❌ Error getting hardware info: {e}")
            journaling_manager.recordError(f"[SynapticPathways] Stack trace: {traceback.format_exc()}")
            return cls.current_hw_info  # Fallback to cached info

    @classmethod
    def format_hw_info(cls) -> str:
        """Format hardware info with proper field names and unit conversions."""
        try:
            # Get hardware info task
            bg = cls.get_basal_ganglia()
            hw_task = bg.get_hardware_info_task() if hasattr(bg, "get_hardware_info_task") else None
            
            # Get current info - either from task or fallback
            hw = hw_task.hardware_info if hw_task else cls.current_hw_info
            
            # Format timestamp
            timestamp = hw.get("timestamp", 0)
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp)) if timestamp else "N/A"
            
            # Get CPU and memory with exact field names from API
            cpu = hw.get("cpu_loadavg", "N/A")
            mem = hw.get("mem", "N/A")
            
            # Handle temperature conversion from millidegrees to degrees
            # API returns temperature in millidegrees (e.g., 39350 = 39.35°C)
            temp_millideg = hw.get("temperature", 0)
            if isinstance(temp_millideg, str):
                try:
                    temp_millideg = int(temp_millideg)
                except (ValueError, TypeError):
                    temp_millideg = 0
            
            # Convert temperature to degrees with proper formatting
            if temp_millideg:
                temp_c = f"{temp_millideg/1000:.1f}"  # Format to one decimal place
            else:
                temp_c = "N/A"
            
            # Format IP if available
            ip_address = hw.get("ip_address", "N/A")
            ip_display = f"IP: {ip_address} | " if ip_address != "N/A" else ""
            
            # Create the formatted string
            return f"""~
{ip_display}CPU: {cpu}% | Memory: {mem}% | Temp: {temp_c}°C | Updated: {time_str}
~"""
            
        except Exception as e:
            journaling_manager.recordError(f"Error formatting hardware info: {e}")
            import traceback
            journaling_manager.recordError(f"Traceback: {traceback.format_exc()}")
            
            # Emergency fallback with empty values
            return "~\nCPU: N/A | Memory: N/A | Temp: N/A | Updated: N/A\n~"

    @classmethod
    async def get_available_models(cls) -> List[Dict[str, Any]]:
        """Get available models with proper error handling."""
        journaling_manager.recordInfo("[SynapticPathways] 🔍 Getting available models")
        
        try:
            # Get model management task
            bg = cls.get_basal_ganglia()
            
            if not bg:
                journaling_manager.recordError("[SynapticPathways] ❌ BasalGanglia not initialized")
                return cls.available_models
            
            # Get model task
            model_task = bg.get_model_management_task() if hasattr(bg, "get_model_management_task") else None
            
            if not model_task:
                journaling_manager.recordError("[SynapticPathways] ❌ ModelManagementTask not found")
                return cls.available_models
            
            # Request models
            journaling_manager.recordInfo("[SynapticPathways] 🔄 Requesting models from task")
            models = await model_task.get_available_models()
            
            # Check if we got models
            if models and len(models) > 0:
                journaling_manager.recordInfo(f"[SynapticPathways] ✅ Retrieved {len(models)} models")
                cls.available_models = models
                return models
            else:
                journaling_manager.recordWarning("[SynapticPathways] ⚠️ No models returned, using cached models")
            return cls.available_models
            
        except Exception as e:
            journaling_manager.recordError(f"[SynapticPathways] ❌ Error getting models: {e}")
            import traceback
            journaling_manager.recordError(f"[SynapticPathways] Stack trace: {traceback.format_exc()}")
            return cls.available_models

    @classmethod
    async def set_active_model(cls, model_name: str) -> bool:
        """Set active model using ModelManagementTask"""
        try:
            # Get model management task
            bg = cls.get_basal_ganglia()
            model_task = bg.get_model_management_task()
            
            # Set active model
            success = await model_task.set_active_model(model_name)
            
            # Update default model if successful
            if success:
                cls.default_llm_model = model_name
                
            return success
                
        except Exception as e:
            journaling_manager.recordError(f"Error setting active model: {e}")
            return False

    @classmethod
    async def reset_llm(cls) -> bool:
        """Reset LLM using ModelManagementTask"""
        try:
            # Get model management task
            bg = cls.get_basal_ganglia()
            model_task = bg.get_model_management_task()
            
            # Reset LLM
            return await model_task.reset_llm()
            
        except Exception as e:
            journaling_manager.recordError(f"Error resetting LLM: {e}")
            return False
    
    @classmethod
    async def reboot_device(cls) -> bool:
        """Reboot the device"""
        journaling_manager.recordInfo("\nRebooting device...")
        
        if not cls._initialized:
            journaling_manager.recordError("Cannot reboot - not connected")
            return False
        
        try:
            # Create reboot command in the correct format
            reboot_command = {
                "request_id": f"reboot_{int(time.time())}",
                "work_id": "sys",
                "action": "reboot",
                "object": "system"  # Use "system" not "sys"
            }
            
            # Send reboot command
            journaling_manager.recordInfo("Sending reboot command...")
            try:
                response = await cls.transmit_json(reboot_command)
                journaling_manager.recordInfo(f"Reboot response: {response}")
                
                # API shows message will be "rebooting ..."
                if response and response.get("error", {}).get("code", -1) == 0:
                    message = response.get("error", {}).get("message", "")
                    journaling_manager.recordInfo(f"Reboot initiated: {message}")
                    
                    # Clean up connection since device will reboot
                    await cls.cleanup()
                    return True
                else:
                    error_msg = response.get("error", {}).get("message", "Unknown error")
                    journaling_manager.recordError(f"Failed to reboot device: {error_msg}")
                    return False
            except Exception:
                # If we get an exception after sending the reboot command,
                # it might be because the device is already rebooting
                journaling_manager.recordInfo("Connection lost after reboot command - device may be rebooting")
                
                # Clean up existing connection
                await cls.cleanup()
                return True
        except Exception as e:
            journaling_manager.recordError(f"Error rebooting device: {e}")
            return False

    @classmethod
    async def get_available_models_from_response(cls, response) -> List[Dict[str, Any]]:
        """Parse models from a response object - helper for testing and debugging"""
        # Implementation is the same as the parsing section in get_available_models
        # This can be used to reprocess a response without making another request
        # You can copy the parsing logic from above
        pass

    @classmethod
    async def final_shutdown(cls) -> None:
        """Final cleanup when application is exiting"""
        journaling_manager.recordInfo("Final application shutdown - cleaning up all resources")
        await cls.cleanup()
        journaling_manager.recordInfo("Cleanup complete - application can safely exit")

    @classmethod
    def _get_ip_address(cls) -> str:
        """Get IP address of the device"""
        try:
            # Get IP address based on connection type
            if cls._connection_type == "tcp":
                # For TCP, return the IP we're connected to
                ip = cls._transport.ip if hasattr(cls._transport, 'ip') else "N/A"
                return ip
            elif cls._connection_type == "adb":
                # For ADB, try to get device IP
                try:
                    output = run_adb_command(["shell", "ip", "addr", "show", "wlan0"])
                    match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                    if match:
                        return match.group(1)
                except Exception:
                    pass
            # If we couldn't get IP based on connection type, try socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            journaling_manager.recordError(f"Error getting IP address: {e}")
            return "N/A"

    @classmethod
    async def ping_system(cls) -> bool:
        """Test the connection with a ping command."""
        journaling_manager.recordInfo("\nPinging system...")
        
        if not cls._initialized:
            journaling_manager.recordError("Cannot ping - not connected")
            return False
        
        try:
            # Get the system command task using the correct method
            bg = cls.get_basal_ganglia()
            # Try both methods in case one exists
            if hasattr(bg, "get_system_command_task"):
                system_task = bg.get_system_command_task()
            elif hasattr(bg, "get_task"):
                system_task = bg.get_task("SystemCommandTask")
            else:
                # Direct access to _tasks if neither method exists
                system_task = bg._tasks.get("SystemCommandTask")
            
            if not system_task:
                journaling_manager.recordError("System command task not found")
                return False
            
            # Configure task for ping
            system_task.command = "ping"
            system_task.data = None
            system_task.completed = False
            system_task.active = True
            
            # Wait for task to complete
            max_wait = 5  # seconds
            start_time = time.time()
            
            while not system_task.completed and (time.time() - start_time) < max_wait:
                await asyncio.sleep(0.1)
            
            # Check result
            if system_task.completed and system_task.result:
                success = system_task.result.get("success", False)
                journaling_manager.recordInfo(f"Ping {'successful' if success else 'failed'}")
                return success
            else:
                journaling_manager.recordError("Ping timed out or failed")
                return False
            
        except Exception as e:
            journaling_manager.recordError(f"Error pinging system: {e}")
            import traceback
            journaling_manager.recordError(f"Ping traceback: {traceback.format_exc()}")
            return False

    @classmethod
    def get_basal_ganglia(cls):
        """Get or create the BasalGanglia instance."""
        if cls._basal_ganglia is None:
            journaling_manager.recordInfo("[SynapticPathways] 🏗️ Creating new BasalGanglia instance")
            
            # Import here to avoid circular imports
            from Mind.Subcortex.BasalGanglia.basal_ganglia_integration import BasalGangliaIntegration
            cls._basal_ganglia = BasalGangliaIntegration()
            
            # Verify initialization
            if hasattr(cls._basal_ganglia, "_tasks") and cls._basal_ganglia._tasks:
                task_names = list(cls._basal_ganglia._tasks.keys())
                journaling_manager.recordInfo(f"[SynapticPathways] ✅ BasalGanglia initialized with tasks: {task_names}")
            else:
                journaling_manager.recordWarning("[SynapticPathways] ⚠️ BasalGanglia may not be fully initialized")
        
        return cls._basal_ganglia

    @classmethod
    async def think(cls, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Use BasalGanglia to perform a thinking task with LLM"""
        journaling_manager.recordInfo(f"Initiating thinking task: {prompt[:50]}...")
        
        try:
            # Register thinking task
            task = cls.get_basal_ganglia().think(prompt, stream)
            
            # Wait for task to complete
            while task.active or not task.has_completed():
                await asyncio.sleep(0.1)
            
            # Return thinking result
            return task.result
        except Exception as e:
            journaling_manager.recordError(f"Error in thinking task: {e}")
            return {"error": str(e)}

    @classmethod
    def display_visual(cls, content: str = None, display_type: str = "text", 
                      visualization_type: str = None, visualization_params: dict = None) -> None:
        """
        Display visual content using BasalGanglia task system
        
        Args:
            content: Text content or image path to display
            display_type: Type of content ("text", "image", "animation")
            visualization_type: Special visualization type ("splash_screen", "game_of_life")
            visualization_params: Parameters for special visualizations
        """
        if visualization_type:
            journaling_manager.recordInfo(f"Registering {visualization_type} visualization task")
        else:
            journaling_manager.recordInfo(f"Registering display task for: {display_type}")
        
        # Register display task - non-blocking
        cls.get_basal_ganglia().display_visual(
            content=content, 
            display_type=display_type,
            visualization_type=visualization_type,
            visualization_params=visualization_params
        )

    @classmethod 
    def show_splash_screen(cls, title: str = "Penphin Mind", subtitle: str = "Neural Architecture") -> None:
        """Show application splash screen"""
        cls.display_visual(
            visualization_type="splash_screen",
            visualization_params={
                "title": title,
                "subtitle": subtitle
            }
        )
        
    @classmethod
    def run_game_of_life(cls, width: int = 20, height: int = 20, iterations: int = 10, 
                        initial_state: list = None) -> None:
        """Run Conway's Game of Life visualization"""
        cls.display_visual(
            visualization_type="game_of_life",
            visualization_params={
                "width": width,
                "height": height, 
                "iterations": iterations,
                "initial_state": initial_state
            }
        )

    @classmethod
    async def setup_llm(cls, model_name: str, params: dict = None) -> Dict[str, Any]:
        """Set up the LLM with specific parameters"""
        # This is a system operation since it configures the system
        data = {
            "model": model_name,
            **(params or {})
        }
        return await cls.send_system_command("setup", data)

    @classmethod
    async def run_llm_inference(cls, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Run inference with the LLM - this is a cognitive operation"""
        # This is a thinking operation, not a system command
        return await cls.think(prompt, stream)

    @classmethod
    async def think_with_pixel_grid(cls, prompt: str, 
                                   width: int = 64, 
                                   height: int = 64,
                                   color_mode: str = "grayscale") -> Dict[str, Any]:
        """
        Use BasalGanglia to perform a thinking task with LLM and visualize the output as a pixel grid
        
        Args:
            prompt: The prompt to send to the LLM
            width: Width of the pixel grid
            height: Height of the pixel grid
            color_mode: Visualization mode ('grayscale' or 'color')
        
        Returns:
            The final LLM response
        """
        journaling_manager.recordInfo(f"Initiating thinking task with pixel grid: {prompt[:50]}...")
        
        try:
            # Create pixel grid visualization task
            visual_task = cls.get_basal_ganglia().display_llm_pixel_grid(
                width=width,
                height=height,
                color_mode=color_mode
            )
            
            # Register thinking task
            task = cls.get_basal_ganglia().think(prompt, stream=True)
            
            # Continuously update visualization as we get results
            result = ""
            while task.active or not task.has_completed():
                if hasattr(task, 'result') and task.result:
                    # Update result and visualization if there's new content
                    if isinstance(task.result, str) and task.result != result:
                        result = task.result
                        # Update the visual task with new content
                        visual_task.update_stream(result)
                
                await asyncio.sleep(0.1)
            
            # Mark visualization as complete
            visual_task.update_stream(task.result, is_complete=True)
            
            # Return final thinking result
            return task.result
        except Exception as e:
            journaling_manager.recordError(f"Error in thinking task with pixel grid: {e}")
            return {"error": str(e)}

    @classmethod
    def create_llm_pixel_grid(cls, 
                             width: int = 64, 
                             height: int = 64,
                             wrap: bool = True,
                             color_mode: str = "grayscale") -> DisplayVisualTask:
        """
        Create an LLM token-to-pixel grid visualization task that can be updated manually
        
        Returns:
            The DisplayVisualTask instance that can be updated with update_stream()
        """
        return cls.get_basal_ganglia().display_llm_pixel_grid(
            width=width,
            height=height,
            wrap=wrap,
            color_mode=color_mode
        )

    @classmethod
    def create_llm_stream_visualization(cls, 
                                      highlight_keywords: bool = False,
                                      keywords: list = None,
                                      show_tokens: bool = False) -> DisplayVisualTask:
        """
        Create an LLM stream visualization task that can be updated manually
        
        Returns:
            The DisplayVisualTask instance that can be updated with update_stream()
        """
        return cls.get_basal_ganglia().display_llm_stream(
            highlight_keywords=highlight_keywords,
            keywords=keywords,
            show_tokens=show_tokens
        )

    @classmethod
    async def think_with_stream_visualization(cls, prompt: str, 
                                            highlight_keywords: bool = False,
                                            keywords: list = None,
                                            show_tokens: bool = False) -> Dict[str, Any]:
        """
        Use BasalGanglia to perform a thinking task with LLM and visualize the streaming output
        
        Args:
            prompt: The prompt to send to the LLM
            highlight_keywords: Whether to highlight keywords in the output
            keywords: List of keywords to highlight (if None, will be extracted from prompt)
            show_tokens: Whether to show token statistics
        
        Returns:
            The final LLM response
        """
        journaling_manager.recordInfo(f"Initiating thinking task with stream visualization: {prompt[:50]}...")
        
        try:
            # Extract keywords if not provided but highlighting is requested
            if highlight_keywords and not keywords:
                # Simple keyword extraction (in a real system, use NLP for better extraction)
                import re
                words = re.findall(r'\b[A-Za-z]{4,}\b', prompt)
                # Filter out common words
                common_words = {'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how'}
                keywords = [word for word in words if word.lower() not in common_words][:5]
                journaling_manager.recordInfo(f"Extracted keywords: {keywords}")
            
            # Create visualization task first
            visual_task = cls.get_basal_ganglia().display_llm_stream(
                highlight_keywords=highlight_keywords,
                keywords=keywords,
                show_tokens=show_tokens
            )
            
            # Register thinking task
            task = cls.get_basal_ganglia().think(prompt, stream=True)
            
            # Continuously update visualization as we get results
            result = ""
            while task.active or not task.has_completed():
                if hasattr(task, 'result') and task.result:
                    # Update result and visualization if there's new content
                    if isinstance(task.result, str) and task.result != result:
                        result = task.result
                        # Update the visual task with new content
                        visual_task.update_stream(result)
            
            await asyncio.sleep(0.1)
            
            # Mark visualization as complete
            visual_task.update_stream(task.result, is_complete=True)
            
            # Return final thinking result
            return task.result
        except Exception as e:
            journaling_manager.recordError(f"Error in thinking task with visualization: {e}")
            return {"error": str(e)}

    @classmethod
    def get_ui_mode(cls) -> str:
        """Get the current UI mode with fallback to fc"""
        if cls._ui_mode is None:
            # If UI mode not explicitly set, derive from brain mode
            if cls._brain_mode == "full":
                return "full"
            elif cls._brain_mode in ["fc", "vc"]:
                return "fc"
            else:
                return "headless"
        return cls._ui_mode

    @classmethod
    async def think_with_visualization(cls, prompt: str, 
                                      highlight_keywords: bool = False,
                                      keywords: list = None,
                                      show_tokens: bool = False) -> Dict[str, Any]:
        """
        Think with visualization based on current UI mode
        
        In full mode, enables communication between cortices (OccipitalLobe gets data from PrefrontalCortex)
        In fc mode, uses text stream visualization
        In headless mode, uses basic thinking without visualization
        
        Args:
            prompt: The prompt to send to the LLM
            highlight_keywords: Whether to highlight keywords (for text visualization)
            keywords: List of keywords to highlight
            show_tokens: Whether to show token statistics
            
        Returns:
            The thinking result
        """
        # Get UI mode based on current settings
        ui_mode = cls.get_ui_mode()
        journaling_manager.recordInfo(f"[CorpusCallosum] Thinking with visualization in {ui_mode} mode")
        
        try:
            # Select visualization based on mode
            if ui_mode == "full":
                # Full UI mode - use pixel grid visualization and enable cortex communication
                journaling_manager.recordInfo("[CorpusCallosum] Using pixel grid visualization with cortex communication")
                
                # Enable direct communication between OccipitalLobe and PrefrontalCortex
                if cls._cortex_communication_enabled:
                    occipital_area = None
                    
                    # Get the OccipitalLobe's visual processing area if registered
                    if "OccipitalLobe" in cls._integration_areas:
                        occipital_area = cls._integration_areas["OccipitalLobe"]
                        journaling_manager.recordInfo("[CorpusCallosum] OccipitalLobe integration area found")
                        
                        # Initialize it if needed
                        if hasattr(occipital_area, "initialize") and callable(occipital_area.initialize):
                            await occipital_area.initialize()
                    
                # Use pixel grid visualization
                return await cls.think_with_pixel_grid(
                    prompt=prompt,
                    width=64,
                    height=64,
                    color_mode="color"
                )
                
            elif ui_mode == "fc":
                # Frontend console mode - use text stream visualization
                journaling_manager.recordInfo("[CorpusCallosum] Using text stream visualization")
                return await cls.think_with_stream_visualization(
                    prompt=prompt,
                    highlight_keywords=highlight_keywords,
                    keywords=keywords,
                    show_tokens=show_tokens
                )
                
            else:
                # Headless or unknown mode - just think with no visualization
                journaling_manager.recordInfo("[CorpusCallosum] Using basic thinking (no visualization)")
                return await cls.think(prompt, stream=False)
                
        except Exception as e:
            journaling_manager.recordError(f"[CorpusCallosum] Error in think_with_visualization: {e}")
            # Fallback to basic thinking
            journaling_manager.recordInfo("[CorpusCallosum] Falling back to basic thinking due to error")
            return await cls.think(prompt, stream=False)

    @classmethod
    def enable_cortex_communication(cls, enabled: bool = True) -> None:
        """
        Enable or disable direct communication between cortices
        
        When enabled, cortices can directly communicate through CorpusCallosum
        When disabled, they operate more independently
        
        Args:
            enabled: Whether to enable cortex communication
        """
        cls._cortex_communication_enabled = enabled
        journaling_manager.recordInfo(f"[CorpusCallosum] Cortex communication {'enabled' if enabled else 'disabled'}")

    @classmethod
    async def relay_between_cortices(cls, source_cortex: str, target_cortex: str, 
                                    data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Relay data between cortices through the CorpusCallosum
        
        Args:
            source_cortex: Source cortex name
            target_cortex: Target cortex name
            data: Data to relay
            
        Returns:
            Response from target cortex
        """
        if not cls._cortex_communication_enabled:
            journaling_manager.recordWarning(f"[CorpusCallosum] Cortex communication disabled, "
                                             f"cannot relay from {source_cortex} to {target_cortex}")
            return {"error": "Cortex communication disabled"}
        
        journaling_manager.recordInfo(f"[CorpusCallosum] Relaying data from {source_cortex} to {target_cortex}")
        
        try:
            # Get the target integration area
            if target_cortex not in cls._integration_areas:
                journaling_manager.recordError(f"[CorpusCallosum] Target cortex not registered: {target_cortex}")
                return {"error": f"Target cortex not registered: {target_cortex}"}
            
            target_area = cls._integration_areas[target_cortex]
            
            # Check if target has process_data method
            if not hasattr(target_area, "process_data") or not callable(target_area.process_data):
                journaling_manager.recordError(f"[CorpusCallosum] Target cortex cannot process data: {target_cortex}")
                return {"error": f"Target cortex cannot process data: {target_cortex}"}
            
            # Relay the data
            response = await target_area.process_data(data)
            journaling_manager.recordInfo(f"[CorpusCallosum] Data relayed successfully to {target_cortex}")
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"[CorpusCallosum] Error relaying data: {e}")
            return {"error": str(e)}
"""
Transport Layer Abstraction:
- Handles communication with hardware
- Manages connection methods (Serial, ADB, WiFi)
- Provides a unified interface for command transmission
"""

import asyncio
import json
import logging
import os
import platform
import socket
import subprocess
import time
import traceback
from typing import Dict, Any, Optional, Union
import paramiko
import serial
import serial.tools.list_ports
import re

from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

# Add recordWarning method to match usage
def recordWarning(self, message):
    """Log a warning message"""
    logging.warning(message)
SystemJournelingManager.recordWarning = recordWarning

# Add these at the module level, right after the imports and journaling manager
_direct_adb_failed = False  # Flag to remember if direct ADB call has failed
_adb_executable_path = None  # Cache the working executable path
_tcp_gateway_active = False  # Flag to indicate if TCP gateway is active and working

class TransportError(Exception):
    """Base exception for transport layer errors"""
    pass

class ConnectionError(TransportError):
    """Raised when connection fails"""
    pass

class CommandError(TransportError):
    """Raised when command transmission fails"""
    pass

class BaseTransport:
    """Abstract base class for all transport types"""
    
    def __init__(self):
        self.connected = False
        self.endpoint = None
        self._serial_connection = None
    
    async def connect(self) -> bool:
        """Establish connection to the device"""
        raise NotImplementedError("Subclasses must implement connect()")
    
    async def disconnect(self) -> None:
        """Close the connection"""
        raise NotImplementedError("Subclasses must implement disconnect()")
    
    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command and receive a response"""
        raise NotImplementedError("Subclasses must implement transmit()")
    
    def is_available(self) -> bool:
        """Check if this transport type is available"""
        raise NotImplementedError("Subclasses must implement is_available()")

class SerialTransport(BaseTransport):
    """Serial communication transport layer"""
    
    def __init__(self):
        super().__init__()
        self._serial_port = None
        self._serial_connection = None
        self.port = str(CONFIG.llm_service["port"])  # 10001
        self._tunnel_active = False
        self.serial_settings = CONFIG.serial_settings
    
    def is_available(self) -> bool:
        """Check if serial connection is available"""
        # Don't fail here, just return True to allow discovery process
        return True
    
    def _find_serial_port(self) -> Optional[str]:
        """Find the device port through serial"""
        journaling_manager.recordInfo("Starting serial port discovery...")
        
        ports = serial.tools.list_ports.comports()
        if not ports:
            journaling_manager.recordInfo("No serial ports found")
            return None
        
        journaling_manager.recordInfo("\nChecking all available ports...")
        for port in ports:
            journaling_manager.recordInfo(f"\nChecking port: {port.device}")
            journaling_manager.recordInfo(f"Description: {port.description}")
            if port.vid is not None and port.pid is not None:
                journaling_manager.recordInfo(f"VID:PID: {port.vid:04x}:{port.pid:04x}")
            journaling_manager.recordInfo(f"Hardware ID: {port.hwid}")
            
            # Check for CH340 device (VID:PID = 1A86:7523)
            if port.vid == 0x1A86 and port.pid == 0x7523:
                journaling_manager.recordInfo(f"\nFound CH340 device on port: {port.device}")
                return port.device
            
            # Check for M5Stack USB device patterns
            patterns = ["m5stack", "m5 module", "m5module", "cp210x", "silicon labs"]
            if any(pattern.lower() in port.description.lower() for pattern in patterns):
                journaling_manager.recordInfo(f"\nFound matching device pattern on port: {port.device}")
                return port.device
                    
            # Check for any USB CDC device
            if "USB" in port.description.upper() and "CDC" in port.description.upper():
                journaling_manager.recordInfo(f"\nFound USB CDC device on port: {port.device}")
                return port.device
                    
            # If we get here and haven't found a match, but it's a CH340 device,
            # return it anyway (some Windows systems might not report the VID/PID correctly)
            if "CH340" in port.description.upper():
                journaling_manager.recordInfo(f"\nFound CH340 device by description on port: {port.device}")
                return port.device
        
        journaling_manager.recordInfo("\nNo suitable serial port found")
        return None
    
    async def _setup_tunnel(self) -> bool:
        """Setup port forwarding tunnel"""
        try:
            journaling_manager.recordInfo(f"\n>>> SETTING UP TUNNEL FOR PORT {self.port}")
            
            # First check shell access
            self._serial_connection.write(b"whoami\n")
            await asyncio.sleep(0.5)
            shell_check = ""
            while self._serial_connection.in_waiting:
                shell_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> SHELL ACCESS: {shell_check.strip()!r}")

            # Check if netcat exists
            self._serial_connection.write(b"which nc\n")
            await asyncio.sleep(0.5)
            nc_check = ""
            while self._serial_connection.in_waiting:
                nc_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> NETCAT AVAILABLE: {nc_check.strip()!r}")

            # Check current port status
            self._serial_connection.write(f"netstat -tln | grep {self.port}\n".encode())
            await asyncio.sleep(0.5)
            port_check = ""
            while self._serial_connection.in_waiting:
                port_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> CURRENT PORT STATUS: {port_check.strip()!r}")

            # Kill any existing netcat
            self._serial_connection.write(b"pkill -f 'nc -l'\n")
            await asyncio.sleep(0.5)
            while self._serial_connection.in_waiting:
                self._serial_connection.read()

            # Start netcat tunnel with error capture
            tunnel_cmd = f"nc -l -p {self.port} 2>&1 &\n"
            journaling_manager.recordInfo(f">>> STARTING TUNNEL: {tunnel_cmd.strip()}")
            self._serial_connection.write(tunnel_cmd.encode())
            await asyncio.sleep(1)

            # Check for any error output
            self._serial_connection.write(b"dmesg | tail\n")
            await asyncio.sleep(0.5)
            error_check = ""
            while self._serial_connection.in_waiting:
                error_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> SYSTEM MESSAGES: {error_check.strip()!r}")

            # Verify tunnel process
            self._serial_connection.write(b"ps | grep nc\n")
            await asyncio.sleep(0.5)
            ps_check = ""
            while self._serial_connection.in_waiting:
                ps_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> TUNNEL PROCESS: {ps_check.strip()!r}")

            # Final port check
            self._serial_connection.write(f"netstat -tln | grep {self.port}\n".encode())
            await asyncio.sleep(0.5)
            final_check = ""
            while self._serial_connection.in_waiting:
                final_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> FINAL PORT STATUS: {final_check.strip()!r}")

            if f":{self.port}" in final_check:
                self._tunnel_active = True
                journaling_manager.recordInfo(">>> TUNNEL ESTABLISHED SUCCESSFULLY")
                return True
            else:
                journaling_manager.recordError(">>> TUNNEL SETUP FAILED - Port not listening")
                return False

        except Exception as e:
            journaling_manager.recordError(f">>> TUNNEL SETUP ERROR: {str(e)}")
            journaling_manager.recordError(f">>> STACK TRACE: {traceback.format_exc()}")
            return False

    async def connect(self) -> bool:
        """Connect to serial and setup tunnel"""
        try:
            journaling_manager.recordInfo(">>> STARTING SERIAL CONNECTION")
            
            # Connect to serial port
            self._serial_port = self.serial_settings["port"]  # COM7
            journaling_manager.recordInfo(f">>> CONNECTING TO {self._serial_port}")
            
            self._serial_connection = serial.Serial(
                port=self._serial_port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            # Clear buffer
            while self._serial_connection.in_waiting:
                self._serial_connection.read()

            # Setup tunnel
            if not await self._setup_tunnel():
                journaling_manager.recordError(">>> FAILED TO SETUP TUNNEL")
                return False

            self.endpoint = f"127.0.0.1:{self.port}"
            self.connected = True
            return True
            
        except Exception as e:
            journaling_manager.recordError(f">>> CONNECTION ERROR: {e}")
            if self._serial_connection and self._serial_connection.is_open:
                self._serial_connection.close()
            return False

    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command through tunnel"""
        if not self.connected or not self._tunnel_active:
            raise ConnectionError("Tunnel not established")
        
        try:
            # Send command through tunnel
            json_data = json.dumps(command) + "\n"
            cmd = f"echo '{json_data.strip()}' | nc localhost {self.port}\n"
            journaling_manager.recordInfo(f">>> SENDING THROUGH TUNNEL: {cmd.strip()}")
            
            self._serial_connection.write(cmd.encode())
            self._serial_connection.flush()
            
            # Read response
            buffer = ""
            start_time = time.time()
            
            while (time.time() - start_time) < 5.0:
                if self._serial_connection.in_waiting:
                    char = self._serial_connection.read().decode()
                    buffer += char
                    journaling_manager.recordInfo(f">>> RECEIVED: {char!r}")
                    
                    if char == '\n':
                        try:
                            response = json.loads(buffer.strip())
                            journaling_manager.recordInfo(f">>> VALID JSON: {response}")
                            return response
                        except json.JSONDecodeError:
                            journaling_manager.recordInfo(f">>> INVALID JSON: {buffer.strip()!r}")
                            buffer = ""
                            continue
                await asyncio.sleep(0.1)
            
            journaling_manager.recordError(">>> NO RESPONSE (timeout)")
            raise CommandError("No valid response received")
            
        except Exception as e:
            journaling_manager.recordError(f">>> TRANSMISSION ERROR: {e}")
            raise CommandError(f"Command transmission failed: {e}")

    async def disconnect(self) -> None:
        """Clean up tunnel and connection"""
        try:
            if self._tunnel_active:
                journaling_manager.recordInfo(">>> CLEANING UP TUNNEL")
                self._serial_connection.write(b"pkill -f 'nc -l'\n")
                await asyncio.sleep(0.5)
                self._tunnel_active = False
            
            if self._serial_connection and self._serial_connection.is_open:
                self._serial_connection.close()
            
            self.connected = False
            journaling_manager.recordInfo(">>> DISCONNECTED")
        except Exception as e:
            journaling_manager.recordError(f">>> DISCONNECT ERROR: {e}")

class WiFiTransport(BaseTransport):
    """TCP communication transport layer"""
    
    def __init__(self):
        super().__init__()
        self.ip = CONFIG.llm_service["ip"]
        self.port = CONFIG.llm_service["port"]
        self.timeout = CONFIG.llm_service["timeout"]
    
    def is_available(self) -> bool:
        """Check if TCP connection is available"""
        try:
            # Try to resolve the hostname/IP
            socket.gethostbyname(self.ip)
            return True
        except Exception:
            return False
    
    async def connect(self) -> bool:
        """Find LLM service port and connect with IP discovery"""
        try:
            # Show clearly what IP we're trying to connect to
            journaling_manager.recordInfo(f"🔌 Attempting TCP connection to {self.ip}:{self.port}...")
            print(f"\n🔌 Attempting TCP connection to {self.ip}:{self.port}...")
            
            # Try direct connection with current IP
            initial_connection = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3.0)
                    journaling_manager.recordInfo(f"Testing socket connection to {self.ip}:{self.port}...")
                    s.connect((self.ip, self.port))
                    
                    # Try a ping to verify LLM service
                    ping_command = {
                        "request_id": "001",
                        "work_id": "sys",
                        "action": "ping"
                    }
                    
                    # Send ping and wait for response
                    json_data = json.dumps(ping_command) + "\n"
                    s.sendall(json_data.encode())
                    
                    # Wait for response
                    response = ""
                    s.settimeout(3.0)
                    while True:
                        chunk = s.recv(1).decode()
                        if not chunk:
                            break
                        response += chunk
                        if chunk == "\n":
                            break
                    
                    # Check if ping was successful
                    if response.strip():
                        response_data = json.loads(response.strip())
                        if response_data.get("error", {}).get("code", -1) == 0:
                            initial_connection = True
                            journaling_manager.recordInfo(f"✅ TCP connection to {self.ip}:{self.port} successful!")
                            print(f"✅ TCP connection to {self.ip}:{self.port} successful!")
                        else:
                            journaling_manager.recordError(f"Ping response indicated failure: {response_data}")
                    else:
                        journaling_manager.recordError("Empty response from ping")
            except Exception as e:
                journaling_manager.recordInfo(f"❌ Initial TCP connection failed: {e}")
                print(f"❌ Initial TCP connection failed: {e}")
            
            # If direct connection worked, we're done
            if initial_connection:
                self.endpoint = f"{self.ip}:{self.port}"
                self.connected = True
                return True
            
            # TCP connection failed, temporarily use ADB to discover current IP
            journaling_manager.recordInfo("🔎 TCP connection failed. Using ADB to discover current device IP...")
            print("\n🔎 TCP connection failed. Using ADB to discover current device IP...")
            
            # Use ADB only for IP discovery
            ip_from_adb = await self._discover_ip_via_adb()
            
            if ip_from_adb:
                journaling_manager.recordInfo(f"✅ Discovered device IP via ADB: {ip_from_adb}")
                print(f"✅ Discovered device IP via ADB: {ip_from_adb}")
                
                # Update IP in instance and config
                old_ip = self.ip
                self.ip = ip_from_adb
                CONFIG.llm_service["ip"] = ip_from_adb
                
                # Save for future use
                if CONFIG.save():
                    journaling_manager.recordInfo(f"💾 Updated configuration: IP changed from {old_ip} to {ip_from_adb}")
                    print(f"💾 Updated configuration: IP changed from {old_ip} to {ip_from_adb}")
                
                # Try TCP connection with the new IP (still using TCP transport)
                try:
                    journaling_manager.recordInfo(f"🔄 Trying TCP connection with new IP: {ip_from_adb}:{self.port}...")
                    print(f"🔄 Trying TCP connection with new IP: {ip_from_adb}:{self.port}...")
                    
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(3.0)
                        s.connect((self.ip, self.port))
                        
                        # Send ping to verify
                        ping_command = {
                            "request_id": "001",
                            "work_id": "sys",
                            "action": "ping"
                        }
                        
                        # Send ping
                        json_data = json.dumps(ping_command) + "\n"
                        s.sendall(json_data.encode())
                        
                        # Get response
                        response = ""
                        s.settimeout(3.0)
                        while True:
                            chunk = s.recv(1).decode()
                            if not chunk:
                                break
                            response += chunk
                            if chunk == "\n":
                                break
                        
                        # Verify ping worked
                        if response.strip():
                            response_data = json.loads(response.strip())
                            if response_data.get("error", {}).get("code", -1) == 0:
                                self.endpoint = f"{self.ip}:{self.port}"
                                self.connected = True
                                journaling_manager.recordInfo(f"✅ TCP connection with new IP successful!")
                                print(f"✅ TCP connection with new IP successful!")
                                return True
                except Exception as e:
                    journaling_manager.recordError(f"❌ TCP connection with new IP failed: {e}")
                    print(f"❌ TCP connection with new IP failed: {e}")
            
            # Both connection attempts failed
            journaling_manager.recordError("❌ Failed to establish TCP connection with both original and discovered IPs")
            print("\n❌ Failed to establish TCP connection with both original and discovered IPs")
            self.connected = False
            return False
            
        except Exception as e:
            journaling_manager.recordError(f"❌ TCP connection error: {e}")
            self.connected = False
            return False
    
    async def _discover_ip_via_adb(self) -> Optional[str]:
        """Discover device IP address using ADB"""
        try:
            # Create an ADB transport to run commands
            adb_transport = get_transport("adb")
            if not await adb_transport.connect():
                journaling_manager.recordError("Failed to establish ADB connection for IP discovery")
                return None
            
            # First try to get IP from wlan0 interface
            try:
                output = run_adb_command(["shell", "ip", "addr", "show", "wlan0"])
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    ip = match.group(1)
                    journaling_manager.recordInfo(f"Found IP from wlan0: {ip}")
                    return ip
            except Exception as e:
                journaling_manager.recordWarning(f"Error getting IP from wlan0: {e}")
            
            # If wlan0 fails, try eth0
            try:
                output = run_adb_command(["shell", "ip", "addr", "show", "eth0"])
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    ip = match.group(1)
                    journaling_manager.recordInfo(f"Found IP from eth0: {ip}")
                    return ip
            except Exception as e:
                journaling_manager.recordWarning(f"Error getting IP from eth0: {e}")
            
            # If specific interfaces fail, try general IP commands
            try:
                # Try to get IP using ifconfig
                output = run_adb_command(["shell", "ifconfig"])
                matches = re.findall(r'inet addr:(\d+\.\d+\.\d+\.\d+)', output)
                if not matches:  # Try newer format
                    matches = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                
                if matches:
                    for ip in matches:
                        if not ip.startswith("127."):  # Skip localhost
                            journaling_manager.recordInfo(f"Found IP from ifconfig: {ip}")
                            return ip
            except Exception as e:
                journaling_manager.recordWarning(f"Error getting IP from ifconfig: {e}")
            
            # If all else fails, try to get device ADB IP address
            try:
                # Get ADB devices with IP
                output = run_adb_command(["devices", "-l"])
                ip_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+:\d+)', output)
                if ip_matches:
                    ip = ip_matches[0].split(':')[0]
                    journaling_manager.recordInfo(f"Found IP from ADB devices: {ip}")
                    return ip
            except Exception as e:
                journaling_manager.recordWarning(f"Error getting IP from ADB devices: {e}")
            
            # No IP found
            return None
        except Exception as e:
            journaling_manager.recordError(f"Error in IP discovery: {e}")
            return None
        finally:
            # Make sure to disconnect ADB transport if created
            if 'adb_transport' in locals() and adb_transport:
                await adb_transport.disconnect()
    
    async def disconnect(self) -> None:
        """Close TCP connection"""
        # Socket connections are closed after each transmission
        self.connected = False
        journaling_manager.recordInfo("TCP connection closed")
    
    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command over TCP and get response"""
        if not self.connected:
            journaling_manager.recordError("TCP connection not established")
            raise ConnectionError("TCP connection not established")
        
        try:
            ip, port = self.endpoint.split(":")
            port = int(port)
            
            # Detailed request logging
            journaling_manager.recordDebug(f"🔶 API REQUEST to {ip}:{port}:")
            journaling_manager.recordDebug(f"🔶 {json.dumps(command, indent=2)}")
            
            # Connect to the LLM service
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                
                # Prepare JSON data
                json_data = json.dumps(command) + "\n"
                
                # Connect and send
                journaling_manager.recordDebug(f"Connecting to {ip}:{port}...")
                s.connect((ip, port))
                s.sendall(json_data.encode())
                journaling_manager.recordDebug(f"Command sent successfully to {ip}:{port}")
                
                # Wait for response using byte-by-byte approach
                buffer = ""
                journaling_manager.recordDebug("Waiting for response...")
                while True:
                    try:
                        data = s.recv(1).decode()
                        if not data:
                            journaling_manager.recordDebug("No more data received")
                            break
                        buffer += data
                        
                        # For chat responses, print characters as they arrive
                        if command.get("action") == "inference":
                            print(data, end="", flush=True)
                        
                        if data == "\n":
                            journaling_manager.recordDebug("Received complete response")
                            break
                    except socket.timeout:
                        journaling_manager.recordError("Socket timeout")
                        break
            
            # Parse response
            try:
                response = json.loads(buffer.strip())
                # Detailed response logging
                journaling_manager.recordDebug(f"🔷 API RESPONSE:")
                journaling_manager.recordDebug(f"🔷 {json.dumps(response, indent=2)}")
                return response
            except json.JSONDecodeError:
                journaling_manager.recordError(f"Failed to parse JSON: {buffer.strip()!r}")
                journaling_manager.recordDebug(f"Raw response data: {buffer.strip()!r}")
                return {
                    "request_id": command.get("request_id", f"error_{int(time.time())}"),
                    "work_id": command.get("work_id", "sys"),
                    "data": "None",
                    "error": {"code": -1, "message": "Failed to parse response"},
                    "object": command.get("object", "None"),
                    "created": int(time.time())
                }
            
        except Exception as e:
            journaling_manager.recordError(f"TCP communication error: {str(e)}")
            journaling_manager.recordError(f"Stack trace: {traceback.format_exc()}")
            raise CommandError(f"TCP communication failed: {str(e)}")

    def _find_llm_port(self, ssh) -> Optional[int]:
        """Find the port where the LLM service is running"""
        journaling_manager.recordInfo("\nChecking for LLM service port...")
        
        # Try netstat first to find the LLM service port
        journaling_manager.recordInfo("\nTrying netstat to find port...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tulpn | grep llm_llm")
        for line in stdout:
            journaling_manager.recordInfo(f"Found port info: {line.strip()}")
            # Look for port number in the output
            if ":" in line:
                port = line.split(":")[-1].split()[0]
                journaling_manager.recordInfo(f"Found LLM service port: {port}")
                return int(port)
        
        # If we still can't find it, try to get the port from the process arguments
        journaling_manager.recordInfo("\nChecking process arguments...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep llm_llm")
        for line in stdout:
            if "llm_llm" in line and not "grep" in line:
                journaling_manager.recordInfo(f"Found process: {line.strip()}")
                # Try to find port in process arguments
                if "--port" in line:
                    port = line.split("--port")[1].split()[0]
                    journaling_manager.recordInfo(f"Found port in arguments: {port}")
                    return int(port)
        
        # If we get here, try common ports
        journaling_manager.recordInfo("\nTrying common ports...")
        common_ports = [10001, 8080, 80, 443, 5000, 8000, 3000]  # Put 10001 first since we know it works
        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    # Get the IP from the SSH connection
                    ip = ssh.get_transport().getpeername()[0]
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        journaling_manager.recordInfo(f"Port {port} is open and accepting connections")
                        return port
            except Exception as e:
                journaling_manager.recordError(f"Error checking port {port}: {e}")
        
        # If no port found, use the default
        journaling_manager.recordInfo(f"No LLM service port found, using default {CONFIG.llm_service['port']}")
        return CONFIG.llm_service["port"]

class ADBTransport(BaseTransport):
    """ADB communication transport layer"""
    
    def __init__(self):
        super().__init__()
        self.adb_path = CONFIG.adb_path
        self.port = str(CONFIG.llm_service["port"])  # Should be "10001"
        
    def _run_adb_command(self, command):
        """Run an ADB command using the module-level function with caching"""
        return run_adb_command(command)
    
    def is_available(self) -> bool:
        """Check if ADB is available and a device is connected"""
        try:
            # Start ADB server
            self._run_adb_command(["start-server"])
            
            # Check for connected devices
            devices_output = self._run_adb_command(["devices"])
            devices = devices_output.strip().split("\n")[1:]  # Skip header
            
            # Check if we have any devices in device state
            has_device = any(device.strip() and "device" in device for device in devices)
            journaling_manager.recordInfo(f"ADB device available: {has_device}")
            
            if not has_device:
                # Try to restart ADB server and check again
                journaling_manager.recordInfo("No devices found, trying to restart ADB server...")
                self._run_adb_command(["kill-server"])
                time.sleep(1)
                self._run_adb_command(["start-server"])
                time.sleep(2)
                
                # Check devices again
                devices_output = self._run_adb_command(["devices"])
                devices = devices_output.strip().split("\n")[1:]
                has_device = any(device.strip() and "device" in device for device in devices)
                journaling_manager.recordInfo(f"ADB device available after restart: {has_device}")
            
            return has_device
        except Exception as e:
            journaling_manager.recordError(f"Error checking ADB availability: {e}")
            return False
    
    async def connect(self) -> bool:
        """Set up port forwarding and connect to the device"""
        global _tcp_gateway_active
        
        try:
            if not self.is_available():
                raise ConnectionError("No ADB devices available")
            
            # Clear any existing forwards for this port
            try:
                self._run_adb_command(["forward", "--remove", f"tcp:{self.port}"])
                _tcp_gateway_active = False
            except Exception:
                pass
            
            # Forward local port to device port (both using LLM service port)
            journaling_manager.recordInfo(f"Setting up ADB port forwarding tcp:{self.port} -> tcp:{self.port}")
            self._run_adb_command(["forward", f"tcp:{self.port}", f"tcp:{self.port}"])
            
            # Verify port forwarding
            forwarding = self._run_adb_command(["forward", "--list"])
            if f"tcp:{self.port}" in forwarding:
                _tcp_gateway_active = True
                journaling_manager.recordInfo("Port forwarding verified")
            else:
                raise ConnectionError("Port forwarding not established")
            
            # Use localhost with the forwarded port
            self.endpoint = f"127.0.0.1:{self.port}"
            self.connected = True
            
            journaling_manager.recordInfo(f"ADB connection established at {self.endpoint}")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Error connecting via ADB: {e}")
            self.connected = False
            _tcp_gateway_active = False
            raise ConnectionError(f"ADB connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Remove port forwarding and disconnect"""
        if self.connected:
            try:
                self._run_adb_command(["forward", "--remove", f"tcp:{self.port}"])
                journaling_manager.recordInfo("ADB port forwarding removed")
                self.connected = False
            except Exception as e:
                journaling_manager.recordError(f"Error removing ADB port forwarding: {e}")
    
    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command via socket to the forwarded port"""
        global _tcp_gateway_active
        
        if not self.connected:
            if _tcp_gateway_active:
                # Try to re-establish the connection if gateway is marked active
                journaling_manager.recordInfo("TCP gateway marked active but connection lost, reconnecting...")
                await self.connect()
            else:
                raise ConnectionError("Not connected to device")
        
        try:
            ip, port = self.endpoint.split(":")
            port = int(port)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                
                try:
                    s.connect((ip, port))
                except Exception as e:
                    # Connection failed, TCP gateway might be down
                    journaling_manager.recordError(f"Socket connection failed: {e}")
                    _tcp_gateway_active = False
                    self.connected = False
                    raise ConnectionError("Failed to connect to forwarded port")
                
                # Mark gateway as active if connection succeeds
                _tcp_gateway_active = True
                
                # Send command
                json_data = json.dumps(command) + "\n"
                s.sendall(json_data.encode())
                
                # Read response with larger buffer
                buffer = bytearray()
                while True:
                    try:
                        chunk = s.recv(4096)
                        if not chunk:
                            break
                        buffer.extend(chunk)
                        if b"\n" in chunk:
                                break
                    except socket.timeout:
                                break
                
                if buffer:
                    try:
                        response = json.loads(buffer.decode().strip())
                        return response
                    except json.JSONDecodeError as e:
                        journaling_manager.recordError(f"Failed to parse JSON: {e}")
                        return {
                            "request_id": command.get("request_id", "error"),
                            "work_id": command.get("work_id", "local"),
                            "data": buffer.decode().strip(),
                            "error": {"code": -1, "message": f"Failed to parse response: {e}"},
                            "object": command.get("object", "None"),
                            "created": int(time.time())
                        }
                else:
                    journaling_manager.recordError("Empty response received")
                    _tcp_gateway_active = False  # Mark gateway as inactive on empty response
                    return {
                    "request_id": command.get("request_id", "error"),
                    "work_id": command.get("work_id", "local"),
                    "data": None,
                    "error": {"code": -2, "message": "Empty response"},
                        "object": command.get("object", "None"),
                        "created": int(time.time())
                    }
            
        except Exception as e:
            journaling_manager.recordError(f"Error transmitting command: {e}")
            _tcp_gateway_active = False  # Mark gateway as inactive on error
            raise CommandError(f"Command transmission failed: {e}")

# Transport factory
def get_transport(transport_type: str) -> BaseTransport:
    """Get the appropriate transport instance based on type"""
    if transport_type == "serial":
        return SerialTransport()
    elif transport_type == "wifi" or transport_type == "tcp":  # Support both for backward compatibility
        return WiFiTransport()  # Will be renamed in a later step
    elif transport_type == "adb":
        return ADBTransport()
    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")

def run_adb_command(command_list):
    """Run an ADB command with fallback to absolute path from config.
    
    This is a standalone utility function that doesn't require a transport instance.
    Once direct ADB command fails, all subsequent calls will use the config path.
    
    Args:
        command_list: List of ADB command arguments
        
    Returns:
        Command output as string if successful
        
    Raises:
        ConnectionError: If command execution fails
    """
    global _direct_adb_failed, _adb_executable_path, _tcp_gateway_active
    
    # If running a command that affects the TCP gateway status
    is_gateway_command = (command_list and 
                         command_list[0] in ["start-server", "forward", "kill-server"])
    
    # If we already know direct ADB failed, use the cached path immediately
    if _direct_adb_failed and _adb_executable_path:
        try:
            journaling_manager.recordInfo(f"Using cached ADB path: {_adb_executable_path} {' '.join(command_list)}")
            result = subprocess.run(
                [_adb_executable_path] + command_list,
                capture_output=True,
                text=True,
                env=os.environ
            )
            if result.returncode == 0:
                # Update TCP gateway status for gateway commands
                if is_gateway_command and command_list[0] == "forward":
                    _tcp_gateway_active = True
                elif is_gateway_command and command_list[0] == "kill-server":
                    _tcp_gateway_active = False
                return result.stdout
            else:
                journaling_manager.recordError(f"ADB command failed with absolute path: {result.stderr}")
                # Mark TCP gateway as inactive on failure
                if is_gateway_command:
                    _tcp_gateway_active = False
                raise ConnectionError(f"ADB command failed: {result.stderr}")
        except Exception as e:
            journaling_manager.recordError(f"Error running ADB with cached path: {e}")
            # Mark TCP gateway as inactive on error
            if is_gateway_command:
                _tcp_gateway_active = False
            raise ConnectionError(f"ADB execution error: {e}")
    
    # If direct ADB hasn't failed yet, try it first
    if not _direct_adb_failed:
        try:
            # Try running adb directly
            journaling_manager.recordInfo(f"Running ADB command: adb {' '.join(command_list)}")
            result = subprocess.run(
                ["adb"] + command_list,
                capture_output=True,
                text=True,
                env=os.environ
            )
            if result.returncode == 0:
                # Update TCP gateway status for gateway commands
                if is_gateway_command and command_list[0] == "forward":
                    _tcp_gateway_active = True
                elif is_gateway_command and command_list[0] == "kill-server":
                    _tcp_gateway_active = False
                return result.stdout
            else:
                journaling_manager.recordError(f"ADB command failed: {result.stderr}")
                # Mark TCP gateway as inactive on failure
                if is_gateway_command:
                    _tcp_gateway_active = False
                _direct_adb_failed = True  # Mark direct ADB as failed
        except Exception as e:
            journaling_manager.recordInfo(f"Error running ADB: {e}. Trying absolute path from config...")
            # Mark TCP gateway as inactive on error
            if is_gateway_command:
                _tcp_gateway_active = False
            _direct_adb_failed = True  # Mark direct ADB as failed

    # Fallback to absolute path from config
    try:
        adb_path = CONFIG.adb_path
        if not adb_path.endswith(".exe") and platform.system() == "Windows":
            adb_path += ".exe"
        
        # Cache the path for future use
        _adb_executable_path = adb_path
            
        journaling_manager.recordInfo(f"Running ADB with absolute path: {adb_path} {' '.join(command_list)}")
        result = subprocess.run(
            [adb_path] + command_list,
            capture_output=True,
            text=True,
            env=os.environ
        )
        if result.returncode == 0:
            # Update TCP gateway status for gateway commands
            if is_gateway_command and command_list[0] == "forward":
                _tcp_gateway_active = True
            elif is_gateway_command and command_list[0] == "kill-server":
                _tcp_gateway_active = False
            return result.stdout
        else:
            journaling_manager.recordError(f"ADB command failed with absolute path: {result.stderr}")
            # Mark TCP gateway as inactive on failure
            if is_gateway_command:
                _tcp_gateway_active = False
            raise ConnectionError(f"ADB command failed: {result.stderr}")
    except Exception as e:
        journaling_manager.recordError(f"Error running ADB with absolute path: {e}")
        # Mark TCP gateway as inactive on error
        if is_gateway_command:
            _tcp_gateway_active = False
        raise ConnectionError(f"ADB execution error: {e}")
"""
CorpusCallosum - Neural communication pathways for PenphinOS
"""

from .neural_commands import (
    BaseCommand, CommandType, CommandFactory, CommandSerializer,
    TTSCommand, ASRCommand, VADCommand, LLMCommand, VLMCommand,
    KWSCommand, SystemCommand, AudioCommand, CameraCommand,
    YOLOCommand, WhisperCommand, MeloTTSCommand
)

from .synaptic_pathways import (
    SynapticPathways,
    SerialConnectionError,
    CommandTransmissionError
)

__all__ = [
    'BaseCommand',
    'CommandType',
    'CommandFactory',
    'CommandSerializer',
    'TTSCommand',
    'ASRCommand',
    'VADCommand',
    'LLMCommand',
    'VLMCommand',
    'KWSCommand',
    'SystemCommand',
    'AudioCommand',
    'CameraCommand',
    'YOLOCommand',
    'WhisperCommand',
    'MeloTTSCommand',
    'SynapticPathways',
    'SerialConnectionError',
    'CommandTransmissionError'
] 
"""
Neurological Function:
    Broca's Area (Inferior Frontal Gyrus) handles:
    - Speech production
    - Language generation
    - Grammar processing
    - Sentence structure
    - Word formation
    - Articulatory planning
    - Language fluency

Project Function:
    Handles language production:
    - Text generation
    - Grammar checking
    - Sentence construction
    - Word selection
    - Language fluency
"""

import logging
from typing import Dict, Any, Optional, List
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from ...CorpusCallosum.neural_commands import CommandType, TTSCommand
from .llm import LLM

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

def get_synaptic_pathways():
    """Get SynapticPathways while avoiding circular imports"""
    from ...CorpusCallosum.synaptic_pathways import SynapticPathways
    return SynapticPathways

class BrocaArea:
    """Handles language production and speech generation"""
    
    def __init__(self):
        """Initialize Broca's area"""
        journaling_manager.recordScope("BrocaArea.__init__")
        self._initialized = False
        self._processing = False
        self._llm = LLM()
        self.current_state = {
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize Broca's area"""
        journaling_manager.recordScope("BrocaArea.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Broca's area already initialized")
            return
            
        try:
            # Initialize LLM
            await self._llm.initialize()
            
            # Initialize components
            self._initialized = True
            journaling_manager.recordInfo("Broca's area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize Broca's area: {e}")
            raise
            
    async def generate_speech(self, text: str, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """Generate speech from text"""
        journaling_manager.recordScope("BrocaArea.generate_speech", text=text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Broca's area not initialized")
                raise RuntimeError("Broca's area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing speech")
                raise RuntimeError("Already processing speech")
                
            self._processing = True
            self.current_state["status"] = "processing"
            
            # Use LLM to process text first
            processed_text = await self._llm.process_input(text)
            
            # Create TTS command with processed text
            command = TTSCommand(
                command_type=CommandType.TTS,
                text=processed_text.get("response", text),
                voice_id=voice_id,
                speed=speed,
                pitch=pitch
            )
            
            # Send command through synaptic pathways
            SynapticPathways = get_synaptic_pathways()
            response = await SynapticPathways.send_command(command.to_dict())
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Speech generated successfully")
            
            return response
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error generating speech: {e}")
            raise
            
    async def check_grammar(self, text: str) -> Dict[str, Any]:
        """Check grammar and sentence structure"""
        journaling_manager.recordScope("BrocaArea.check_grammar", text=text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Broca's area not initialized")
                raise RuntimeError("Broca's area not initialized")
                
            # Use LLM to check grammar
            prompt = f"Check the grammar and sentence structure of the following text. Return a JSON with 'is_correct' (boolean), 'corrections' (list of corrections), and 'explanation' (string): {text}"
            response = await self._llm.process_input(prompt)
            
            journaling_manager.recordInfo("Grammar check completed")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error checking grammar: {e}")
            raise
            
    async def construct_sentence(self, words: List[str]) -> Dict[str, Any]:
        """Construct a grammatically correct sentence from words"""
        journaling_manager.recordScope("BrocaArea.construct_sentence", words=words)
        try:
            if not self._initialized:
                journaling_manager.recordError("Broca's area not initialized")
                raise RuntimeError("Broca's area not initialized")
                
            # Use LLM to construct sentence
            prompt = f"Construct a grammatically correct sentence using these words: {', '.join(words)}"
            response = await self._llm.process_input(prompt)
            
            journaling_manager.recordInfo("Sentence constructed successfully")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error constructing sentence: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up Broca's area"""
        journaling_manager.recordScope("BrocaArea.cleanup")
        try:
            await self._llm.cleanup()
            self._initialized = False
            self.current_state["model"] = None
            journaling_manager.recordInfo("Broca's area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up Broca's area: {e}")
            raise 
"""
Neurological Function:
    Language Model System:
    - Natural language processing
    - Text generation
    - Context understanding
    - Semantic analysis
    - Response generation
    - Language comprehension
    - Cognitive processing

Project Function:
    Handles language processing:
    - Text input processing
    - Response generation
    - Context management
    - Model interaction
"""

import logging
from typing import Dict, Any, Optional
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from ...CorpusCallosum.neural_commands import (
    LLMCommand, TTSCommand, ASRCommand, VADCommand, WhisperCommand,
    CommandType, BaseCommand, SystemCommand
)
import time
import traceback

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

def get_synaptic_pathways():
    """Get the SynapticPathways class, avoiding circular imports"""
    from ...CorpusCallosum.synaptic_pathways import SynapticPathways
    return SynapticPathways

class LLM:
    """Handles language model interactions"""
    
    def __init__(self):
        """Initialize the language model"""
        journaling_manager.recordScope("LLM.__init__")
        self._initialized = False
        self._processing = False
        self.current_state = {
            "model": None,
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize the language model"""
        journaling_manager.recordScope("LLM.initialize")
        if self._initialized:
            journaling_manager.recordDebug("LLM already initialized")
            return
            
        try:
            # Initialize model with configuration
            self.current_state["model"] = {
                "name": CONFIG.llm_model,
                "temperature": CONFIG.llm_temperature,
                "max_tokens": CONFIG.llm_max_tokens
            }
            journaling_manager.recordDebug(f"LLM model configured: {self.current_state['model']}")
            
            # Initialize synaptic pathways for hardware communication
            SynapticPathways = get_synaptic_pathways()
            await SynapticPathways.initialize()
            
            # Register as an integration area for command handling
            SynapticPathways.register_integration_area("llm", self)
            journaling_manager.recordInfo("LLM registered as integration area")
            
            self._initialized = True
            journaling_manager.recordInfo("Language model initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize language model: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the language model"""
        journaling_manager.recordScope("LLM.cleanup")
        try:
            self._initialized = False
            self.current_state["model"] = None
            journaling_manager.recordInfo("Language model cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up language model: {e}")
            raise
            
    async def process_input(self, input_text: str) -> Dict[str, Any]:
        """Process text input through the language model"""
        journaling_manager.recordScope("LLM.process_input", input_text=input_text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Language model not initialized")
                raise RuntimeError("Language model not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing input")
                raise RuntimeError("Already processing input")
                
            self._processing = True
            self.current_state["status"] = "processing"
            
            # Process input through model
            response = await self._generate_response(input_text)
            journaling_manager.recordDebug(f"Generated response: {response}")
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Input processed successfully")
            
            return response
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error processing input: {e}")
            raise
            
    async def _generate_response(self, prompt, system_prompt=None, max_tokens=None, temperature=None) -> Dict[str, Any]:
        """Generate a response from the LLM using the current configuration"""
        try:
            # Use provided parameters or fall back to current state
            max_tokens = max_tokens if max_tokens is not None else self.current_state["model"]["max_tokens"]
            temperature = temperature if temperature is not None else self.current_state["model"]["temperature"]
            
            # Create unique request ID for this generation
            request_id = f"generate_{int(time.time())}"
            
            # Structure the command in M5Stack API format
            command = {
                "type": "LLM",
                "command": "generate",
                "data": {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "request_id": request_id
                }
            }
            
            journaling_manager.recordInfo(f"Sending LLM inference command: {command}")
            
            # Send command through synaptic pathways
            SynapticPathways = get_synaptic_pathways()
            response = await SynapticPathways.send_command(command)
            
            journaling_manager.recordDebug(f"LLM response: {response}")
            
            # Check for errors
            if not response or isinstance(response, dict) and response.get("error"):
                error_code = response.get("error", {}).get("code", "unknown")
                error_message = response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"LLM generation error: {error_code} - {error_message}")
                return {
                    "text": f"Error: {error_message}",
                    "error": True,
                    "request_id": request_id,
                    "finished": True
                }
            
            # Parse the response based on M5Stack API format
            if isinstance(response, dict):
                # Check if it's an error response
                if "error" in response:
                    error_code = response.get("error", {}).get("code", "unknown")
                    error_message = response.get("error", {}).get("message", "Unknown error")
                    journaling_manager.recordError(f"LLM generation error: {error_code} - {error_message}")
                    return {
                        "text": f"Error: {error_message}",
                        "error": True,
                        "request_id": request_id,
                        "finished": True
                    }
                
                # Check if the response has data field
                if "data" in response:
                    data = response["data"]
                    # Data could be a string or a dictionary
                    if isinstance(data, str):
                        return {
                            "text": data,
                            "request_id": request_id,
                            "finished": True
                        }
                    elif isinstance(data, dict):
                        return {
                            "text": data.get("generated_text", ""),
                            "request_id": request_id,
                            "finished": data.get("finished", True)
                        }
            
            # Fallback for other response formats
            journaling_manager.recordWarning(f"Unknown response format: {response}")
            return {
                "text": str(response) if response else "",
                "request_id": request_id,
                "finished": True
            }
            
        except Exception as e:
            journaling_manager.recordError(f"Error in LLM response generation: {e}")
            journaling_manager.recordError(traceback.format_exc())
            return {
                "text": f"Error: {str(e)}",
                "error": True,
                "finished": True
            }
            
    async def send_tts(self, text: str, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """Send a TTS command"""
        try:
            command = TTSCommand(
                command_type=CommandType.TTS,
                text=text,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch
            )
            SynapticPathways = get_synaptic_pathways()
            return await SynapticPathways.send_command(command.to_dict())
        except Exception as e:
            journaling_manager.recordError(f"Error sending TTS command: {e}")
            raise
            
    async def send_asr(self, audio_data: bytes, language: str = "en", model_type: str = "base") -> Dict[str, Any]:
        """Send an ASR command"""
        try:
            command = ASRCommand(
                command_type=CommandType.ASR,
                input_audio=audio_data,
                language=language,
                model_type=model_type
            )
            SynapticPathways = get_synaptic_pathways()
            return await SynapticPathways.send_command(command.to_dict())
        except Exception as e:
            journaling_manager.recordError(f"Error sending ASR command: {e}")
            raise
            
    async def send_vad(self, audio_chunk: bytes, threshold: float = 0.5, frame_duration: int = 30) -> Dict[str, Any]:
        """Send a VAD command"""
        try:
            command = VADCommand(
                command_type=CommandType.VAD,
                audio_chunk=audio_chunk,
                threshold=threshold,
                frame_duration=frame_duration
            )
            SynapticPathways = get_synaptic_pathways()
            return await SynapticPathways.send_command(command.to_dict())
        except Exception as e:
            journaling_manager.recordError(f"Error sending VAD command: {e}")
            raise
            
    async def send_whisper(self, audio_data: bytes, language: str = "en", model_type: str = "base") -> Dict[str, Any]:
        """Send a Whisper command"""
        try:
            command = WhisperCommand(
                command_type=CommandType.WHISPER,
                audio_data=audio_data,
                language=language,
                model_type=model_type
            )
            SynapticPathways = get_synaptic_pathways()
            return await SynapticPathways.send_command(command.to_dict())
        except Exception as e:
            journaling_manager.recordError(f"Error sending Whisper command: {e}")
            raise
            
    async def process_assistant_interaction(self, audio_data: bytes = None, text_input: str = None) -> Dict[str, Any]:
        """High-level method to process a complete assistant interaction"""
        try:
            # Process audio input if provided
            if audio_data and not text_input:
                asr_response = await self.send_asr(audio_data)
                text_input = asr_response.get("text", "")
                if not text_input:
                    return {"status": "error", "message": "Failed to transcribe audio"}

            # Process text through LLM
            llm_response = await self.process_input(text_input)
            assistant_response = llm_response.get("text", "")

            # Generate audio response
            audio_path = None
            if assistant_response:
                tts_response = await self.send_tts(assistant_response)
                audio_path = tts_response.get("audio_path")

            return {
                "status": "ok",
                "input_text": text_input,
                "assistant_response": assistant_response,
                "audio_path": audio_path
            }

        except Exception as e:
            journaling_manager.recordError(f"Assistant interaction failed: {e}")
            return {"status": "error", "message": str(e)}

    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process an LLM command"""
        try:
            command_type = command.get("command_type")
            if command_type != CommandType.LLM.value:
                raise ValueError(f"Invalid command type for LLM: {command_type}")
                
            # Extract command parameters
            action = command.get("action")
            parameters = command.get("parameters", {})
            
            if action == "generate" or action == "inference":
                # Handle text generation
                prompt = None
                
                # Extract prompt from different possible locations
                if "prompt" in parameters:
                    prompt = parameters["prompt"]
                elif "data" in command and isinstance(command["data"], dict) and "prompt" in command["data"]:
                    prompt = command["data"]["prompt"]
                elif "data" in command and isinstance(command["data"], str):
                    prompt = command["data"]
                else:
                    journaling_manager.recordWarning(f"No prompt found in command: {command}")
                    prompt = ""
                
                # Get other parameters
                max_tokens = parameters.get("max_tokens", 100)
                if "data" in command and isinstance(command["data"], dict) and "max_tokens" in command["data"]:
                    max_tokens = command["data"]["max_tokens"]
                    
                temperature = parameters.get("temperature", 0.7)
                if "data" in command and isinstance(command["data"], dict) and "temperature" in command["data"]:
                    temperature = command["data"]["temperature"]
                
                # Generate response
                response = await self._generate_response(prompt, max_tokens=max_tokens, temperature=temperature)
                
                # Format response according to M5Stack API
                return {
                    "request_id": command.get("request_id", response.get("request_id", f"resp_{int(time.time())}")),
                    "work_id": "llm",
                    "data": {
                        "text": response.get("text", "")
                    },
                    "error": {"code": 0, "message": ""} if not response.get("error") else {"code": -1, "message": response.get("text", "Error")},
                    "object": "llm.utf-8.stream",
                    "created": int(time.time())
                }
                
            elif action == "analyze":
                # Handle text analysis
                text = parameters.get("text", "")
                analysis_type = parameters.get("analysis_type", "sentiment")
                
                if analysis_type == "sentiment":
                    result = await self.analyze_sentiment(text)
                elif analysis_type == "entities":
                    result = await self.extract_entities(text)
                else:
                    raise ValueError(f"Unsupported analysis type: {analysis_type}")
                    
                # Format response according to M5Stack API
                return {
                    "request_id": command.get("request_id", f"analyze_{int(time.time())}"),
                    "work_id": "llm",
                    "data": result,
                    "error": {"code": 0, "message": ""},
                    "object": "llm.utf-8",
                    "created": int(time.time())
                }
                
            else:
                raise ValueError(f"Unsupported action: {action}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error processing LLM command: {e}")
            journaling_manager.recordError(traceback.format_exc())
            
            # Return error in M5Stack API format
            return {
                "request_id": command.get("request_id", f"error_{int(time.time())}"),
                "work_id": "llm",
                "data": None,
                "error": {"code": -1, "message": str(e)},
                "object": "llm",
                "created": int(time.time())
            } 
"""
Neurological Function:
    Wernicke's Area (Inferior Frontal Gyrus) handles:
    - Language comprehension
    - Speech recognition
    - Word meaning
    - Semantic understanding
    - Context processing
    - Language interpretation
    - Meaning extraction

Project Function:
    Handles language comprehension:
    - Text understanding
    - Speech recognition
    - Word meaning extraction
    - Context analysis
    - Semantic processing
    - Language interpretation
"""

import logging
from typing import Dict, Any, Optional, List
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType, ASRCommand, WhisperCommand
from .llm import LLM

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class WernickeArea:
    """Handles language comprehension and speech recognition"""
    
    def __init__(self):
        """Initialize Wernicke's area"""
        journaling_manager.recordScope("WernickeArea.__init__")
        self._initialized = False
        self._processing = False
        self._llm = LLM()
        self.current_state = {
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize Wernicke's area"""
        journaling_manager.recordScope("WernickeArea.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Wernicke's area already initialized")
            return
            
        try:
            # Initialize LLM
            await self._llm.initialize()
            
            # Initialize components
            self._initialized = True
            journaling_manager.recordInfo("Wernicke's area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize Wernicke's area: {e}")
            raise
            
    async def recognize_speech(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """Recognize speech from audio data"""
        journaling_manager.recordScope("WernickeArea.recognize_speech", language=language)
        try:
            if not self._initialized:
                journaling_manager.recordError("Wernicke's area not initialized")
                raise RuntimeError("Wernicke's area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing speech")
                raise RuntimeError("Already processing speech")
                
            self._processing = True
            self.current_state["status"] = "processing"
            
            # Use LLM's ASR functionality
            response = await self._llm.send_asr(audio_data, language)
            
            # Process recognized text through LLM for better understanding
            if response.get("text"):
                processed_text = await self._llm.process_input(response["text"])
                response["processed_text"] = processed_text
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Speech recognized successfully")
            
            return response
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error recognizing speech: {e}")
            raise
            
    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """Transcribe audio to text"""
        journaling_manager.recordScope("WernickeArea.transcribe_audio", language=language)
        try:
            if not self._initialized:
                journaling_manager.recordError("Wernicke's area not initialized")
                raise RuntimeError("Wernicke's area not initialized")
                
            # Use LLM's Whisper functionality
            response = await self._llm.send_whisper(audio_data, language)
            
            # Process transcribed text through LLM for better understanding
            if response.get("text"):
                processed_text = await self._llm.process_input(response["text"])
                response["processed_text"] = processed_text
            
            journaling_manager.recordInfo("Audio transcribed successfully")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error transcribing audio: {e}")
            raise
            
    async def extract_meaning(self, text: str) -> Dict[str, Any]:
        """Extract meaning and context from text"""
        journaling_manager.recordScope("WernickeArea.extract_meaning", text=text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Wernicke's area not initialized")
                raise RuntimeError("Wernicke's area not initialized")
                
            # Use LLM to extract meaning
            prompt = f"Analyze the following text and extract its meaning, key concepts, and context. Return a JSON with 'main_idea' (string), 'key_concepts' (list), 'context' (string), and 'tone' (string): {text}"
            response = await self._llm.process_input(prompt)
            
            journaling_manager.recordInfo("Meaning extracted successfully")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error extracting meaning: {e}")
            raise
            
    async def analyze_context(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze text in context"""
        journaling_manager.recordScope("WernickeArea.analyze_context", text=text, context=context)
        try:
            if not self._initialized:
                journaling_manager.recordError("Wernicke's area not initialized")
                raise RuntimeError("Wernicke's area not initialized")
                
            # Use LLM to analyze context
            prompt = f"Analyze the following text in the given context. Return a JSON with 'interpretation' (string), 'relevance' (string), 'implications' (list), and 'connections' (list):\nText: {text}\nContext: {context}"
            response = await self._llm.process_input(prompt)
            
            journaling_manager.recordInfo("Context analyzed successfully")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error analyzing context: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up Wernicke's area"""
        journaling_manager.recordScope("WernickeArea.cleanup")
        try:
            await self._llm.cleanup()
            self._initialized = False
            self.current_state["model"] = None
            journaling_manager.recordInfo("Wernicke's area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up Wernicke's area: {e}")
            raise 
"""
Inferior Frontal Gyrus package containing language processing components:
- Broca's Area (language production)
- Wernicke's Area (language comprehension)
- LLM (core language model)
"""

from .llm import LLM
from .broca_area import BrocaArea
from .wernicke_area import WernickeArea

__all__ = ['LLM', 'BrocaArea', 'WernickeArea'] 
"""
Motor Integration Area - Processes and integrates motor commands
"""

import logging
from typing import Dict, Any, Optional
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.config import CONFIG

logger = logging.getLogger(__name__)

class IntegrationArea:
    """Processes and integrates motor commands"""
    
    def __init__(self):
        """Initialize the integration area"""
        self._initialized = False
        self._processing = False
        
        # Register with SynapticPathways
        SynapticPathways.register_integration_area("motor", self)
        
    async def initialize(self) -> None:
        """Initialize the integration area"""
        if self._initialized:
            return
            
        try:
            # Initialize motor processing components
            self._initialized = True
            logger.info("Motor integration area initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize motor integration area: {e}")
            raise
            
    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a motor command"""
        if not self._initialized:
            raise RuntimeError("Integration area not initialized")
            
        if self._processing:
            raise RuntimeError("Already processing a command")
            
        try:
            self._processing = True
            
            # Process command based on type
            command_type = command.get("type")
            if command_type == "MOVE":
                return await self._process_movement(command)
            elif command_type == "STOP":
                return await self._process_stop()
            else:
                raise ValueError(f"Unknown command type: {command_type}")
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            self._processing = False
            
    async def _process_movement(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process movement command"""
        try:
            # Process movement parameters
            return {"status": "ok", "message": "Movement processed"}
            
        except Exception as e:
            logger.error(f"Error processing movement: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_stop(self) -> Dict[str, Any]:
        """Process stop command"""
        try:
            # Stop all movement
            return {"status": "ok", "message": "Movement stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping movement: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            logger.info("Motor integration area cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up motor integration area: {e}")
            raise 
"""
Neurological Function:
    Motor Cortex (M1) handles:
    - Voluntary muscle movements
    - Motor planning
    - Movement execution
    - Fine motor control

Project Function:
    Handles motor control:
    - Movement commands
    - Motor state management
    - Movement coordination
    - Hardware control
"""

import logging
from typing import Dict, Any, Optional
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class Motor:
    """Handles motor control functionality"""
    
    def __init__(self):
        """Initialize the motor controller"""
        journaling_manager.recordScope("Motor.__init__")
        self._initialized = False
        self._processing = False
        self.current_state = {
            "position": {"x": 0, "y": 0},
            "velocity": {"x": 0, "y": 0},
            "acceleration": {"x": 0, "y": 0}
        }
        
    async def initialize(self) -> None:
        """Initialize the motor controller"""
        journaling_manager.recordScope("Motor.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Motor already initialized")
            return
            
        try:
            self._initialized = True
            journaling_manager.recordInfo("Motor controller initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize motor controller: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the motor controller"""
        journaling_manager.recordScope("Motor.cleanup")
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Motor not initialized, skipping cleanup")
                return
                
            self._initialized = False
            self._processing = False
            journaling_manager.recordInfo("Motor controller cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up motor controller: {e}")
            raise
            
    async def execute_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a movement command
        
        Args:
            movement_data: Dictionary containing movement parameters
            
        Returns:
            Dict[str, Any]: Movement execution result
        """
        journaling_manager.recordScope("Motor.execute_movement", movement_data=movement_data)
        try:
            if not self._initialized:
                journaling_manager.recordError("Motor controller not initialized")
                raise RuntimeError("Motor controller not initialized")
                
            if self._processing:
                journaling_manager.recordDebug("Movement already in progress")
                return {"status": "busy", "message": "Movement already in progress"}
                
            self._processing = True
            journaling_manager.recordDebug("Starting movement execution")
            
            # Process movement command
            await SynapticPathways.transmit_command({
                "command_type": "motor",
                "operation": "execute",
                "data": movement_data
            })
            
            # Update state
            self.current_state.update(movement_data)
            journaling_manager.recordDebug(f"Updated motor state: {self.current_state}")
            
            self._processing = False
            journaling_manager.recordInfo("Movement executed successfully")
            return {"status": "ok", "message": "Movement executed"}
            
        except Exception as e:
            self._processing = False
            journaling_manager.recordError(f"Error executing movement: {e}")
            return {"status": "error", "message": str(e)}
            
    async def stop_movement(self) -> None:
        """Stop all current movements"""
        journaling_manager.recordScope("Motor.stop_movement")
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Motor not initialized, skipping stop")
                return
                
            if not self._processing:
                journaling_manager.recordDebug("No movement in progress")
                return
                
            # Send stop command
            await SynapticPathways.transmit_command({
                "command_type": "motor",
                "operation": "stop"
            })
            
            # Reset state
            self.current_state = {
                "position": self.current_state["position"],
                "velocity": {"x": 0, "y": 0},
                "acceleration": {"x": 0, "y": 0}
            }
            
            self._processing = False
            journaling_manager.recordInfo("All movements stopped")
            
        except Exception as e:
            journaling_manager.recordError(f"Error stopping movement: {e}")
            raise 
#!/usr/bin/env python3
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class SystemState(Enum):
    """System states that affect behavior"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    THINKING = "thinking"
    LISTENING = "listening"
    SPEAKING = "speaking"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class BehaviorManager:
    """Manages system-wide behaviors and state transitions"""
    
    def __init__(self):
        """Initialize behavior manager"""
        self.current_state: SystemState = SystemState.INITIALIZING
        self.state_handlers: Dict[SystemState, Any] = {}
        self.is_running = False
        
    def register_state_handler(self, state: SystemState, handler: Any) -> None:
        """Register a handler for a specific state"""
        self.state_handlers[state] = handler
        
    def set_state(self, new_state: SystemState) -> None:
        """Set new system state and notify handlers"""
        if new_state != self.current_state:
            logger.info(f"State transition: {self.current_state.value} -> {new_state.value}")
            self.current_state = new_state
            
            # Notify handler if registered
            if new_state in self.state_handlers:
                handler = self.state_handlers[new_state]
                if hasattr(handler, 'on_state_change'):
                    handler.on_state_change(new_state)
                    
    def start(self) -> None:
        """Start behavior management"""
        self.is_running = True
        self.set_state(SystemState.INITIALIZING)
        
    def stop(self) -> None:
        """Stop behavior management"""
        self.is_running = False
        self.set_state(SystemState.SHUTDOWN)
        
    def get_current_state(self) -> SystemState:
        """Get current system state"""
        return self.current_state 
"""
Neurological Function:
    Dorsolateral Prefrontal Cortex (DLPFC) handles executive functions:
    - Working memory maintenance
    - Decision making and planning
    - Cognitive flexibility
    - Abstract reasoning
    - Attention control
    - Task switching

Potential Project Implementation:
    Could handle:
    - Task prioritization
    - Decision tree processing
    - Working memory management
    - Multi-task coordination
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Language Processing Coordinator:
    - Coordinates between Broca's and Wernicke's areas
    - Manages language comprehension and production
    - Handles high-level language tasks
    - Integrates language with other cognitive functions

Project Function:
    Coordinates language processing:
    - Manages LLM instance
    - Coordinates between language areas
    - Provides high-level language interface
    - Handles complex language tasks
"""

import logging
from typing import Dict, Any, Optional
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from ...FrontalLobe.InferiorFrontalGyrus.broca_area import BrocaArea
from ...FrontalLobe.InferiorFrontalGyrus.wernicke_area import WernickeArea
from ...FrontalLobe.InferiorFrontalGyrus.llm import LLM

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class LanguageProcessor:
    """Coordinates language processing between Broca's and Wernicke's areas"""
    
    def __init__(self):
        """Initialize the language processor"""
        journaling_manager.recordScope("LanguageProcessor.__init__")
        self._initialized = False
        self._processing = False
        self._llm = None
        self._broca = None
        self._wernicke = None
        self.current_state = {
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize the language processor"""
        journaling_manager.recordScope("LanguageProcessor.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Language processor already initialized")
            return
            
        try:
            # Initialize components
            self._llm = LLM()
            self._broca = BrocaArea()
            self._wernicke = WernickeArea()
            
            # Initialize all components
            await self._llm.initialize()
            await self._broca.initialize()
            await self._wernicke.initialize()
            
            self._initialized = True
            journaling_manager.recordInfo("Language processor initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize language processor: {e}")
            raise
            
    async def process_input(self, input_text: str) -> Dict[str, Any]:
        """Process text input through language system"""
        journaling_manager.recordScope("LanguageProcessor.process_input", input_text=input_text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Language processor not initialized")
                raise RuntimeError("Language processor not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing input")
                raise RuntimeError("Already processing input")
                
            self._processing = True
            self.current_state["status"] = "processing"
            
            # Process through LLM for response generation
            llm_response = await self._llm.process_input(input_text)
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Input processed successfully")
            
            return {
                "response": llm_response
            }
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error processing input: {e}")
            raise
            
    async def process_speech(self, audio_data: bytes) -> Dict[str, Any]:
        """Process speech input through language system"""
        journaling_manager.recordScope("LanguageProcessor.process_speech")
        try:
            if not self._initialized:
                journaling_manager.recordError("Language processor not initialized")
                raise RuntimeError("Language processor not initialized")
                
            # First, recognize speech through Wernicke's area
            recognition = await self._wernicke.recognize_speech(audio_data)
            
            if not recognition.get("text"):
                return {"status": "error", "message": "Failed to recognize speech"}
                
            # Then, process the recognized text
            return await self.process_input(recognition["text"])
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing speech: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the language processor"""
        journaling_manager.recordScope("LanguageProcessor.cleanup")
        try:
            if self._llm:
                await self._llm.cleanup()
            if self._broca:
                await self._broca.cleanup()
            if self._wernicke:
                await self._wernicke.cleanup()
                
            self._initialized = False
            self._llm = None
            self._broca = None
            self._wernicke = None
            journaling_manager.recordInfo("Language processor cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up language processor: {e}")
            raise 
"""
Neurological Function:
    Orbitofrontal Cortex (OFC) manages:
    - Reward evaluation
    - Expectation adjustment
    - Impulse control
    - Adaptive learning
    - Emotional response regulation
    - Sensory integration

Potential Project Implementation:
    Could handle:
    - Reward system processing
    - Behavior optimization
    - Response inhibition
    - Adaptive learning algorithms
"""

# Implementation will be added when needed 
"""
system_journeling_manager.py

A psychologically inspired logging (journaling) system that supports four levels:
ERROR, INFO, DEBUG, and SCOPE.

'SCOPE' logs every method call (with parameters) plus all lower-level messages.
"""

from enum import Enum
from typing import Union, Any

class SystemJournelingLevel(Enum):
    """
    Describes the log detail level for system journaling.
    """
    ERROR = 1  # Only show errors
    INFO = 2   # Show info + error
    DEBUG = 3  # Show debug + info + error
    SCOPE = 4  # Show scope-based method calls + debug + info + error

    @classmethod
    def from_string(cls, level_str: str) -> 'SystemJournelingLevel':
        """
        Convert a string to a SystemJournelingLevel.
        Raises ValueError if the string is not a valid level.
        """
        try:
            return cls[level_str.upper()]
        except KeyError:
            valid_levels = [level.name for level in cls]
            raise ValueError(f"Invalid log level: {level_str}. Must be one of {valid_levels}")

class SystemJournelingManager:
    """
    A psychology-inspired journaling manager that provides multi-level logging.
    """

    def __init__(self, level: Union[str, SystemJournelingLevel] = SystemJournelingLevel.ERROR):
        """
        Initialize with a chosen journaling level.
        Default is ERROR to ensure critical issues are always logged.
        
        Args:
            level: Either a SystemJournelingLevel enum value or a string representing the level
        """
        if isinstance(level, str):
            level = SystemJournelingLevel.from_string(level)
        elif not isinstance(level, SystemJournelingLevel):
            raise ValueError(f"Invalid log level: {level}. Must be a SystemJournelingLevel enum value or string.")
            
        self.currentLevel = level
        self.recordDebug(f"SystemJournelingManager initialized with level: {level.name}")

    def setLevel(self, newLevel: Union[str, SystemJournelingLevel]) -> None:
        """
        Update the journaling level at runtime.
        
        Args:
            newLevel: Either a SystemJournelingLevel enum value or a string representing the level
        """
        if isinstance(newLevel, str):
            newLevel = SystemJournelingLevel.from_string(newLevel)
        elif not isinstance(newLevel, SystemJournelingLevel):
            raise ValueError(f"Invalid log level: {newLevel}. Must be a SystemJournelingLevel enum value or string.")
            
        self.currentLevel = newLevel
        self.recordDebug(f"Logging level changed to: {newLevel.name}")

    def getLevel(self) -> SystemJournelingLevel:
        """
        Get the current journaling level.
        """
        return self.currentLevel

    def recordError(self, message: str, exc_info: bool = False) -> None:
        """
        Record an error message if current level is >= ERROR.
        
        Args:
            message: The error message to record
            exc_info: If True, include exception info in the message
        """
        if self.currentLevel.value >= SystemJournelingLevel.ERROR.value:
            if exc_info:
                import traceback
                print(f"[ERROR] ✖  {message}")
                print(traceback.format_exc())
            else:
                print(f"[ERROR] ✖  {message}")

    def recordInfo(self, message: str) -> None:
        """
        Record an informational message if current level is >= INFO.
        """
        if self.currentLevel.value >= SystemJournelingLevel.INFO.value:
            print(f"[INFO]  ℹ  {message}")

    def recordDebug(self, message: str) -> None:
        """
        Record a debug message if current level is >= DEBUG.
        """
        if self.currentLevel.value >= SystemJournelingLevel.DEBUG.value:
            print(f"[DEBUG] ⚙  {message}")

    def recordScope(self, methodName: str, *args: Any, **kwargs: Any) -> None:
        """
        Record a scope-level method call if current level is >= SCOPE.
        Displays the method name and parameters for deeper psychological insight.
        """
        if self.currentLevel.value >= SystemJournelingLevel.SCOPE.value:
            print(f"[SCOPE] ⚗  Method: {methodName}, Args: {args}, Kwargs: {kwargs}")


# Example usage (remove or edit this when integrating):
if __name__ == "__main__":
    journalingManager = SystemJournelingManager(SystemJournelingLevel.ERROR)

    journalingManager.recordError("This is an error message.")
    journalingManager.recordInfo("An informational update.")
    journalingManager.recordDebug("Some debug details.")
    journalingManager.recordScope("fakeMethod", 123, user="Alice")

    # Elevate the log level to SCOPE for full insight
    journalingManager.setLevel(SystemJournelingLevel.SCOPE)
    journalingManager.recordScope("anotherFakeMethod", "testParam", debug=True)
    journalingManager.recordDebug("Debug message at SCOPE level.")
    journalingManager.recordInfo("Info message at SCOPE level.")
    journalingManager.recordError("Error message at SCOPE level.") 
"""
Neurological Function:
    Ventromedial Prefrontal Cortex (vmPFC) processes:
    - Emotional regulation
    - Risk assessment
    - Value-based decision making
    - Social cognition
    - Personal/moral judgment
    - Reward processing

Potential Project Implementation:
    Could handle:
    - Risk evaluation algorithms
    - Value-based decision making
    - Emotional state processing
    - Social interaction decisions
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Emotional Memory in Amygdala:
    - Emotional event tagging
    - Affective memory enhancement
    - Emotional context processing
    - Memory consolidation
    - Emotional learning
    - Experience valuation
    - Emotional pattern recognition

Potential Project Implementation:
    Could handle:
    - Emotional context storage
    - Experience evaluation
    - Memory prioritization
    - Affective tagging
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Fear Processing Circuit in Amygdala:
    - Threat detection
    - Fear conditioning
    - Emotional memory formation
    - Autonomic response regulation
    - Defensive behavior
    - Anxiety processing
    - Survival response coordination

Potential Project Implementation:
    Could handle:
    - Threat assessment algorithms
    - Risk evaluation
    - Emergency response triggers
    - Safety protocol activation
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Reward Processing in Amygdala:
    - Positive emotion processing
    - Reward value assessment
    - Motivational state processing
    - Pleasure response
    - Appetitive learning
    - Social reward processing
    - Goal-directed motivation

Potential Project Implementation:
    Could handle:
    - Reward calculation
    - Motivation assessment
    - Positive reinforcement
    - Goal value assessment
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Social-Emotional Processing in Amygdala:
    - Face recognition
    - Social cue processing
    - Emotional expression analysis
    - Social behavior regulation
    - Trust assessment
    - Social memory formation
    - Group dynamics processing

Potential Project Implementation:
    Could handle:
    - Social signal processing
    - Interaction assessment
    - Trust calculations
    - Social context analysis
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Emotional Inhibition System:
    - Emotion suppression
    - Response modulation
    - Impulse control
    - Affect regulation
    - Emotional interference control
    - Reactive control
    - Emotional dampening

Potential Project Implementation:
    Could handle:
    - Response inhibition
    - Emotion modulation
    - Control mechanisms
    - Interference management
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Cognitive Reappraisal System:
    - Emotional reinterpretation
    - Perspective shifting
    - Situation revaluation
    - Emotional context updating
    - Alternative meaning generation
    - Adaptive interpretation
    - Emotional flexibility

Potential Project Implementation:
    Could handle:
    - Context revaluation
    - Perspective adjustment
    - Interpretation updates
    - Adaptive responses
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Episodic Memory System handles autobiographical and event memories:
    - Personal experience storage
    - Temporal sequence memory
    - Context binding
    - Event reconstruction
    - Autobiographical memory
    - Future event simulation

Potential Project Implementation:
    Could handle:
    - Event sequence storage
    - Context-based retrieval
    - Temporal organization
    - Experience logging
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Hippocampus manages memory formation and spatial processing:
    - Short-term to long-term memory conversion
    - Spatial navigation and mapping
    - Pattern separation and completion
    - Episodic memory formation
    - Contextual learning

Potential Project Implementation:
    Could handle:
    - Memory storage/retrieval
    - Spatial mapping
    - Context management
    - Pattern recognition
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Semantic Memory System manages factual knowledge:
    - Concept organization
    - Knowledge categorization
    - Fact storage
    - Relationship mapping
    - Abstract concept processing
    - General knowledge integration

Potential Project Implementation:
    Could handle:
    - Knowledge base management
    - Concept relationships
    - Fact organization
    - Semantic networks
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Spatial Memory System (including place cells and grid cells):
    - Cognitive map formation
    - Spatial navigation
    - Environmental mapping
    - Route planning
    - Location memory
    - Spatial relationships

Potential Project Implementation:
    Could handle:
    - Spatial mapping
    - Navigation algorithms
    - Environment modeling
    - Path planning
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Working Memory System manages temporary information:
    - Short-term storage
    - Information manipulation
    - Temporary binding
    - Active maintenance
    - Task-relevant info
    - Quick access storage

Potential Project Implementation:
    Could handle:
    - Cache management
    - Active data manipulation
    - Temporary storage
    - Task context holding
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Neural Adaptation System:
    - Synaptic scaling
    - Homeostatic plasticity
    - Network optimization
    - Response calibration
    - Efficiency improvement
    - Dynamic adjustment
    - Performance tuning

Potential Project Implementation:
    Could handle:
    - System optimization
    - Performance tuning
    - Resource allocation
    - Adaptive scaling
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Memory Consolidation System:
    - Short to long-term conversion
    - Memory stabilization
    - Pattern integration
    - Knowledge crystallization
    - Schema formation
    - Memory reorganization
    - Information integration

Potential Project Implementation:
    Could handle:
    - Memory stabilization
    - Pattern integration
    - Knowledge organization
    - Information consolidation
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Hebbian Learning System:
    - Synaptic strengthening
    - Association formation
    - Pattern reinforcement
    - Neural connection modification
    - Activity-dependent plasticity
    - Coincidence detection
    - Connection weight adjustment

Potential Project Implementation:
    Could handle:
    - Pattern learning
    - Connection strengthening
    - Association building
    - Weight adjustments
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Reinforcement Learning System:
    - Reward-based learning
    - Punishment processing
    - Behavior modification
    - Value updating
    - Action-outcome association
    - Policy learning
    - Adaptive behavior

Potential Project Implementation:
    Could handle:
    - Reward processing
    - Behavior adaptation
    - Policy updates
    - Learning rates
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Schema Formation System:
    - Knowledge organization
    - Pattern abstraction
    - Category formation
    - Framework building
    - Knowledge integration
    - Conceptual organization
    - Mental model formation

Potential Project Implementation:
    Could handle:
    - Knowledge structuring
    - Pattern organization
    - Category management
    - Model building
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Drive Generation System:
    - Basic needs processing
    - Homeostatic motivation
    - Drive state maintenance
    - Energy regulation
    - Behavioral activation
    - Internal state monitoring
    - Action initiation

Potential Project Implementation:
    Could handle:
    - Need priority calculation
    - State maintenance
    - Action triggering
    - Resource monitoring
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Incentive Processing System:
    - Goal value computation
    - Effort calculation
    - Cost-benefit analysis
    - Future reward processing
    - Motivational conflict resolution
    - Effort-reward balance
    - Achievement motivation

Potential Project Implementation:
    Could handle:
    - Value assessment
    - Effort calculation
    - Cost-benefit analysis
    - Goal prioritization
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Motivational Persistence System:
    - Goal maintenance
    - Sustained motivation
    - Obstacle overcome processing
    - Long-term drive
    - Resilience calculation
    - Effort sustainability
    - Achievement drive

Potential Project Implementation:
    Could handle:
    - Goal persistence
    - Effort maintenance
    - Obstacle assessment
    - Drive sustainability
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Reward Motivation System:
    - Reward value assessment
    - Incentive processing
    - Motivation generation
    - Goal-directed drive
    - Pleasure response
    - Reward prediction
    - Motivational learning

Potential Project Implementation:
    Could handle:
    - Reward calculation
    - Goal valuation
    - Motivation levels
    - Drive generation
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Motor Coordination System:
    - Movement planning
    - Execution coordination
    - Balance maintenance
    - Posture control
    - Movement sequencing
    - Motor learning
    - Error correction

Project Function:
    Handles motor coordination:
    - Movement planning
    - Execution coordination
    - Error handling
    - State management
"""

import logging
from typing import Dict, Any, Optional
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType, SystemCommand
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

logger = logging.getLogger(__name__)

class CoordinationArea:
    """Coordinates motor movements"""
    
    def __init__(self):
        """Initialize the coordination area"""
        journaling_manager.recordScope("CoordinationArea.__init__")
        self._initialized = False
        self._processing = False
        self.current_state = {
            "movement": None,
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize the coordination area"""
        journaling_manager.recordScope("CoordinationArea.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Coordination area already initialized")
            return
            
        try:
            self._initialized = True
            journaling_manager.recordInfo("Coordination area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize coordination area: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the coordination area"""
        journaling_manager.recordScope("CoordinationArea.cleanup")
        try:
            self._initialized = False
            journaling_manager.recordInfo("Coordination area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up coordination area: {e}")
            raise
            
    async def coordinate_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate motor movement"""
        try:
            # Process movement data
            return {"status": "ok", "message": "Movement coordinated"}
            
        except Exception as e:
            journaling_manager.recordError(f"Error coordinating movement: {e}")
            return {"status": "error", "message": str(e)}

    async def execute_movement_plan(self, movement_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a movement plan"""
        journaling_manager.recordScope("CoordinationArea.execute_movement_plan", movement_plan=movement_plan)
        try:
            if not self._initialized:
                journaling_manager.recordError("Coordination area not initialized")
                raise RuntimeError("Coordination area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing a movement")
                raise RuntimeError("Already processing a movement")
                
            self._processing = True
            self.current_state["movement"] = movement_plan
            self.current_state["status"] = "executing"
            
            # Initialize command
            await self._initialize_command(movement_plan)
            
            # Execute command steps
            result = await self._execute_command_steps(movement_plan)
            
            # Finalize command
            await self._finalize_command()
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Movement plan executed successfully")
            
            return result
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error executing movement plan: {e}")
            raise
            
    async def execute_command(self, command_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a motor command"""
        try:
            # Initialize command execution
            await self._initialize_command(command_plan)
            
            # Execute command steps
            result = await self._execute_command_steps(command_plan)
            
            # Finalize command
            await self._finalize_command()
            
            return result
        except Exception as e:
            journaling_manager.recordError(f"Error executing command: {e}")
            return {}
            
    async def stop_all_movements(self) -> None:
        """Stop all current movements"""
        journaling_manager.recordScope("CoordinationArea.stop_all_movements")
        try:
            if not self._initialized:
                journaling_manager.recordError("Coordination area not initialized")
                raise RuntimeError("Coordination area not initialized")
                
            await SynapticPathways.send_system_command(
                command_type="stop_all_movements"
            )
            self._processing = False
            self.current_state["status"] = "stopped"
            journaling_manager.recordInfo("All movements stopped")
            
        except Exception as e:
            journaling_manager.recordError(f"Error stopping movements: {e}")
            raise
            
    async def _initialize_movement(self, movement_plan: Dict[str, Any]) -> None:
        """Initialize movement execution"""
        try:
            await SynapticPathways.send_system_command(
                command_type="initialize_movement",
                data={"plan": movement_plan}
            )
            self._processing = True
        except Exception as e:
            journaling_manager.recordError(f"Error initializing movement: {e}")
            
    async def _execute_sequence(self, sequence: Dict[str, Any]) -> Dict[str, Any]:
        """Execute movement sequence"""
        try:
            response = await SynapticPathways.send_system_command(
                command_type="execute_sequence",
                data={"sequence": sequence}
            )
            return response.get("result", {})
        except Exception as e:
            journaling_manager.recordError(f"Error executing sequence: {e}")
            return {}
            
    async def _finalize_movement(self) -> None:
        """Finalize movement execution"""
        journaling_manager.recordScope("CoordinationArea._finalize_movement")
        try:
            await SynapticPathways.send_system_command(
                command_type="finalize_movement"
            )
            self._processing = False
            journaling_manager.recordDebug("Movement finalized")
            
        except Exception as e:
            journaling_manager.recordError(f"Error finalizing movement: {e}")
            raise
            
    async def _initialize_command(self, command_plan: Dict[str, Any]) -> None:
        """Initialize command execution"""
        journaling_manager.recordScope("CoordinationArea._initialize_command", command_plan=command_plan)
        try:
            await SynapticPathways.send_system_command(
                command_type="initialize_command",
                data={"plan": command_plan}
            )
            journaling_manager.recordDebug("Command initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing command: {e}")
            raise
            
    async def _execute_command_steps(self, command_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command steps"""
        journaling_manager.recordScope("CoordinationArea._execute_command_steps", command_plan=command_plan)
        try:
            response = await SynapticPathways.send_system_command(
                command_type="execute_steps",
                data={"plan": command_plan}
            )
            journaling_manager.recordDebug("Command steps executed")
            return response.get("result", {})
            
        except Exception as e:
            journaling_manager.recordError(f"Error executing command steps: {e}")
            raise
            
    async def _finalize_command(self) -> None:
        """Finalize command execution"""
        journaling_manager.recordScope("CoordinationArea._finalize_command")
        try:
            await SynapticPathways.send_system_command(
                command_type="finalize_command"
            )
            journaling_manager.recordDebug("Command finalized")
            
        except Exception as e:
            journaling_manager.recordError(f"Error finalizing command: {e}")
            raise 
"""
Neurological Function:
    Motor Integration System:
    - Command processing
    - Movement planning
    - Execution coordination
    - State management
    - Error handling
    - Feedback processing
    - Motor learning

Project Function:
    Handles motor integration:
    - Command processing
    - Movement planning
    - Execution coordination
    - State management
"""

import logging
import traceback
from typing import Dict, Any, Optional
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType, SystemCommand
from ...config import CONFIG
from .planning_area import PlanningArea
from .coordination_area import CoordinationArea
from .pin_definitions import PinDefinitions
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class IntegrationArea:
    """Processes and integrates motor commands"""
    
    def __init__(self):
        """Initialize the motor integration area"""
        journaling_manager.recordScope("MotorIntegrationArea.__init__")
        self._initialized = False
        self._processing = False
        self.current_state = {
            "command": None,
            "status": "idle",
            "error": None
        }
        
        # Register with SynapticPathways
        SynapticPathways.register_integration_area("motor", self)
        
        self.planning = PlanningArea()
        self.coordination = CoordinationArea()
        self.pins = PinDefinitions()
        
        try:
            # Initialize components
            journaling_manager.recordInfo("Motor integration area initialized")
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize motor integration area: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise
        
    async def initialize(self) -> None:
        """Initialize the motor integration area"""
        journaling_manager.recordScope("IntegrationArea.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Integration area already initialized")
            return
            
        try:
            self._initialized = True
            journaling_manager.recordInfo("Motor integration area initialized")
            
            # Initialize motor processing components
            await self.planning.initialize()
            await self.coordination.initialize()
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize motor integration area: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the integration area"""
        journaling_manager.recordScope("IntegrationArea.cleanup")
        try:
            self._initialized = False
            journaling_manager.recordInfo("Motor integration area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up motor integration area: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise
            
    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming command"""
        try:
            # Process command
            return {"status": "ok"}
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise
            
    async def process_movement(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process movement command"""
        try:
            # Process movement
            return {"status": "ok"}
        except Exception as e:
            journaling_manager.recordError(f"Error processing movement: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise
            
    async def stop_movement(self) -> Dict[str, Any]:
        """Stop current movement"""
        try:
            # Stop movement
            return {"status": "ok"}
        except Exception as e:
            journaling_manager.recordError(f"Error stopping movement: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise
            
    async def execute_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a movement command"""
        journaling_manager.recordScope("IntegrationArea.execute_movement", movement_data=movement_data)
        try:
            if not self._initialized:
                journaling_manager.recordError("Integration area not initialized")
                raise RuntimeError("Integration area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing a movement")
                raise RuntimeError("Already processing a movement")
                
            self._processing = True
            self.current_state["command"] = movement_data
            self.current_state["status"] = "executing"
            
            # Plan the movement
            movement_plan = await self.planning.plan_movement(movement_data)
            journaling_manager.recordDebug(f"Movement plan created: {movement_plan}")
            
            # Coordinate the execution
            result = await self.coordination.execute_movement_plan(movement_plan)
            journaling_manager.recordDebug(f"Movement execution result: {result}")
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Movement executed successfully")
            
            return result
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error executing movement: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise
            
    async def process_motor_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a motor command"""
        journaling_manager.recordScope("IntegrationArea.process_motor_command", command=command)
        try:
            if not self._initialized:
                journaling_manager.recordError("Integration area not initialized")
                raise RuntimeError("Integration area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing a command")
                raise RuntimeError("Already processing a command")
                
            self._processing = True
            self.current_state["command"] = command
            self.current_state["status"] = "processing"
            
            # Plan the command
            command_plan = await self.planning.plan_command(command)
            journaling_manager.recordDebug(f"Command plan created: {command_plan}")
            
            # Execute the command
            result = await self.coordination.execute_command(command_plan)
            journaling_manager.recordDebug(f"Command execution result: {result}")
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Command processed successfully")
            
            return result
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error processing motor command: {str(e)}")
            journaling_manager.recordError(f"Error processing motor command: {e}")
            raise 
"""
Hardware Pin Configuration:
    - GPIO pin definitions
    - Motor control pins
    - PWM pins
    - Servo control pins
    - Button and LED pins
"""

from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class PinDefinitions:
    """
    Centralized pin configuration for motor control and physical outputs
    """
    def __init__(self):
        """Initialize pin definitions"""
        journaling_manager.recordScope("PinDefinitions.__init__")
        
        # GPIO Pin Definitions
        self.BUTTON_PIN = 17
        self.LED_PIN = 18
        journaling_manager.recordDebug("Initialized GPIO pins")
        
        # Motor Control Pins
        self.MOTOR_LEFT_FORWARD = 23
        self.MOTOR_LEFT_BACKWARD = 24
        self.MOTOR_RIGHT_FORWARD = 25
        self.MOTOR_RIGHT_BACKWARD = 26
        journaling_manager.recordDebug("Initialized motor control pins")
        
        # PWM Pins
        self.MOTOR_LEFT_PWM = 12
        self.MOTOR_RIGHT_PWM = 13
        journaling_manager.recordDebug("Initialized PWM pins")
        
        # Servo Pins
        self.SERVO_HEAD_PAN = 19
        self.SERVO_HEAD_TILT = 20
        journaling_manager.recordDebug("Initialized servo pins")
        
        journaling_manager.recordInfo("Pin definitions initialized")
        
    def get_all_pins(self) -> dict:
        """Get all pin definitions"""
        journaling_manager.recordScope("PinDefinitions.get_all_pins")
        pins = {
            "button": self.BUTTON_PIN,
            "led": self.LED_PIN,
            "motor": {
                "left_forward": self.MOTOR_LEFT_FORWARD,
                "left_backward": self.MOTOR_LEFT_BACKWARD,
                "right_forward": self.MOTOR_RIGHT_FORWARD,
                "right_backward": self.MOTOR_RIGHT_BACKWARD
            },
            "pwm": {
                "left": self.MOTOR_LEFT_PWM,
                "right": self.MOTOR_RIGHT_PWM
            },
            "servo": {
                "head_pan": self.SERVO_HEAD_PAN,
                "head_tilt": self.SERVO_HEAD_TILT
            }
        }
        journaling_manager.recordDebug(f"Retrieved all pin definitions: {pins}")
        return pins
        
    def validate_pins(self) -> bool:
        """Validate pin configuration"""
        journaling_manager.recordScope("PinDefinitions.validate_pins")
        try:
            # Check for duplicate pins
            all_pins = [
                self.BUTTON_PIN,
                self.LED_PIN,
                self.MOTOR_LEFT_FORWARD,
                self.MOTOR_LEFT_BACKWARD,
                self.MOTOR_RIGHT_FORWARD,
                self.MOTOR_RIGHT_BACKWARD,
                self.MOTOR_LEFT_PWM,
                self.MOTOR_RIGHT_PWM,
                self.SERVO_HEAD_PAN,
                self.SERVO_HEAD_TILT
            ]
            
            if len(all_pins) != len(set(all_pins)):
                journaling_manager.recordError("Duplicate pin assignments detected")
                return False
                
            # Check pin ranges (assuming BCM numbering)
            for pin in all_pins:
                if not (0 <= pin <= 27):  # Raspberry Pi BCM pins 0-27
                    journaling_manager.recordError(f"Invalid pin number: {pin}")
                    return False
                    
            journaling_manager.recordInfo("Pin configuration validated successfully")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating pins: {e}")
            return False 
"""
Neurological Function:
    Motor Planning System:
    - Movement planning
    - Trajectory calculation
    - Path optimization
    - Obstacle avoidance
    - Goal-directed planning
    - Action sequencing
    - Error prevention

Project Function:
    Handles motor planning:
    - Movement planning
    - Path calculation
    - Command planning
    - State validation
"""

import logging
from typing import Dict, Any, Optional
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType, SystemCommand
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

logger = logging.getLogger(__name__)

class PlanningArea:
    """Plans motor movements and commands"""
    
    def __init__(self):
        """Initialize the planning area"""
        journaling_manager.recordScope("PlanningArea.__init__")
        self._initialized = False
        self._processing = False
        self.current_state = {
            "plan": None,
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize the planning area"""
        journaling_manager.recordScope("PlanningArea.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Planning area already initialized")
            return
            
        try:
            self._initialized = True
            journaling_manager.recordInfo("Planning area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize planning area: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the planning area"""
        journaling_manager.recordScope("PlanningArea.cleanup")
        try:
            self._initialized = False
            journaling_manager.recordInfo("Planning area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up planning area: {e}")
            raise
            
    async def plan_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a motor movement"""
        journaling_manager.recordScope("PlanningArea.plan_movement", movement_data=movement_data)
        try:
            if not self._initialized:
                journaling_manager.recordError("Planning area not initialized")
                raise RuntimeError("Planning area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already planning a movement")
                raise RuntimeError("Already planning a movement")
                
            self._processing = True
            self.current_state["status"] = "planning"
            
            # Validate movement data
            self._validate_movement_data(movement_data)
            
            # Calculate movement plan
            movement_plan = await self._calculate_movement_plan(movement_data)
            journaling_manager.recordDebug(f"Movement plan calculated: {movement_plan}")
            
            # Optimize the plan
            optimized_plan = await self._optimize_plan(movement_plan)
            journaling_manager.recordDebug(f"Movement plan optimized: {optimized_plan}")
            
            self._processing = False
            self.current_state["status"] = "completed"
            self.current_state["plan"] = optimized_plan
            journaling_manager.recordInfo("Movement plan created successfully")
            
            return optimized_plan
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error planning movement: {e}")
            raise
            
    async def plan_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a motor command"""
        journaling_manager.recordScope("PlanningArea.plan_command", command=command)
        try:
            if not self._initialized:
                journaling_manager.recordError("Planning area not initialized")
                raise RuntimeError("Planning area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already planning a command")
                raise RuntimeError("Already planning a command")
                
            self._processing = True
            self.current_state["status"] = "planning"
            
            # Validate command data
            self._validate_command_data(command)
            
            # Calculate command plan
            command_plan = await this._calculate_command_plan(command)
            journaling_manager.recordDebug(f"Command plan calculated: {command_plan}")
            
            # Optimize the plan
            optimized_plan = await this._optimize_plan(command_plan)
            journaling_manager.recordDebug(f"Command plan optimized: {optimized_plan}")
            
            self._processing = False
            self.current_state["status"] = "completed"
            self.current_state["plan"] = optimized_plan
            journaling_manager.recordInfo("Command plan created successfully")
            
            return optimized_plan
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error planning command: {e}")
            raise
            
    def _validate_movement_data(self, movement_data: Dict[str, Any]) -> None:
        """Validate movement data"""
        journaling_manager.recordScope("PlanningArea._validate_movement_data", movement_data=movement_data)
        try:
            required_fields = ["type", "direction", "speed"]
            for field in required_fields:
                if field not in movement_data:
                    journaling_manager.recordError(f"Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")
                    
            journaling_manager.recordDebug("Movement data validated successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating movement data: {e}")
            raise
            
    def _validate_command_data(self, command: Dict[str, Any]) -> None:
        """Validate command data"""
        journaling_manager.recordScope("PlanningArea._validate_command_data", command=command)
        try:
            required_fields = ["type", "action", "parameters"]
            for field in required_fields:
                if field not in command:
                    journaling_manager.recordError(f"Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")
                    
            journaling_manager.recordDebug("Command data validated successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating command data: {e}")
            raise
            
    async def _calculate_movement_plan(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate movement plan"""
        journaling_manager.recordScope("PlanningArea._calculate_movement_plan", movement_data=movement_data)
        try:
            # Calculate movement parameters
            movement_type = movement_data["type"]
            direction = movement_data["direction"]
            speed = movement_data["speed"]
            
            # Create movement plan
            plan = {
                "type": movement_type,
                "direction": direction,
                "speed": speed,
                "steps": []
            }
            
            journaling_manager.recordDebug(f"Movement plan calculated: {plan}")
            return plan
            
        except Exception as e:
            journaling_manager.recordError(f"Error calculating movement plan: {e}")
            raise
            
    async def _calculate_command_plan(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate command plan"""
        journaling_manager.recordScope("PlanningArea._calculate_command_plan", command=command)
        try:
            # Calculate command parameters
            command_type = command["type"]
            action = command["action"]
            parameters = command["parameters"]
            
            # Create command plan
            plan = {
                "type": command_type,
                "action": action,
                "parameters": parameters,
                "steps": []
            }
            
            journaling_manager.recordDebug(f"Command plan calculated: {plan}")
            return plan
            
        except Exception as e:
            journaling_manager.recordError(f"Error calculating command plan: {e}")
            raise
            
    async def _optimize_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a movement or command plan"""
        journaling_manager.recordScope("PlanningArea._optimize_plan", plan=plan)
        try:
            # Add optimization steps
            optimized_plan = {
                **plan,
                "optimized": True,
                "optimization_steps": []
            }
            
            journaling_manager.recordDebug(f"Plan optimized: {optimized_plan}")
            return optimized_plan
            
        except Exception as e:
            journaling_manager.recordError(f"Error optimizing plan: {e}")
            raise

    async def _optimize_path(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize movement path"""
        journaling_manager.recordScope("PlanningArea._optimize_path", movement_data=movement_data)
        try:
            response = await SynapticPathways.send_system_command(
                command_type="optimize_path",
                data=movement_data
            )
            path = response.get("path", {})
            journaling_manager.recordDebug(f"Path optimized: {path}")
            return path
            
        except Exception as e:
            journaling_manager.recordError(f"Error optimizing path: {e}")
            raise
            
    async def _prepare_sequence(self, path: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare movement sequence"""
        journaling_manager.recordScope("PlanningArea._prepare_sequence", path=path)
        try:
            response = await SynapticPathways.send_system_command(
                command_type="prepare_sequence",
                data={"path": path}
            )
            sequence = response.get("sequence", {})
            journaling_manager.recordDebug(f"Sequence prepared: {sequence}")
            return sequence
            
        except Exception as e:
            journaling_manager.recordError(f"Error preparing sequence: {e}")
            raise
            
    async def _calculate_timing(self, sequence: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate movement timing"""
        journaling_manager.recordScope("PlanningArea._calculate_timing", sequence=sequence)
        try:
            response = await SynapticPathways.send_system_command(
                command_type="calculate_timing",
                data={"sequence": sequence}
            )
            timing = response.get("timing", {})
            journaling_manager.recordDebug(f"Timing calculated: {timing}")
            return timing
            
        except Exception as e:
            journaling_manager.recordError(f"Error calculating timing: {e}")
            raise
            
    async def _parse_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Parse motor command"""
        journaling_manager.recordScope("PlanningArea._parse_command", command=command)
        try:
            response = await SynapticPathways.send_system_command(
                command_type="parse_command",
                data=command
            )
            parsed = response.get("parsed", {})
            journaling_manager.recordDebug(f"Command parsed: {parsed}")
            return parsed
            
        except Exception as e:
            journaling_manager.recordError(f"Error parsing command: {e}")
            raise
            
    async def _generate_execution_plan(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution plan"""
        journaling_manager.recordScope("PlanningArea._generate_execution_plan", parsed=parsed)
        try:
            response = await SynapticPathways.send_system_command(
                command_type="generate_plan",
                data={"parsed": parsed}
            )
            plan = response.get("plan", {})
            journaling_manager.recordDebug(f"Execution plan generated: {plan}")
            return plan
            
        except Exception as e:
            journaling_manager.recordError(f"Error generating plan: {e}")
            raise
            
    async def _validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution plan"""
        journaling_manager.recordScope("PlanningArea._validate_plan", plan=plan)
        try:
            response = await SynapticPathways.send_system_command(
                command_type="validate_plan",
                data={"plan": plan}
            )
            validated = response.get("validated", {})
            journaling_manager.recordDebug(f"Plan validated: {validated}")
            return validated
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating plan: {e}")
            raise 
"""
Neurological Terms:
    - V3 (Visual Area 3): Dynamic form processing
    - V4 (Visual Area 4): Color processing and form recognition
    - V5/MT (Middle Temporal): Motion processing
    - Extrastriate Visual Cortex
    - Brodmann Areas 19, 37

Neurological Function:
    Associative Visual Area System:
    - Visual pattern recognition
    - Object identification
    - Visual memory integration
    - Spatial awareness
    - Visual feedback
    - Error handling
    - State management

Project Function:
    Handles complex visual processing:
    - Pattern recognition
    - Object identification
    - Visual memory
    - Spatial awareness
    - Visual feedback
"""

from typing import Dict, Any, Optional, Tuple, List, NamedTuple
from enum import Enum
import logging
from ...config import CONFIG
import math
import asyncio
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
import time
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from PIL import Image
import random
import colorsys

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class Expression(Enum):
    """Standard expressions for Penphin"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    CONTEMPT = "contempt"

class Size(Enum):
    """Standard size presets for Penphin"""
    SMALL = 16
    MEDIUM = 32
    LARGE = 48
    XLARGE = 64

class MenuItem:
    """Represents a menu item"""
    def __init__(self, text: str, action: str, icon: Optional[str] = None):
        journaling_manager.recordScope("MenuItem.__init__", text=text, action=action, icon=icon)
        self.text = text
        self.action = action
        self.icon = icon
        self.selected = False
        journaling_manager.recordDebug(f"Created menu item: {text}")

# Logo colors in RGB
class LogoColors:
    """Color constants for the logo"""
    DOLPHIN = (64, 200, 255)  # Cyan/Light blue
    DOLPHIN_HIGHLIGHT = (255, 255, 255)  # White
    PENGUIN = (255, 223, 128)  # Gold/Yellow
    BACKGROUND = (48, 32, 64)  # Dark purple
    
class Point(NamedTuple):
    """2D point representation"""
    x: int
    y: int

class AssociativeVisualArea:
    """Handles complex visual processing and effects"""
    
    def __init__(self):
        """Initialize the associative visual area"""
        journaling_manager.recordScope("AssociativeVisualArea.__init__")
        try:
            self.current_expression = Expression.NEUTRAL
            self.current_x = 0
            self.current_y = 0
            self.current_size = Size.MEDIUM
            self.is_listening = False
            self.menu_items: List[MenuItem] = []
            self.selected_index = -1
            self.animation_task = None
            self.WIDTH = 64
            self.HEIGHT = 64
            self.grid = [[random.randint(0, 1) for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
            self.text_buffer = []
            self.current_col = 0
            self.current_row = 0
            self.char_map = {}
            self._setup_spectrum_char_map()
            journaling_manager.recordDebug("Initialized associative visual area")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing associative visual area: {e}")
            raise
            
    async def initialize(self) -> None:
        """Initialize the visual area"""
        journaling_manager.recordScope("AssociativeVisualArea.initialize")
        try:
            # Initialize visual components
            journaling_manager.recordInfo("Visual area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing visual area: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the visual area"""
        journaling_manager.recordScope("AssociativeVisualArea.cleanup")
        try:
            if self.animation_task:
                self.animation_task.cancel()
            journaling_manager.recordInfo("Visual area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up visual area: {e}")
            raise
            
    async def show_gear_animation(self, duration: float = 1.0, color: Optional[tuple] = None) -> None:
        """Show a gear animation"""
        journaling_manager.recordScope("AssociativeVisualArea.show_gear_animation", duration=duration, color=color)
        try:
            if self.animation_task:
                self.animation_task.cancel()
                
            self.animation_task = asyncio.create_task(
                self._animate_gear(duration, color)
            )
            journaling_manager.recordDebug(f"Started gear animation for {duration} seconds")
            
        except Exception as e:
            journaling_manager.recordError(f"Error showing gear animation: {e}")
            raise
            
    async def set_expression(self, expression: Expression) -> None:
        """Set the current expression"""
        journaling_manager.recordScope("AssociativeVisualArea.set_expression", expression=expression)
        try:
            self.current_expression = expression
            journaling_manager.recordDebug(f"Set expression to: {expression}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting expression: {e}")
            raise
            
    async def set_size(self, size: Size) -> None:
        """Set the current size"""
        journaling_manager.recordScope("AssociativeVisualArea.set_size", size=size)
        try:
            self.current_size = size
            journaling_manager.recordDebug(f"Set size to: {size}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting size: {e}")
            raise
            
    async def add_menu_item(self, text: str, action: str, icon: Optional[str] = None) -> None:
        """Add a menu item"""
        journaling_manager.recordScope("AssociativeVisualArea.add_menu_item", text=text, action=action, icon=icon)
        try:
            item = MenuItem(text, action, icon)
            self.menu_items.append(item)
            journaling_manager.recordDebug(f"Added menu item: {text}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error adding menu item: {e}")
            raise
            
    async def select_menu_item(self, index: int) -> None:
        """Select a menu item"""
        journaling_manager.recordScope("AssociativeVisualArea.select_menu_item", index=index)
        try:
            if 0 <= index < len(self.menu_items):
                self.selected_index = index
                for i, item in enumerate(self.menu_items):
                    item.selected = (i == index)
                journaling_manager.recordDebug(f"Selected menu item at index: {index}")
            else:
                journaling_manager.recordError(f"Invalid menu item index: {index}")
                raise ValueError(f"Invalid menu item index: {index}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error selecting menu item: {e}")
            raise
            
    async def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a pixel color"""
        journaling_manager.recordScope("AssociativeVisualArea.set_pixel", x=x, y=y, r=r, g=g, b=b)
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_pixel",
                "x": x,
                "y": y,
                "color": (r, g, b)
            })
            journaling_manager.recordDebug(f"Drew pixel at ({x}, {y}) with color RGB({r}, {g}, {b})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting pixel: {e}")
            raise
            
    async def update(self) -> None:
        """Update the visual display"""
        journaling_manager.recordScope("AssociativeVisualArea.update")
        try:
            # Implementation for updating display
            journaling_manager.recordDebug("Updated visual display")
            
        except Exception as e:
            journaling_manager.recordError(f"Error updating display: {e}")
            raise
            
    async def _animate_gear(self, duration: float, color: Optional[tuple] = None) -> None:
        """Animate a gear"""
        journaling_manager.recordScope("AssociativeVisualArea._animate_gear", duration=duration, color=color)
        try:
            # Implementation for gear animation
            journaling_manager.recordDebug(f"Animated gear for {duration} seconds")
            
        except Exception as e:
            journaling_manager.recordError(f"Error animating gear: {e}")
            raise

    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data received from other cortical areas"""
        if "visualization" in data:
            # Handle visualization data
            return await self.update_llm_visualization(data["content"])
        # Handle other data types...
        return {"status": "ok"}
        
    async def draw_penphin(
        self,
        expression: Expression = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        size: Optional[Size] = None,
        is_listening: bool = None,
        rotation: float = 0.0
    ) -> None:
        """
        Draw Penphin with specified parameters
        
        Args:
            expression: Emotional expression to display
            x: X coordinate (0 to screen width)
            y: Y coordinate (0 to screen height)
            size: Size preset (SMALL, MEDIUM, LARGE, XLARGE)
            is_listening: Whether to show listening state
            rotation: Rotation angle in degrees
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea.draw_penphin",
            expression=expression,
            x=x,
            y=y,
            size=size,
            is_listening=is_listening,
            rotation=rotation
        )
        try:
            # Update state if parameters provided
            if expression:
                self.current_expression = expression
                journaling_manager.recordDebug(f"Updated expression to: {expression}")
                
            if x is not None:
                self.current_x = max(0, min(CONFIG.visual_width, x))
                journaling_manager.recordDebug(f"Updated x position to: {self.current_x}")
                
            if y is not None:
                self.current_y = max(0, min(CONFIG.visual_height, y))
                journaling_manager.recordDebug(f"Updated y position to: {self.current_y}")
                
            if size:
                self.current_size = size
                journaling_manager.recordDebug(f"Updated size to: {size}")
                
            if is_listening is not None:
                self.is_listening = is_listening
                journaling_manager.recordDebug(f"Updated listening state to: {is_listening}")
                
            # Draw body
            await self._draw_penphin_body(
                self.current_x,
                self.current_y,
                self.current_size.value,
                rotation
            )
            journaling_manager.recordDebug("Drew Penphin body")
            
            # Draw expression
            await self._draw_expression(
                self.current_x,
                self.current_y,
                self.current_size.value,
                rotation
            )
            journaling_manager.recordDebug("Drew Penphin expression")
            
            # Draw ears if listening
            if self.is_listening:
                await self._draw_listening_ears(
                    self.current_x,
                    self.current_y,
                    self.current_size.value,
                    rotation
                )
                journaling_manager.recordDebug("Drew listening ears")
                
            journaling_manager.recordInfo("Successfully drew Penphin")
                
        except Exception as e:
            journaling_manager.recordError(f"Error drawing Penphin: {e}")
            raise

    async def move_to(
        self,
        target_x: int,
        target_y: int,
        duration: float = 0.5,
        easing: str = "linear"
    ) -> None:
        """
        Animate Penphin moving to a target position
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            duration: Animation duration in seconds
            easing: Easing function ("linear", "ease_in", "ease_out", "ease_in_out")
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea.move_to",
            target_x=target_x,
            target_y=target_y,
            duration=duration,
            easing=easing
        )
        try:
            start_x, start_y = self.current_x, self.current_y
            steps = int(duration * CONFIG.visual_animation_fps)
            journaling_manager.recordDebug(f"Starting movement from ({start_x}, {start_y}) to ({target_x}, {target_y})")
            
            for i in range(steps):
                t = i / steps
                if easing == "linear":
                    current_x = start_x + (target_x - start_x) * t
                    current_y = start_y + (target_y - start_y) * t
                elif easing == "ease_in":
                    t = t * t
                    current_x = start_x + (target_x - start_x) * t
                    current_y = start_y + (target_y - start_y) * t
                elif easing == "ease_out":
                    t = 1 - (1 - t) * (1 - t)
                    current_x = start_x + (target_x - start_x) * t
                    current_y = start_y + (target_y - start_y) * t
                elif easing == "ease_in_out":
                    t = 0.5 - 0.5 * math.cos(t * math.pi)
                    current_x = start_x + (target_x - start_x) * t
                    current_y = start_y + (target_y - start_y) * t
                else:
                    journaling_manager.recordError(f"Invalid easing function: {easing}")
                    raise ValueError(f"Invalid easing function: {easing}")
                    
                await self.draw_penphin(x=int(current_x), y=int(current_y))
                await asyncio.sleep(1 / CONFIG.visual_animation_fps)
                
            journaling_manager.recordDebug(f"Completed movement to ({target_x}, {target_y})")
            journaling_manager.recordInfo("Movement animation completed successfully")
                
        except Exception as e:
            journaling_manager.recordError(f"Error moving Penphin: {e}")
            raise
        
    async def _draw_penphin_body(
        self,
        x: int,
        y: int,
        size: int,
        rotation: float
    ) -> None:
        """
        Draw Penphin's body shape
        
        Args:
            x: Center X coordinate
            y: Center Y coordinate
            size: Size of the body
            rotation: Rotation angle in degrees
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_penphin_body",
            x=x,
            y=y,
            size=size,
            rotation=rotation
        )
        try:
            # Convert rotation to radians
            angle = math.radians(rotation)
            journaling_manager.recordDebug(f"Converted rotation {rotation}° to radians")
            
            # Define body points (normalized coordinates)
            body_points = [
                Point(-0.3, 0.1),   # Start at nose
                Point(-0.2, 0.0),   # Upper curve
                Point(-0.1, -0.1),  # Head top
                Point(0.0, -0.1),   # Body top
                Point(0.1, 0.0),    # Tail start
                Point(0.2, 0.2),    # Tail tip
                Point(0.1, 0.1),    # Tail bottom
                Point(0.0, 0.0),    # Body bottom
                Point(-0.2, 0.1),   # Back to nose
            ]
            
            # Draw body outline
            await self._draw_curved_shape(
                points=body_points,
                center_x=x,
                center_y=y,
                scale=size,
                color=LogoColors.DOLPHIN,
                highlight_color=LogoColors.DOLPHIN_HIGHLIGHT
            )
            journaling_manager.recordDebug("Drew body outline")
            
            # Draw fin
            fin_points = [
                Point(-0.1, 0.0),   # Fin base
                Point(0.0, -0.15),  # Fin tip
                Point(0.1, 0.0),    # Fin back
            ]
            
            await self._draw_curved_shape(
                points=fin_points,
                center_x=x,
                center_y=y,
                scale=size,
                color=LogoColors.DOLPHIN,
                highlight_color=LogoColors.DOLPHIN_HIGHLIGHT
            )
            journaling_manager.recordDebug("Drew fin")
            
            journaling_manager.recordInfo("Successfully drew Penphin body")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing Penphin body: {e}")
            raise
        
    async def _draw_expression(
        self,
        x: int,
        y: int,
        size: int,
        rotation: float
    ) -> None:
        """Draw current expression"""
        # Implementation for drawing expression
        pass
        
    async def _draw_listening_ears(
        self,
        x: int,
        y: int,
        size: int,
        rotation: float
    ) -> None:
        """Draw animated listening ears"""
        # Implementation for drawing ears
        pass
        
    async def show_splash_screen(self) -> None:
        """
        Display the PenphinMind splash screen with logo and loading animation
        """
        journaling_manager.recordScope("[Visual Cortex] show_splash_screen")
        try:
            # Create a new image for the splash screen
            image = Image.new("RGB", (64, 64), LogoColors.BACKGROUND)
            pixels = image.load()
            
            # Draw logo
            # Center coordinates
            center_x = 32
            center_y = 32
            scale = 20  # Scale for 64x64 matrix

            # Draw dolphin (left side)
            dolphin_points = [
                (-0.3, 0.1),   # Start at nose
                (-0.2, 0.0),   # Upper curve
                (-0.1, -0.1),  # Head top
                (0.0, -0.1),   # Body top
                (0.1, 0.0),    # Tail start
                (0.2, 0.2),    # Tail tip
                (0.1, 0.1),    # Tail bottom
                (0.0, 0.0),    # Body bottom
                (-0.2, 0.1),   # Back to nose
            ]

            # Convert and draw dolphin points
            for i in range(len(dolphin_points) - 1):
                x1 = int(center_x - 10 + dolphin_points[i][0] * scale)
                y1 = int(center_y + dolphin_points[i][1] * scale)
                x2 = int(center_x - 10 + dolphin_points[i + 1][0] * scale)
                y2 = int(center_y + dolphin_points[i + 1][1] * scale)
                self._draw_line_on_image(pixels, x1, y1, x2, y2, LogoColors.DOLPHIN)

            # Draw penguin (right side)
            penguin_points = [
                (0.2, 0.1),    # Start at beak
                (0.1, 0.0),    # Head top
                (0.0, 0.0),    # Body top
                (-0.1, 0.1),   # Back
                (0.0, 0.2),    # Bottom
                (0.1, 0.15),   # Front
                (0.2, 0.1),    # Back to beak
            ]

            # Convert and draw penguin points
            for i in range(len(penguin_points) - 1):
                x1 = int(center_x + 10 + penguin_points[i][0] * scale)
                y1 = int(center_y + penguin_points[i][1] * scale)
                x2 = int(center_x + 10 + penguin_points[i + 1][0] * scale)
                y2 = int(center_y + penguin_points[i + 1][1] * scale)
                self._draw_line_on_image(pixels, x1, y1, x2, y2, LogoColors.PENGUIN)

            # Display initial logo
            await self.primary_area.set_image(image)
            await asyncio.sleep(1.0)

            # Animate loading bar
            bar_width = 40  # 40 pixels wide
            bar_height = 3  # 3 pixels high
            bar_x = (64 - bar_width) // 2  # Centered
            bar_y = 50  # Near bottom

            # Loading bar animation
            for progress in range(bar_width + 1):
                # Update loading bar
                for y in range(bar_y, bar_y + bar_height):
                    for x in range(bar_x, bar_x + bar_width):
                        if x - bar_x < progress:
                            # Calculate pulse effect
                            dist_from_edge = abs(x - (bar_x + progress))
                            if dist_from_edge < 5:  # 5-pixel pulse width
                                pulse = 1.0 - (dist_from_edge / 5.0)
                                color = self._blend_colors(
                                    LogoColors.DOLPHIN,
                                    LogoColors.DOLPHIN_HIGHLIGHT,
                                    pulse
                                )
                            else:
                                color = LogoColors.DOLPHIN
                        else:
                            color = (32, 32, 48)  # Dark background
                        pixels[x, y] = color

                # Update display
                await self.primary_area.set_image(image)
                await asyncio.sleep(0.05)

            # Final pause
            await asyncio.sleep(0.5)

            journaling_manager.recordInfo("Splash screen displayed successfully")
                
        except Exception as e:
            journaling_manager.recordError(f"Error showing splash screen: {e}")
            raise
            
    def _draw_line_on_image(self, pixels, x1: int, y1: int, x2: int, y2: int, color: tuple) -> None:
        """Draw a line on the image using Bresenham's algorithm"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= x < 64 and 0 <= y < 64:  # Check bounds
                pixels[x, y] = color
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def _blend_colors(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int],
        factor: float
    ) -> Tuple[int, int, int]:
        """Blend two colors with a factor between 0 and 1"""
        return tuple(
            int(c1 + (c2 - c1) * factor)
            for c1, c2 in zip(color1, color2)
        )

    async def _draw_curved_shape(
        self,
        points: List[Point],
        center_x: int,
        center_y: int,
        scale: int,
        color: Tuple[int, int, int],
        highlight_color: Optional[Tuple[int, int, int]] = None
    ) -> None:
        """
        Draw a curved shape using points
        
        Args:
            points: List of normalized points (-1 to 1)
            center_x: Center X coordinate
            center_y: Center Y coordinate
            scale: Size scale
            color: RGB color tuple
            highlight_color: Optional highlight color
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_curved_shape",
            points=points,
            center_x=center_x,
            center_y=center_y,
            scale=scale,
            color=color,
            highlight_color=highlight_color
        )
        try:
            # Convert normalized points to screen coordinates
            screen_points = []
            for point in points:
                x = center_x + int(point.x * scale)
                y = center_y + int(point.y * scale)
                screen_points.append(Point(x, y))
            journaling_manager.recordDebug(f"Converted {len(points)} points to screen coordinates")
                
            # Draw main shape
            for i in range(len(screen_points) - 1):
                p1 = screen_points[i]
                p2 = screen_points[i + 1]
                
                # Draw line segment
                await self._draw_antialiased_line(
                    p1.x, p1.y,
                    p2.x, p2.y,
                    color
                )
                
                # Draw highlight if specified
                if highlight_color:
                    # Offset highlight slightly
                    await self._draw_antialiased_line(
                        p1.x - 1, p1.y - 1,
                        p2.x - 1, p2.y - 1,
                        highlight_color
                    )
                    
            journaling_manager.recordDebug(f"Drew curved shape with {len(screen_points)} points")
            journaling_manager.recordInfo("Successfully drew curved shape")
                    
        except Exception as e:
            journaling_manager.recordError(f"Error drawing curved shape: {e}")
            raise

    async def _draw_antialiased_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: Tuple[int, int, int]
    ) -> None:
        """
        Draw an anti-aliased line using Xiaolin Wu's algorithm
        
        Args:
            x1, y1: Start point
            x2, y2: End point
            color: RGB color tuple
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_antialiased_line",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            color=color
        )
        try:
            # Implementation of Xiaolin Wu's line algorithm
            dx = x2 - x1
            dy = y2 - y1
            
            if abs(dx) > abs(dy):
                # Horizontal-ish line
                if x2 < x1:
                    x1, x2 = x2, x1
                    y1, y2 = y2, y1
                    journaling_manager.recordDebug("Swapped endpoints for horizontal line")
                    
                gradient = dy / dx
                journaling_manager.recordDebug(f"Calculated gradient: {gradient}")
                
                # Handle first endpoint
                xend = round(x1)
                yend = y1 + gradient * (xend - x1)
                xgap = 1 - ((x1 + 0.5) - int(x1))
                
                xpxl1 = xend
                ypxl1 = int(yend)
                
                await self._plot_pixel(xpxl1, ypxl1, color, xgap * (1 - (yend - int(yend))))
                await self._plot_pixel(xpxl1, ypxl1 + 1, color, xgap * (yend - int(yend)))
                
                intery = yend + gradient
                
                # Handle second endpoint
                xend = round(x2)
                yend = y2 + gradient * (xend - x2)
                xgap = (x2 + 0.5) - int(x2)
                
                xpxl2 = xend
                ypxl2 = int(yend)
                
                await self._plot_pixel(xpxl2, ypxl2, color, xgap * (1 - (yend - int(yend))))
                await self._plot_pixel(xpxl2, ypxl2 + 1, color, xgap * (yend - int(yend)))
                
                # Main loop
                for x in range(xpxl1 + 1, xpxl2):
                    await self._plot_pixel(x, int(intery), color, 1 - (intery - int(intery)))
                    await self._plot_pixel(x, int(intery) + 1, color, intery - int(intery))
                    intery += gradient
                    
            else:
                # Vertical-ish line
                if y2 < y1:
                    x1, x2 = x2, x1
                    y1, y2 = y2, y1
                    journaling_manager.recordDebug("Swapped endpoints for vertical line")
                    
                gradient = dx / dy
                journaling_manager.recordDebug(f"Calculated gradient: {gradient}")
                
                # Similar implementation for vertical lines...
                # (Implementation follows same pattern as horizontal case)
                pass
                
            journaling_manager.recordDebug(f"Drew anti-aliased line from ({x1}, {y1}) to ({x2}, {y2})")
            journaling_manager.recordInfo("Successfully drew anti-aliased line")
                
        except Exception as e:
            journaling_manager.recordError(f"Error drawing anti-aliased line: {e}")
            raise

    async def _plot_pixel(
        self,
        x: int,
        y: int,
        color: Tuple[int, int, int],
        brightness: float
    ) -> None:
        """
        Plot a pixel with given brightness
        
        Args:
            x, y: Pixel coordinates
            color: RGB color tuple
            brightness: Brightness factor (0-1)
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea._plot_pixel",
            x=x,
            y=y,
            color=color,
            brightness=brightness
        )
        try:
            if 0 <= x < CONFIG.visual_width and 0 <= y < CONFIG.visual_height:
                r = int(color[0] * brightness)
                g = int(color[1] * brightness)
                b = int(color[2] * brightness)
                await self._draw_pixel(x, y, r, g, b)
                journaling_manager.recordDebug(f"Plotted pixel at ({x}, {y}) with brightness {brightness}")
            else:
                journaling_manager.recordError(f"Pixel coordinates out of bounds: ({x}, {y})")
                raise ValueError(f"Pixel coordinates out of bounds: ({x}, {y})")
                
        except Exception as e:
            journaling_manager.recordError(f"Error plotting pixel: {e}")
            raise
        
    async def _animate_loading_bar(self) -> None:
        """
        Animate loading bar during splash screen with neural synapse-inspired effect
        """
        journaling_manager.recordScope("AssociativeVisualArea._animate_loading_bar")
        try:
            # Loading bar dimensions
            bar_width = int(CONFIG.visual_width * 0.8)  # 80% of screen width
            bar_height = 3  # 3 pixels high
            bar_x = (CONFIG.visual_width - bar_width) // 2  # Centered
            bar_y = int(CONFIG.visual_height * 0.8)  # Near bottom
            
            journaling_manager.recordDebug(f"Loading bar dimensions: {bar_width}x{bar_height} at ({bar_x}, {bar_y})")
            
            # Colors
            empty_color = (32, 32, 48)  # Dark background
            fill_color = LogoColors.DOLPHIN  # Match dolphin color
            pulse_color = LogoColors.DOLPHIN_HIGHLIGHT  # White pulse
            
            # Draw empty bar background
            for x in range(bar_width):
                for y in range(bar_height):
                    await self._draw_pixel(
                        bar_x + x,
                        bar_y + y,
                        *empty_color
                    )
            journaling_manager.recordDebug("Drew empty bar background")
            
            # Animate fill with neural pulse effect
            steps = 50  # Total animation steps
            pulse_width = 10  # Width of the bright pulse
            
            journaling_manager.recordDebug(f"Starting animation with {steps} steps and pulse width {pulse_width}")
            
            for step in range(steps):
                # Calculate fill position
                fill_percent = step / steps
                fill_x = int(bar_width * fill_percent)
                
                # Draw filled portion
                for x in range(fill_x):
                    for y in range(bar_height):
                        # Calculate distance from pulse center
                        dist_from_pulse = abs(x - fill_x)
                        
                        if dist_from_pulse < pulse_width:
                            # Create pulse effect
                            pulse_factor = 1 - (dist_from_pulse / pulse_width)
                            color = self._blend_colors(
                                fill_color,
                                pulse_color,
                                pulse_factor
                            )
                        else:
                            color = fill_color
                            
                        await self._draw_pixel(
                            bar_x + x,
                            bar_y + y,
                            *color
                        )
                
                # Add neural synapse dots above and below
                if step % 5 == 0:  # Every 5th step
                    synapse_y_offsets = [-2, 4]  # Dots above and below
                    for y_offset in synapse_y_offsets:
                        if 0 <= bar_y + y_offset < CONFIG.visual_height:
                            await self._draw_pixel(
                                bar_x + fill_x,
                                bar_y + y_offset,
                                *pulse_color
                            )
                
                # Pause for animation
                await asyncio.sleep(0.05)
                
            journaling_manager.recordDebug("Completed main animation loop")
            
            # Final pulse across the whole bar
            for pulse_step in range(bar_width):
                for x in range(bar_width):
                    dist_from_pulse = abs(x - pulse_step)
                    if dist_from_pulse < pulse_width:
                        pulse_factor = 1 - (dist_from_pulse / pulse_width)
                        color = self._blend_colors(
                            fill_color,
                            pulse_color,
                            pulse_factor
                        )
                        
                        for y in range(bar_height):
                            await self._draw_pixel(
                                bar_x + x,
                                bar_y + y,
                                *color
                            )
                
                await asyncio.sleep(0.01)
                
            journaling_manager.recordDebug("Completed final pulse animation")
            journaling_manager.recordInfo("Loading bar animation completed successfully")
                
        except Exception as e:
            journaling_manager.recordError(f"Error animating loading bar: {e}")
            raise
        
    async def _fade_transition(self) -> None:
        """Fade transition effect"""
        journaling_manager.recordScope("AssociativeVisualArea._fade_transition")
        try:
            # Fade out duration
            fade_duration = 0.5  # seconds
            steps = 20  # Number of fade steps
            step_duration = fade_duration / steps
            
            journaling_manager.recordDebug(f"Starting fade transition with {steps} steps over {fade_duration} seconds")
            
            # Fade out current screen
            for step in range(steps):
                # Calculate fade factor (1 to 0)
                fade_factor = 1 - (step / steps)
                
                # Apply fade to all pixels
                for x in range(CONFIG.visual_width):
                    for y in range(CONFIG.visual_height):
                        # Get current pixel color
                        current_color = await self._get_pixel_color(x, y)
                        
                        # Apply fade
                        faded_color = tuple(
                            int(c * fade_factor)
                            for c in current_color
                        )
                        
                        await self._draw_pixel(x, y, *faded_color)
                
                # Update display
                await self.update()
                await asyncio.sleep(step_duration)
                
            journaling_manager.recordDebug("Completed fade out")
            
            # Clear screen completely
            await self._clear_screen()
            journaling_manager.recordDebug("Cleared screen")
            
            # Fade in new screen
            for step in range(steps):
                # Calculate fade factor (0 to 1)
                fade_factor = step / steps
                
                # Apply fade to all pixels
                for x in range(CONFIG.visual_width):
                    for y in range(CONFIG.visual_height):
                        # Get target pixel color
                        target_color = await self._get_target_pixel_color(x, y)
                        
                        # Apply fade
                        faded_color = tuple(
                            int(c * fade_factor)
                            for c in target_color
                        )
                        
                        await self._draw_pixel(x, y, *faded_color)
                
                # Update display
                await self.update()
                await asyncio.sleep(step_duration)
                
            journaling_manager.recordDebug("Completed fade in")
            journaling_manager.recordInfo("Fade transition completed successfully")
                
        except Exception as e:
            journaling_manager.recordError(f"Error during fade transition: {e}")
            raise
            
    async def _get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get current color of a pixel"""
        try:
            # Implementation would get current pixel color
            return (0, 0, 0)  # Placeholder
        except Exception as e:
            journaling_manager.recordError(f"Error getting pixel color: {e}")
            raise
            
    async def _get_target_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get target color for a pixel"""
        try:
            # Implementation would get target pixel color
            return (0, 0, 0)  # Placeholder
        except Exception as e:
            journaling_manager.recordError(f"Error getting target pixel color: {e}")
            raise
        
    async def play_penguin_animation(self) -> None:
        """Play the penguin character animation"""
        journaling_manager.recordScope("AssociativeVisualArea.play_penguin_animation")
        try:
            # Implementation for penguin animation
            journaling_manager.recordDebug("Starting penguin animation")
            
            # Draw penguin body
            await self._draw_penphin_body(
                self.current_x,
                self.current_y,
                self.current_size.value,
                0.0  # No rotation
            )
            
            # Draw penguin expression
            await self._draw_expression(
                self.current_x,
                self.current_y,
                self.current_size.value,
                0.0
            )
            
            journaling_manager.recordDebug("Completed penguin animation")
            journaling_manager.recordInfo("Penguin animation played successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error playing penguin animation: {e}")
            raise
            
    async def play_dolphin_animation(self) -> None:
        """Play the dolphin character animation"""
        journaling_manager.recordScope("AssociativeVisualArea.play_dolphin_animation")
        try:
            # Implementation for dolphin animation
            journaling_manager.recordDebug("Starting dolphin animation")
            
            # Draw dolphin body
            await self._draw_penphin_body(
                self.current_x,
                self.current_y,
                self.current_size.value,
                0.0  # No rotation
            )
            
            # Draw dolphin expression
            await self._draw_expression(
                self.current_x,
                self.current_y,
                self.current_size.value,
                0.0
            )
            
            journaling_manager.recordDebug("Completed dolphin animation")
            journaling_manager.recordInfo("Dolphin animation played successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error playing dolphin animation: {e}")
            raise
            
    async def draw_menu(self, items: List[MenuItem]) -> None:
        """
        Draw the menu system
        
        Args:
            items: List of menu items to display
        """
        journaling_manager.recordScope("AssociativeVisualArea.draw_menu", num_items=len(items))
        try:
            self.menu_items = items
            self.selected_index = 0
            
            # Clear screen
            await self._clear_screen()
            journaling_manager.recordDebug("Cleared screen for menu")
            
            # Draw menu background
            await self._draw_menu_background()
            journaling_manager.recordDebug("Drew menu background")
            
            # Draw menu items
            for i, item in enumerate(items):
                await self._draw_menu_item(item.text, i, item.selected)
                journaling_manager.recordDebug(f"Drew menu item {i+1}/{len(items)}")
                
            # Draw navigation hints
            await self._draw_menu_navigation()
            journaling_manager.recordDebug("Drew menu navigation")
            
            journaling_manager.recordInfo("Menu drawn successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu: {e}")
            raise

    async def _draw_menu_background(self) -> None:
        """Draw menu background"""
        # Implementation for menu background
        pass
        
    async def _draw_menu_item(
        self,
        text: str,
        index: int,
        is_selected: bool = False
    ) -> None:
        """Draw a menu item on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu_item",
            text=text,
            index=index,
            is_selected=is_selected
        )
        try:
            # Calculate position
            x = 2  # Left margin
            y = 8 + (index * 6)  # Start below title
            
            # Draw selection indicator
            if is_selected:
                await self._draw_menu_selection(x, y)
                
            # Draw text
            await self._draw_text(text, x + 4, y, 255, 255, 255)
            
            journaling_manager.recordDebug(
                f"Drew menu item '{text}' at index {index}, "
                f"selected={is_selected}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu item: {e}")
            raise
        
    async def _draw_menu_navigation(self) -> None:
        """Draw menu navigation hints"""
        journaling_manager.recordScope("AssociativeVisualArea._draw_menu_navigation")
        try:
            # Draw up/down arrows for navigation
            await self._draw_text("^", CONFIG.visual_width // 2, 0, 255, 255, 255)
            await self._draw_text("v", CONFIG.visual_width // 2, CONFIG.visual_height - 8, 255, 255, 255)
            
            # Draw selection hint
            await self._draw_text(">", 2, CONFIG.visual_height - 8, 255, 255, 255)
            
            journaling_manager.recordDebug("Drew menu navigation hints")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu navigation: {e}")
            raise
        
    async def navigate_menu(self, direction: int) -> None:
        """
        Navigate the menu
        
        Args:
            direction: 1 for down, -1 for up
        """
        journaling_manager.recordScope("AssociativeVisualArea.navigate_menu", direction=direction)
        try:
            if not self.menu_items:
                journaling_manager.recordDebug("No menu items to navigate")
                return
                
            self.selected_index = (
                (self.selected_index + direction) % len(self.menu_items)
            )
            
            # Update selection state
            for i, item in enumerate(self.menu_items):
                item.selected = (i == self.selected_index)
                
            journaling_manager.recordDebug(f"Navigated menu to index {self.selected_index}")
            
            # Redraw menu with new selection
            await self.draw_menu(self.menu_items)
            
        except Exception as e:
            journaling_manager.recordError(f"Error navigating menu: {e}")
            raise
            
    async def select_menu_item(self) -> str:
        """
        Select the current menu item
        
        Returns:
            str: Action associated with selected item
        """
        journaling_manager.recordScope("AssociativeVisualArea.select_menu_item")
        try:
            if not self.menu_items:
                journaling_manager.recordDebug("No menu items to select")
                return ""
                
            selected_item = self.menu_items[self.selected_index]
            journaling_manager.recordDebug(f"Selected menu item: {selected_item.text}")
            return selected_item.action
            
        except Exception as e:
            journaling_manager.recordError(f"Error selecting menu item: {e}")
            raise

    async def _clear_screen(self) -> None:
        """Clear the LED matrix screen"""
        journaling_manager.recordScope("AssociativeVisualArea._clear_screen")
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "clear"
            })
            journaling_manager.recordDebug("Cleared LED matrix screen")
            journaling_manager.recordInfo("Screen cleared successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error clearing screen: {e}")
            raise
            
    async def _set_background(self, r: int, g: int, b: int) -> None:
        """Set the background color of the LED matrix"""
        journaling_manager.recordScope("AssociativeVisualArea._set_background", r=r, g=g, b=b)
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "set_background",
                "color": (r, g, b)
            })
            journaling_manager.recordDebug(f"Set background color to RGB({r}, {g}, {b})")
            journaling_manager.recordInfo("Background color set successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting background: {e}")
            raise
            
    async def _draw_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Draw a single pixel on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_pixel",
            x=x,
            y=y,
            r=r,
            g=g,
            b=b
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_pixel",
                "x": x,
                "y": y,
                "color": (r, g, b)
            })
            journaling_manager.recordDebug(f"Drew pixel at ({x}, {y}) with color RGB({r}, {g}, {b})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing pixel: {e}")
            raise

    async def show_gear_animation(self, duration: float = 5.0, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Show a rotating gear animation"""
        journaling_manager.recordScope("AssociativeVisualArea.show_gear_animation", duration=duration, color=color)
        try:
            start_time = time.time()
            r, g, b = color
            
            while time.time() - start_time < duration:
                # Calculate gear position
                self._gear_rotation = (self._gear_rotation + 0.1) % (2 * math.pi)
                
                # Draw gear teeth
                for i in range(8):
                    angle = self._gear_rotation + (i * math.pi / 4)
                    x = int(32 + 12 * math.cos(angle))
                    y = int(16 + 12 * math.sin(angle))
                    await self.set_pixel(x, y, r, g, b)
                    
                # Draw center
                await self.set_pixel(32, 16, r, g, b)
                
                # Update display
                await self.update()
                time.sleep(0.05)
                
            journaling_manager.recordDebug("Gear animation completed")
            
        except Exception as e:
            journaling_manager.recordError(f"Error showing gear animation: {e}")
            raise

    async def set_expression(self, expression: Expression) -> None:
        """Set the current expression"""
        journaling_manager.recordScope("AssociativeVisualArea.set_expression", expression=expression)
        try:
            self.current_expression = expression
            journaling_manager.recordDebug(f"Expression set to: {expression.value}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting expression: {e}")
            raise
            
    async def set_size(self, size: Size) -> None:
        """Set the current size"""
        journaling_manager.recordScope("AssociativeVisualArea.set_size", size=size)
        try:
            self.current_size = size
            journaling_manager.recordDebug(f"Size set to: {size.value}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting size: {e}")
            raise
            
    async def add_menu_item(self, text: str, action: str, icon: Optional[str] = None) -> None:
        """Add a menu item"""
        journaling_manager.recordScope("AssociativeVisualArea.add_menu_item", text=text, action=action, icon=icon)
        try:
            item = MenuItem(text, action, icon)
            self.menu_items.append(item)
            journaling_manager.recordDebug(f"Added menu item: {text}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error adding menu item: {e}")
            raise
            
    async def select_menu_item(self, index: int) -> None:
        """Select a menu item"""
        journaling_manager.recordScope("AssociativeVisualArea.select_menu_item", index=index)
        try:
            if 0 <= index < len(self.menu_items):
                self.selected_index = index
                for i, item in enumerate(self.menu_items):
                    item.selected = (i == index)
                journaling_manager.recordDebug(f"Selected menu item: {self.menu_items[index].text}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error selecting menu item: {e}")
            raise
            
    async def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a pixel color"""
        journaling_manager.recordScope("AssociativeVisualArea.set_pixel", x=x, y=y, r=r, g=g, b=b)
        try:
            # Implementation would go here
            pass
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting pixel: {e}")
            raise
            
    async def update(self) -> None:
        """Update the display"""
        journaling_manager.recordScope("AssociativeVisualArea.update")
        try:
            current_time = time.time()
            if current_time - self._last_update >= 1.0 / 30.0:  # 30 FPS
                self._last_update = current_time
                self.animation_frame = (self.animation_frame + 1) % 30
                
        except Exception as e:
            journaling_manager.recordError(f"Error updating display: {e}")
            raise

    async def _draw_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        r: int,
        g: int,
        b: int
    ) -> None:
        """Draw a line on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_line",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            r=r,
            g=g,
            b=b
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_line",
                "start": (x1, y1),
                "end": (x2, y2),
                "color": (r, g, b)
            })
            journaling_manager.recordDebug(f"Drew line from ({x1}, {y1}) to ({x2}, {y2}) with color RGB({r}, {g}, {b})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing line: {e}")
            raise

    async def _draw_circle(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        r: int,
        g: int,
        b: int,
        fill: bool = False
    ) -> None:
        """Draw a circle on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_circle",
            center_x=center_x,
            center_y=center_y,
            radius=radius,
            r=r,
            g=g,
            b=b,
            fill=fill
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_circle",
                "center": (center_x, center_y),
                "radius": radius,
                "color": (r, g, b),
                "fill": fill
            })
            journaling_manager.recordDebug(
                f"Drew circle at ({center_x}, {center_y}) with radius {radius}, "
                f"color RGB({r}, {g}, {b}), fill={fill}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing circle: {e}")
            raise

    async def _draw_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        r: int,
        g: int,
        b: int,
        fill: bool = False
    ) -> None:
        """Draw a rectangle on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_rectangle",
            x=x,
            y=y,
            width=width,
            height=height,
            r=r,
            g=g,
            b=b,
            fill=fill
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_rectangle",
                "position": (x, y),
                "size": (width, height),
                "color": (r, g, b),
                "fill": fill
            })
            journaling_manager.recordDebug(
                f"Drew rectangle at ({x}, {y}) with size {width}x{height}, "
                f"color RGB({r}, {g}, {b}), fill={fill}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing rectangle: {e}")
            raise

    async def _draw_text(
        self,
        text: str,
        x: int,
        y: int,
        r: int,
        g: int,
        b: int,
        font_size: int = 1,
        font_name: str = "default"
    ) -> None:
        """Draw text on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_text",
            text=text,
            x=x,
            y=y,
            r=r,
            g=g,
            b=b,
            font_size=font_size,
            font_name=font_name
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_text",
                "text": text,
                "position": (x, y),
                "color": (r, g, b),
                "font_size": font_size,
                "font_name": font_name
            })
            journaling_manager.recordDebug(
                f"Drew text '{text}' at ({x}, {y}) with color RGB({r}, {g}, {b}), "
                f"font_size={font_size}, font_name={font_name}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing text: {e}")
            raise

    async def _draw_image(
        self,
        image_data: List[List[Tuple[int, int, int]]],
        x: int,
        y: int,
        scale: float = 1.0
    ) -> None:
        """Draw an image on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_image",
            x=x,
            y=y,
            scale=scale,
            image_size=f"{len(image_data)}x{len(image_data[0])}"
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_image",
                "image_data": image_data,
                "position": (x, y),
                "scale": scale
            })
            journaling_manager.recordDebug(
                f"Drew image at ({x}, {y}) with scale {scale}, "
                f"size {len(image_data)}x{len(image_data[0])}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing image: {e}")
            raise

    async def _draw_animation(
        self,
        frames: List[List[List[Tuple[int, int, int]]]],
        x: int,
        y: int,
        duration: float = 1.0,
        loop: bool = True
    ) -> None:
        """Draw an animation on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_animation",
            x=x,
            y=y,
            duration=duration,
            loop=loop,
            num_frames=len(frames)
        )
        try:
            frame_duration = duration / len(frames)
            journaling_manager.recordDebug(f"Starting animation with {len(frames)} frames, duration {duration}s")
            
            while True:
                for i, frame in enumerate(frames):
                    await self._draw_image(frame, x, y)
                    journaling_manager.recordDebug(f"Drew frame {i+1}/{len(frames)}")
                    await asyncio.sleep(frame_duration)
                
                if not loop:
                    break
                    
            journaling_manager.recordInfo("Animation completed successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing animation: {e}")
            raise

    async def _draw_progress_bar(
        self,
        progress: float,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (255, 255, 255),
        background_color: Tuple[int, int, int] = (0, 0, 0),
        show_percentage: bool = True
    ) -> None:
        """Draw a progress bar on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_progress_bar",
            progress=progress,
            x=x,
            y=y,
            width=width,
            height=height,
            color=color,
            background_color=background_color,
            show_percentage=show_percentage
        )
        try:
            # Draw background
            await self._draw_rectangle(x, y, width, height, *background_color, fill=True)
            
            # Draw progress
            fill_width = int(width * progress)
            if fill_width > 0:
                await self._draw_rectangle(x, y, fill_width, height, *color, fill=True)
                
            # Draw percentage text if enabled
            if show_percentage:
                percentage_text = f"{progress:.0%}"
                text_width = len(percentage_text) * 4  # Approximate width
                text_x = x + (width - text_width) // 2
                text_y = y + (height - 4) // 2
                await self._draw_text(percentage_text, text_x, text_y, *color)
                
            journaling_manager.recordDebug(
                f"Drew progress bar at ({x}, {y}) with progress {progress:.2%}, "
                f"size {width}x{height}, show_percentage={show_percentage}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing progress bar: {e}")
            raise

    async def _draw_menu(
        self,
        title: str,
        items: List[str],
        selected_index: int = 0,
        scroll_offset: int = 0,
        max_visible_items: int = 5
    ) -> None:
        """Draw a menu on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu",
            title=title,
            num_items=len(items),
            selected_index=selected_index,
            scroll_offset=scroll_offset,
            max_visible_items=max_visible_items
        )
        try:
            # Draw title
            await self._draw_menu_title(title)
            
            # Draw menu items
            visible_items = items[scroll_offset:scroll_offset + max_visible_items]
            for i, item in enumerate(visible_items):
                is_selected = (i + scroll_offset) == selected_index
                await self._draw_menu_item(item, i, is_selected)
                
            # Draw scroll indicators if needed
            if scroll_offset > 0:
                await self._draw_menu_scroll("up")
            if scroll_offset + max_visible_items < len(items):
                await self._draw_menu_scroll("down")
                
            journaling_manager.recordDebug(
                f"Drew menu '{title}' with {len(items)} items, "
                f"selected={selected_index}, scroll={scroll_offset}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu: {e}")
            raise

    async def _draw_menu_selection(self, x: int, y: int) -> None:
        """Draw a selection indicator for a menu item"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu_selection",
            x=x,
            y=y
        )
        try:
            # Draw selection arrow
            await self._draw_text(">", x, y, 255, 255, 255)
            journaling_manager.recordDebug(f"Drew selection indicator at ({x}, {y})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu selection: {e}")
            raise

    async def _draw_menu_scroll(self, direction: str) -> None:
        """Draw a scroll indicator for a menu"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu_scroll",
            direction=direction
        )
        try:
            if direction == "up":
                # Draw up arrow at top
                await self._draw_text("^", CONFIG.visual_width // 2, 0, 255, 255, 255)
            elif direction == "down":
                # Draw down arrow at bottom
                await self._draw_text("v", CONFIG.visual_width // 2, CONFIG.visual_height - 8, 255, 255, 255)
                
            journaling_manager.recordDebug(f"Drew scroll indicator in {direction} direction")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu scroll: {e}")
            raise

    async def _draw_menu_title(self, title: str) -> None:
        """Draw a menu title on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu_title",
            title=title
        )
        try:
            # Draw title at top center
            title_width = len(title) * 4  # Approximate width
            x = (CONFIG.visual_width - title_width) // 2
            y = 2  # Top margin
            
            await self._draw_text(title, x, y, 255, 255, 255)
            journaling_manager.recordDebug(f"Drew menu title '{title}' at ({x}, {y})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu title: {e}")
            raise

    def count_neighbors(self, x: int, y: int) -> int:
        """Count live neighbors for a cell"""
        return sum(
            self.grid[(y + dy) % self.HEIGHT][(x + dx) % self.WIDTH]
            for dy in [-1, 0, 1]
            for dx in [-1, 0, 1]
            if not (dx == 0 and dy == 0)
        )

    def update_grid(self):
        """Update the game grid"""
        new_grid = [[0]*self.WIDTH for _ in range(self.HEIGHT)]
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                neighbors = self.count_neighbors(x, y)
                if self.grid[y][x] == 1:
                    new_grid[y][x] = 1 if neighbors in [2, 3] else 0
                else:
                    new_grid[y][x] = 1 if neighbors == 3 else 0
        self.grid = new_grid

    async def draw_game_of_life(self) -> None:
        """Draw current game state"""
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT))
        pixels = image.load()
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                if self.grid[y][x]:
                    fitness = self.count_neighbors(x, y)
                    color = (0, min(255, fitness * 40), 255 - fitness * 20)
                    pixels[x, y] = color
                else:
                    pixels[x, y] = (0, 0, 0)
        
        # Use primary area to display the image
        await self.primary_area.set_image(image)

    def _setup_spectrum_char_map(self):
        """Map each character to a unique color in the full spectrum"""
        # Define all characters we want to map
        chars = (
            'abcdefghijklmnopqrstuvwxyz'  # 26 lowercase letters
            '0123456789'                   # 10 numbers
            ' .,!?-_:;\'\"()[]{}#@$%^&*+=' # 22 punctuation/special chars
        )
        total_chars = len(chars)  # 58 total characters

        journaling_manager.recordDebug(f"[Visual Cortex] Mapping {total_chars} characters to spectrum")

        # Map each character to a color in the spectrum
        for i, char in enumerate(chars):
            # Convert position to hue (0-1)
            hue = i / total_chars
            # Convert HSV to RGB (S and V at 100% for vibrant colors)
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            # Convert to 8-bit color values
            color = tuple(int(c * 255) for c in rgb)
            self.char_map[char] = color
            journaling_manager.recordDebug(f"[Visual Cortex] Mapped '{char}' to RGB{color}")

    async def update_llm_visualization(self, text: str) -> None:
        """
        Update the LED matrix with new LLM text
        
        Args:
            text: New text to visualize
        """
        journaling_manager.recordScope("[Visual Cortex] update_llm_visualization")
        try:
            # Create or get existing image
            if not hasattr(self, 'llm_image'):
                self.llm_image = Image.new("RGB", (64, 64), (0, 0, 0))
                self.pixels = self.llm_image.load()

            # Process each character
            for char in text.lower():
                if char in self.char_map:
                    # Get spectrum color for character
                    color = self.char_map[char]
                    
                    # Set pixel color
                    self.pixels[self.current_col, self.current_row] = color
                    
                    # Move to next position
                    self.current_col += 1
                    if self.current_col >= 64:
                        self.current_col = 0
                        self.current_row += 1
                        if self.current_row >= 64:
                            # Reset to top when full
                            self.current_row = 0
                    
                    # Update display
                    await self.primary_area.set_image(self.llm_image)
                    # Small delay for visual effect
                    await asyncio.sleep(0.01)

            journaling_manager.recordDebug(
                f"Updated visualization at position ({self.current_col}, {self.current_row})"
            )

        except Exception as e:
            journaling_manager.recordError(f"Error updating LLM visualization: {e}")
            raise

    async def clear_llm_visualization(self) -> None:
        """Clear the LLM visualization"""
        journaling_manager.recordScope("[Visual Cortex] clear_llm_visualization")
        try:
            if hasattr(self, 'llm_image'):
                self.llm_image = Image.new("RGB", (64, 64), (0, 0, 0))
                self.pixels = self.llm_image.load()
                self.current_col = 0
                self.current_row = 0
                await self.primary_area.set_image(self.llm_image)
                journaling_manager.recordDebug("Cleared LLM visualization")
        except Exception as e:
            journaling_manager.recordError(f"Error clearing LLM visualization: {e}")
            raise 
"""
Neurological Function:
    Fusiform Face Area (FFA) specializes in face processing:
    - Face detection and recognition
    - Holistic face processing
    - Expert-level discrimination
    - Identity processing
    - Expression analysis

Potential Project Implementation:
    Could handle:
    - Face detection
    - Facial recognition
    - Expression analysis
    - Identity matching
"""

# Implementation will be added when needed 
"""
Visual Integration Area - Integrates visual processing
"""

import logging
from typing import Dict, Any, Optional
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.config import CONFIG
from .primary_visual_area import PrimaryVisualArea
from .secondary_visual_area import SecondaryVisualArea
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import asyncio
from PIL import Image

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class IntegrationArea:
    """Integrates visual processing"""
    
    def __init__(self):
        """Initialize the visual integration area"""
        journaling_manager.recordScope("[Visual Cortex] IntegrationArea.__init__")
        self._initialized = False
        self._processing = False
        self.primary_area = PrimaryVisualArea()
        self.secondary_area = SecondaryVisualArea()
        self.grid = [[0 for _ in range(64)] for _ in range(64)]  # Initialize empty grid
        self.is_running = False
        
    async def initialize(self):
        """Initialize the visual integration area"""
        try:
            await self.primary_area.initialize()
            await self.secondary_area.initialize()
            self._initialized = True
            journaling_manager.recordInfo("Visual integration area initialized")
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize visual integration area: {e}")
            raise
            
    async def process_visual(self, visual_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process visual input through all areas"""
        try:
            # Process through primary area first
            primary_result = await self.primary_area.process_visual(visual_data)
            
            # Then through secondary area
            secondary_result = await self.secondary_area.process_visual(primary_result)
            
            # Combine results
            return {
                "primary": primary_result,
                "secondary": secondary_result,
                "status": "ok"
            }
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing visual input: {e}")
            return {"status": "error", "message": str(e)}
            
    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a visual command"""
        if not self._initialized:
            raise RuntimeError("Integration area not initialized")
            
        if self._processing:
            raise RuntimeError("Already processing a command")
            
        try:
            self._processing = True
            
            # Process command based on type
            command_type = command.get("type")
            if command_type == "DISPLAY":
                return await self._process_display(command)
            elif command_type == "SPLASH":
                return await self._process_splash(command)
            else:
                raise ValueError(f"Unknown command type: {command_type}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            self._processing = False
            
    async def _process_display(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process display command"""
        try:
            content = command.get("content")
            if not content:
                raise ValueError("No content provided for display")
                
            # Process display command
            return {"status": "ok", "message": "Display updated"}
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing display command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_splash(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process splash screen command"""
        try:
            # Process splash screen command
            return {"status": "ok", "message": "Splash screen displayed"}
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing splash command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def set_background(self, r: int, g: int, b: int) -> None:
        """Set the LED matrix background color"""
        try:
            await SynapticPathways.send_system_command(
                command_type="set_background",
                data={"r": r, "g": g, "b": b}
            )
        except Exception as e:
            raise Exception(f"Error setting background: {e}")
            
    async def clear(self) -> None:
        """Clear the LED matrix"""
        try:
            await SynapticPathways.send_system_command(
                command_type="clear_matrix"
            )
        except Exception as e:
            raise Exception(f"Error clearing matrix: {e}")
            
    async def set_brightness(self, brightness: int) -> None:
        """
        Set LED matrix brightness
        
        Args:
            brightness: Brightness level (0-100)
        """
        try:
            brightness = max(0, min(100, brightness))
            await SynapticPathways.send_system_command(
                command_type="set_brightness",
                data={"brightness": brightness}
            )
        except Exception as e:
            raise Exception(f"Error setting brightness: {e}")
            
    async def draw_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """
        Draw a single pixel on the LED matrix
        
        Args:
            x: X coordinate
            y: Y coordinate
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        try:
            await SynapticPathways.send_system_command(
                command_type="draw_pixel",
                data={
                    "x": x,
                    "y": y,
                    "r": r,
                    "g": g,
                    "b": b
                }
            )
        except Exception as e:
            raise Exception(f"Error drawing pixel: {e}")
            
    async def draw_circle(self, x: int, y: int, radius: int, r: int, g: int, b: int) -> None:
        """
        Draw a circle on the LED matrix
        
        Args:
            x: Center X coordinate
            y: Center Y coordinate
            radius: Circle radius
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        try:
            await SynapticPathways.send_system_command(
                command_type="draw_circle",
                data={
                    "x": x,
                    "y": y,
                    "radius": radius,
                    "r": r,
                    "g": g,
                    "b": b
                }
            )
        except Exception as e:
            raise Exception(f"Error drawing circle: {e}")
            
    async def draw_line(self, x1: int, y1: int, x2: int, y2: int, r: int, g: int, b: int) -> None:
        """
        Draw a line on the LED matrix
        
        Args:
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        try:
            await SynapticPathways.send_system_command(
                command_type="draw_line",
                data={
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "r": r,
                    "g": g,
                    "b": b
                }
            )
        except Exception as e:
            raise Exception(f"Error drawing line: {e}")
            
    async def draw_text(self, x: int, y: int, text: str, r: int, g: int, b: int) -> None:
        """
        Draw text on the LED matrix
        
        Args:
            x: Starting X coordinate
            y: Starting Y coordinate
            text: Text to draw
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        try:
            await SynapticPathways.send_system_command(
                command_type="draw_text",
                data={
                    "x": x,
                    "y": y,
                    "text": text,
                    "r": r,
                    "g": g,
                    "b": b
                }
            )
        except Exception as e:
            raise Exception(f"Error drawing text: {e}")
            
    async def create_sprite(self, width: int, height: int) -> Dict[str, Any]:
        """
        Create a sprite for animation
        
        Args:
            width: Sprite width
            height: Sprite height
            
        Returns:
            Dict containing sprite data and metadata
        """
        try:
            response = await SynapticPathways.send_system_command(
                command_type="create_sprite",
                data={
                    "width": width,
                    "height": height
                }
            )
            sprite_id = response.get("sprite_id")
            if sprite_id:
                self._sprite_cache[sprite_id] = response
            return response
        except Exception as e:
            raise Exception(f"Error creating sprite: {e}")
            
    async def draw_sprite(self, sprite_id: str, x: int, y: int) -> None:
        """
        Draw a sprite at the specified position
        
        Args:
            sprite_id: ID of the sprite to draw
            x: X coordinate
            y: Y coordinate
        """
        try:
            if sprite_id not in self._sprite_cache:
                raise Exception(f"Sprite {sprite_id} not found")
                
            await SynapticPathways.send_system_command(
                command_type="draw_sprite",
                data={
                    "sprite_id": sprite_id,
                    "x": x,
                    "y": y
                }
            )
        except Exception as e:
            raise Exception(f"Error drawing sprite: {e}")
            
    async def update_sprite(self, sprite_id: str, frame_data: bytes) -> None:
        """
        Update sprite frame data
        
        Args:
            sprite_id: ID of the sprite to update
            frame_data: New frame data
        """
        try:
            if sprite_id not in self._sprite_cache:
                raise Exception(f"Sprite {sprite_id} not found")
                
            await SynapticPathways.send_system_command(
                command_type="update_sprite",
                data={
                    "sprite_id": sprite_id,
                    "frame_data": frame_data
                }
            )
        except Exception as e:
            raise Exception(f"Error updating sprite: {e}")
            
    async def delete_sprite(self, sprite_id: str) -> None:
        """
        Delete a sprite
        
        Args:
            sprite_id: ID of the sprite to delete
        """
        try:
            if sprite_id in self._sprite_cache:
                await SynapticPathways.send_system_command(
                    command_type="delete_sprite",
                    data={"sprite_id": sprite_id}
                )
                del self._sprite_cache[sprite_id]
        except Exception as e:
            raise Exception(f"Error deleting sprite: {e}")
            
    async def start_animation(self, sprite_id: str, fps: Optional[int] = None) -> None:
        """
        Start sprite animation
        
        Args:
            sprite_id: ID of the sprite to animate
            fps: Optional frames per second (defaults to config)
        """
        try:
            if sprite_id not in self._sprite_cache:
                raise Exception(f"Sprite {sprite_id} not found")
                
            await SynapticPathways.send_system_command(
                command_type="start_animation",
                data={
                    "sprite_id": sprite_id,
                    "fps": fps or CONFIG.visual_animation_fps
                }
            )
        except Exception as e:
            raise Exception(f"Error starting animation: {e}")
            
    async def stop_animation(self, sprite_id: str) -> None:
        """
        Stop sprite animation
        
        Args:
            sprite_id: ID of the sprite to stop
        """
        try:
            if sprite_id not in self._sprite_cache:
                raise Exception(f"Sprite {sprite_id} not found")
                
            await SynapticPathways.send_system_command(
                command_type="stop_animation",
                data={"sprite_id": sprite_id}
            )
        except Exception as e:
            raise Exception(f"Error stopping animation: {e}")
            
    async def process_visual_input(self, image_data: bytes) -> Dict[str, Any]:
        """Process visual input data"""
        try:
            # Process basic features
            basic_features = await self.primary_area.process_raw_visual(image_data)
            
            # Process complex features
            complex_features = await self.secondary_area.analyze_complex_features(image_data)
            
            return {
                "basic_features": basic_features,
                "complex_features": complex_features,
                "status": "ok"
            }
        except Exception as e:
            journaling_manager.recordError(f"Error processing visual input: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Visual integration area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up visual integration area: {e}")
            raise

    async def update_cell(self, x: int, y: int, state: int) -> None:
        """
        Update a single cell in the grid
        
        Args:
            x: X coordinate (0-63)
            y: Y coordinate (0-63)
            state: Cell state (0 or 1)
        """
        journaling_manager.recordScope("[Visual Cortex] update_cell", x=x, y=y, state=state)
        try:
            if 0 <= x < 64 and 0 <= y < 64 and state in (0, 1):
                self.grid[y][x] = state
                journaling_manager.recordDebug(f"Updated cell at ({x}, {y}) to {state}")
            else:
                journaling_manager.recordError(f"Invalid cell update parameters: x={x}, y={y}, state={state}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error updating cell: {e}")
            raise

    async def update_region(self, x: int, y: int, region: list[list[int]]) -> None:
        """
        Update a rectangular region of the grid
        
        Args:
            x: Starting X coordinate
            y: Starting Y coordinate
            region: 2D list of cell states (0s and 1s)
        """
        journaling_manager.recordScope("[Visual Cortex] update_region", x=x, y=y, region_size=f"{len(region)}x{len(region[0])}")
        try:
            height = len(region)
            width = len(region[0])
            
            for dy in range(height):
                for dx in range(width):
                    grid_x = x + dx
                    grid_y = y + dy
                    if 0 <= grid_x < 64 and 0 <= grid_y < 64:
                        self.grid[grid_y][grid_x] = region[dy][dx]
                        
            journaling_manager.recordDebug(f"Updated region at ({x}, {y}) with size {width}x{height}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error updating region: {e}")
            raise

    async def set_grid(self, new_grid: list[list[int]]) -> None:
        """
        Replace the entire grid
        
        Args:
            new_grid: New 64x64 grid of cell states
        """
        journaling_manager.recordScope("[Visual Cortex] set_grid")
        try:
            if len(new_grid) == 64 and all(len(row) == 64 for row in new_grid):
                self.grid = [row[:] for row in new_grid]  # Deep copy
                journaling_manager.recordDebug("Grid replaced successfully")
            else:
                journaling_manager.recordError("Invalid grid dimensions")
                raise ValueError("Grid must be 64x64")
                
        except Exception as e:
            journaling_manager.recordError(f"Error setting grid: {e}")
            raise

    async def run_game_of_life(self):
        """Run the Game of Life simulation"""
        journaling_manager.recordScope("[Visual Cortex] run_game_of_life")
        try:
            self.is_running = True
            while self.is_running:
                # Create image from current grid state
                image = Image.new("RGB", (64, 64))
                pixels = image.load()
                
                for y in range(64):
                    for x in range(64):
                        if self.grid[y][x]:
                            # Calculate neighbors for color
                            neighbors = sum(
                                self.grid[(y + dy) % 64][(x + dx) % 64]
                                for dy in [-1, 0, 1]
                                for dx in [-1, 0, 1]
                                if not (dx == 0 and dy == 0)
                            )
                            color = (0, min(255, neighbors * 40), 255 - neighbors * 20)
                            pixels[x, y] = color
                
                # Display current state
                await self.primary_area.set_image(image)
                
                # Update grid for next generation
                new_grid = [[0]*64 for _ in range(64)]
                for y in range(64):
                    for x in range(64):
                        neighbors = sum(
                            self.grid[(y + dy) % 64][(x + dx) % 64]
                            for dy in [-1, 0, 1]
                            for dx in [-1, 0, 1]
                            if not (dx == 0 and dy == 0)
                        )
                        if self.grid[y][x]:
                            new_grid[y][x] = 1 if neighbors in [2, 3] else 0
                        else:
                            new_grid[y][x] = 1 if neighbors == 3 else 0
                
                self.grid = new_grid
                await asyncio.sleep(0.1)
                
        except Exception as e:
            journaling_manager.recordError(f"Error in game of life: {e}")
            raise
        finally:
            self.is_running = False
            await self.primary_area.clear()

    async def stop_game(self) -> None:
        """Stop the Game of Life simulation"""
        journaling_manager.recordScope("[Visual Cortex] stop_game")
        self.is_running = False
        journaling_manager.recordInfo("Game of Life stopped") 
"""
Primary Visual Area - Core visual processing and LED matrix control
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType
from ...config import CONFIG
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

logger = logging.getLogger(__name__)

class PrimaryVisualArea:
    """Core visual processing and LED matrix control"""
    
    def __init__(self):
        """Initialize the primary visual area"""
        self._initialized = False
        self._processing = False
        self._matrix = None
        self._options = RGBMatrixOptions()
        self._options.rows = 64
        self._options.cols = 64
        self._options.chain_length = 1
        self._options.parallel = 1
        self._options.hardware_mapping = 'regular'
        self._options.brightness = 30
        self._options.disable_hardware_pulsing = True
        
    async def initialize(self) -> None:
        """Initialize the primary visual area"""
        if self._initialized:
            return
            
        try:
            # Initialize LED matrix with the same options as test
            self._matrix = RGBMatrix(options=self._options)
            self._initialized = True
            logger.info("Primary visual area initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize primary visual area: {e}")
            raise
            
    async def toggle_processing(self, enabled: bool) -> None:
        """Toggle visual processing"""
        self._processing = enabled
        logger.info(f"Visual processing {'enabled' if enabled else 'disabled'}")
        
    async def process_raw_visual(self, image_data: bytes) -> Dict[str, Any]:
        """Process raw visual input"""
        try:
            # Convert image data to numpy array
            image = np.frombuffer(image_data, dtype=np.uint8)
            image = image.reshape((CONFIG.visual_height, CONFIG.visual_width, 3))
            
            # Process basic visual features
            features = {
                "brightness": np.mean(image),
                "contrast": np.std(image),
                "edges": self._detect_edges(image)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error processing raw visual: {e}")
            return {}
            
    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Detect edges in image"""
        try:
            # Convert to grayscale
            gray = np.mean(image, axis=2)
            
            # Simple edge detection
            edges = np.zeros_like(gray)
            edges[1:-1, 1:-1] = np.abs(gray[1:-1, 2:] - gray[1:-1, :-2]) + \
                               np.abs(gray[2:, 1:-1] - gray[:-2, 1:-1])
            
            return edges
            
        except Exception as e:
            logger.error(f"Error detecting edges: {e}")
            return np.zeros_like(image[:,:,0]) 

    async def set_image(self, image: Image.Image) -> None:
        """Set an image to the matrix"""
        if not self._initialized:
            raise RuntimeError("Matrix not initialized")
        self._matrix.SetImage(image)

    async def clear(self) -> None:
        """Clear the matrix"""
        if not self._initialized:
            raise RuntimeError("Matrix not initialized")
        self._matrix.Clear()
"""
Neurological Terms:
    - Primary Visual Cortex
    - Striate Cortex
    - V1 (Visual Area 1)
    - Brodmann Area 17

Neurological Function:
    Primary Visual Area (V1) processes basic visual information:
    - Edge detection
    - Basic shape processing
    - Color detection
    - Orientation selectivity
    - Spatial frequency analysis
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class PrimaryVisualArea:
    """Core visual processing and LED matrix control"""
    
    def __init__(self):
        """Initialize the primary visual area"""
        journaling_manager.recordScope("PrimaryVisualArea.__init__")
        self._initialized = False
        self._processing = False
        self._matrix = None
        
    async def initialize(self) -> None:
        """Initialize the primary visual area"""
        if self._initialized:
            return
            
        try:
            # Initialize LED matrix
            self._matrix = np.zeros((CONFIG.visual_height, CONFIG.visual_width, 3), dtype=np.uint8)
            self._initialized = True
            journaling_manager.recordInfo("Primary visual area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize primary visual area: {e}")
            raise
            
    async def toggle_processing(self, enabled: bool) -> None:
        """Toggle visual processing"""
        self._processing = enabled
        logger.info(f"Visual processing {'enabled' if enabled else 'disabled'}")
        
    async def process_raw_visual(self, image_data: bytes) -> Dict[str, Any]:
        """Process raw visual input"""
        try:
            # Convert image data to numpy array
            image = np.frombuffer(image_data, dtype=np.uint8)
            image = image.reshape((CONFIG.visual_height, CONFIG.visual_width, 3))
            
            # Process basic visual features
            features = {
                "brightness": np.mean(image),
                "contrast": np.std(image),
                "edges": self._detect_edges(image)
            }
            
            return features
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing raw visual: {e}")
            return {}
            
    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Detect edges in image"""
        try:
            # Convert to grayscale
            gray = np.mean(image, axis=2)
            
            # Simple edge detection
            edges = np.zeros_like(gray)
            edges[1:-1, 1:-1] = np.abs(gray[1:-1, 2:] - gray[1:-1, :-2]) + \
                               np.abs(gray[2:, 1:-1] - gray[:-2, 1:-1])
            
            return edges
            
        except Exception as e:
            journaling_manager.recordError(f"Error detecting edges: {e}")
            return np.zeros_like(image[:,:,0])

    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Primary visual area cleaned up")
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up primary visual area: {e}")
            raise 
"""
Neurological Terms:
    - Secondary Visual Cortex
    - Prestriate Cortex
    - V2 (Visual Area 2)
    - Brodmann Area 18

Neurological Function:
    Secondary Visual Area (V2) - Complex feature processing:
    - Complex shape analysis
    - Pattern recognition
    - Figure-ground separation
"""
import logging
import numpy as np
from typing import Dict, Any, List
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class SecondaryVisualArea:
    """Complex visual feature processing"""
    
    def __init__(self):
        """Initialize the secondary visual area"""
        journaling_manager.recordScope("SecondaryVisualArea.__init__")
        self._initialized = False
        self._processing = False
        
    async def initialize(self) -> None:
        """Initialize the secondary visual area"""
        if self._initialized:
            return
            
        try:
            # Initialize components
            self._initialized = True
            journaling_manager.recordInfo("Secondary visual area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize secondary visual area: {e}")
            raise
            
    async def analyze_complex_features(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze complex visual features"""
        try:
            # Convert image data to numpy array
            image = np.frombuffer(image_data, dtype=np.uint8)
            image = image.reshape((CONFIG.visual_height, CONFIG.visual_width, 3))
            
            # Analyze complex features
            features = {
                "texture": self._analyze_texture(image),
                "shapes": self._detect_shapes(image),
                "motion": self._detect_motion(image)
            }
            
            return features
            
        except Exception as e:
            journaling_manager.recordError(f"Error analyzing complex features: {e}")
            return {}
            
    def _analyze_texture(self, image: np.ndarray) -> Dict[str, float]:
        """Analyze image texture"""
        try:
            # Convert to grayscale
            gray = np.mean(image, axis=2)
            
            # Calculate texture features
            features = {
                "smoothness": np.std(gray),
                "contrast": np.max(gray) - np.min(gray),
                "energy": np.sum(gray**2)
            }
            
            return features
            
        except Exception as e:
            journaling_manager.recordError(f"Error analyzing texture: {e}")
            return {}
            
    def _detect_shapes(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect shapes in image"""
        try:
            # Convert to grayscale
            gray = np.mean(image, axis=2)
            
            # Simple shape detection
            shapes = []
            # TODO: Implement shape detection
            
            return shapes
            
        except Exception as e:
            journaling_manager.recordError(f"Error detecting shapes: {e}")
            return []
            
    def _detect_motion(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect motion in image"""
        try:
            # Convert to grayscale
            gray = np.mean(image, axis=2)
            
            # Simple motion detection
            motion = {
                "magnitude": 0.0,
                "direction": 0.0
            }
            # TODO: Implement motion detection
            
            return motion
            
        except Exception as e:
            journaling_manager.recordError(f"Error detecting motion: {e}")
            return {"magnitude": 0.0, "direction": 0.0}

    async def process_motion(self, image_data: bytes) -> Dict[str, Any]:
        """Process motion in visual input"""
        try:
            # Process motion
            return {"status": "ok"}
        except Exception as e:
            journaling_manager.recordError(f"Error processing motion: {e}")
            raise
            
    async def detect_objects(self, image_data: bytes) -> Dict[str, Any]:
        """Detect objects in visual input"""
        try:
            # Detect objects
            return {"status": "ok"}
        except Exception as e:
            journaling_manager.recordError(f"Error detecting objects: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Secondary visual area cleaned up")
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up secondary visual area: {e}")
            raise 
"""
Neurological Function:
    Mirror Neuron System:
    - Action understanding
    - Behavior mimicry
    - Motor empathy
    - Action learning
    - Social synchronization
    - Movement recognition
    - Imitation learning

Potential Project Implementation:
    Could handle:
    - Action learning
    - Behavior matching
    - Pattern mimicry
    - Movement analysis
"""

# Implementation will be added when needed 
"""
Somatosensory Integration Area - Processes and integrates tactile information
"""

import logging
from typing import Dict, Any, Optional
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class IntegrationArea:
    """Processes and integrates tactile information"""
    
    def __init__(self):
        """Initialize the integration area"""
        journaling_manager.recordScope("SomatosensoryIntegrationArea.__init__")
        self._initialized = False
        self._processing = False
        
        # Register with SynapticPathways
        SynapticPathways.register_integration_area("somatosensory", self)
        
    async def initialize(self) -> None:
        """Initialize the integration area"""
        if self._initialized:
            return
            
        try:
            # Initialize tactile processing components
            self._initialized = True
            journaling_manager.recordInfo("Somatosensory integration area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize somatosensory integration area: {e}")
            raise
            
    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a tactile command"""
        if not self._initialized:
            raise RuntimeError("Integration area not initialized")
            
        if self._processing:
            raise RuntimeError("Already processing a command")
            
        try:
            self._processing = True
            
            # Process command based on type
            command_type = command.get("type")
            if command_type == "TACTILE":
                return await self._process_tactile(command)
            else:
                raise ValueError(f"Unknown command type: {command_type}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            self._processing = False
            
    async def _process_tactile(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process tactile command"""
        try:
            # Process tactile input
            return {"status": "ok", "message": "Tactile command processed"}
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing tactile command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Somatosensory integration area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up somatosensory integration area: {e}")
            raise

    async def process_button_press(self, button_id: str) -> Dict[str, Any]:
        """Process button press events"""
        try:
            response = await SynapticPathways.send_system_command(
                command_type="button_press",
                data={"button_id": button_id}
            )
            return response
        except Exception as e:
            raise Exception(f"Error processing button press: {e}")
            
    async def process_button_release(self, button_id: str) -> Dict[str, Any]:
        """Process button release events"""
        try:
            response = await SynapticPathways.send_system_command(
                command_type="button_release",
                data={"button_id": button_id}
            )
            return response
        except Exception as e:
            raise Exception(f"Error processing button release: {e}")
            
    async def process_touch_input(self, touch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process touch input events"""
        try:
            response = await SynapticPathways.send_system_command(
                command_type="touch_input",
                data=touch_data
            )
            return response
        except Exception as e:
            raise Exception(f"Error processing touch input: {e}") 
"""
Mock GPIO module for development environments

This module provides a mock implementation of RPi.GPIO for development
and testing on non-Raspberry Pi systems.
"""

import logging
from typing import Optional, Callable, Dict
from enum import Enum
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# GPIO modes
BCM = "BCM"
BOARD = "BOARD"

# Pin directions
IN = "IN"
OUT = "OUT"

# Pull up/down resistor configurations
PUD_UP = "PUD_UP"
PUD_DOWN = "PUD_DOWN"
PUD_OFF = "PUD_OFF"

# Edge detection types
BOTH = "BOTH"
RISING = "RISING"
FALLING = "FALLING"

# Pin states
HIGH = 1
LOW = 0

# Software PWM
HARD_PWM = 0
SOFT_PWM = 1

# Version info (for compatibility)
VERSION = "0.7.0"
RPI_INFO = {
    "P1_REVISION": 3,
    "RAM": "1024M",
    "REVISION": "a02082",
    "TYPE": "Pi 3 Model B",
    "PROCESSOR": "BCM2837",
    "MANUFACTURER": "Embest"
}

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class MockGPIO:
    """Mock GPIO implementation"""
    
    def __init__(self):
        self._mode: Optional[str] = None
        self._pin_states: Dict[int, int] = {}
        self._pin_events: Dict[int, Dict] = {}
        self._cleanup_handlers: Dict[int, Callable] = {}
        self._pwm_pins: Dict[int, Dict] = {}
        
    def setmode(self, mode: str) -> None:
        """Set GPIO mode"""
        try:
            self._mode = mode
            journaling_manager.recordDebug(f"GPIO mode set to {mode}")
        except Exception as e:
            journaling_manager.recordError(f"Error setting GPIO mode: {e}")
            raise
        
    def setup(self, pin: int, direction: str, pull_up_down: str = None) -> None:
        """Set up GPIO pin"""
        try:
            self._pin_states[pin] = HIGH if pull_up_down == PUD_UP else LOW
            journaling_manager.recordDebug(f"Pin {pin} setup with direction {direction} and pull_up_down {pull_up_down}")
        except Exception as e:
            journaling_manager.recordError(f"Error setting up GPIO pin: {e}")
            raise
        
    def input(self, pin: int) -> int:
        """Read input from pin"""
        return self._pin_states.get(pin, LOW)
        
    def output(self, pin: int, state: bool) -> None:
        """Set GPIO output"""
        try:
            self._pin_states[pin] = state
            journaling_manager.recordDebug(f"Pin {pin} set to {state}")
        except Exception as e:
            journaling_manager.recordError(f"Error setting GPIO output: {e}")
            raise
        
    def add_event_detect(self, pin: int, edge: str, callback: Callable) -> None:
        """Add event detection to GPIO pin"""
        try:
            self._pin_events[pin] = {
                "edge": edge,
                "callback": callback,
                "bouncetime": None
            }
            journaling_manager.recordDebug(f"Event detection added to pin {pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error adding event detection: {e}")
            raise
        
    def remove_event_detect(self, pin: int) -> None:
        """Remove event detection from GPIO pin"""
        try:
            if pin in self._pin_events:
                del self._pin_events[pin]
                journaling_manager.recordDebug(f"Event detection removed from pin {pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error removing event detection: {e}")
            raise
        
    def cleanup(self) -> None:
        """Clean up GPIO resources"""
        try:
            self._pin_states.clear()
            self._pin_events.clear()
            self._pwm_pins.clear()
            journaling_manager.recordDebug("All GPIO resources cleaned up")
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up GPIO: {e}")
            raise
        
    def cleanup_pin(self, pin: int) -> None:
        """Clean up specific GPIO pin"""
        try:
            if pin in self._pin_states:
                del self._pin_states[pin]
            if pin in self._pin_events:
                del self._pin_events[pin]
            if pin in self._pwm_pins:
                del self._pwm_pins[pin]
            journaling_manager.recordDebug(f"Pin {pin} cleaned up")
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up GPIO pin: {e}")
            raise
        
    def simulate_input(self, pin: int, state: bool) -> None:
        """Simulate input on GPIO pin"""
        try:
            if pin in self._pin_events:
                old_state = self._pin_states.get(pin, LOW)
                self._pin_states[pin] = state
                
                event = self._pin_events[pin]
                if event["callback"] and (
                    event["edge"] == BOTH or
                    (event["edge"] == RISING and state == HIGH) or
                    (event["edge"] == FALLING and state == LOW)
                ):
                    event["callback"](pin)
                    journaling_manager.recordDebug(f"Simulated input on pin {pin}: {state}")
        except Exception as e:
            journaling_manager.recordError(f"Error simulating GPIO input: {e}")
            raise
        
    def PWM(self, pin: int, frequency: float) -> 'PWM':
        """Create PWM instance for a pin"""
        if pin not in self._pwm_pins:
            self._pwm_pins[pin] = {"frequency": frequency, "duty_cycle": 0}
        return PWM(pin, frequency)

class PWM:
    """Mock PWM class"""
    
    def __init__(self, pin: int, frequency: float):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        
    def start(self, duty_cycle: float) -> None:
        """Start PWM"""
        try:
            self.duty_cycle = duty_cycle
            journaling_manager.recordDebug(f"PWM started on pin {self.pin} with duty cycle {duty_cycle}")
        except Exception as e:
            journaling_manager.recordError(f"Error starting PWM: {e}")
            raise
        
    def stop(self) -> None:
        """Stop PWM"""
        try:
            journaling_manager.recordDebug(f"PWM stopped on pin {self.pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error stopping PWM: {e}")
            raise
        
    def ChangeDutyCycle(self, duty_cycle: float) -> None:
        """Change PWM duty cycle"""
        try:
            self.duty_cycle = duty_cycle
            journaling_manager.recordDebug(f"PWM duty cycle changed to {duty_cycle} on pin {self.pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error changing PWM duty cycle: {e}")
            raise
        
    def ChangeFrequency(self, frequency: float) -> None:
        """Change PWM frequency"""
        try:
            self.frequency = frequency
            journaling_manager.recordDebug(f"PWM frequency changed to {frequency} on pin {self.pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error changing PWM frequency: {e}")
            raise

# Create global instance
_gpio = MockGPIO()

# Export module functions
setmode = _gpio.setmode
setup = _gpio.setup
input = _gpio.input
output = _gpio.output
add_event_detect = _gpio.add_event_detect
remove_event_detect = _gpio.remove_event_detect
cleanup = _gpio.cleanup
simulate_input = _gpio.simulate_input
PWM = _gpio.PWM 
"""
Neurological Function:
    Primary somatosensory cortex (S1) processes tactile information.
    - Brodmann areas 1, 2, and 3
    - Processes touch, pressure, temperature, and pain
    - Maps physical sensations to specific body regions

Project Function:
    Maps to touch/button/GPIO functionality:
    - Button press/release detection
    - GPIO input handling
    - Tactile feedback processing
"""

import asyncio
from typing import Optional, Callable, Any, Dict
import logging
import platform
from pathlib import Path

from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType, SystemCommand
from ...config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

# Use RPi.GPIO if available, otherwise use mock
try:
    import RPi.GPIO as GPIO
    logger = logging.getLogger(__name__)
    logger.info("Using RPi.GPIO module")
except ImportError:
    from . import mock_gpio as GPIO
    logger = logging.getLogger(__name__)
    logger.info("Using mock GPIO module for development")

class TactileStimulusError(Exception):
    """Error handling tactile input"""
    pass

class PrimaryArea:
    """Primary somatosensory area handling tactile input"""
    
    def __init__(self):
        """Initialize the primary somatosensory area"""
        journaling_manager.recordScope("PrimarySomatosensoryArea.__init__")
        self._initialized = False
        self._processing = False
        self._gpio = None
        self.logger = logging.getLogger(__name__)
        self.button_pin = CONFIG.tactile_button_pin
        self.pressed = False
        self.press_callback: Optional[Callable] = None
        self.release_callback: Optional[Callable] = None
        self._setup_tactile_pathway()
        
    def _setup_tactile_pathway(self) -> None:
        """Configure GPIO for tactile input"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                self.button_pin, 
                GPIO.BOTH, 
                callback=self._process_tactile_stimulus,
                bouncetime=50
            )
            self.logger.info(f"Tactile pathway initialized on pin {self.button_pin}")
        except Exception as e:
            self.logger.error(f"Tactile pathway setup error: {e}")
            raise TactileStimulusError(f"Failed to setup tactile pathway: {e}")
            
    def _process_tactile_stimulus(self, channel: int) -> None:
        """Process incoming tactile stimulus"""
        try:
            state = GPIO.input(self.button_pin)
            self.pressed = not state  # Button is active LOW
            
            if self.pressed and self.press_callback:
                asyncio.create_task(self._transmit_tactile_signal("tactile_press"))
                self.press_callback()
            elif not self.pressed and self.release_callback:
                asyncio.create_task(self._transmit_tactile_signal("tactile_release"))
                self.release_callback()
                
        except Exception as e:
            self.logger.error(f"Tactile stimulus processing error: {e}")
            
    async def _transmit_tactile_signal(self, signal_type: str) -> None:
        """Transmit tactile signal through synaptic pathways"""
        try:
            await SynapticPathways.transmit_json(
                SystemCommand(
                    command_type=CommandType.SYSTEM,
                    event=signal_type,
                    data={
                        "pin": self.button_pin,
                        "state": self.pressed
                    }
                )
            )
        except Exception as e:
            self.logger.error(f"Tactile signal transmission error: {e}")
            
    def register_press_receptor(self, callback: Callable) -> None:
        """Register callback for tactile press"""
        self.press_callback = callback
        
    def register_release_receptor(self, callback: Callable) -> None:
        """Register callback for tactile release"""
        self.release_callback = callback
        
    async def await_tactile_press(self) -> None:
        """Wait for tactile press stimulus"""
        while not self.pressed:
            await asyncio.sleep(0.01)
            
    async def await_tactile_release(self) -> None:
        """Wait for tactile release stimulus"""
        while self.pressed:
            await asyncio.sleep(0.01)
            
    def cleanup_tactile_pathway(self) -> None:
        """Clean up tactile pathway resources"""
        try:
            GPIO.cleanup(self.button_pin)
            self.logger.info("Tactile pathway cleanup complete")
        except Exception as e:
            self.logger.error(f"Tactile pathway cleanup error: {e}")
            raise TactileStimulusError(f"Failed to cleanup tactile pathway: {e}")
            
    async def process_tactile_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process complex tactile input data
        
        Args:
            input_data: Dictionary containing tactile input parameters
            
        Returns:
            Dict[str, Any]: Processed tactile data
        """
        try:
            # Process tactile input and return results
            # This can be expanded for more complex tactile processing
            return {
                "pin": self.button_pin,
                "state": self.pressed,
                "processed": True,
                **input_data
            }
        except Exception as e:
            self.logger.error(f"Tactile input processing error: {e}")
            return {
                "error": str(e),
                "processed": False
            }

    async def initialize(self) -> None:
        """Initialize the primary somatosensory area"""
        try:
            # Initialize GPIO
            if platform.system() == "Linux":
                journaling_manager.recordInfo("Using RPi.GPIO module")
                import RPi.GPIO as GPIO
                self._gpio = GPIO
            else:
                journaling_manager.recordInfo("Using mock GPIO module for development")
                from .mock_gpio import GPIO
                self._gpio = GPIO
                
            # Set up tactile pathway
            self._gpio.setmode(self._gpio.BCM)
            self._gpio.setup(self.button_pin, self._gpio.IN, pull_up_down=self._gpio.PUD_UP)
            self._gpio.add_event_detect(self.button_pin, self._gpio.FALLING, callback=self._handle_button_press)
            
            self._initialized = True
            journaling_manager.recordInfo(f"Tactile pathway initialized on pin {self.button_pin}")
            
        except Exception as e:
            journaling_manager.recordError(f"Tactile pathway setup error: {e}")
            raise
            
    async def process_tactile_stimulus(self, stimulus_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process tactile stimulus"""
        try:
            # Process stimulus
            return {"status": "ok"}
        except Exception as e:
            journaling_manager.recordError(f"Tactile stimulus processing error: {e}")
            raise
            
    async def transmit_tactile_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transmit tactile signal"""
        try:
            # Transmit signal
            return {"status": "ok"}
        except Exception as e:
            journaling_manager.recordError(f"Tactile signal transmission error: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self._gpio:
                self._gpio.remove_event_detect(self.button_pin)
                self._gpio.cleanup()
            self._initialized = False
            journaling_manager.recordInfo("Tactile pathway cleanup complete")
        except Exception as e:
            journaling_manager.recordError(f"Tactile pathway cleanup error: {e}")
            raise
            
    def _handle_button_press(self, channel: int) -> None:
        """Handle button press event"""
        try:
            # Handle button press
            pass
        except Exception as e:
            journaling_manager.recordError(f"Tactile input processing error: {e}")
            raise 
import wifi
import subprocess
from typing import List, Dict

class WifiManager:
    def __init__(self):
        self.interface = "wlan0"
        self.current_network = None

    def scan_networks(self) -> List[Dict]:
        """
        Scan for available WiFi networks
        """
        try:
            cmd = ['iwlist', self.interface, 'scan']
            scan_output = subprocess.check_output(cmd).decode('utf-8')
            networks = []
            for line in scan_output.split('\n'):
                if "ESSID:" in line:
                    ssid = line.split('ESSID:"')[1].split('"')[0]
                    networks.append({"ssid": ssid})
            return networks
        except Exception as e:
            print(f"Error scanning networks: {e}")
            return []

    def connect_to_network(self, ssid: str, password: str) -> bool:
        """
        Connect to a specific WiFi network
        """
        try:
            cmd = [
                'nmcli', 'device', 'wifi', 'connect', ssid,
                'password', password
            ]
            subprocess.check_call(cmd)
            self.current_network = ssid
            return True
        except Exception as e:
            print(f"Error connecting to network: {e}")
            return False

    def disconnect(self):
        """
        Disconnect from current WiFi network
        """
        try:
            cmd = ['nmcli', 'device', 'disconnect', self.interface]
            subprocess.check_call(cmd)
            self.current_network = None
            return True
        except Exception as e:
            print(f"Error disconnecting: {e}")
            return False

    def get_current_network(self) -> str:
        """
        Get current connected network name
        """
        return self.current_network 
import logging
from typing import Optional, Dict, Any
import asyncio
import time
import traceback

from Mind.Subcortex.BasalGanglia.task_manager import BasalGanglia
from Mind.Subcortex.BasalGanglia.tasks.think_task import ThinkTask
from Mind.Subcortex.BasalGanglia.tasks.system_command_task import SystemCommandTask
from Mind.Subcortex.BasalGanglia.tasks.display_visual_task import DisplayVisualTask
from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask
from Mind.Subcortex.BasalGanglia.tasks.hardware_info_task import HardwareInfoTask
from Mind.Subcortex.BasalGanglia.tasks.model_management_task import ModelManagementTask
from Mind.Subcortex.BasalGanglia.tasks.cortex_communication_task import CortexCommunicationTask
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class BasalGangliaIntegration:
    """Integration for the basal ganglia task system."""
    
    def __init__(self):
        """Initialize the basal ganglia integration."""
        self._tasks = {}  # Dictionary to store tasks
        self._running = True
        
        # Log initialization
        journaling_manager.recordInfo("[BasalGanglia] 🚀 Initializing BasalGanglia task system")
        
        # Create core tasks
        self._create_core_tasks()
        
        # Start task loop
        self._task_loop = asyncio.create_task(self.task_loop())
        journaling_manager.recordInfo("[BasalGanglia] 🔄 Task loop started")
    
    def _create_core_tasks(self):
        """Create and register core tasks."""
        try:
            # Import task classes directly here to avoid circular imports
            from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask
            from Mind.Subcortex.BasalGanglia.tasks.hardware_info_task import HardwareInfoTask
            from Mind.Subcortex.BasalGanglia.tasks.system_command_task import SystemCommandTask
            from Mind.Subcortex.BasalGanglia.tasks.model_management_task import ModelManagementTask
            
            # Create and register tasks
            self.add_task(CommunicationTask(priority=1))
            self.add_task(HardwareInfoTask(priority=5))
            self.add_task(SystemCommandTask(priority=3))
            self.add_task(ModelManagementTask(priority=4))
            
            journaling_manager.recordInfo(f"[BasalGanglia] ✅ Core tasks created: {', '.join(self._tasks.keys())}")
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] ❌ Error creating core tasks: {e}")
            import traceback
            journaling_manager.recordError(f"[BasalGanglia] Stack trace: {traceback.format_exc()}")
    
    def add_task(self, task):
        """Add a task to the basal ganglia."""
        self._tasks[task.name] = task
        journaling_manager.recordInfo(f"[BasalGanglia] ➕ Added task: {task.name}")
    
    def get_task(self, task_name):
        """Get a task by name."""
        task = self._tasks.get(task_name)
        if not task:
            journaling_manager.recordWarning(f"[BasalGanglia] ⚠️ Task not found: {task_name}")
        return task
    
    def get_communication_task(self):
        """Get the communication task."""
        return self.get_task("CommunicationTask")
    
    def get_hardware_info_task(self):
        """Get the hardware info task."""
        return self.get_task("HardwareInfoTask")
    
    def get_system_command_task(self):
        """Get the system command task."""
        return self.get_task("SystemCommandTask")
    
    def get_model_management_task(self):
        """Get the model management task."""
        return self.get_task("ModelManagementTask")
    
    async def task_loop(self):
        """Main task execution loop."""
        last_execution = {}
        
        while self._running:
            try:
                current_time = time.time()
                
                # Process tasks
                for task in sorted(self._tasks.values(), key=lambda t: t.priority):
                    if not task.active:
                        continue
                    
                    # Set appropriate intervals
                    interval = 1.0
                    if "HardwareInfoTask" in task.name:
                        interval = 60.0  # Once per minute
                    elif "ModelManagementTask" in task.name:
                        interval = 120.0  # Every 2 minutes
                    elif "SystemCommandTask" in task.name:
                        interval = 0.1  # Systems commands run immediately
                    
                    # Check if it's time to run
                    last_time = last_execution.get(task.name, 0)
                    if current_time - last_time >= interval:
                        try:
                            await task.execute()
                            last_execution[task.name] = current_time
                        except Exception as e:
                            journaling_manager.recordError(f"[BasalGanglia] ❌ Error executing {task.name}: {e}")
                
                # Sleep to prevent CPU spinning
                await asyncio.sleep(0.5)
                
            except Exception as e:
                journaling_manager.recordError(f"[BasalGanglia] ❌ Error in task loop: {e}")
                await asyncio.sleep(1)
    
    def shutdown(self):
        """Shutdown the basal ganglia task system."""
        self._running = False
        if hasattr(self, '_task_loop'):
            self._task_loop.cancel()
        journaling_manager.recordInfo("[BasalGanglia] 🛑 Task system shutdown")

    def think(self, prompt: str, stream: bool = False, priority: int = 3) -> ThinkTask:
        """Create and register a ThinkTask for LLM operations"""
        journaling_manager.recordScope("[BasalGanglia] Creating ThinkTask", prompt=prompt[:50])
        task = ThinkTask(prompt=prompt, stream=stream, priority=priority)
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo(f"[BasalGanglia] Registered ThinkTask with prompt: {prompt[:50]}...")
        return task
    
    def system_command(self, command_type: str, data: Dict[str, Any] = None, 
                      priority: int = 1) -> SystemCommandTask:
        """Create and register a SystemCommandTask for system operations"""
        journaling_manager.recordScope("[BasalGanglia] Creating SystemCommandTask", command_type=command_type)
        task = SystemCommandTask(command_type=command_type, data=data, priority=priority)
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo(f"[BasalGanglia] Registered SystemCommandTask: {command_type}")
        return task
        
    def display_visual(self, content: str = None, display_type: str = "text", 
                      visualization_type: str = None, visualization_params: dict = None,
                      priority: int = 2) -> DisplayVisualTask:
        """Create and register a DisplayVisualTask for visual output"""
        journaling_manager.recordScope("[BasalGanglia] Creating DisplayVisualTask", 
                                    display_type=display_type, visualization_type=visualization_type)
        task = DisplayVisualTask(
            content=content, 
            display_type=display_type,
            visualization_type=visualization_type,
            visualization_params=visualization_params,
            priority=priority
        )
        self.basal_ganglia.register_task(task)
        
        if visualization_type:
            journaling_manager.recordInfo(f"[BasalGanglia] Registered DisplayVisualTask with visualization: {visualization_type}")
        else:
            journaling_manager.recordInfo(f"[BasalGanglia] Registered DisplayVisualTask with type: {display_type}")
        
        return task
        
    def get_pending_tasks(self) -> int:
        """Get count of pending tasks"""
        count = len([t for t in self.basal_ganglia.task_queue if t.active])
        journaling_manager.recordDebug(f"[BasalGanglia] Pending tasks: {count}")
        return count
        
    def display_llm_pixel_grid(self, initial_content: str = "", 
                              width: int = 64, 
                              height: int = 64,
                              wrap: bool = True,
                              color_mode: str = "grayscale",
                              priority: int = 2) -> DisplayVisualTask:
        """Create and register an LLM token-to-pixel grid visualization task"""
        journaling_manager.recordScope("[BasalGanglia] Creating LLM pixel grid visualization", 
                                    width=width, height=height, color_mode=color_mode)
        task = DisplayVisualTask(
            content=initial_content,
            visualization_type="llm_pixel_grid",
            visualization_params={
                "width": width,
                "height": height,
                "wrap": wrap,
                "color_mode": color_mode
            },
            stream_mode=True,  # This is a streaming task
            priority=priority
        )
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo(f"[BasalGanglia] Registered LLM pixel grid visualization task ({width}x{height})")
        return task

    def display_llm_stream(self, initial_content: str = "", 
                          highlight_keywords: bool = False,
                          keywords: list = None,
                          show_tokens: bool = False,
                          priority: int = 2) -> DisplayVisualTask:
        """Create and register an LLM stream visualization task"""
        journaling_manager.recordScope("[BasalGanglia] Creating LLM stream visualization")
        task = DisplayVisualTask(
            content=initial_content,
            visualization_type="llm_stream",
            visualization_params={
                "highlight_keywords": highlight_keywords,
                "keywords": keywords or [],
                "show_tokens": show_tokens
            },
            stream_mode=True,  # Important: This is a streaming task
            priority=priority
        )
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo("[BasalGanglia] Registered LLM stream visualization task")
        return task

    def initialize_communication(self, connection_type: str) -> bool:
        """Initialize the communication task with specified connection type"""
        comm_task = self.get_communication_task()
        # Run in event loop
        return asyncio.run(comm_task.initialize(connection_type))

    def register_cortex_communication_task(self, source_cortex: str, target_cortex: str, 
                                         data: dict, priority: int = 2) -> 'CortexCommunicationTask':
        """
        Register a task for inter-cortex communication
        
        Args:
            source_cortex: Source cortex name
            target_cortex: Target cortex name
            data: Data to communicate
            priority: Task priority
            
        Returns:
            The registered task
        """
        from Mind.Subcortex.BasalGanglia.tasks.cortex_communication_task import CortexCommunicationTask
        
        task = CortexCommunicationTask(
            source_cortex=source_cortex,
            target_cortex=target_cortex,
            data=data,
            priority=priority
        )
        
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo(f"[BasalGanglia] Registered cortex communication task: {source_cortex} → {target_cortex}")
        return task 
# PenphinMind/Mind/Subcortex/BasalGanglia/task_base.py

from abc import ABC, abstractmethod
from typing import Optional, Any

class NeuralTask(ABC):
    """
    Base class for all neuro-behavioral tasks in the Basal Ganglia system.

    Symbolically represents a neural intent or behavior unit with a lifecycle.
    """

    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority  # Lower number = higher priority
        self.active = False       # Whether the task is currently running
        self.result: Optional[Any] = None  # Optional return value from task
        self._has_run = False     # Internal flag for single-run tasks

    @abstractmethod
    def run(self) -> None:
        """
        Core logic of the task.
        Subclasses must implement this method.
        """
        pass

    def pause(self) -> None:
        """Symbolic inhibition of task activity."""
        self.active = False

    def resume(self) -> None:
        """Resume active state (used for long-running or streamable tasks)."""
        self.active = True

    def stop(self) -> None:
        """Fully deactivate task and signal completion."""
        self.active = False
        self._has_run = True

    def has_completed(self) -> bool:
        """Return whether the task has fully finished."""
        return self._has_run

    def describe(self) -> str:
        """Return a descriptive string of the task for logging."""
        return f"{self.name} (Priority: {self.priority}, Active: {self.active})"
# Mind/Subcortex/BasalGanglia/task_manager.py

import time
import threading
import logging

from .task_base import NeuralTask

class BasalGanglia:
    """
    Central orchestrator for prioritized cognitive and motor tasks.
    Emulates the behavior selection of the biological basal ganglia.
    """

    def __init__(self):
        self.task_queue: list[NeuralTask] = []
        self.running = False
        self.lock = threading.Lock()
        self.log = logging.getLogger("BasalGanglia")

    def register_task(self, task: NeuralTask):
        """
        Add a new task to the queue and sort by priority.
        """
        with self.lock:
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority)
            self.log.info(f"[BasalGanglia] Registered task: {task.describe()}")

    def run_cycle(self):
        """
        One execution cycle: run all active tasks by order of priority.
        """
        with self.lock:
            for task in self.task_queue:
                if task.active:
                    self.log.info(f"[BasalGanglia] Running: {task.describe()}")
                    try:
                        task.run()
                    except Exception as e:
                        self.log.error(f"[BasalGanglia] Task failed: {task.name} - {e}")

    def start(self, interval: float = 0.1):
        """
        Begin the continuous execution loop.
        """
        if self.running:
            return

        def loop():
            self.running = True
            self.log.info("[BasalGanglia] Task loop started.")
            while self.running:
                self.run_cycle()
                time.sleep(interval)
            self.log.info("[BasalGanglia] Task loop stopped.")

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()

    def stop(self):
        """
        Gracefully stop the loop.
        """
        self.running = False
# Mind/Subcortex/BasalGanglia/task_types.py

from enum import Enum, auto

class TaskType(Enum):
    """Enumeration of different neural task types"""
    THINK = auto()                 # Thinking/reasoning tasks using LLM
    SYSTEM_COMMAND = auto()        # System operation commands
    DISPLAY_VISUAL = auto()        # Visual display operations
    SPEECH = auto()                # Speech generation
    LISTEN = auto()                # Audio input processing
    MEMORY = auto()                # Memory operations
    COMMUNICATION = auto()         # Hardware communication tasks
    HARDWARE_INFO = auto()         # Hardware information monitoring
    MODEL_MANAGEMENT = auto()      # Model selection and management
    CORTEX_COMMUNICATION = auto()  # Inter-cortex communication
    DEVICE_CONTROL = auto()        # Device control operations (reboot, etc.)
    INPUT_PROCESSING = auto()      # User input processing
    OUTPUT_FORMATTING = auto()     # Output formatting and presentation
    ERROR_HANDLING = auto()        # Specialized error handling and recovery

class TaskCategory(Enum):
    """
    Broader classification for filtering or analytics.
    """
    COGNITIVE = auto()       # LLM, decision, planning
    SENSORY = auto()         # ASR, KWS
    MOTOR = auto()           # TTS, display, system
    COMMUNICATION = auto()   # Hardware communication tasks
    META = auto()            # Internal state, idle, logging

# Optional: tag mapping
TASK_CATEGORY_MAP = {
    TaskType.THINK: TaskCategory.COGNITIVE,
    TaskType.SYSTEM_COMMAND: TaskCategory.META,
    TaskType.DISPLAY_VISUAL: TaskCategory.MOTOR,
    TaskType.SPEECH: TaskCategory.MOTOR,
    TaskType.LISTEN: TaskCategory.SENSORY,
    TaskType.MEMORY: TaskCategory.COGNITIVE,
    TaskType.COMMUNICATION: TaskCategory.COGNITIVE,
}
from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.CorpusCallosum.transport_layer import get_transport, ConnectionError
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import json
import time
import asyncio
from typing import Dict, Any, Optional, Callable, List
import traceback

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class CommunicationTask(NeuralTask):
    """Task to manage communication with the hardware"""
    
    # Shared instance (singleton pattern)
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get or create the shared instance"""
        if cls._instance is None:
            cls._instance = CommunicationTask()
            journaling_manager.recordInfo("[BasalGanglia] Created CommunicationTask instance")
        return cls._instance
    
    def __init__(self, priority=1):
        """Initialize the communication task."""
        super().__init__("CommunicationTask", priority)
        self.connection_type = None
        self._transport = None
        self.active = True
        self.log = logging.getLogger("CommunicationTask")
        journaling_manager.recordInfo("[BasalGanglia] Initialized CommunicationTask")
        
        # Connection state
        self._initialized = False
        self._last_activity = 0
        self._connection_monitor_active = False
        
        # Request queue and callbacks
        self._request_queue = []
        self._callbacks = {}
        
    def run(self):
        """Implementation of required abstract method.
        
        In this task, operations happen asynchronously via execute()
        """
        # This synchronous method satisfies the Task abstract requirement
        # But actual work is done in the async methods
        return {"status": "ready"}
    
    async def execute(self):
        """Execute communication task operations"""
        # Just return current status - this task works on-demand
        is_connected = hasattr(self, '_transport') and self._transport is not None
        return {
            "status": "connected" if is_connected else "disconnected",
            "connection_type": self.connection_type,
            "endpoint": self._transport.endpoint if is_connected else None
        }
    
    async def initialize(self, connection_type):
        """Initialize the communication task."""
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.transport_layer import get_transport
            
            # Log initialization
            journaling_manager.recordInfo(f"[CommunicationTask] 🔌 Initializing {connection_type} connection")
            
            # Create and store transport
            self._transport = get_transport(connection_type)
            self.connection_type = connection_type
            
            # Try to connect
            journaling_manager.recordInfo(f"[CommunicationTask] 🔄 Connecting to {connection_type}...")
            connected = await self._transport.connect()
            
            if connected:
                journaling_manager.recordInfo(f"[CommunicationTask] ✅ Connected using {connection_type}")
                return True
            else:
                journaling_manager.recordError(f"[CommunicationTask] ❌ Failed to connect using {connection_type}")
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"[CommunicationTask] ❌ Error initializing: {e}")
            import traceback
            journaling_manager.recordError(f"[CommunicationTask] Stack trace: {traceback.format_exc()}")
            return False
    
    async def send_command(self, command):
        """Send command using the method that works for models."""
        if not self._transport or not hasattr(self._transport, 'transmit'):
            journaling_manager.recordError("[CommunicationTask] ❌ Transport not initialized")
            return {"error": {"code": -1, "message": "Transport not initialized"}}
        
        try:
            action = command.get("action", "unknown")
            journaling_manager.recordInfo(f"[CommunicationTask] 📤 Sending {action} command")
            
            # Send command via transport
            response = await self._transport.transmit(command)
            journaling_manager.recordInfo(f"[CommunicationTask] 📥 Received {action} response")
            
            # Return raw response without modification
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"[CommunicationTask] ❌ Error sending command: {e}")
            import traceback
            journaling_manager.recordError(f"[CommunicationTask] Stack trace: {traceback.format_exc()}")
            return {"error": {"code": -1, "message": str(e)}}
    
    async def queue_command(self, command: Dict[str, Any], callback: Callable = None) -> str:
        """Queue a command for asynchronous processing"""
        journaling_manager.recordScope("[BasalGanglia] Queuing command", command_type=command.get("action"))
        # Generate request ID if not present
        if "request_id" not in command:
            command["request_id"] = f"req_{int(time.time())}"
            
        request_id = command["request_id"]
        
        # Register callback if provided
        if callback:
            self._callbacks[request_id] = callback
            
        # Add to queue
        self._request_queue.append(command)
        journaling_manager.recordInfo(f"[BasalGanglia] Command queued with ID: {request_id}")
        
        return request_id
    
    async def shutdown(self) -> None:
        """Shutdown the communication channel"""
        journaling_manager.recordScope("[BasalGanglia] Shutting down communication channel")
        try:
            if self._transport:
                await self._transport.disconnect()
                
            self._initialized = False
            self._transport = None
            journaling_manager.recordInfo("[BasalGanglia] Communication channel shutdown complete")
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error during communication shutdown: {e}")
    
    async def _process_queue(self) -> None:
        """Process queued commands"""
        if not self._request_queue:
            return
            
        try:
            # Take first command from queue
            command = self._request_queue.pop(0)
            journaling_manager.recordInfo(f"[BasalGanglia] Processing queued command: {command.get('action')}")
            
            # Process it
            await self.send_command(command)
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error processing command queue: {e}")
    
    async def _monitor_connection(self) -> None:
        """Monitor connection health and attempt reconnection if needed"""
        self._connection_monitor_active = True
        journaling_manager.recordInfo("[BasalGanglia] Starting connection monitor")
        
        try:
            while self.active:
                # Check if connection needs refresh
                if self._initialized and time.time() - self._last_activity > 300:  # 5 minutes
                    # Do a ping to verify connection
                    try:
                        journaling_manager.recordInfo("[BasalGanglia] Checking connection with ping")
                        await self.send_command({
                            "request_id": f"ping_{int(time.time())}",
                            "work_id": "sys",
                            "action": "ping",
                            "object": "system",
                            "data": None
                        })
                    except Exception as e:
                        journaling_manager.recordWarning(f"[BasalGanglia] Connection ping failed: {e}")
                        # Try to reconnect
                        self._initialized = False
                        await self.initialize()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error in connection monitor: {e}")
        finally:
            self._connection_monitor_active = False 
from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import asyncio
from typing import Dict, Any

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class CortexCommunicationTask(NeuralTask):
    """Task to manage communication between cortices"""
    
    def __init__(self, source_cortex: str, target_cortex: str, 
                data: Dict[str, Any], priority: int = 2):
        """
        Initialize a cortex communication task
        
        Args:
            source_cortex: Source cortex name
            target_cortex: Target cortex name
            data: Data to communicate
            priority: Task priority (lower = higher priority)
        """
        super().__init__(name="CortexCommunicationTask", priority=priority)
        self.task_type = TaskType.CORTEX_COMMUNICATION
        self.source_cortex = source_cortex
        self.target_cortex = target_cortex
        self.data = data
        self.active = True
        self.log = logging.getLogger("CortexCommunicationTask")
        journaling_manager.recordInfo(f"[BasalGanglia] Created CortexCommunicationTask: {source_cortex} → {target_cortex}")
        
    def run(self):
        """Execute the cortex communication task"""
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running CortexCommunicationTask", 
                                    source=self.source_cortex, target=self.target_cortex)
        
        try:
            self.log.info(f"Relaying data from {self.source_cortex} to {self.target_cortex}")
            
            # Create event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Use SynapticPathways to relay between cortices
            self.result = loop.run_until_complete(
                SynapticPathways.relay_between_cortices(
                    self.source_cortex,
                    self.target_cortex,
                    self.data
                )
            )
            
            journaling_manager.recordInfo(f"[BasalGanglia] Data relay complete: {self.source_cortex} → {self.target_cortex}")
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error in cortex communication: {e}")
            self.result = {"error": str(e)}
            
        self.stop()  # Communication task completes after one relay 
from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
import logging
import asyncio
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class DisplayVisualTask(NeuralTask):
    """Task to handle displaying visual information to the user"""
    
    def __init__(self, content: str = None, display_type: str = "text", 
                 visualization_type: str = None, visualization_params: dict = None,
                 stream_mode: bool = False, priority: int = 2):
        """
        Initialize a visual display task
        
        Args:
            content: The content to display (text or image path)
            display_type: The type of content ("text", "image", "animation")
            visualization_type: Type of visualization ("splash", "game_of_life", "llm_stream", "llm_pixel_grid")
            visualization_params: Parameters for the visualization
            stream_mode: Whether this task will continuously update with new content
            priority: Task priority (lower number = higher priority)
        """
        super().__init__(name="DisplayVisualTask", priority=priority)
        self.task_type = TaskType.DISPLAY_VISUAL
        self.content = content or ""
        self.display_type = display_type
        self.visualization_type = visualization_type
        self.visualization_params = visualization_params or {}
        self.stream_mode = stream_mode
        self.active = True
        self.complete = False
        self.stream_buffer = ""
        self.log = logging.getLogger("DisplayVisualTask")
        
        # For token-to-pixel grid
        self.pixel_grid = None
        self.cursor_pos = [0, 0]  # Position in the grid [x, y]
        
        journaling_manager.recordInfo(f"[BasalGanglia] Created DisplayVisualTask: {visualization_type or display_type}")
        
    def run(self):
        """Execute the display task"""
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running DisplayVisualTask", 
                                    visualization_type=self.visualization_type, 
                                    display_type=self.display_type)
        
        try:
            # Handle special visualizations
            if self.visualization_type:
                if self.visualization_type == "llm_pixel_grid":
                    # For token-to-pixel grid, run once to set up, then keep task alive
                    if not hasattr(self, '_grid_initialized'):
                        self._initialize_pixel_grid()
                        self._grid_initialized = True
                    
                    # Process any new content in the buffer
                    if self.content != self.stream_buffer:
                        new_content = self.content[len(self.stream_buffer):]
                        self._update_pixel_grid(new_content)
                        self.stream_buffer = self.content
                        
                    # If stream is complete, mark task as done
                    if self.complete:
                        self.log.info("[OccipitalCortex] LLM pixel grid visualization completed")
                        self.result = {"status": "completed", "type": "llm_pixel_grid"}
                        self.stop()
                    
                    return  # Return to keep task alive for streaming
                    
                elif self.visualization_type == "llm_stream":
                    # For LLM streaming, run once to set up, then keep task alive
                    if not hasattr(self, '_stream_initialized'):
                        self._initialize_llm_stream()
                        self._stream_initialized = True
                    
                    # Process any new content in the buffer
                    if self.content != self.stream_buffer:
                        self._update_llm_stream()
                        self.stream_buffer = self.content
                        
                    # If stream is complete, mark task as done
                    if self.complete:
                        self.log.info("[OccipitalCortex] LLM stream visualization completed")
                        self.result = {"status": "completed", "type": "llm_stream"}
                        self.stop()
                    
                    return  # Return to keep task alive for streaming
                    
                elif self.visualization_type == "splash_screen":
                    self._render_splash_screen()
                elif self.visualization_type == "game_of_life":
                    self._render_game_of_life()
                else:
                    self.log.warning(f"Unsupported visualization type: {self.visualization_type}")
                    self.result = {"error": f"Unsupported visualization type: {self.visualization_type}"}
                    self.stop()
                    return
                    
                self.result = {"status": "displayed", "type": self.visualization_type}
            # Handle standard content display
            else:
                self.log.info(f"[OccipitalCortex] Displaying {self.display_type}: {self.content[:50] if self.content else 'None'}...")
                
                if self.display_type == "text":
                    # For now, just log the output
                    self.log.info(f"[OUTPUT] {self.content}")
                    self.result = {"status": "displayed", "type": self.display_type}
                elif self.display_type == "image":
                    # Image display would be handled here
                    self.log.info(f"[OUTPUT] Image display requested: {self.content}")
                    self.result = {"status": "displayed", "type": self.display_type}
                else:
                    self.log.warning(f"Unsupported display type: {self.display_type}")
                    self.result = {"error": f"Unsupported display type: {self.display_type}"}
                    
        except Exception as e:
            self.log.error(f"[OccipitalCortex] Display failed: {e}")
            self.result = {"error": str(e)}
            
        # Only stop for non-streaming tasks or on errors
        if not self.stream_mode:
            self.stop()
        
    def _render_splash_screen(self):
        """Render a splash screen"""
        try:
            title = self.visualization_params.get("title", "Penphin Mind")
            subtitle = self.visualization_params.get("subtitle", "Neural Architecture")
            
            # Create ASCII art splash screen (as a simple example)
            splash_text = f"""
            {'*' * 50}
            {'*' + ' ' * 48 + '*'}
            {'*' + ' ' * 10 + title.center(28) + ' ' * 10 + '*'}
            {'*' + ' ' * 10 + subtitle.center(28) + ' ' * 10 + '*'}
            {'*' + ' ' * 48 + '*'}
            {'*' * 50}
            """
            
            # Display the splash screen (for now, just log it)
            self.log.info(f"[SPLASH]\n{splash_text}")
        except Exception as e:
            self.log.error(f"Failed to render splash screen: {e}")
            raise
            
    def _render_game_of_life(self):
        """Render Conway's Game of Life simulation"""
        try:
            # Get parameters
            width = self.visualization_params.get("width", 20)
            height = self.visualization_params.get("height", 20)
            iterations = self.visualization_params.get("iterations", 10)
            initial_state = self.visualization_params.get("initial_state", None)
            
            # Create initial grid (random if not provided)
            import random
            grid = initial_state if initial_state else [
                [random.choice([0, 1]) for _ in range(width)]
                for _ in range(height)
            ]
            
            # Run simulation for specified number of iterations
            for i in range(iterations):
                # Display current state (for now, just log it)
                display = "\n".join([''.join(['■' if cell else '□' for cell in row]) for row in grid])
                self.log.info(f"[GAME_OF_LIFE] Generation {i}:\n{display}")
                
                # Calculate next generation
                new_grid = [[0 for _ in range(width)] for _ in range(height)]
                
                for y in range(height):
                    for x in range(width):
                        # Count live neighbors
                        neighbors = sum(
                            grid[(y+dy) % height][(x+dx) % width]
                            for dy in [-1, 0, 1]
                            for dx in [-1, 0, 1]
                            if not (dy == 0 and dx == 0)
                        )
                        
                        # Apply Game of Life rules
                        if grid[y][x] == 1 and neighbors in [2, 3]:
                            new_grid[y][x] = 1  # Cell stays alive
                        elif grid[y][x] == 0 and neighbors == 3:
                            new_grid[y][x] = 1  # Cell becomes alive
                            
                grid = new_grid
                
                # Small delay between generations
                import time
                time.sleep(0.5)
                
        except Exception as e:
            self.log.error(f"Failed to render Game of Life: {e}")
            raise

    def _initialize_pixel_grid(self):
        """Initialize the 64x64 token-to-pixel grid"""
        self.log.info("[OccipitalCortex] Initializing 64x64 token-to-pixel grid")
        
        # Get grid dimensions from params or default to 64x64
        self.grid_width = self.visualization_params.get("width", 64)
        self.grid_height = self.visualization_params.get("height", 64)
        self.wrap_text = self.visualization_params.get("wrap", True)
        self.color_mode = self.visualization_params.get("color_mode", "grayscale")
        
        # Create empty grid (0 = empty/black)
        self.pixel_grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.cursor_pos = [0, 0]  # Start at top-left
        
        # Display the initial empty grid
        self._display_pixel_grid()
    
    def _update_pixel_grid(self, new_text: str):
        """Update the pixel grid with new text content"""
        for char in new_text:
            # Map character to pixel value (0-255)
            pixel_value = self._char_to_pixel_value(char)
            
            # Place pixel value at current cursor position
            x, y = self.cursor_pos
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                self.pixel_grid[y][x] = pixel_value
            
            # Move cursor
            self.cursor_pos[0] += 1
            
            # Handle wrapping or scrolling
            if self.cursor_pos[0] >= self.grid_width:
                if self.wrap_text:
                    # Wrap to next line
                    self.cursor_pos[0] = 0
                    self.cursor_pos[1] += 1
                    
                    # Scroll if needed
                    if self.cursor_pos[1] >= self.grid_height:
                        # Scroll the grid up
                        self.pixel_grid = self.pixel_grid[1:] + [[0 for _ in range(self.grid_width)]]
                        self.cursor_pos[1] = self.grid_height - 1
                else:
                    # No wrapping - stay at the edge
                    self.cursor_pos[0] = self.grid_width - 1
        
        # Display the updated grid
        self._display_pixel_grid()
    
    def _char_to_pixel_value(self, char: str) -> int:
        """Convert a character to a pixel value (0-255)"""
        # Simple mapping based on ASCII value
        # Space is darkest, printable chars get brighter values
        if char == ' ':
            return 0
        elif char.isprintable():
            # Map ASCII values to intensity range (20-255)
            # This ensures even the darkest character is still slightly visible
            ascii_val = ord(char)
            return max(20, min(255, 20 + (ascii_val % 95) * 235 // 94))
        else:
            # Non-printable characters get medium intensity
            return 128
    
    def _display_pixel_grid(self):
        """Display the pixel grid (implementation depends on UI system)"""
        # For console display, we'll use ASCII characters of different densities
        # to represent grayscale values
        
        # Characters from darkest to brightest
        gray_chars = ' .:-=+*#%@'
        color_start = '\033[38;5;'  # ANSI color escape sequence start
        
        grid_display = []
        for row in self.pixel_grid:
            if self.color_mode == "grayscale":
                # Map pixel values (0-255) to ASCII characters
                line = ''
                for pixel in row:
                    # Map 0-255 to 0-9 (index in gray_chars)
                    idx = min(9, pixel * 10 // 256)
                    line += gray_chars[idx]
                grid_display.append(line)
            else:
                # Use ANSI colors for terminal display
                line = ''
                for pixel in row:
                    # Map 0-255 to terminal color (16-255)
                    color = 232 + (pixel * 24 // 256)  # 232-255 are grayscale in 256-color mode
                    line += f"{color_start}{color}m█\033[0m"
                grid_display.append(line)
        
        # Join lines and log
        display_str = '\n'.join(grid_display)
        self.log.info(f"[LLM_PIXEL_GRID]\n{display_str}")

    def _initialize_llm_stream(self):
        """Initialize the LLM streaming visualization"""
        self.log.info("[OccipitalCortex] Starting LLM stream visualization")
        
        # Get visualization parameters
        self.show_tokens = self.visualization_params.get("show_tokens", False)
        self.highlight_keywords = self.visualization_params.get("highlight_keywords", False)
        self.keywords = self.visualization_params.get("keywords", [])
        self.token_count = 0
        self.start_time = self._get_time()
        
        # Set up the display
        self.log.info("[LLM_STREAM] Stream initialized")
        
        # Initial empty display
        self._display_stream("")
    
    def _update_llm_stream(self):
        """Update the LLM stream visualization with new content"""
        # Process the content
        display_content = self.content
        
        # Calculate tokens and timing
        new_tokens = len(self.content.split()) - self.token_count
        self.token_count = len(self.content.split())
        current_time = self._get_time()
        elapsed_time = current_time - self.start_time
        tokens_per_second = self.token_count / max(0.1, elapsed_time)
        
        # Apply any processing like keyword highlighting
        if self.highlight_keywords and self.keywords:
            for keyword in self.keywords:
                # Use simple string replacement for highlighting
                # In a real UI, this would be handled differently
                display_content = display_content.replace(
                    keyword, 
                    f"[HIGHLIGHT]{keyword}[/HIGHLIGHT]"
                )
        
        # Add token statistics if requested
        if self.show_tokens:
            stats = f"\n\n[Tokens: {self.token_count}, Rate: {tokens_per_second:.1f} tokens/sec]"
            display_content += stats
        
        # Display the updated content
        self._display_stream(display_content)
    
    def _display_stream(self, content: str):
        """Display the stream content"""
        # Log it for debugging
        self.log.info(f"[LLM_STREAM] {content}")
        
        # Use OccipitalLobe's AssociativeVisualArea to display the content
        try:
            from Mind.OccipitalLobe.VisualCortex.associative_visual_area import AssociativeVisualArea
            
            # Get or create a singleton instance
            if not hasattr(self, '_visual_area'):
                self._visual_area = AssociativeVisualArea()
            
            # Use asyncio to handle the async call without blocking
            asyncio.create_task(self._visual_area.update_llm_visualization(content))
        except Exception as e:
            self.log.error(f"Error in visual stream display: {e}")
    
    def _get_time(self):
        """Get current time"""
        import time
        return time.time()
from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import time
import asyncio
from typing import Dict, Any
import psutil
import json

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class HardwareInfoTask(NeuralTask):
    """Task to fetch and monitor hardware information"""
    
    def __init__(self, priority=5):
        """Initialize hardware info task with default values."""
        super().__init__("HardwareInfoTask", priority)
        self.hardware_info = {
            "cpu_loadavg": "N/A",
            "mem": "N/A",
            "temperature": "N/A",
            "timestamp": 0
        }
        self.last_refresh_time = 0
        self.refresh_interval = 60.0  # Refresh once per minute
        self.active = True  # Make sure it's active by default
        self.first_run = True  # Flag to indicate first run
        
        # Schedule immediate initial refresh
        asyncio.create_task(self._initial_refresh())
        
    async def _initial_refresh(self):
        """Perform immediate initial refresh after a slight delay to ensure connections are ready."""
        await asyncio.sleep(1.0)  # Short delay to let system initialize
        journaling_manager.recordInfo("[HardwareInfoTask] 🔄 Performing initial hardware info refresh")
        
        try:
            # First refresh might fail if connections aren't ready, so try a few times
            for attempt in range(3):
                try:
                    await self._refresh_hardware_info()
                    self.last_refresh_time = time.time()
                    journaling_manager.recordInfo(f"[HardwareInfoTask] ✅ Initial hardware info obtained: {self.hardware_info}")
                    break
                except Exception as e:
                    if attempt < 2:  # Try again if not last attempt
                        journaling_manager.recordWarning(f"[HardwareInfoTask] Initial refresh attempt {attempt+1} failed: {e}")
                        await asyncio.sleep(1.0)  # Wait before retrying
                    else:
                        journaling_manager.recordError(f"[HardwareInfoTask] All initial refresh attempts failed: {e}")
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] Error in initial refresh: {e}")
        
    async def execute(self):
        """Execute the hardware info task."""
        try:
            current_time = time.time()
            
            # Check if it's time to refresh or if it's the first run
            if self.first_run or (current_time - self.last_refresh_time >= self.refresh_interval):
                journaling_manager.recordInfo("[HardwareInfoTask] 🔄 Refreshing hardware info")
                
                # Refresh the hardware info
                await self._refresh_hardware_info()
                self.last_refresh_time = current_time
                self.first_run = False
                
                # Log updated values
                journaling_manager.recordInfo(f"[HardwareInfoTask] ✅ Hardware info updated: {self.hardware_info}")
            
            # Always return the current info (cached or freshly fetched)
            return self.hardware_info
            
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] ❌ Error in execute: {e}")
            import traceback
            journaling_manager.recordError(f"[HardwareInfoTask] Stack trace: {traceback.format_exc()}")
            return self.hardware_info
            
    async def _refresh_hardware_info(self):
        """Refresh hardware information from API."""
        try:
            # Get communication task
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            bg = SynapticPathways.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                raise Exception("Communication task not found")
            
            # Create request with exact API format
            hwinfo_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "hwinfo"
            }
            
            # Send command
            journaling_manager.recordInfo("[HardwareInfoTask] 📤 Requesting hardware info")
            response = await comm_task.send_command(hwinfo_command)
            
            # Process response with proper field mapping
            if response and "data" in response:
                api_data = response["data"]
                
                # Update hardware info with exact field names from API
                self.hardware_info = {
                    "cpu_loadavg": api_data.get("cpu_loadavg", 0),
                    "mem": api_data.get("mem", 0),
                    "temperature": api_data.get("temperature", 0),
                    "timestamp": time.time()
                }
                
                # Update shared cache in SynapticPathways
                SynapticPathways.current_hw_info = self.hardware_info
                
                journaling_manager.recordInfo(f"[HardwareInfoTask] ✅ Hardware info refreshed: {self.hardware_info}")
            else:
                journaling_manager.recordError(f"[HardwareInfoTask] ❌ Invalid API response: {response}")
                
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] ❌ Error refreshing hardware info: {e}")
            raise

    def run(self):
        """Implementation of abstract method from Task base class."""
        # This synchronous method is required but we'll use async execute instead
        # You can make this a proxy to the async method if needed
        journaling_manager.recordDebug("[BasalGanglia] HardwareInfoTask.run called (using async execute instead)")
        return self.hardware_info

    def _refresh_local_hardware_info(self):
        """Fallback to local hardware info when API fails."""
        try:
            import psutil
            
            # Get CPU, memory, and temperature info locally
            self.hardware_info = {
                "cpu_loadavg": psutil.cpu_percent(),
                "mem": psutil.virtual_memory().percent,
                "temperature": 0,  # No good way to get temperature cross-platform
                "timestamp": time.time(),
                "ip_address": self._get_ip_address() if hasattr(self, "_get_ip_address") else "N/A"
            }
            
            journaling_manager.recordInfo(f"[HardwareInfoTask] Using local hardware info: {self.hardware_info}")
            
        except ImportError:
            journaling_manager.recordWarning("[HardwareInfoTask] psutil not installed - using dummy values")
            self.hardware_info = {
                "cpu_loadavg": 0,
                "mem": 0,
                "temperature": 0,
                "timestamp": time.time(),
                "ip_address": "N/A"
            }

    def _get_ip_address(self):
        """Get the system IP address."""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] Error getting IP: {e}")
            return "N/A"
    
    def get_hardware_info(self):
        """Return cached hardware info without forcing a refresh"""
        return self.hardware_info
    
    def format_hw_info(self) -> str:
        """Format hardware info for display"""
        hw = self.hardware_info
        
        # Format timestamp as readable time
        timestamp = hw.get("timestamp", 0)
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp)) if timestamp else "N/A"
        
        # Format the hardware info in the requested format
        info_str = f"""~
CPU: {hw.get('cpu_loadavg', 'N/A')} | Memory: {hw.get('mem', 'N/A')} | Updated: {time_str}
~"""
        
        return info_str 
from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import time
import asyncio
from typing import Dict, Any, List

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ModelManagementTask(NeuralTask):
    """Task to manage LLM models"""
    
    def __init__(self, priority: int = 4):
        """
        Initialize a model management task
        
        Args:
            priority: Task priority (lower = higher priority)
        """
        super().__init__(name="ModelManagementTask", priority=priority)
        self.task_type = TaskType.MODEL_MANAGEMENT
        self.active = True
        self.log = logging.getLogger("ModelManagementTask")
        journaling_manager.recordInfo("[BasalGanglia] Created ModelManagementTask")
        
        # Model information
        self.models = []
        self.default_model = ""
        self.active_model = ""
        self.models_loaded = False  # Track if we've already loaded models
        self.model_info = {}  # Cache for model info
        
    async def execute(self):
        """Execute the model management task."""
        # This task primarily works on-demand
        return {"status": "ready", "model_count": len(self.models)}
    
    def run(self):
        """Periodic task to check model status"""
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running ModelManagementTask")
        
        # This task normally runs only when explicitly called
        # For continuous model monitoring, additional logic would be needed
        
        # Continue running
        return
    
    async def get_available_models(self):
        """Get available models from the API."""
        try:
            # Get communication task
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            bg = SynapticPathways.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[ModelManagementTask] ❌ Communication task not found")
                return self.models
            
            # Use EXACT format from documentation - this was working
            lsmode_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "lsmode"
            }
            
            # Log request
            journaling_manager.recordInfo("[ModelManagementTask] 📤 Requesting available models")
            
            # Send command and get response
            response = await comm_task.send_command(lsmode_command)
            journaling_manager.recordInfo(f"[ModelManagementTask] 📥 Models response received")
            journaling_manager.recordDebug(f"[ModelManagementTask] 📥 Response: {response}")
            
            if response and "data" in response:
                models_data = response["data"]
                if isinstance(models_data, list):
                    self.models = models_data
                    
                    # Update in SynapticPathways
                    SynapticPathways.available_models = self.models
                    
                    # Find default LLM model
                    for model in self.models:
                        if model.get("type") == "llm":
                            SynapticPathways.default_llm_model = model.get("model", "")
                            break
                    
                    journaling_manager.recordInfo(f"[ModelManagementTask] ✅ Found {len(self.models)} models")
                    return self.models
                else:
                    journaling_manager.recordError(f"[ModelManagementTask] ❌ Invalid models data format")
            else:
                journaling_manager.recordError(f"[ModelManagementTask] ❌ Invalid API response")
            
            return self.models
            
        except Exception as e:
            journaling_manager.recordError(f"[ModelManagementTask] ❌ Error getting models: {e}")
            import traceback
            journaling_manager.recordError(f"[ModelManagementTask] Stack trace: {traceback.format_exc()}")
            return self.models
    
    async def set_active_model(self, model_name: str, params: Dict[str, Any] = None) -> bool:
        """Set the active model"""
        journaling_manager.recordScope("[BasalGanglia] Setting active model", model=model_name)
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Default parameters
            default_params = {
                "response_format": "llm.utf-8",
                "input": "llm.utf-8",
                "enoutput": True,
                "enkws": False,
                "max_token_len": 127,
                "prompt": "You are a helpful assistant named Penphin."
            }
            
            # Merge with provided params
            model_params = {**default_params, **(params or {})}
            
            # Create setup command
            setup_command = {
                "request_id": f"setup_{int(time.time())}",
                "work_id": "sys",
                "action": "setup",
                "object": "llm.setup",
                "data": {
                    "model": model_name,
                    **model_params
                }
            }
            
            # Send command
            response = await SynapticPathways.transmit_json(setup_command)
            
            # Check response
            if response and not response.get("error", {}).get("code", 0):
                self.active_model = model_name
                journaling_manager.recordInfo(f"[BasalGanglia] Set active model to: {model_name}")
                self.result = {"success": True, "model": model_name}
                return True
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"[BasalGanglia] Failed to set active model: {error_msg}")
                self.result = {"success": False, "error": error_msg}
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error setting active model: {e}")
            self.result = {"success": False, "error": str(e)}
            return False
    
    async def reset_llm(self) -> bool:
        """Reset the LLM system"""
        journaling_manager.recordScope("[BasalGanglia] Resetting LLM system")
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Create reset command
            reset_command = {
                "request_id": f"reset_{int(time.time())}",
                "work_id": "sys",
                "action": "reset",
                "object": "system"
            }
            
            # Send command
            response = await SynapticPathways.transmit_json(reset_command)
            
            # Check response
            if response and response.get("error", {}).get("code", -1) == 0:
                message = response.get("error", {}).get("message", "")
                journaling_manager.recordInfo(f"[BasalGanglia] Reset successful: {message}")
                
                # Clear caches
                self.models = []
                self.default_model = ""
                self.active_model = ""
                
                # Wait for reset to complete
                await asyncio.sleep(3)
                
                self.result = {"success": True, "message": message}
                return True
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"[BasalGanglia] Failed to reset LLM: {error_msg}")
                self.result = {"success": False, "error": error_msg}
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error resetting LLM: {e}")
            self.result = {"success": False, "error": str(e)}
            return False
    
    # Add a method to manually request reload
    def request_reload(self):
        """Request that models be reloaded on next execution"""
        self.models_loaded = False
        self.active = True 
from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import asyncio
import time
from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class SystemCommandTask(NeuralTask):
    """Task to handle system command operations"""
    
    def __init__(self, priority=3, command_type=None):
        """Initialize the system command task.
        
        Args:
            priority: Task priority (lower numbers = higher priority)
            command_type: Type of system command (can be set later)
        """
        super().__init__("SystemCommandTask", priority)
        self.command = command_type  # Store command_type as command
        self.data = None
        self.result = None
        self.completed = False
        self.active = False  # Start as inactive
        self.task_type = TaskType.SYSTEM_COMMAND
        self.log = logging.getLogger("SystemCommandTask")
        journaling_manager.recordInfo(f"[BasalGanglia] Created SystemCommandTask: {command_type}")
        
    async def _execute_command(self):
        """Execute the system command asynchronously"""
        journaling_manager.recordScope("[BasalGanglia] Executing system command", 
                                    command_type=self.command, 
                                    data=self.data)
        try:
            # Import SynapticPathways at runtime when needed, not at module level
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Create appropriate command format
            command = {
                "request_id": f"{self.command}_{int(time.time())}",
                "work_id": "sys",
                "action": self.command,
                "object": "system", 
                "data": self.data
            }
            
            # Use SynapticPathways to send the command
            response = await SynapticPathways.transmit_json(command)
            
            journaling_manager.recordInfo(f"[BasalGanglia] System command completed: {self.command}")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] System command failed: {e}")
            return {"error": str(e)}
        
    def run(self):
        """Run the system command task"""
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running SystemCommandTask", command_type=self.command)
        
        try:
            # Create an event loop if there isn't one already
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Execute the command and get the result
            self.result = loop.run_until_complete(self._execute_command())
            journaling_manager.recordDebug(f"[BasalGanglia] System command result: {str(self.result)[:100]}...")
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] System command task failed: {e}")
            self.result = {"error": str(e)}
            
        self.stop()  # Task completes after execution

    async def execute(self):
        """Execute system command with better error handling."""
        if not self.command:
            return None
            
        try:
            journaling_manager.recordInfo(f"[SystemCommandTask] Running command: {self.command}")
            
            # Special handling for ping command
            if self.command == "ping":
                self.result = await self._ping_system()
            # Handle other commands...
            # ...
            
            # Mark as completed
            self.completed = True
            self.active = False  # Auto-deactivate after completion
            
            return self.result
            
        except Exception as e:
            journaling_manager.recordError(f"[SystemCommandTask] Execution error: {e}")
            import traceback
            journaling_manager.recordError(f"[SystemCommandTask] Traceback: {traceback.format_exc()}")
            self.result = {"error": str(e), "success": False}
            self.completed = True
            self.active = False
            return self.result
            
    async def _ping_system(self):
        """Send ping command using same pattern as working model call."""
        try:
            # Get communication task
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            bg = SynapticPathways.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[SystemCommandTask] ❌ Communication task not found")
                return {"success": False, "error": "Communication task not found"}
            
            # Use EXACT format that works for model calls
            ping_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "ping"
            }
            
            # Log command
            journaling_manager.recordInfo("[SystemCommandTask] 📤 Sending ping command")
            
            # Send command using same method that works for models
            response = await comm_task.send_command(ping_command)
            journaling_manager.recordInfo(f"[SystemCommandTask] 📥 Ping response received")
            journaling_manager.recordDebug(f"[SystemCommandTask] 📥 Response: {response}")
            
            # Check response - EXACT format from your shared example
            if response and "error" in response:
                error_code = response["error"].get("code", -1)
                success = (error_code == 0)
                
                return {
                    "success": success,
                    "response": response,
                    "timestamp": time.time()
                }
            else:
                journaling_manager.recordError(f"[SystemCommandTask] ❌ Invalid ping response")
                return {"success": False, "error": "Invalid response"}
            
        except Exception as e:
            journaling_manager.recordError(f"[SystemCommandTask] ❌ Error in ping: {e}")
            import traceback
            journaling_manager.recordError(f"[SystemCommandTask] Stack trace: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
# Mind/Subcortex/BasalGanglia/tasks/think_task.py

from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ThinkTask(NeuralTask):
    def __init__(self, prompt: str, stream: bool = False, priority: int = 3, 
                visual_task = None):
        super().__init__(name="ThinkTask", priority=priority)
        self.task_type = TaskType.THINK
        self.prompt = prompt
        self.stream = stream
        self.active = True
        self.visual_task = visual_task  # Optional link to a visual task
        self.log = logging.getLogger("ThinkTask")
        # Import LLMManager here instead of at module level
        from Mind.FrontalLobe.PrefrontalCortex.language_processor import LLMManager
        self.llm = LLMManager()
        journaling_manager.recordInfo(f"[BasalGanglia] Created ThinkTask with prompt: {prompt[:50]}...")

    def run(self):
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running ThinkTask", prompt=self.prompt[:50])

        try:
            if self.stream:
                journaling_manager.recordInfo("[BasalGanglia] Streaming thought response")
                stream_response = self.llm.stream(self.prompt)
                self.result = ""
                for chunk in stream_response:
                    self.result += chunk
                    journaling_manager.recordDebug(f"[BasalGanglia] Streamed chunk: {len(chunk)} chars")
                    
                    # Update visual task if connected
                    if self.visual_task:
                        self.visual_task.update_stream(self.result)
            else:
                journaling_manager.recordInfo("[BasalGanglia] Generating thought response")
                self.result = self.llm.generate(self.prompt)
                journaling_manager.recordDebug(f"[BasalGanglia] Thought completed: {len(self.result)} chars")
                
                # Update visual task if connected
                if self.visual_task:
                    self.visual_task.update_stream(self.result, is_complete=True)
                    
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Thought failed: {e}")
            self.result = {"error": str(e)}
            
            # Update visual task with error if connected
            if self.visual_task:
                self.visual_task.update_stream(f"Error: {str(e)}", is_complete=True)

        self.stop()  # Task completes after one thought
#!/usr/bin/env python3
import asyncio
import argparse
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways

async def main():
    parser = argparse.ArgumentParser(description="Test UI Modes")
    parser.add_argument("--mode", "-m", choices=["full", "fc", "headless"], 
                       default="fc", help="UI mode")
    parser.add_argument("--prompt", "-p", default="What is the capital of France?",
                      help="Test prompt")
    args = parser.parse_args()
    
    # Set UI mode
    print(f"Setting UI mode to: {args.mode}")
    SynapticPathways.set_ui_mode(args.mode)
    
    # Initialize connection
    print("Initializing connection...")
    await SynapticPathways.initialize("tcp")
    
    # Perform thinking with visualization
    print(f"\nThinking with prompt: '{args.prompt}'")
    print(f"This should use {'pixel grid' if args.mode == 'full' else 'text stream' if args.mode == 'fc' else 'basic'} visualization.")
    
    result = await SynapticPathways.think_with_visualization(args.prompt)
    
    # Print result
    print("\nResult:")
    print(result)
    
    # Cleanup
    print("\nCleaning up...")
    await SynapticPathways.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
"""
Neurological Terms:
    - Auditory Belt Area
    - Non-Primary Auditory Cortex
    - Brodmann Areas 42, 22

Neurological Function:
    Belt area processes intermediate features from primary auditory area:
    - Complex sound processing
    - Spectrotemporal pattern analysis
    - Sound localization
"""

import logging
from typing import Dict, Any, Optional
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType, ASRCommand
from ...config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class BeltArea:
    """Processes complex auditory features"""
    
    def __init__(self):
        """Initialize the belt area"""
        journaling_manager.recordScope("BeltArea.__init__")
        self._initialized = False
        self._processing = False
        
    async def initialize(self) -> None:
        """Initialize the belt area"""
        if self._initialized:
            return
            
        try:
            self._initialized = True
            journaling_manager.recordInfo("Belt area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize belt area: {e}")
            raise
            
    async def process_complex_audio(self, audio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process complex audio features"""
        try:
            # Process complex audio data
            return {"status": "ok", "message": "Complex audio processed"}
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing complex audio: {e}")
            return {"status": "error", "message": str(e)}

    async def process_complex_features(self, audio_data: bytes) -> Dict[str, Any]:
        """Process complex auditory features"""
        try:
            # Convert audio to text using ASR
            text = await self._process_speech(audio_data)
            
            # Analyze complex patterns
            patterns = await self._analyze_patterns(audio_data)
            
            # Localize sound
            location = await self._localize_sound(audio_data)
            
            return {
                "text": text,
                "patterns": patterns,
                "location": location
            }
        except Exception as e:
            journaling_manager.recordError(f"Error processing complex features: {e}")
            return {}
            
    async def _process_speech(self, audio_data: bytes) -> str:
        """Convert speech to text"""
        try:
            response = await SynapticPathways.send_asr(
                audio_data=audio_data,
                language=CONFIG.asr_language,
                model_type=CONFIG.asr_model_type
            )
            return response.get("text", "")
        except Exception as e:
            journaling_manager.recordError(f"Error processing speech: {e}")
            return ""
            
    async def _analyze_patterns(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze complex sound patterns"""
        try:
            response = await SynapticPathways.send_system_command(
                command_type="analyze_patterns",
                data={"audio_data": audio_data}
            )
            return response.get("patterns", {})
        except Exception as e:
            journaling_manager.recordError(f"Error analyzing patterns: {e}")
            return {}
            
    async def _localize_sound(self, audio_data: bytes) -> Dict[str, Any]:
        """Determine sound source location"""
        try:
            response = await SynapticPathways.send_system_command(
                command_type="localize_sound",
                data={"audio_data": audio_data}
            )
            return response.get("location", {})
        except Exception as e:
            journaling_manager.recordError(f"Error localizing sound: {e}")
            return {} 
"""
Auditory Integration Area - Processes and integrates auditory information
"""

import logging
from typing import Dict, Any, Optional
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class IntegrationArea:
    """Processes and integrates auditory information"""
    
    def __init__(self):
        """Initialize the integration area"""
        journaling_manager.recordScope("AuditoryIntegrationArea.__init__")
        self._initialized = False
        self._processing = False
        
        # Register with SynapticPathways
        SynapticPathways.register_integration_area("auditory", self)
        
    async def initialize(self) -> None:
        """Initialize the integration area"""
        if self._initialized:
            return
            
        try:
            # Initialize audio processing components
            self._initialized = True
            journaling_manager.recordInfo("Auditory integration area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize auditory integration area: {e}")
            raise
            
    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process an auditory command"""
        if not self._initialized:
            raise RuntimeError("Integration area not initialized")
            
        if self._processing:
            raise RuntimeError("Already processing a command")
            
        try:
            self._processing = True
            
            # Process command based on type
            command_type = command.get("type")
            if command_type == "TTS":
                return await self._process_tts(command)
            elif command_type == "ASR":
                return await self._process_asr(command)
            elif command_type == "VAD":
                return await self._process_vad(command)
            else:
                raise ValueError(f"Unknown command type: {command_type}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            self._processing = False
            
    async def _process_tts(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process text-to-speech command"""
        try:
            text = command.get("text", "")
            voice_id = command.get("voice_id", "default")
            speed = command.get("speed", 1.0)
            pitch = command.get("pitch", 1.0)
            
            # Process TTS command
            response = await SynapticPathways.send_tts(
                text=text,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch
            )
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing TTS command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_asr(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process automatic speech recognition command"""
        try:
            audio_data = command.get("audio_data")
            language = command.get("language", "en")
            model_type = command.get("model_type", "base")
            
            # Process ASR command
            response = await SynapticPathways.send_asr(
                audio_data=audio_data,
                language=language,
                model_type=model_type
            )
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing ASR command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _process_vad(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice activity detection command"""
        try:
            audio_chunk = command.get("audio_chunk")
            threshold = command.get("threshold", 0.5)
            frame_duration = command.get("frame_duration", 30)
            
            # Process VAD command
            response = await SynapticPathways.send_vad(
                audio_chunk=audio_chunk,
                threshold=threshold,
                frame_duration=frame_duration
            )
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing VAD command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Auditory integration area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up auditory integration area: {e}")
            raise 
"""
Neurological Function:
    Heschl's Gyrus (Primary Auditory Cortex/A1) is the first cortical region
    for auditory processing.

Project Function:
    Maps to core AudioManager functionality:
    - Audio device setup
    - Raw audio I/O
    - Basic volume control
    - Direct audio playback
"""

import logging
from typing import Dict, Any, Optional
import numpy as np
import subprocess
from pathlib import Path
from ....CorpusCallosum.synaptic_pathways import SynapticPathways
from ....CorpusCallosum.neural_commands import CommandType, AudioCommand, VADCommand
from ....config import CONFIG, AudioOutputType
import platform
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class AcousticProcessingError(Exception):
    """Acoustic processing related errors"""
    pass

class PrimaryAcousticArea:
    """Maps to AudioManager's core device functionality"""
    
    def __init__(self):
        """Initialize the primary acoustic area"""
        journaling_manager.recordScope("PrimaryAcousticArea.__init__")
        self._initialized = False
        self._processing = False
        self.logger = logging.getLogger(__name__)
        self.frequency_range = (20, 20000)  # Human auditory range in Hz
        self.audio_device = None
        self.vad_active: bool = False
        self.current_stream: Optional[bytes] = None
        
    async def initialize(self) -> None:
        """Initialize the primary acoustic area"""
        if self._initialized:
            return
            
        try:
            # Set up audio device
            await self.configure_audio_device()
            
            # Register with synaptic pathways
            SynapticPathways.register_integration_area("auditory", self)
            
            self._initialized = True
            journaling_manager.recordInfo("Primary acoustic area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize primary acoustic area: {e}")
            raise
            
    async def configure_audio_device(self) -> None:
        """Configure audio device"""
        try:
            # Check if we're on Raspberry Pi
            is_raspberry_pi = self._is_raspberry_pi()
            
            if is_raspberry_pi:
                # Use WaveShare audio HAT implementation
                for control in CONFIG.audio_device_controls:
                    subprocess.run(
                        ["amixer", "-c", "0", "sset", control, f"{CONFIG.audio_device_controls['volume']}%"],
                        check=True
                    )
                journaling_manager.recordInfo("WaveShare audio HAT configured")
            else:
                # Use LLM audio output for non-Raspberry Pi platforms
                CONFIG.audio_output_type = AudioOutputType.LOCAL_LLM
                journaling_manager.recordInfo("Using LLM audio output")
                
        except Exception as e:
            journaling_manager.recordError(f"Failed to configure audio device: {e}")
            raise
            
    def _is_raspberry_pi(self) -> bool:
        """Check if running on a Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False
            
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
            journaling_manager.recordInfo("VAD started")
        except Exception as e:
            journaling_manager.recordError(f"VAD start error: {e}")
            self.vad_active = False
            raise
            
    async def initiate_voice_detection(self) -> None:
        """Start Voice Activity Detection (alias for start_vad)"""
        return await self.start_vad()
            
    async def stop_vad(self) -> None:
        """Stop Voice Activity Detection"""
        if not self.vad_active:
            return
            
        self.vad_active = False
        journaling_manager.recordInfo("VAD stopped")
        
    async def terminate_voice_detection(self) -> None:
        """Stop Voice Activity Detection (alias for stop_vad)"""
        return await self.stop_vad()
        
    async def process_acoustic_signal(self, audio_data: bytes, operation: str = "normalize") -> bytes:
        """
        Process acoustic signal with specified operation
        
        Args:
            audio_data: Raw acoustic data
            operation: Processing operation to perform
            
        Returns:
            bytes: Processed acoustic data
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
            journaling_manager.recordError(f"Acoustic processing error: {e}")
            return audio_data
            
    async def play_sound(self, audio_data: bytes) -> None:
        """
        Play audio data through the system
        
        Args:
            audio_data: Audio data to play
        """
        try:
            # Use WaveShare audio system by default
            # Save audio data to temporary file
            temp_file = Path("temp_audio.wav")
            temp_file.write_bytes(audio_data)
            
            try:
                # Play using aplay
                subprocess.run(
                    ['aplay', '-D', CONFIG.audio_device_name, str(temp_file)],
                    check=True,
                    capture_output=True
                )
            finally:
                # Cleanup temp file
                if temp_file.exists():
                    temp_file.unlink()
                    
        except subprocess.CalledProcessError as e:
            journaling_manager.recordError(f"WaveShare playback error: {e}")
            raise AcousticProcessingError(f"Failed to play audio: {e}")
        except Exception as e:
            journaling_manager.recordError(f"Audio playback error: {e}")
            raise AcousticProcessingError(f"Failed to play audio: {e}")
            
    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech using configured TTS implementation
        
        Args:
            text: Text to convert to speech
            
        Returns:
            bytes: Audio data
        """
        try:
            command_data = {
                "command_type": CommandType.AUDIO,
                "operation": "tts",
                "text": text,
                "sample_rate": CONFIG.audio_sample_rate,
                "channels": CONFIG.audio_channels
            }
            
            # Add ElevenLabs specific parameters if using fallback
            if CONFIG.tts_implementation == "elevenlabs":
                command_data.update({
                    "model": CONFIG.elevenlabs_model,
                    "voice_id": CONFIG.elevenlabs_voice_id
                })
                
            response = await SynapticPathways.transmit_command(
                AudioCommand(**command_data)
            )
            return response.get("audio_data", b'')
        except Exception as e:
            journaling_manager.recordError(f"TTS error: {e}")
            raise AcousticProcessingError(f"Failed to convert text to speech: {e}")
            
    async def speech_to_text(self, audio_data: bytes) -> str:
        """
        Convert speech to text using configured ASR provider
        
        Args:
            audio_data: Audio data to convert
            
        Returns:
            str: Transcribed text
        """
        try:
            command_data = {
                "command_type": CommandType.AUDIO,
                "operation": "asr",
                "audio_data": audio_data,
                "sample_rate": CONFIG.audio_sample_rate,
                "channels": CONFIG.audio_channels
            }
            
            response = await SynapticPathways.transmit_command(
                AudioCommand(**command_data)
            )
            return response.get("text", "")
        except Exception as e:
            journaling_manager.recordError(f"ASR error: {e}")
            raise AcousticProcessingError(f"Failed to convert speech to text: {e}")
            
    async def detect_wake_word(self, audio_data: bytes) -> bool:
        """
        Detect wake word using configured KWS provider
        
        Args:
            audio_data: Audio data to analyze
            
        Returns:
            bool: True if wake word detected
        """
        try:
            command_data = {
                "command_type": CommandType.AUDIO,
                "operation": "kws",
                "audio_data": audio_data,
                "sample_rate": CONFIG.audio_sample_rate,
                "channels": CONFIG.audio_channels,
                "wake_word": CONFIG.wake_word
            }
            
            response = await SynapticPathways.transmit_command(
                AudioCommand(**command_data)
            )
            return response.get("wake_word_detected", False)
        except Exception as e:
            journaling_manager.recordError(f"KWS error: {e}")
            return False
            
    async def transmit_acoustic_signal(self, audio_data: bytes) -> None:
        """Transmit acoustic signal through the system (alias for play_sound)"""
        return await self.play_sound(audio_data)
            
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
                journaling_manager.recordInfo(f"WaveShare volume set to {volume}%")
            except subprocess.CalledProcessError as e:
                journaling_manager.recordError(f"Error setting WaveShare volume: {e}")
                raise AcousticProcessingError(f"Failed to set volume: {e}")
                
    def adjust_sensitivity(self, sensitivity: int) -> None:
        """Adjust acoustic sensitivity (alias for set_volume)"""
        return self.set_volume(sensitivity)
            
    async def start_stream(self) -> None:
        """Start audio streaming"""
        self.current_stream = b''
        journaling_manager.recordInfo("Audio stream started")
        
    async def initiate_acoustic_stream(self) -> None:
        """Start acoustic streaming (alias for start_stream)"""
        return await self.start_stream()
        
    async def stop_stream(self) -> bytes:
        """
        Stop audio streaming and return collected data
        
        Returns:
            bytes: Collected audio data
        """
        data = self.current_stream
        self.current_stream = None
        journaling_manager.recordInfo("Audio stream stopped")
        return data
        
    async def terminate_acoustic_stream(self) -> bytes:
        """Stop acoustic streaming and return collected data (alias for stop_stream)"""
        return await self.stop_stream()
        
    async def add_to_stream(self, chunk: bytes) -> None:
        """Add chunk to current audio stream"""
        if self.current_stream is not None:
            self.current_stream += chunk
            
    async def append_to_stream(self, chunk: bytes) -> None:
        """Append chunk to current acoustic stream (alias for add_to_stream)"""
        return await self.add_to_stream(chunk)

    async def record_acoustic_signal(self, duration: float) -> bytes:
        """Record audio for specified duration"""
        try:
            response = await SynapticPathways.send_system_command(
                command_type="record_audio",
                data={"duration": duration}
            )
            return response.get("audio_data", b"")
        except Exception as e:
            journaling_manager.recordError(f"Error recording audio: {e}")
            return b""
            
    async def _analyze_auditory_frequency(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Analyze frequency components of auditory input
        
        Args:
            audio_data: Raw auditory data
            
        Returns:
            Dict[str, Any]: Frequency analysis data
        """
        try:
            response = await SynapticPathways.send_system_command(
                command_type="analyze_frequency",
                data={"audio_data": audio_data}
            )
            return response.get("frequency_data", {})
        except Exception as e:
            journaling_manager.recordError(f"Error analyzing auditory frequency: {e}")
            return {}
            
    async def _analyze_frequency(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze frequency components (alias for _analyze_auditory_frequency)"""
        return await self._analyze_auditory_frequency(audio_data)
            
    async def _analyze_auditory_amplitude(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Analyze amplitude characteristics of auditory input
        
        Args:
            audio_data: Raw auditory data
            
        Returns:
            Dict[str, Any]: Amplitude analysis data
        """
        try:
            response = await SynapticPathways.send_system_command(
                command_type="process_amplitude",
                data={"audio_data": audio_data}
            )
            return response.get("amplitude_data", {})
        except Exception as e:
            journaling_manager.recordError(f"Error analyzing auditory amplitude: {e}")
            return {}
            
    async def _process_amplitude(self, audio_data: bytes) -> Dict[str, Any]:
        """Process audio amplitude (alias for _analyze_auditory_amplitude)"""
        return await self._analyze_auditory_amplitude(audio_data)
            
    async def _extract_auditory_temporal_features(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Extract temporal features from auditory input
        
        Args:
            audio_data: Raw auditory data
            
        Returns:
            Dict[str, Any]: Temporal feature data
        """
        try:
            response = await SynapticPathways.send_system_command(
                command_type="extract_temporal",
                data={"audio_data": audio_data}
            )
            return response.get("temporal_data", {})
        except Exception as e:
            journaling_manager.recordError(f"Error extracting auditory temporal features: {e}")
            return {}
            
    async def _extract_temporal_features(self, audio_data: bytes) -> Dict[str, Any]:
        """Extract temporal features (alias for _extract_auditory_temporal_features)"""
        return await self._extract_auditory_temporal_features(audio_data)

    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Process raw audio data"""
        if not self._initialized:
            raise RuntimeError("Primary acoustic area not initialized")
            
        try:
            # Process audio data
            # TODO: Implement actual audio processing
            return {
                "status": "success",
                "processed": True
            }
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing audio: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._processing = False
            self._initialized = False
            journaling_manager.recordInfo("Primary acoustic area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up primary acoustic area: {e}")
            raise
"""
Neurological Function:
    Heschl's Gyrus contains the primary auditory cortex (A1) and is the first
    cortical structure to process auditory information. It processes basic
    acoustic features including:
    - Frequency discrimination
    - Sound intensity
    - Temporal resolution
    - Pitch processing

Project Function:
    Primary acoustic signal processing including:
    - Frequency analysis
    - Amplitude processing
    - Temporal feature extraction
    - Basic pitch detection
"""

import logging
from typing import Dict, Any
import numpy as np

class PrimaryAcousticProcessor:
    """
    Processes fundamental acoustic features in Heschl's Gyrus.
    Acts as the primary receiver of auditory input.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.frequency_range = (20, 20000)  # Human auditory range in Hz
        
    async def process_frequency_components(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Analyze frequency components of incoming audio
        
        Args:
            audio_data: Raw audio input
            
        Returns:
            Dict containing frequency analysis
        """
        pass
        
    async def analyze_temporal_features(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Extract temporal features from audio input
        
        Args:
            audio_data: Raw audio input
            
        Returns:
            Dict containing temporal feature analysis
        """
        pass 
"""
Neurological Function:
    The Planum Temporale, located in the superior temporal gyrus posterior to 
    Heschl's gyrus, is crucial for:
    - Processing complex sound patterns
    - Speech sound analysis
    - Musical pattern processing
    - Phonological working memory
    It shows marked left-hemisphere asymmetry in most humans.

Project Function:
    Processes complex auditory patterns including:
    - Speech rhythm analysis
    - Prosodic feature extraction
    - Musical sequence processing
    - Temporal pattern recognition
"""

import logging
from typing import Dict, List, Any
from ..AuditoryCortex.belt_area import BeltArea

class AuditoryPatternProcessor:
    """
    Processes complex temporal patterns in auditory input,
    specializing in speech and musical sequences.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.belt_area = BeltArea()
        self.working_memory: List[Dict[str, Any]] = []
        
    async def analyze_speech_rhythm(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Analyze rhythmic patterns in speech
        
        Args:
            audio_data: Processed audio input
            
        Returns:
            Dict containing rhythm analysis results
        """
        # Get complex features from belt area first
        complex_features = await self.belt_area.process_complex_features(audio_data)
        # Process rhythmic patterns
        pass
        
    async def process_prosodic_features(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Extract and analyze prosodic features of speech
        
        Args:
            audio_data: Audio input
            
        Returns:
            Dict containing prosody analysis
        """
        pass 
"""
Neurological Function:
    The Planum Temporale, located in the superior temporal gyrus posterior to 
    Heschl's gyrus, is crucial for:
    - Processing complex sound patterns
    - Speech sound analysis
    - Musical pattern processing
    - Phonological working memory
    It shows marked left-hemisphere asymmetry in most humans.

Project Function:
    Processes complex auditory patterns including:
    - Speech rhythm analysis
    - Prosodic feature extraction
    - Musical sequence processing
    - Temporal pattern recognition
"""

import logging
from typing import Dict, List, Any
from ..AuditoryCortex.belt_area import BeltArea

class PlanumTemporaleArea:
    """
    Processes complex temporal patterns in auditory input,
    specializing in speech and musical sequences.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.belt_area = BeltArea()
        self.working_memory: List[Dict[str, Any]] = [] 
"""
Neurological Function:
    Alerting Attention Network:
    - Vigilance maintenance
    - Arousal regulation
    - Warning signal processing
    - Readiness states
    - Temporal attention
    - Sustained attention
    - Alert state modulation

Potential Project Implementation:
    Could handle:
    - System alertness
    - Warning detection
    - Vigilance monitoring
    - State maintenance
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Association Nuclei of Thalamus integrate multiple processes:
    - Combines different sensory modalities
    - Links emotion and cognition
    - Coordinates memory retrieval
    - Manages executive function input
    - Facilitates learning and plasticity
    - Supports consciousness

Potential Project Implementation:
    Could handle:
    - Cross-modal integration
    - State coordination
    - System synchronization
    - Global workspace management
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Motor Relay Nuclei of Thalamus coordinate motor signals:
    - Processes motor feedback
    - Coordinates motor planning
    - Integrates cerebellar input
    - Modulates motor commands
    - Synchronizes motor timing
    - Facilitates motor learning

Potential Project Implementation:
    Could handle:
    - Motor command routing
    - Movement coordination
    - Timing synchronization
    - Motor feedback processing
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Thalamic Reticular Nucleus acts as attention gateway:
    - Controls thalamic sensory gating
    - Manages attention switching
    - Filters irrelevant information
    - Coordinates sleep-wake transitions
    - Modulates arousal states
    - Enhances relevant signals

Potential Project Implementation:
    Could handle:
    - Attention management
    - Signal prioritization
    - State transitions
    - Information gating
"""

# Implementation will be added when needed 
"""
Neurological Function:
    Sensory Relay Nuclei of Thalamus act as gateway for sensory information:
    - Filters incoming sensory signals
    - Routes information to appropriate cortical areas
    - Modulates attention and arousal
    - Coordinates sensory integration
    - Gates information flow based on relevance
    - Maintains sensory maps

Potential Project Implementation:
    Could handle:
    - Input routing and filtering
    - Signal priority management
    - Cross-modal coordination
    - Attention-based filtering
"""

# Implementation will be added when needed 
import socket
import json
import time

def test_connection():
    try:
        # Try to connect
        print(f"Connecting to 10.0.0.194:10001...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)  # Increased timeout
        s.connect(('10.0.0.194', 10001))
        print("Connected!")
        
        # First send a reset command
        reset_cmd = {
            "request_id": "sys_reset",
            "work_id": "sys",
            "action": "reset",
            "object": "None",
            "data": "None"
        }
        print(f"\nSending reset command: {json.dumps(reset_cmd)}")
        s.send((json.dumps(reset_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Reset response: {buffer.strip()}")
        
        # Test ping
        ping_cmd = {
            "request_id": "sys_ping",
            "work_id": "sys",
            "action": "ping",
            "object": "None",
            "data": "None"
        }
        print(f"\nSending ping command: {json.dumps(ping_cmd)}")
        s.send((json.dumps(ping_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Ping response: {buffer.strip()}")
        
        # Initialize the LLM
        setup_cmd = {
            "request_id": "llm_setup",
            "work_id": "llm.1000",
            "action": "setup",
            "object": "llm.utf-8.stream",
            "data": json.dumps({
                "system_message": "You are a helpful assistant.",
                "enkws": True,
                "model": "default",
                "enoutput": True,
                "version": "1.0",
                "max_token_len": 2048,
                "wake_word": "hey penphin"
            })
        }
        print(f"\nSending setup command: {json.dumps(setup_cmd)}")
        s.send((json.dumps(setup_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Setup response: {buffer.strip()}")
        
        # Try a simple inference 
        print("\n\nTrying inference command")
        infer_cmd = {
            "request_id": "llm_inference",
            "work_id": "llm.1000", 
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "delta": "Hello, how are you?",
                "index": 0,
                "finish": True
            }
        }
        print(f"Sending inference command: {json.dumps(infer_cmd)}")
        s.send((json.dumps(infer_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Inference response: {buffer.strip()}")
        
        s.close()
        print("\nConnection closed")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection() 
import socket
import json
import time
import paramiko

# LLM Device IP and Port
LLM_IP = "10.0.0.85"  # Your IP.14
    """Find the port where the LLM service is running"""
    print("\nChecking for LLM service port...")
    
    # First try to find the port from the process
    stdin, stdout, stderr = ssh.exec_command("lsof -i -P -n | grep llm_llm")
    for line in stdout:
        print(f"Found port info: {line.strip()}")
        # Look for port number in the output
        if ":" in line:
            port = line.split(":")[-1].split()[0
            print(f"Found LLM service port: {port}")
            return int(port)
    
    # If we couldn't find it through lsof, try netstat
    print("\nTrying netstat to find port...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tulpn | grep llm_llm")
    for line in stdout:
        print(f"Found port info: {line.strip()}")
        # Look for port number in the output
        if ":" in line:
            port = line.split(":")[-1].split()[0]
            print(f"Found LLM service port: {port}")
            return int(port)
    
    # If we still can't find it, try to get the port from the process arguments
    print("\nChecking process arguments...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep llm_llm")
    for line in stdout:
        if "llm_llm" in line and not "grep" in line:
            print(f"Found process: {line.strip()}")
            # Try to find port in process arguments
            if "--port" in line:
                port = line.split("--port")[1].split()[0]
                print(f"Found port in arguments: {port}")
                return int(port)
    
    # If we get here, try common ports
    print("\nTrying common ports...")
    common_ports = [8080, 80, 443, 5000, 8000, 3000, 10001]  # Added 10001 since it was in the listening ports
    for port in common_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((LLM_IP, port))
                if result == 0:
                    print(f"Port {port} is open and accepting connections")
                    return port
        except Exception as e:
            print(f"Error checking port {port}: {e}")
    
    raise Exception("Could not find LLM service port")

def send_command(command: dict, timeout: float = 5.0) -> dict:
    """Send a command to the LLM device and wait for response"""
    try:
        # First, use SSH to check if the LLM service is running
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"\nConnecting to {LLM_IP}:{LLM_PORT}...")
        ssh.connect(
            LLM_IP, 
            port=LLM_PORT, 
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
            timeout=timeout
        )
        
        # Find the LLM service port
        service_port = find_llm_port(ssh)
        print(f"\nFound LLM service on port {service_port}")
        
        # Now connect to the LLM service directly
        print(f"Connecting to LLM service on port {service_port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((LLM_IP, service_port))
            
            # Convert command to the format expected by the service
            if command["type"] == "LLM" and command["command"] == "generate":
                command_json = {
                    "request_id": command["data"]["request_id"],
                    "work_id": "llm",
                    "action": "inference",
                    "object": "llm.utf-8.stream",
                    "data": {
                        "delta": command["data"]["prompt"],
                        "index": 0,
                        "finish": True
                    }
                }
            else:
                command_json = command
            
            # Convert to string and send it
            command_str = json.dumps(command_json) + "\n"
            print(f"Sending command: {command_str.strip()}")
            s.sendall(command_str.encode())
            
            # Receive the response
            buffer = ""
            while True:
                try:
                    data = s.recv(1).decode()
                    if not data:
                        break
                    buffer += data
                    if data == "\n":
                        break
                except socket.timeout:
                    break
            
            print(f"Received response: {buffer.strip()}")
            try:
                return json.loads(buffer.strip())
            except json.JSONDecodeError:
                return {"error": "Failed to parse response", "raw": buffer.strip()}

    except paramiko.AuthenticationException:
        return {"error": "Authentication failed - check username and password"}
    except paramiko.SSHException as e:
        return {"error": f"SSH error: {str(e)}"}
    except ConnectionRefusedError:
        return {"error": "Connection refused - device may be offline or wrong port"}
    except socket.timeout:
        return {"error": "Connection timed out"}
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}
    finally:
        if 'ssh' in locals():
            ssh.close()

def test_ping():
    """Test basic connectivity with a ping command"""
    print("\n=== Testing Ping ===")
    ping_command = {
        "request_id": "sys_ping",
        "work_id": "sys",
        "action": "ping",
        "object": "None",
        "data": "None"
    }
    response = send_command(ping_command)
    print(f"Ping response: {response}")

def test_generate():
    """Test LLM generation with a simple prompt"""
    print("\n=== Testing Generate ===")
    prompt = "What is the capital of France?"
    generate_command = {
        "type": "LLM",
        "command": "generate",
        "data": {
            "prompt": prompt,
            "timestamp": int(time.time() * 1000),
            "version": "1.0",
            "request_id": f"generate_{int(time.time())}"
        }
    }
    response = send_command(generate_command)
    print(f"Generate response: {response}")

def main():
    """Main function"""
    while True:
        print("\n=== LLM Ethernet Test ===")
        print("1. Test Ping")
        print("2. Test Generate")
        print("3. Exit")
        
        try:
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == "1":
                test_ping()
            elif choice == "2":
                test_generate()
            elif choice == "3":
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please select 1-3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import serial
import json
import time
import subprocess

def setup_port():
    """Get the device port and set permissions"""
    # Get device info
    devices = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
    print("\nADB Devices List:")
    print(devices.stdout)
    
    if "axera-ax620e" not in devices.stdout:
        raise Exception("AX620e device not found")
    
    # Find available ports
    result = subprocess.run(
        ["adb", "shell", "ls -l /dev/tty*"],
        capture_output=True,
        text=True
    )
    print("\nAvailable ports:")
    print(result.stdout)
    
    # Set permissions for ttyS1
    port = "/dev/ttyS1"
    subprocess.run(["adb", "shell", f"chmod 666 {port}"])
    return port

def login_to_device(port: str):
    """Login to the device with default credentials"""
    print("\nAttempting to login...")
    
    # Configure port
    subprocess.run([
        "adb", "shell", 
        f"stty -F {port} 115200 cs8 -cstopb -parenb"
    ])
    
    # Send username
    print("Sending username...")
    subprocess.run([
        "adb", "shell",
        f"echo 'root' > {port}"
    ])
    time.sleep(1)
    
    # Send password
    print("Sending password...")
    subprocess.run([
        "adb", "shell",
        f"echo '123456' > {port}"
    ])
    time.sleep(1)
    
    # Read any response
    print("Checking login response...")
    subprocess.run([
        "adb", "shell",
        f"cat {port}"
    ])
    
    print("Login sequence completed")

def send_raw_command(command: str):
    """Send a raw command to the device"""
    # Convert to JSON if not already
    try:
        json.loads(command)
        json_data = command
    except json.JSONDecodeError:
        json_data = json.dumps({
            "type": "LLM",
            "command": "generate",
            "data": {
                "prompt": command,
                "timestamp": int(time.time() * 1000),
                "version": "1.0",
                "request_id": f"chat_{int(time.time())}"
            }
        })
    
    # Add newline if not present
    if not json_data.endswith("\n"):
        json_data += "\n"
    
    print(f"\nSending: {json_data.strip()}")
    subprocess.run(["adb", "shell", f"echo -n '{json_data}' > /dev/ttyS1"])
    
    # Read response
    print("\nResponse:")
    subprocess.run(["adb", "shell", "dd if=/dev/ttyS1 bs=1 count=1024 2>/dev/null"])

def main():
    """Main function"""
    try:
        port = setup_port()
        print(f"\nUsing port: {port}")
        
        # Login first
        login_to_device(port)
        
        print("\nEnter commands (type 'exit' to quit):")
        print("1. For raw JSON, start with '{'")
        print("2. For text prompts, just type normally")
        
        while True:
            command = input("\n> ").strip()
            if command.lower() == 'exit':
                break
            send_raw_command(command)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 
'''
#!/usr/bin/env python3
import subprocess
import json
import time
import sys
from typing import Dict, Any, Optional
import platform
import re
import serial.tools.list_ports
import serial
import os
import threading
import paramiko
import socket

# Constants
BAUD_RATE = 115200
MAX_RETRIES = 3
RETRY_DELAY = 1.0
WINDOWS_SERIAL_PATTERNS = [
    "m5stack",
    "m5 module",
    "m5module",
    "cp210x",
    "silicon labs"
]

class LLMInterface:
    """Interface for communicating with the LLM hardware"""
    
    def __init__(self, preferred_mode: str = None):
        """Initialize the LLM interface"""
        self.port = None
        self.connection_type = None
        self._initialized = False
        self._ser = None
        self.preferred_mode = preferred_mode  # Can be "serial", "adb", or None for auto-detect
        self.response_buffer = ""
        self.response_callback = None
        self._response_thread = None
        self._stop_thread = False
        
    def _start_response_thread(self):
        """Start thread to continuously read responses"""
        self._stop_thread = False
        self._response_thread = threading.Thread(target=self._read_responses)
        self._response_thread.daemon = True
        self._response_thread.start()

    def _stop_response_thread(self):
        """Stop the response reading thread"""
        self._stop_thread = True
        if self._response_thread:
            self._response_thread.join()

    def _read_responses(self):
        """Continuously read responses from the serial port"""
        while not self._stop_thread:
            if self.connection_type == "serial" and self._ser and self._ser.is_open:
                try:
                    if self._ser.in_waiting:
                        char = self._ser.read().decode('utf-8')
                        self.response_buffer += char
                        
                        # Check for complete JSON response
                        if char == '\n' and self.response_buffer.strip():
                            try:
                                response = json.loads(self.response_buffer.strip())
                                if self.response_callback:
                                    self.response_callback(response.get('data', ''))
                            except json.JSONDecodeError:
                                print(f"Error decoding JSON: {self.response_buffer}")
                            finally:
                                self.response_buffer = ""
                except Exception as e:
                    print(f"Error reading from serial: {e}")
            elif self.connection_type == "adb":
                try:
                    # Read one character at a time using ADB
                    read_result = subprocess.run(
                        ["adb", "shell", f"dd if={self.port} bs=1 count=1 iflag=nonblock 2>/dev/null"],
                        capture_output=True,
                        text=True
                    )
                    
                    if read_result.returncode == 0 and read_result.stdout:
                        char = read_result.stdout
                        self.response_buffer += char
                        
                        # Check for complete JSON response
                        if char == '\n' and self.response_buffer.strip():
                            try:
                                response = json.loads(self.response_buffer.strip())
                                if self.response_callback:
                                    self.response_callback(response.get('data', ''))
                            except json.JSONDecodeError:
                                print(f"Error decoding JSON: {self.response_buffer}")
                            finally:
                                self.response_buffer = ""
                except Exception as e:
                    print(f"Error reading from ADB: {e}")
            time.sleep(0.01)

    def parse_response(self, response_str: str) -> Dict[str, Any]:
        """Parse the response from the LLM hardware"""
        try:
            response = json.loads(response_str)
            
            # Check for error response
            if "error" in response:
                return {
                    "error": {
                        "code": response.get("error", {}).get("code", -1),
                        "message": response.get("error", {}).get("message", "Unknown error")
                    }
                }
            
            # Check for system response
            if response.get("work_id") == "sys":
                if response.get("action") == "ping":
                    return {
                        "status": "ok",
                        "message": "Ping successful"
                    }
                elif response.get("action") == "reset":
                    return {
                        "status": "ok",
                        "message": "Reset successful"
                    }
                elif response.get("action") == "setup":
                    return {
                        "status": "ok",
                        "message": "Setup successful"
                    }
            
            # Check for LLM response
            if response.get("work_id") == "llm":
                if response.get("action") == "inference":
                    # Handle streaming response format
                    response_data = {
                        "status": "ok",
                        "response": response.get("data", {}).get("delta", ""),
                        "finished": response.get("data", {}).get("finish", False),
                        "index": response.get("data", {}).get("index", 0)
                    }
                    if response_data["finished"]:
                        response_data["response"] += "\n"
                    return response_data
            
            # Unknown response type
            return {
                "error": {
                    "code": -1,
                    "message": f"Unknown response type: {response}"
                }
            }
            
        except json.JSONDecodeError:
            return {
                "error": {
                    "code": -1,
                    "message": f"Failed to parse response: {response_str}"
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -1,
                    "message": f"Error processing response: {str(e)}"
                }
            }

    def initialize(self) -> None:
        """Initialize the connection to the LLM hardware"""
        if self._initialized:
            print("Already initialized")
            return
            
        try:
            print("\n🔍 Initializing LLM interface...")
            print(f"Preferred mode: {self.preferred_mode if self.preferred_mode else 'auto-detect'}")
            
            # Try to find the device port based on preferred mode
            if self.preferred_mode == "wifi":
                print("Attempting WiFi connection...")
                wifi_ip = None
                
                # First try to get IP through ADB
                if self._is_adb_available():
                    print("Trying to get IP through ADB...")
                    result = subprocess.run(
                        ["adb", "shell", "ip addr show wlan0"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                        if ip_match:
                            wifi_ip = ip_match.group(1)
                            print(f"Found WiFi IP through ADB: {wifi_ip}")
                
                # If ADB lookup failed, use known IP
                if not wifi_ip:
                    print("Using known IP address...")
                    wifi_ip = "10.0.0.177"
                    print(f"Using WiFi IP: {wifi_ip}")
                
                # Use SSH to find the LLM service port
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(f"\nConnecting to {wifi_ip}:22...")
                ssh.connect(wifi_ip, port=22, username="root", password="123456")
                
                # Find the LLM service port
                service_port = self._find_llm_port(ssh)
                ssh.close()
                
                self.port = f"{wifi_ip}:{service_port}"  # Use IP:port format
                self.connection_type = "wifi"
                print(f"Found WiFi connection at {self.port}")
                self._initialized = True
                return
                    
            elif self.preferred_mode == "serial":
                print("Attempting serial connection...")
                if self._is_serial_available():
                    self.port = self._find_serial_port()
                    if self.port:
                        self.connection_type = "serial"
                        print(f"Found serial port: {self.port}")
                    else:
                        print("No suitable serial port found")
                else:
                    print("No serial ports available")
                    
            elif self.preferred_mode == "adb":
                print("Attempting ADB connection...")
                if self._is_adb_available():
                    self.port = self._find_adb_port()
                    if self.port:
                        self.connection_type = "adb"
                        print(f"Found ADB port: {self.port}")
                    else:
                        print("No suitable ADB port found")
                else:
                    print("ADB not available")
                    
            else:
                # Auto-detect mode
                print("Auto-detecting connection mode...")
                self.port = self._find_device_port()
                
            if not self.port:
                raise Exception("No suitable device port found")
                
            print(f"\nUsing {self.connection_type} mode with port {self.port}")
            
            # Initialize the connection
            if self.connection_type == "serial":
                print("Setting up serial connection...")
                print(f"Using baud rate: {BAUD_RATE}")
                
                try:
                self._ser = serial.Serial(
                    port=self.port,
                    baudrate=BAUD_RATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.1,
                    xonxoff=False,
                    rtscts=False,
                        dsrdtr=True  # Enable DTR for reset
                    )
                    
                    # Try to reset the device
                    print("Attempting device reset...")
                    self._ser.setDTR(False)
                    time.sleep(0.5)  # Longer delay for reset
                    self._ser.setDTR(True)
                    time.sleep(1.0)  # Give device time to stabilize
                    
                # Clear any existing data
                    print("Clearing any existing data...")
                while self._ser.in_waiting:
                        data = self._ser.read()
                        print(f"Cleared data: {data!r}")
                    
                    # Try a simple ping to test the connection
                    print("Testing connection...")
                    test_command = "AT\r\n"  # Simple AT command
                    self._ser.write(test_command.encode())
                    time.sleep(0.5)  # Give device time to respond
                    
                    if self._ser.in_waiting:
                        response = self._ser.read(self._ser.in_waiting)
                        print(f"Test response: {response!r}")
                    
                print("Serial connection established")
                    
                except Exception as e:
                    print(f"Error setting up serial connection: {e}")
                    if self._ser:
                        self._ser.close()
                        self._ser = None
                    raise
            
            # Start response thread
            self._start_response_thread()
            
            # Set initialized flag before sending commands
            self._initialized = True
            
            # 1. Check connection with ping
            print("\nSending initial ping command...")
            ping_command = {
                "type": "SYSTEM",
                "command": "ping",
                "data": {
                    "timestamp": int(time.time() * 1000),
                    "version": "1.0",
                    "request_id": "sys_ping",
                    "echo": True
                }
            }
            try:
                ping_result = self.send_command(ping_command)
                if not ping_result or "error" in ping_result:
                    print("Failed to ping device")
                    self._initialized = False
                    return
            except Exception as e:
                print(f"Error during ping: {e}")
                self._initialized = False
                return
            
            print(f"Successfully initialized {self.connection_type} connection to {self.port}")
            
        except Exception as e:
            print(f"Failed to initialize: {e}")
            self._initialized = False
            if self.connection_type == "adb":
                print("\nTrying to recover ADB connection...")
                try:
                    # Kill any existing ADB server
                    subprocess.run([self.adb_path, "kill-server"], capture_output=True, text=True)
                    time.sleep(1)
                    # Start new ADB server
                    subprocess.run([self.adb_path, "start-server"], capture_output=True, text=True)
                    time.sleep(2)
                    # Try initialization again
                    print("Retrying initialization...")
                    self.initialize()
                    return
                except Exception as retry_error:
                    print(f"Recovery failed: {retry_error}")
            
            raise

    def _find_device_port(self) -> Optional[str]:
        """Find the appropriate device port"""
        print("\nChecking for available connection methods...")
        
        # First try serial (preferred for direct connection)
        if self._is_serial_available():
            print("Found potential serial connection")
            serial_port = self._find_serial_port()
            if serial_port:
                print(f"Found valid serial port: {serial_port}")
                self.connection_type = "serial"
                return serial_port
                
        # Then try ADB
        if self._is_adb_available():
            print("Found ADB connection")
            adb_port = self._find_adb_port()
            if adb_port:
                print(f"Found valid ADB port: {adb_port}")
                self.connection_type = "adb"
                return adb_port
                
        print("No suitable connection method found")
        return None
        
    def _is_adb_available(self) -> bool:
        """Check if ADB is available"""
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            devices = result.stdout.strip().split("\n")[1:]
            return any(device.strip() and "device" in device for device in devices)
        except FileNotFoundError:
            return False
            
    def _is_serial_available(self) -> bool:
        """Check if serial connection is available"""
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("No serial ports found")
            return False
            
        print("\nAvailable serial ports:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")
            if port.vid is not None and port.pid is not None:
                print(f"    VID:PID: {port.vid:04x}:{port.pid:04x}")
            print(f"    Hardware ID: {port.hwid}")
            
        return bool(ports)
        
    def _find_adb_port(self) -> Optional[str]:
        """Find the device port through ADB"""
        try:
            # Try to get the port through device properties
            result = subprocess.run(
                ["adb", "shell", "ls -l /dev/tty*"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if "ttyS" in line and "dialout" in line:
                        port_match = re.search(r'/dev/ttyS\d+', line)
                        if port_match:
                            return port_match.group(0)
            
            # Try ttyUSB or ttyACM
            result = subprocess.run(
                ["adb", "shell", "ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.split('\n'):
                    if "ttyUSB" in line or "ttyACM" in line:
                        port_match = re.search(r'/dev/tty(USB|ACM)\d+', line)
                        if port_match:
                            return port_match.group(0)
                            
        except Exception as e:
            print(f"Error finding ADB port: {e}")
    
        return None
    
    def _find_serial_port(self) -> Optional[str]:
        """Find the device port through serial"""
        if platform.system() == "Windows":
            ports = serial.tools.list_ports.comports()
            
            print("\nChecking all available ports...")
            for port in ports:
                print(f"\nChecking port: {port.device}")
                print(f"Description: {port.description}")
                    if port.vid is not None and port.pid is not None:
                        print(f"VID:PID: {port.vid:04x}:{port.pid:04x}")
                    print(f"Hardware ID: {port.hwid}")
                
                # Check for CH340 device (VID:PID = 1A86:7523)
                if port.vid == 0x1A86 and port.pid == 0x7523:
                    print(f"\nFound CH340 device on port: {port.device}")
                    return port.device
                    
                # Check for M5Stack USB device patterns
                if any(pattern.lower() in port.description.lower() for pattern in WINDOWS_SERIAL_PATTERNS):
                    print(f"\nFound matching device pattern on port: {port.device}")
                    return port.device
                    
                # Check for any USB CDC device
                if "USB" in port.description.upper() and "CDC" in port.description.upper():
                    print(f"\nFound USB CDC device on port: {port.device}")
                    return port.device
                
                # If we get here and haven't found a match, but it's a CH340 device,
                # return it anyway (some Windows systems might not report the VID/PID correctly)
                if "CH340" in port.description.upper():
                    print(f"\nFound CH340 device by description on port: {port.device}")
                    return port.device
            
            print("\nNo suitable serial port found")
            return None
            
        return None
        
    def send_command(self, command: Dict[str, Any], timeout: float = 1.0) -> Dict[str, Any]:
        """Send a command to the LLM hardware"""
        if not self._initialized:
            raise RuntimeError("LLM interface not initialized")
            
        # Convert to simpler command structure like M5Module-LLM
        if command["type"] == "SYSTEM":
            if command["command"] == "ping":
                # Use exact same format as M5Module-LLM
                command_json = json.dumps({
                    "request_id": "sys_ping",  # Fixed request_id for ping
                    "work_id": "sys",
                    "action": "ping",
                    "object": "None",
                    "data": "None"
                }) + "\n"
            elif command["command"] == "reset":
                command_json = json.dumps({
                    "request_id": "sys_reset",  # Fixed request_id for reset
                    "work_id": "sys",
                    "action": "reset",
                    "object": "None",
                    "data": "None"
                }) + "\n"
            elif command["command"] == "setup":
                command_json = json.dumps({
                    "request_id": "sys_setup",  # Fixed request_id for setup
                    "work_id": "llm",
                    "action": "setup",
                    "object": "None",
                    "data": json.dumps({"max_token_len": command["data"]["max_token_len"]})
                }) + "\n"
            else:
                raise ValueError(f"Unsupported system command: {command['command']}")
        elif command["type"] == "LLM" and command["command"] == "generate":
            # Match M5Module-LLM inference format exactly
            command_json = json.dumps({
                "request_id": command["data"].get("request_id", "generate"),
                "work_id": "llm",
                "action": "inference",
                "object": "llm.utf-8.stream",
                "data": {
                    "delta": command["data"]["prompt"],
                    "index": 0,
                    "finish": True
                }
            }) + "\n"
        else:
            raise ValueError(f"Unsupported command type: {command['type']}")
            
        print(f"\nSending command: {command_json.strip()}")
        
        try:
            if self.connection_type == "wifi":
                print("📡 Using WiFi mode")
                # Parse IP and port from self.port
                ip, port = self.port.split(":")
                port = int(port)
                
                # Connect to the LLM service
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(timeout)
                    print(f"Connecting to {ip}:{port}...")
                    s.connect((ip, port))
                    print("Connected successfully")
                    
                    # Send command
                    print("Sending command...")
                    print(f"Command bytes: {command_json.encode()}")
                    s.sendall(command_json.encode())
                    print("Command sent successfully")
                    
                    # Wait for response
                    buffer = ""
                    print("Waiting for response...")
                    while True:
                        try:
                            data = s.recv(1).decode()
                            if not data:
                                print("No more data received")
                                break
                            buffer += data
                            print(f"Received byte: {data!r}")
                            if data == "\n":
                                print("Received newline, ending read")
                                break
                        except socket.timeout:
                            print("Socket timeout")
                            break
                    
                    print(f"Received response: {buffer.strip()}")
                    try:
                        return json.loads(buffer.strip())
                    except json.JSONDecodeError:
                        print(f"Failed to parse JSON: {buffer.strip()}")
                        return {"error": "Failed to parse response", "raw": buffer.strip()}
                        
            elif self.connection_type == "serial":
                print("🔌 Using Serial mode")
                if not self._ser:
                    raise Exception("Serial connection not initialized")
                    
                # Clear any existing data first
                print("Clearing any existing data...")
                while self._ser.in_waiting:
                    data = self._ser.read()
                    print(f"Cleared data: {data!r}")
                    
                # Write command
                print("Writing command...")
                self._ser.write(command_json.encode())
                print("Command written successfully")
                
                # Wait for response with more detailed debugging
                start_time = time.time()
                buffer = ""
                got_message = False
                last_data_time = time.time()
                
                print("\nWaiting for response...")
                try:
                    while True:
                        if self._ser.in_waiting:
                            char = self._ser.read(1)
                            print(f"Received byte: {char!r}")
                            try:
                                char_decoded = char.decode('utf-8')
                                buffer += char_decoded
                                got_message = True
                                last_data_time = time.time()
                                print(f"Current buffer: {buffer!r}")
                                
                                # Return immediately if we see a newline
                                if char_decoded == "\n":
                                    response = buffer.strip()
                                    print(f"Complete message: {response}")
                                    return self.parse_response(response)
                            except UnicodeDecodeError:
                                print(f"Failed to decode byte: {char!r}")
                        
                        # Check if we have a complete message (50ms without new data)
                        if got_message and time.time() - last_data_time > 0.05:
                            if buffer:
                                response = buffer.strip()
                                print(f"End of message detected: {response}")
                                return self.parse_response(response)
                            break
                        
                        # Check for timeout
                        if time.time() - start_time > timeout:
                            print(f"Timeout waiting for response. Buffer: {buffer!r}")
                            return {
                                "error": {
                                    "code": -2,
                                    "message": "Timeout waiting for response"
                                }
                            }
                        
                        time.sleep(0.005)  # 5ms delay
                        
                except KeyboardInterrupt:
                    print("\nInterrupted by user")
                    raise  # Re-raise to be caught by outer try/except
                
            else:
                # Use ADB mode (USB or Wi-Fi)
                print("📡 Using ADB mode")
                
                # Configure port with recommended settings
                print("Configuring port with recommended settings...")
                setup_commands = [
                    f"stty -F {self.port} {BAUD_RATE} raw -echo -crtscts -ixon -ixoff -parodd -cstopb cs8"
                ]
                
                for cmd in setup_commands:
                    result = subprocess.run(
                        ["adb", "shell", cmd],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        print(f"Warning: Failed to run {cmd}: {result.stderr}")
                    else:
                        print(f"Successfully ran: {cmd}")
                
                # Clear any existing data first (like ModuleMsg::clearMsg)
                print("Clearing any existing data...")
                clear_result = subprocess.run(
                    ["adb", "shell", f"dd if={self.port} of=/dev/null bs=1 count=2048 iflag=nonblock 2>/dev/null"],
                    capture_output=True,
                    text=True
                )
                print(f"Clear result: {clear_result.stdout}")
                
                # Write command (like ModuleComm::sendCmd)
                print("Writing command to port...")
                write_result = subprocess.run(
                    ["adb", "shell", f"echo -n '{command_json}' > {self.port}"],
                    capture_output=True,
                    text=True
                )
                print(f"Write result: returncode={write_result.returncode}, stderr={write_result.stderr!r}")
                
                # Wait for response with proper timeout
                start_time = time.time()
                buffer = ""
                got_message = False
                last_data_time = time.time()
                
                while True:
                    # Read one character at a time
                    read_result = subprocess.run(
                        ["adb", "shell", f"dd if={self.port} bs=1 count=1 iflag=nonblock 2>/dev/null"],
                        capture_output=True,
                        text=True
                    )
                    
                    if read_result.returncode == 0 and read_result.stdout:
                        char = read_result.stdout
                        buffer += char
                        got_message = True
                        last_data_time = time.time()
                        print(f"Received char: {char!r}")
                        
                        # Return immediately if we see a newline
                        if char == "\n":
                            response = buffer.strip()
                            print(f"Complete message: {response}")
                            return self.parse_response(response)
                    
                    # Check if we have a complete message (50ms without new data)
                    if got_message and time.time() - last_data_time > 0.05:
                        if buffer:
                            response = buffer.strip()
                            print(f"End of message detected: {response}")
                            return self.parse_response(response)
                        break
                    
                    # Check for timeout (use 2000ms like M5Module-LLM)
                    if time.time() - start_time > 2.0:
                        print(f"Timeout waiting for response. Buffer: {buffer!r}")
                        return {
                            "error": {
                                "code": -2,
                                "message": "Timeout waiting for response"
                            }
                        }
                    
                    time.sleep(0.005)  # 5ms delay
                
        except Exception as e:
            print(f"Error sending command: {e}")
            return {"error": str(e)}

    def cleanup(self) -> None:
        """Clean up the connection"""
        self._stop_response_thread()
        if self._ser:
            self._ser.close()
            self._ser = None
        self._initialized = False
        self.response_buffer = ""
        self.response_callback = None
            
    def change_mode(self, new_mode: str) -> None:
        """Change the connection mode"""
        if new_mode not in ["serial", "adb"]:
            raise ValueError("Invalid mode. Use 'serial' or 'adb'")
            
        print(f"\nSwitching to {new_mode} mode...")
        
        # Clean up existing connection
        self.cleanup()
        
        # Try to find port in new mode
        if new_mode == "serial":
            if self._is_serial_available():
                self.port = self._find_serial_port()
                if self.port:
                    self.connection_type = "serial"
                    print(f"Found serial port: {self.port}")
                else:
                    raise Exception("No suitable serial port found")
            else:
                raise Exception("No serial ports available")
        else:  # adb
            if self._is_adb_available():
                self.port = self._find_adb_port()
                if self.port:
                    self.connection_type = "adb"
                    print(f"Found ADB port: {self.port}")
                else:
                    raise Exception("No suitable ADB port found")
            else:
                raise Exception("ADB not available")
                
        # Initialize new connection
        if self.connection_type == "serial":
            print("Setting up serial connection...")
            self._ser = serial.Serial(
                port=self.port,
                baudrate=BAUD_RATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            while self._ser.in_waiting:
                self._ser.read()
            print("Serial connection established")
            
        self._initialized = True
        print(f"Successfully switched to {self.connection_type} mode with port {self.port}")
        
        # Test the new connection
        print("\nTesting new connection...")
        ping_command = {
            "type": "SYSTEM",
            "command": "ping",
            "data": {
                "timestamp": int(time.time() * 1000),
                "version": "1.0",
                "request_id": "mode_switch_ping",
                "echo": True
            }
        }
        response = self.send_command(ping_command)
        print(f"Mode switch test response: {response}")

    def set_device_mode(self, mode: str) -> None:
        """Change the device's mode (serial, adb, or wifi)"""
        if mode not in ["serial", "adb", "wifi"]:
            raise ValueError("Invalid mode. Use 'serial', 'adb', or 'wifi'")
            
        print(f"\nSetting device to {mode} mode...")
        
        try:
            # Clean up current connection first
            self.cleanup()
            
            # For WiFi mode, we need to use a different approach
            if mode == "wifi":
                print("WiFi mode requires device to be in WiFi mode first")
                print("Please ensure the device is in WiFi mode before continuing")
                time.sleep(5)  # Give user time to switch device mode
                
                # Try to find WiFi port
                if self._is_adb_available():
                    # Try to find WiFi-specific port
                    result = subprocess.run(
                        ["adb", "shell", "ip addr show wlan0"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                        if ip_match:
                            wifi_ip = ip_match.group(1)
                            # Use SSH to find the LLM service port
                            ssh = paramiko.SSHClient()
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            ssh.connect(wifi_ip, port=22, username="root", password="123456")
                            
                            # Find the LLM service port
                            service_port = self._find_llm_port(ssh)
                            ssh.close()
                            
                            self.port = f"{wifi_ip}:{service_port}"  # Use IP:port format
                            self.connection_type = "wifi"
                            print(f"Found WiFi connection at {self.port}")
                        else:
                            raise Exception("No WiFi IP address found")
                    else:
                        raise Exception("Failed to get WiFi information")
                else:
                    raise Exception("ADB not available for WiFi mode")
                    
            else:
                # For Serial and ADB modes, wait for device to switch
                print("Waiting for device to switch modes...")
                time.sleep(5)  # Give device time to switch
                
                # Try to find port in new mode with retries
                max_retries = 3
                retry_delay = 2
                for attempt in range(max_retries):
                    print(f"\nAttempt {attempt + 1} to find port in {mode} mode...")
                    
                    if mode == "serial":
                        if self._is_serial_available():
                            self.port = self._find_serial_port()
                            if self.port:
                                self.connection_type = "serial"
                                print(f"Found serial port: {self.port}")
                                break
                            else:
                                print("No suitable serial port found")
                        else:
                            print("No serial ports available")
                    else:  # adb
                        if self._is_adb_available():
                            self.port = self._find_adb_port()
                            if self.port:
                                self.connection_type = "adb"
                                print(f"Found ADB port: {self.port}")
                                break
                            else:
                                print("No suitable ADB port found")
                        else:
                            print("ADB not available")
                    
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                
                if not self.port:
                    raise Exception(f"Failed to find port in {mode} mode after {max_retries} attempts")
            
            # Initialize new connection
            if self.connection_type == "serial":
                print("Setting up serial connection...")
                self._ser = serial.Serial(
                    port=self.port,
                    baudrate=BAUD_RATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False
                )
                while self._ser.in_waiting:
                    self._ser.read()
                print("Serial connection established")
            
            self._initialized = True
            print(f"Successfully switched to {self.connection_type} mode with port {self.port}")
            
            # Test the new mode with retries
            print("\nTesting new mode...")
            for attempt in range(max_retries):
                try:
                    ping_command = {
                        "type": "SYSTEM",
                        "command": "ping",
                        "data": {
                            "timestamp": int(time.time() * 1000),
                            "version": "1.0",
                            "request_id": "mode_switch_ping",
                            "echo": True
                        }
                    }
                    response = self.send_command(ping_command)
                    print(f"Mode switch test response: {response}")
                    break  # Success, exit retry loop
                except Exception as e:
                    print(f"Ping attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying ping in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        raise Exception(f"Failed to verify mode switch after {max_retries} attempts")
            
        except Exception as e:
            print(f"Error changing device mode: {e}")
            raise

    def _find_llm_port(self, ssh) -> int:
        """Find the port where the LLM service is running"""
        print("\nChecking for LLM service port...")
        
        # First try to find the port from the process
        stdin, stdout, stderr = ssh.exec_command("lsof -i -P -n | grep llm_llm")
        for line in stdout:
            print(f"Found port info: {line.strip()}")
            # Look for port number in the output
            if ":" in line:
                port = line.split(":")[-1].split()[0]
                print(f"Found LLM service port: {port}")
                return int(port)
        
        # If we couldn't find it through lsof, try netstat
        print("\nTrying netstat to find port...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tulpn | grep llm_llm")
        for line in stdout:
            print(f"Found port info: {line.strip()}")
            # Look for port number in the output
            if ":" in line:
                port = line.split(":")[-1].split()[0]
                print(f"Found LLM service port: {port}")
                return int(port)
        
        # If we still can't find it, try to get the port from the process arguments
        print("\nChecking process arguments...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep llm_llm")
        for line in stdout:
            if "llm_llm" in line and not "grep" in line:
                print(f"Found process: {line.strip()}")
                # Try to find port in process arguments
                if "--port" in line:
                    port = line.split("--port")[1].split()[0]
                    print(f"Found port in arguments: {port}")
                    return int(port)
        
        # If we get here, try common ports
        print("\nTrying common ports...")
        common_ports = [10001, 8080, 80, 443, 5000, 8000, 3000]  # Put 10001 first since we know it works
        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    # Get the IP from the SSH connection
                    ip = ssh.get_transport().getpeername()[0]
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        print(f"Port {port} is open and accepting connections")
                        return port
            except Exception as e:
                print(f"Error checking port {port}: {e}")
        
        raise Exception("Could not find LLM service port")

    def check_connection(self) -> bool:
        """Check connection like M5Module-LLM"""
        try:
            # Send ping command
            ping_command = {
                "type": "SYSTEM",
                "command": "ping",
                "data": {
                    "timestamp": int(time.time() * 1000),
                    "version": "1.0",
                    "request_id": "connection_check",
                    "echo": True
                }
            }
            response = self.send_command(ping_command)
            
            # Check for OK response
            if isinstance(response, dict) and response.get("error", {}).get("code") == 0:
                print("Connection check successful")
                return True
            else:
                print(f"Connection check failed: {response}")
                return False
                
        except Exception as e:
            print(f"Connection check error: {e}")
            return False

def main():
    """Main function"""
    try:
        # First ask for connection mode
        print("\n=== M5Module-LLM Connection Mode ===")
        print("1. Serial (direct USB)")
        print("2. ADB (Android Debug Bridge)")
        print("3. WiFi")
        
        while True:
            try:
                mode_choice = input("\nSelect connection mode (1-3): ").strip()
                if mode_choice == "1":
                    preferred_mode = "serial"
                    break
                elif mode_choice == "2":
                    preferred_mode = "adb"
                    break
                elif mode_choice == "3":
                    preferred_mode = "wifi"
                    break
                else:
                    print("\n❌ Invalid choice. Please select 1-3.")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
        
        # Initialize with preferred mode
        print(f"\n🔍 Initializing in {preferred_mode} mode...")
        llm = LLMInterface(preferred_mode=preferred_mode)
        llm.initialize()
        current_mode = llm.connection_type or "auto-detect"
        
        while True:
            try:
            print("\n=== M5Module-LLM Interface ===")
            print("1. Send ping command")
            print("2. Generate text")
            print("3. Change connection mode")
            print("4. Exit")
            
                choice = input("\nSelect an option (1-4): ").strip()
                
                if choice == "1":
                    print("\n📡 Sending ping command...")
                    ping_command = {
                        "type": "SYSTEM",
                        "command": "ping",
                        "data": {
                            "timestamp": int(time.time() * 1000),
                            "version": "1.0",
                            "request_id": "ping_test",
                            "echo": True
                        }
                    }
                    try:
                    response = llm.send_command(ping_command)
                    print(f"Ping response: {response}")
                    except KeyboardInterrupt:
                        print("\nPing command interrupted by user")
                        continue
                    
                elif choice == "2":
                    prompt = input("\n💭 Enter your prompt: ").strip()
                    if prompt:
                        print("\n🤖 Generating response...")
                        command = {
                            "type": "LLM",
                            "command": "generate",
                            "data": {
                                "prompt": prompt,
                                "timestamp": int(time.time() * 1000),
                                "version": "1.0",
                                "request_id": f"generate_{int(time.time())}"
                            }
                        }
                        try:
                        response = llm.send_command(command)
                        print(f"\nResponse: {response}")
                        except KeyboardInterrupt:
                            print("\nGenerate command interrupted by user")
                            continue
                    
                elif choice == "3":
                    print("\n🔄 Available connection modes:")
                    print(f"1. Serial (direct USB) {' (CURRENT)' if current_mode == 'serial' else ''}")
                    print(f"2. ADB (Android Debug Bridge) {' (CURRENT)' if current_mode == 'adb' else ''}")
                    print(f"3. WiFi {' (CURRENT)' if current_mode == 'wifi' else ''}")
                    
                    mode_choice = input("\nSelect mode (1-3): ").strip()
                    if mode_choice == "1":
                        new_mode = "serial"
                    elif mode_choice == "2":
                        new_mode = "adb"
                    elif mode_choice == "3":
                        new_mode = "wifi"
                    else:
                        print("Invalid mode selection")
                        continue
                        
                    if new_mode != current_mode:
                        print(f"\n🔄 Switching to {new_mode} mode...")
                        try:
                            llm.set_device_mode(new_mode)
                            current_mode = new_mode
                            print(f"✅ Successfully switched to {new_mode} mode")
                        except Exception as e:
                            print(f"❌ Error switching mode: {e}")
                    else:
                        print(f"\nAlready in {current_mode} mode")
                    
                elif choice == "4":
                    print("\n👋 Goodbye!")
                    break
                    
                else:
                    print("\n❌ Invalid choice. Please select 1-4.")
                    
            except KeyboardInterrupt:
                print("\nOperation interrupted by user")
                continue
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Returning to main menu...")
                continue
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        if 'llm' in locals():
            llm.cleanup()

if __name__ == "__main__":
    main() '''
import os
import subprocess
import serial
import json
import time

# Constants
SERIAL_PORT = "/dev/ttyUSB0"  # Change if necessary
BAUD_RATE = 115200
ADB_IP = "192.168.1.100"  # Change to your device's IP

def is_adb_available():
    """Check if an ADB device is connected via USB or Wi-Fi."""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        devices = result.stdout.strip().split("\n")[1:]  # Ignore header
        return any(device.strip() and "device" in device for device in devices)
    except FileNotFoundError:
        return False  # ADB not installed

def is_serial_available():
    """Check if the Serial device is connected."""
    return os.path.exists(SERIAL_PORT)

def send_command(command):
    """Unified function to send a JSON command over ADB (USB/Wi-Fi) or Serial."""
    command_json = json.dumps(command)

    if is_adb_available():
        # Use ADB mode (USB or Wi-Fi)
        print("📡 Using ADB mode")
        try:
            adb_command = f"adb shell 'echo {command_json}'"
            result = subprocess.run(adb_command, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"ADB Error: {e}"

    elif is_serial_available():
        # Use Serial mode
        print("🔌 Using Serial mode")
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                ser.write(command_json.encode() + b'\n')
                time.sleep(0.5)  # Wait for response
                response = ser.readline().decode().strip()
                return response
        except Exception as e:
            return f"Serial Error: {e}"
    
    else:
        return "❌ No connection available"

# Example JSON Command
command_to_send = {"cmd": "set_mode", "mode": "active"}

# Send the command using the best available transport
response = send_command(command_to_send)
print("Response:", response)
import serial
import time

ser = serial.Serial('COM', 115200, timeout=1)

ser.write(b'{"request_id":"ping","action":"ping"}\n')

time.sleep(1)

response = ser.read_all()
print("Response:", response)

ser.close()
import socket
import json
import time

def test_connection():
    try:
        # Try to connect
        print(f"Connecting to 10.0.0.194:10001...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)  # Increased timeout
        s.connect(('10.0.0.194', 10001))
        print("Connected!")
        
        # Initialize the LLM with setup parameters
        init_cmd = {
            "request_id": "sys_setup",
            "work_id": "sys",
            "action": "setup",
            "object": "None",
            "data": json.dumps({
                "system_message": "You are a helpful assistant.",
                "enkws": True,
                "model": "default",
                "enoutput": True,
                "version": "1.0",
                "max_token_len": 2048,
                "wake_word": "hey penphin"
            })
        }
        print(f"\nSending setup: {json.dumps(init_cmd)}")
        s.send((json.dumps(init_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                print(f"Received byte: {data!r}")
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Setup response: {buffer.strip()}")
        
        # First try a ping command
        ping_cmd = {
            "request_id": "sys_ping",
            "work_id": "sys",
            "action": "ping",
            "object": "None",
            "data": {}
        }
        print(f"\nSending ping: {json.dumps(ping_cmd)}")
        s.send((json.dumps(ping_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                print(f"Received byte: {data!r}")
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Ping response: {buffer.strip()}")
        
        # Now try an inference command
        print("\n\nTrying inference command")
        time.sleep(1)
        
        # Send an inference command
        infer_cmd = {
            "request_id": "test_inference",
            "work_id": "llm", 
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "text": "Hello, how are you?",
                "index": 0,
                "finish": True
            }
        }
        print(f"Sending inference command: {json.dumps(infer_cmd)}")
        s.send((json.dumps(infer_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                print(f"Received byte: {data!r}")
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Inference response: {buffer.strip()}")
        
        # Try alternative command format - using delta instead of text
        print("\n\nTrying alternative command format")
        time.sleep(1)
        
        alt_cmd = {
            "request_id": "test_alt",
            "work_id": "llm",
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "delta": "Alternative format test",
                "index": 0,
                "finish": True
            }
        }
        print(f"Sending alternative command: {json.dumps(alt_cmd)}")
        s.send((json.dumps(alt_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                print(f"Received byte: {data!r}")
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Alternative response: {buffer.strip()}")
        
        s.close()
        print("\nConnection closed")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection() 
import socket
import json
import time

def test_llm_service():
    # Connect to the service
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('10.0.0.177', 10001))
    
    # First send setup command
    setup = {
        "request_id": "sys_setup",
        "work_id": "llm",
        "action": "setup",
        "object": "None",
        "data": json.dumps({"max_token_len": 2048})
    }
    print("\nSending setup command:")
    print(f"Sending: {json.dumps(setup)}")
    s.send((json.dumps(setup) + "\n").encode())
    response = s.recv(1024).decode()
    print(f"Setup response: {response}")
    
    # Test 1: Send a command with proper request_id format
    test1 = {
        "request_id": "generate",  # Use fixed request_id like prototype
        "work_id": "llm",
        "action": "inference",
        "object": "llm.utf-8.stream",
        "data": {
            "delta": "hi",
            "index": 0,
            "finish": True
        }
    }
    print("\nTest 1 - Command with proper request_id:")
    print(f"Sending: {json.dumps(test1)}")
    s.send((json.dumps(test1) + "\n").encode())
    
    # Read response byte by byte
    buffer = ""
    while True:
        try:
            data = s.recv(1).decode()
            if not data:
                print("No more data received")
                break
            buffer += data
            print(f"Received byte: {data!r}")
            if data == "\n":
                print("Received newline, ending read")
                break
        except socket.timeout:
            print("Socket timeout")
            break
    print(f"Full response: {buffer.strip()}")
    
    # Test 2: Send command with longer prompt
    test2 = {
        "request_id": "generate",
        "work_id": "llm",
        "action": "inference",
        "object": "llm.utf-8.stream",
        "data": {
            "delta": "Hello, how are you today?",
            "index": 0,
            "finish": True
        }
    }
    print("\nTest 2 - Longer prompt:")
    print(f"Sending: {json.dumps(test2)}")
    s.send((json.dumps(test2) + "\n").encode())
    
    # Read response byte by byte
    buffer = ""
    while True:
        try:
            data = s.recv(1).decode()
            if not data:
                print("No more data received")
                break
            buffer += data
            print(f"Received byte: {data!r}")
            if data == "\n":
                print("Received newline, ending read")
                break
        except socket.timeout:
            print("Socket timeout")
            break
    print(f"Full response: {buffer.strip()}")
    
    # Test 3: Send command with streaming disabled
    test3 = {
        "request_id": "generate",
        "work_id": "llm",
        "action": "inference",
        "object": "llm.utf-8",  # No .stream suffix
        "data": {
            "delta": "hi",
            "index": 0,
            "finish": True
        }
    }
    print("\nTest 3 - Streaming disabled:")
    print(f"Sending: {json.dumps(test3)}")
    s.send((json.dumps(test3) + "\n").encode())
    
    # Read response byte by byte
    buffer = ""
    while True:
        try:
            data = s.recv(1).decode()
            if not data:
                print("No more data received")
                break
            buffer += data
            print(f"Received byte: {data!r}")
            if data == "\n":
                print("Received newline, ending read")
                break
        except socket.timeout:
            print("Socket timeout")
            break
    print(f"Full response: {buffer.strip()}")
    
    s.close()

if __name__ == "__main__":
    test_llm_service() 
import time
import random
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

# === MATRIX CONFIG ===
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'
options.brightness = 30
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)

# === GAME CONFIG ===
WIDTH, HEIGHT = 64, 64
grid = [[random.randint(0, 1) for _ in range(WIDTH)] for _ in range(HEIGHT)]

def count_neighbors(x, y):
    return sum(
        grid[(y + dy) % HEIGHT][(x + dx) % WIDTH]
        for dy in [-1, 0, 1]
        for dx in [-1, 0, 1]
        if not (dx == 0 and dy == 0)
    )

def update_grid():
    global grid
    new_grid = [[0]*WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            neighbors = count_neighbors(x, y)
            if grid[y][x] == 1:
                new_grid[y][x] = 1 if neighbors in [2, 3] else 0
            else:
                new_grid[y][x] = 1 if neighbors == 3 else 0
    grid = new_grid

def draw_grid():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if grid[y][x]:
                fitness = count_neighbors(x, y)  # 👈 basic "fitness" proxy
                color = (0, min(255, fitness * 40), 255 - fitness * 20)
                pixels[x, y] = color
    matrix.SetImage(image)

# === MAIN LOOP ===
try:
    while True:
        draw_grid()
        update_grid()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
    matrix.Clear()
