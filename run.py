"""
Main entry point for PenphinMind system
"""

import argparse
import asyncio
import logging
import sys
import signal
import os
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import subprocess
import json
from PIL import Image, ImageDraw

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

from Mind.mind import Mind, setup_connection
from config import CONFIG  # Use absolute import
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from menu_system import clear_screen, run_menu_system
from Mind.Subcortex.transport_layer import run_adb_command, get_transport, BaseTransport

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
    
    def __init__(self, mind_id=None, persona="You are a helpful assistant."):
        self.logger = logger
        self.running = False
        # Ensure persona is provided
        if not persona:
            self.logger.warning("Empty persona provided, using default")
            persona = "You are a helpful assistant."
        self.mind = Mind(mind_id, persona)
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
    was_initialized = False
    splash_manager = None
    
    try:
        logger.info("Starting interactive menu system...")
        
        # Initialize auditory capabilities FIRST for testing hardware audio
        brain_mode = SynapticPathways._brain_mode
        if brain_mode in ["full", "ac"]:
            logger.info(f"Running in {brain_mode} mode with auditory capabilities...")
            try:
                # Ensure mind is initialized for basic functionality
                if not mind._initialized:
                    logger.info("Initializing basic mind capabilities...")
                    await mind.initialize(auditory_only=True)  # Only initialize basic components
                
                # Play a simple sine wave test using aplay BEFORE any visual initialization
                logger.info("Running audio test before visual initialization...")
                try:
                    # First test using speaker-test with a sine wave
                    import os
                    audio_test_cmd = "speaker-test -D plughw:0,0 -t sine -f 1000 -c 2 -l 1"
                    logger.info(f"Running audio test command: {audio_test_cmd}")
                    os.system(audio_test_cmd)
                    logger.info("Audio hardware test completed")
                    
                    # Additionally try using the auditory cortex if available
                    if "auditory" in mind.temporal_lobe:
                        logger.info("Testing audio through auditory cortex...")
                        auditory_cortex = mind.temporal_lobe["auditory"]
                        
                        # Play a test sound if available
                        try:
                            from Mind.TemporalLobe.SuperiorTemporalGyrus.AuditoryCortex.audio_playback_utils import play_sound
                            # Test with both direct audio play and fallback
                            play_sound("front_center_fixed.wav")
                            logger.info("Audio test through cortex completed")
                        except Exception as audio_err:
                            logger.error(f"Error during cortex audio test: {audio_err}")
                            # Non-fatal, continue with initialization
                    else:
                        logger.warning("Auditory cortex component not found in temporal lobe")
                except Exception as e:
                    logger.error(f"Error during audio test: {e}")
                    # Continue despite audio errors - don't block initialization
            except Exception as e:
                logger.error(f"Error initializing auditory capabilities: {e}", exc_info=True)
                # Continue despite errors to allow visual to initialize
        
        # NOW initialize visual capabilities after audio test
        if brain_mode in ["full", "vc"]:
            logger.info(f"Running in {brain_mode} mode with visual capabilities...")
            try:
                # Ensure mind is fully initialized for basic functionality
                if not mind._initialized:
                    logger.info("Initializing basic mind capabilities...")
                    await mind.initialize(visual_only=True)  # Only initialize basic components
                
                # Initialize visual cortex for splash screen BEFORE connection
                if "visual" in mind.occipital_lobe:
                    logger.info("Accessing visual cortex for splash screen...")
                    visual_cortex = mind.occipital_lobe["visual"]
                    
                    # Initialize the primary visual area first
                    logger.info("Initializing primary visual area...")
                    if hasattr(visual_cortex, 'primary_area'):
                        try:
                            if not visual_cortex.primary_area._initialized:
                                logger.info("Primary visual area not initialized, initializing now...")
                                await visual_cortex.primary_area.initialize()
                                logger.info(f"Primary visual area initialized: {visual_cortex.primary_area._initialized}")
                                
                                # Get splash manager if available
                                if hasattr(visual_cortex, 'splash_manager') and visual_cortex.splash_manager:
                                    splash_manager = visual_cortex.splash_manager
                                    logger.info("Found existing splash manager in visual cortex")
                                else:
                                    # Initialize a new splash manager
                                    from Mind.OccipitalLobe.VisualCortex.splash_screen import SplashScreenManager
                                    splash_manager = SplashScreenManager(visual_cortex.primary_area)
                                    logger.info("Created new splash manager")
                                
                                # Initial splash screen immediately after primary area initialization
                                if visual_cortex.primary_area._initialized:
                                    # Show splash screen and start loading animation
                                    logger.info("Showing startup splash screen...")
                                    if splash_manager:
                                        await splash_manager.show_startup_splash(duration=2.0)
                                        await splash_manager.start_loading_animation("Initializing systems...")
                                        # Signal visual_init event
                                        await splash_manager.handle_event("visual_init")
                                    else:
                                        # Fallback to old method
                                        await visual_cortex.show_splash_screen()
                        except Exception as e:
                            logger.error(f"Error initializing primary visual area: {e}")
                    else:
                        logger.error("Primary visual area not found")
                else:
                    logger.error("Visual cortex component not found in occipital lobe")
            except Exception as e:
                logger.error(f"Error initializing visual capabilities: {e}", exc_info=True)
        
        # Signal matrix initialization
        if splash_manager:
            await splash_manager.handle_event("matrix_init")
        
        # NOW establish connection after splash screen is showing
        if connection_type:
            logger.info(f"Initializing connection with type: {connection_type}")
            # Use Mind to establish connection
            result = await mind.connect(connection_type)
            was_initialized = result
            
            # Signal connection event
            if splash_manager:
                await splash_manager.handle_event("connection")
                
        else:
            # Try to auto-detect connection from mind config
            logger.info("Using connection from mind configuration...")
            # Use Mind to establish connection with config
            result = await mind.connect()
            was_initialized = result
            
            # Signal connection event
            if splash_manager:
                await splash_manager.handle_event("connection")
            
        # Signal synaptic pathways initialized
        if splash_manager:
            await splash_manager.handle_event("synaptic_init")
            
        # Complete mind initialization now that connection is established
        if brain_mode in ["full", "vc"]:
            try:
                # Complete full mind initialization
                logger.info("Completing full mind initialization...")
                await mind.initialize(complete=True)
                
                # Signal neural networks initialized
                if splash_manager:
                    await splash_manager.handle_event("neural_init")
                
                # Signal mind processes initialized
                if splash_manager:
                    await splash_manager.handle_event("mind_init")
                    
                # Update the splash screen to indicate completion
                if "visual" in mind.occipital_lobe:
                    visual_cortex = mind.occipital_lobe["visual"]
                    
                    # Signal completion
                    if splash_manager:
                        await splash_manager.handle_event("complete")
                    
                    # Test pattern after full initialization
                    if hasattr(visual_cortex, 'primary_area') and visual_cortex.primary_area._initialized:
                        logger.info("Verifying matrix with test pattern after full initialization...")
                        test_result = await visual_cortex.primary_area.test_pattern()
                        if test_result:
                            logger.info("Test pattern displayed successfully!")
                            # Sleep briefly to show the test pattern
                            await asyncio.sleep(1)
                        else:
                            logger.error("Failed to display test pattern on matrix")
            except Exception as e:
                logger.error(f"Error completing mind initialization: {e}", exc_info=True)
        
        # Run the menu system with the Mind instance
        await run_menu_system(mind)
        
    except Exception as e:
        logger.error(f"Menu system error: {e}")
    finally:
        # Only clean up if we initialized here
        if was_initialized:
            logger.info("Cleaning up after menu system...")
            await mind.cleanup()

