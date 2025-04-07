"""
Test runner for games in the GameCortex, properly integrated with the PenphinMind brain architecture.
"""

import time
import sys
import os
import asyncio
from pathlib import Path

# Add project root to sys.path to allow imports from Mind
project_root = Path(__file__).parent.parent.parent.parent # Adjust based on actual structure
sys.path.insert(0, str(project_root))

# Import the proper brain regions
from Mind.GameCortex.game_manager import GameManager
from Mind.OccipitalLobe.VisualCortex.primary_area import PrimaryVisualArea
from Mind.OccipitalLobe.visual_layout_manager import VisualLayoutManager
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

# === MAIN BRAIN INTEGRATION APPROACH ===
# Instead of initializing the matrix directly, we'll access it through the PrimaryVisualArea
# which represents the visual cortex of the brain architecture.

# Check if running as root
is_root = os.geteuid() == 0
print(f"Running as {'root' if is_root else 'non-root'} user")

# Set environment variables for audio
os.environ["AUDIODEV"] = "plughw:0,0"

async def initialize_brain_regions():
    """Initialize required brain regions for the game"""
    print("[Brain] Initializing visual processing regions...")
    
    # Create and initialize PrimaryVisualArea
    print("[Brain] Creating PrimaryVisualArea instance...")
    primary_visualArea = PrimaryVisualArea()
    
    # Initialize the visual area
    print("[Brain] Initializing visual cortex...")
    init_success = await primary_visualArea.initialize()
    
    if init_success:
        print("[Brain] Visual cortex initialized successfully.")
        # Create VisualLayoutManager that uses the PrimaryVisualArea
        print("[Brain] Creating VisualLayoutManager with visual cortex...")
        layout_manager = VisualLayoutManager(visual_cortex=primary_visualArea)
    else:
        print("[Brain] Failed to initialize visual cortex. Using direct matrix instead.")
        # FALLBACK: Create matrix directly if PrimaryVisualArea couldn't initialize
        options = RGBMatrixOptions()
        options.rows = 64
        options.cols = 64
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'regular'
        options.brightness = 30
        options.disable_hardware_pulsing = True
        options.gpio_slowdown = 2
        options.pwm_lsb_nanoseconds = 130
        options.pwm_bits = 11
        
        print("[Brain] Initializing direct RGB Matrix...")
        matrix = RGBMatrix(options=options)
        
        # Create VisualLayoutManager with direct matrix
        print("[Brain] Creating VisualLayoutManager with direct matrix...")
        layout_manager = VisualLayoutManager(matrix=matrix)
        
        # Set primary_visualArea to None to signal direct matrix usage
        primary_visualArea = None
    
    # Initialize GameManager
    print("[Brain] Initializing GameManager...")
    game_cortex_path = project_root / "Mind" / "GameCortex"
    game_manager = GameManager(game_directory=str(game_cortex_path))
    
    return primary_visualArea, layout_manager, game_manager

async def main():
    # Initialize all brain regions
    primary_visualArea, layout_manager, game_manager = await initialize_brain_regions()
    
    print("[Brain] Available games:", game_manager.list_available_games())
    
    # Launch RoverSlots through the brain architecture (or direct matrix if fallback)
    if primary_visualArea:
        # Use brain architecture
        print("[Brain] Launching RoverSlots through brain architecture...")
        active_game = game_manager.launch_game(
            "RoverSlots", 
            primary_visualArea,  # Pass the PrimaryVisualArea
            layout_manager
        )
    else:
        # Use direct matrix (layout_manager already has reference to it)
        print("[Brain] Launching RoverSlots with direct matrix...")
        active_game = game_manager.launch_game(
            "RoverSlots",
            layout_manager._matrix,  # Get matrix from layout_manager
            layout_manager
        )
    
    if not active_game:
        print("[Brain] Failed to launch RoverSlots game.")
        # Clean up based on what's available
        if primary_visualArea:
            await primary_visualArea.clear()
        elif hasattr(layout_manager, '_matrix'):
            layout_manager._matrix.Clear()
        return
        
    # === GAME LOOP WITH BRAIN ARCHITECTURE ===
    TARGET_FPS = 30
    FRAME_TIME = 1.0 / TARGET_FPS
    
    last_time = time.time()
    try:
        print("[Brain] Starting game loop...")
        while active_game.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Update Game Logic
            active_game.update(dt)
            
            # Draw Frame - this will draw to the layout manager's canvas
            active_game.draw()
            
            # Update Display - this will rotate and send to the matrix through PrimaryVisualArea
            layout_manager.update_display(rotate_degrees=0)
            
            # Frame Limiter
            elapsed = time.time() - current_time
            sleep_time = FRAME_TIME - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("[Brain] Exiting...")
    finally:
        game_manager.stop_active_game()
        # Clean up based on what's available
        if primary_visualArea:
            await primary_visualArea.clear()
            print("[Brain] Display cleared through visual cortex.")
        elif hasattr(layout_manager, '_matrix'):
            layout_manager._matrix.Clear()
            print("[Brain] Display cleared through direct matrix.")
        print("[Brain] Game stopped.")

if __name__ == "__main__":
    asyncio.run(main())
