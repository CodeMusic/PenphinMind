## Game Manager
## includes games types
## Game Type > eg: Slots
## Each game has a list of themes: RoverSlots, CodeMusai's SYmbols, and Penphin's Magic

"""
Game Cortex - Manages game loading, execution, and state.
"""

import os
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

# Import the actual BaseModule
from .base_module import BaseModule
from Mind.OccipitalLobe.visual_layout_manager import VisualLayoutManager
from Mind.OccipitalLobe.VisualCortex.primary_area import PrimaryVisualArea
from rgbmatrix import RGBMatrix

# Placeholder for BaseGame until defined
class BaseGame:
    def __init__(self, matrix, config=None):
        self.matrix = matrix
        self.config = config
        self.running = False
        
    def initialize(self):
        self.running = True
        print(f"Initializing {self.__class__.__name__}")
        
    def update(self, dt):
        pass
        
    def draw(self, image):
        pass
        
    def handle_input(self, event):
        pass
        
    def cleanup(self):
        self.running = False
        print(f"Cleaning up {self.__class__.__name__}")

class GameManager:
    """Discovers, loads, and manages different game modules."""
    
    def __init__(self, game_directory: str = "Mind/GameCortex"):
        """Initializes the GameManager."""
        self.logger = logging.getLogger(__name__)
        self.game_directory = Path(game_directory)
        self.available_games: Dict[str, Type[BaseModule]] = {}
        self.active_game: Optional[BaseModule] = None
        self.discover_games()
        
    def discover_games(self) -> None:
        """Scans the game directory for available game modules and classes."""
        self.available_games = {}
        self.logger.info(f"Discovering games in {self.game_directory}...")
        
        # Correct module path construction assuming game_directory is relative to project root
        base_module_import_path = self.game_directory.as_posix().replace('/', '.')
        
        # First scan for game type directories
        for game_type_dir in self.game_directory.iterdir():
            if game_type_dir.is_dir() and not game_type_dir.name.startswith('__'):
                self.logger.debug(f"Scanning game type directory: {game_type_dir.name}")
                
                # Scan for Python files in the game type directory
                for file_path in game_type_dir.glob("*.py"):
                    module_name = file_path.stem
                    if not module_name.startswith('__') and module_name != 'base_module' and not module_name.startswith('base_'): # Avoid base classes
                        # Construct the full Python import path
                        full_module_path = f"{base_module_import_path}.{game_type_dir.name}.{module_name}"
                        self._process_game_module(full_module_path)
                        
        # When done, log the discovered games
        self.logger.info(f"Found {len(self.available_games)} available games: {list(self.available_games.keys())}")
        
    def _process_game_module(self, full_module_path: str) -> None:
        """Process a module to find games that inherit from BaseModule."""
        self.logger.debug(f"Attempting to import: {full_module_path}")
        try:
            module = importlib.import_module(full_module_path)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                # Check if it's a class, inherits from BaseModule, and is not BaseModule itself
                if isinstance(attr, type) and issubclass(attr, BaseModule) and attr is not BaseModule:
                    game_name = attr.__name__ # Use class name as game name
                    self.available_games[game_name] = attr
                    self.logger.info(f"Discovered game: {game_name} from {full_module_path}")
        except ImportError as e:
            self.logger.error(f"Failed to import game module {full_module_path}: {e}")
        except Exception as e:
             self.logger.error(f"Error processing game module {full_module_path}: {e}")

    def list_available_games(self) -> List[str]:
        """Returns a list of names of the discovered games."""
        return list(self.available_games.keys())
        
    def launch_game(self, 
                    game_name: str, 
                    matrix_or_visualCortex: Union[RGBMatrix, PrimaryVisualArea],
                    layout_manager: Optional[VisualLayoutManager] = None,
                    config: Optional[Dict] = None) -> Optional[BaseModule]:
        """
        Launches a specific game by name, using either:
        1. PrimaryVisualArea from the brain architecture (preferred)
        2. Direct RGBMatrix (fallback)
        
        Args:
            game_name: Name of the game to launch
            matrix_or_visualCortex: Either PrimaryVisualArea or RGBMatrix instance
            layout_manager: Optional VisualLayoutManager instance, will create one if None
            config: Optional game configuration
        """
        if self.active_game:
            self.logger.warning(f"Cannot launch {game_name}, game {self.active_game.__class__.__name__} is already active.")
            return None
            
        if game_name in self.available_games:
            game_class = self.available_games[game_name]
            try:
                # Determine if we're using visual_cortex or direct matrix
                using_visual_cortex = isinstance(matrix_or_visualCortex, PrimaryVisualArea)
                direct_matrix = None
                
                if using_visual_cortex:
                    visual_cortex = matrix_or_visualCortex
                    # Get matrix from visual_cortex if needed
                    if hasattr(visual_cortex, '_matrix'):
                        direct_matrix = visual_cortex._matrix
                    self.logger.info(f"Launching game with visual_cortex: {visual_cortex}")
                else:
                    # Using direct matrix
                    visual_cortex = None
                    direct_matrix = matrix_or_visualCortex
                    self.logger.info(f"Launching game with direct matrix")
                
                # Create layout_manager if not provided
                if layout_manager is None:
                    if using_visual_cortex:
                        layout_manager = VisualLayoutManager(visual_cortex=visual_cortex)
                    else:
                        layout_manager = VisualLayoutManager(matrix=direct_matrix)
                
                # Pass matrix and layout_manager to the game constructor
                if using_visual_cortex:
                    self.logger.info(f"Creating game with visual_cortex")
                    # Game gets the actual matrix, but layout_manager knows about visual_cortex
                    self.active_game = game_class(direct_matrix, layout_manager, config)
                else:
                    self.logger.info(f"Creating game with direct matrix")
                    self.active_game = game_class(direct_matrix, layout_manager, config)
                
                self.active_game.initialize()
                self.logger.info(f"Launched game: {game_name}")
                return self.active_game
            except Exception as e:
                self.logger.error(f"Failed to launch game {game_name}: {e}", exc_info=True)
                self.active_game = None
                return None
        else:
            self.logger.error(f"Game not found: {game_name}")
            return None
            
    def stop_active_game(self) -> None:
        """Stops the currently running game."""
        if self.active_game:
            game_name = self.active_game.__class__.__name__
            try:
                self.active_game.cleanup()
            except Exception as e:
                 self.logger.error(f"Error during cleanup of game {game_name}: {e}", exc_info=True)
            self.active_game = None
            self.logger.info(f"Stopped game: {game_name}")
        else:
            self.logger.warning("No active game to stop.")

    def get_active_game(self) -> Optional[BaseModule]:
        """Returns the currently active game instance."""
        return self.active_game

# Example Usage (can be removed later)
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.DEBUG)
#     # This assumes the script is run from the project root
#     relative_game_dir = Path(__file__).parent 
#     
#     # Mock matrix and layout manager for testing
#     class MockMatrix: width=64; height=64; SetImage=lambda s,i: None; Clear=lambda s: None
#     class MockLayoutManager: pass # Add necessary methods if needed for testing discovery
#         
#     mock_matrix = MockMatrix()
#     mock_layout = MockLayoutManager()
# 
#     manager = GameManager(game_directory=str(relative_game_dir))
#     print("Available games:", manager.list_available_games())
#     
#     # Example: Launch a game (replace 'RoverSlots' with an actual discovered game name)
#     # game_instance = manager.launch_game('RoverSlots', mock_matrix, mock_layout) 
#     # if game_instance:
#     #     # Simulate game loop
#     #     import time
#     #     time.sleep(2) 
#     #     manager.stop_active_game()