def load_available_minds():
    """Load list of available minds from minds_config.json"""
    from Mind.mind_config import get_available_minds
    return get_available_minds()

def parse_args():
    """Parse command line arguments"""
    # Get available minds for argument choices
    available_minds = load_available_minds()
    
    parser = argparse.ArgumentParser(
        description="""PenphinMind - A Neuromorphic AI System

This system implements a bicameral mind architecture with various neural subsystems:
- Visual Cortex (vc): LED Matrix and visual processing
- Auditory Cortex (ac): Audio processing and speech
- Frontal Cortex (fc): Language processing and LLM with interactive menu
- Full Mind (full): Complete system integration

If no mode is specified, the system defaults to the full mode.
Each mode provides direct interaction with its respective subsystem.""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--mode',
        choices=['vc', 'ac', 'fc', 'full'],
        default='full',  # Default to full mode
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
        
  full - Full Mind (Default)
        Run the complete system
        Example: python run.py --mode full"""
    )
    
    parser.add_argument(
        '--connection',
        choices=['serial', 'adb', 'tcp'],
        help="""Select connection mode (Note: mostly redundant as connection is set in minds_config.json):
serial - Direct USB connection
adb    - Android Debug Bridge
tcp    - TCP/IP network connection"""
    )
    
    parser.add_argument(
        '--mind',
        choices=available_minds if available_minds else None,
        help="""Select which mind configuration to use from minds_config.json.
Available mind configurations: {}""".format(", ".join(available_minds) if available_minds else "None")
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help="""Enable debug logging for detailed system information.
This will show all debug messages and system state changes."""
    )
    
    parser.add_argument(
        '--show-json',
        action='store_true',
        help="""Enable raw JSON logging for network communication.
This will show all JSON requests and responses between components."""
    )
    
    parser.add_argument(
        '--persona',
        type=str,
        help="""Specify the persona for the mind.
This defines the behavior and personality of the AI.
Example: python run.py --persona "You are a friendly assistant with a sense of humor."
"""
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
    
    # Set SystemJournelingManager debug level
    if args.debug:
        journaling_manager = SystemJournelingManager()
        journaling_manager.setLevel(SystemJournelingLevel.DEBUG)
        print("Debug logging enabled - all system transactions will be visible")
    
    # Set JSON logging if requested
    if args.show_json:
        journaling_manager = SystemJournelingManager()
        journaling_manager.setLevel(SystemJournelingLevel.DEBUG)
        
        # Update CONFIG.log_level to ensure all components log at DEBUG level
        CONFIG.log_level = "DEBUG"
        
        # Also modify transport layer to make JSON visible
        # Make _log_transport_json always print to console
        original_log_method = BaseTransport._log_transport_json
        def enhanced_log_json(self, direction, data, transport_type=None):
            # Call original method
            original_log_method(self, direction, data, transport_type)
            # Also print to console
            if isinstance(data, dict):
                import json
                data_str = json.dumps(data, indent=2)
            else:
                data_str = str(data)
            
            print(f"\n{'='*40}")
            print(f"🔍 {direction} JSON via {transport_type or self.__class__.__name__}")
            print(f"{'='*40}")
            print(data_str)
            print(f"{'='*40}\n")
        
        # Replace the method
        BaseTransport._log_transport_json = enhanced_log_json
        print("Enhanced JSON logging enabled - all transport messages will be displayed")
    
    try:
        # Set mode in SynapticPathways
        # If no mode specified, default to 'full'
        if args.mode:
            mode = args.mode
        else:
            mode = 'full'
            logger.info("No mode specified, defaulting to 'full' mode")
        
        SynapticPathways.set_mode(mode)
        
        # Create PenphinMind instance with selected mind or mind selection menu
        selected_mind_id = args.mind
        if selected_mind_id:
            from Mind.mind_config import get_mind_by_id
            mind_config = get_mind_by_id(selected_mind_id)
            print(f"\n🧠 Using mind: {mind_config['name']} ({selected_mind_id})")
            print(f"   Connection: {mind_config['connection']['type'].upper()} - {mind_config['connection']['ip']}:{mind_config['connection']['port']}")
            
            # Get persona from mind config's llm section
            persona = None
            if "llm" in mind_config and "persona" in mind_config["llm"]:
                persona = mind_config["llm"]["persona"]
                print(f"🎭 Using persona from mind config: {persona[:50]}...")
        else:
            print("\n🧠 No specific mind selected, using interactive selection")
            persona = None  # Will use default in PenphinMind constructor
        
        # Override persona with command line argument if provided
        if args.persona:
            persona = args.persona
            print(f"🎭 Using custom persona from command line: {persona[:50]}...")
            
        # Create PenphinMind with the selected mind and persona
        penphin = PenphinMind(mind_id=selected_mind_id, persona=persona)
            
        # Set connection mode if specified
        # Note: This is somewhat redundant as connection info is in minds_config.json,
        # but kept for flexibility and backward compatibility
        connection_type = args.connection
        if connection_type:
            print(f"\n🔍 Setting connection mode to {connection_type}... (Note: this overrides the mind config)")
            try:
                if await setup_connection(connection_type):
                    print(f"{connection_type.capitalize()} connection established successfully")
                else:
                    print(f"Failed to establish {connection_type} connection")
            except Exception as e:
                print(f"Error setting up connection: {e}")
        
        if mode == 'vc':
            await run_visual_cortex_test(penphin.mind)
        elif mode == 'ac':
            await run_auditory_cortex_test(penphin.mind)
        elif mode == 'fc':
            # Use the menu system when in frontal cortex mode
            await run_menu(penphin.mind, connection_type)
        elif mode == 'full':
            # Set full mode flag in SynapticPathways for access to all features
            SynapticPathways.set_mode('full')
            # Run the full menu system with all features
            await run_menu(penphin.mind, connection_type)
        else:
            # Default to menu system if no mode specified (though we now default to 'full')
            await run_menu_system(penphin.mind)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

async def shutdown(mind_instance: Mind = None):
    """Clean up resources before shutdown"""
    try:
        if mind_instance:
            # Use the provided Mind instance
            await mind_instance.complete_cleanup()
        else:
            # Create a new Mind instance if none provided
            mind = Mind(persona="You are a helpful assistant.")
            await mind.complete_cleanup()
            
        print("All connections and resources cleaned up.")
    except Exception as e:
        print(f"Error during shutdown cleanup: {e}")

# Make sure this is called when the program exits
# For example, at the end of main() or in a signal handler

if __name__ == "__main__":
    asyncio.run(main()) 