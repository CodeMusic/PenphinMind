"""
Game of Life - An interactive cellular automaton that also visualizes typed input.
"""

import random
import asyncio
import time
from PIL import Image, ImageDraw, ImageFont
from Mind.GameCortex.base_module import BaseModule

# Color schemes
COLORS = {
    "DEFAULT": {
        "ALIVE": (0, 255, 255),  # Cyan
        "BACKGROUND": (0, 0, 32),  # Dark blue
        "TEXT": (255, 255, 255),  # White
        "TITLE_BG": (0, 0, 64)    # Dark blue for title
    },
    "PSYCHEDELIC": {
        "ALIVE": (255, 0, 255),   # Magenta
        "BACKGROUND": (0, 0, 0),  # Black
        "TEXT": (255, 255, 0),    # Yellow
        "TITLE_BG": (32, 0, 32)   # Dark purple
    },
    "FOREST": {
        "ALIVE": (0, 200, 50),    # Green
        "BACKGROUND": (0, 20, 0), # Dark green
        "TEXT": (200, 255, 200),  # Light green
        "TITLE_BG": (0, 40, 0)    # Medium dark green
    }
}

# Pattern definitions for different characters
PATTERNS = {
    # Basic patterns
    'a': [[0, 1, 0], [1, 0, 1], [1, 1, 1], [1, 0, 1]],  # Simple A
    'b': [[1, 1, 0], [1, 0, 1], [1, 1, 0], [1, 0, 1], [1, 1, 0]],  # Simple B
    'c': [[0, 1, 1], [1, 0, 0], [1, 0, 0], [0, 1, 1]],  # Simple C
    
    # Default pattern for other characters is a glider
    'default': [[0, 1, 0], [0, 0, 1], [1, 1, 1]],
    
    # Special patterns
    ' ': [[0, 0, 0], [0, 1, 0], [0, 0, 0]],  # Single cell for space
    '.': [[1, 1], [1, 1]],  # Block for period
    '!': [[1], [1], [1], [0], [1]],  # Exclamation mark
    
    # Numbers
    '0': [[1, 1, 1], [1, 0, 1], [1, 0, 1], [1, 1, 1]],
    '1': [[0, 1, 0], [1, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 1]],
}

class InteractiveGameOfLife(BaseModule):
    """
    Interactive Game of Life that also functions as an LLM visualizer.
    You can type text that feeds patterns into the simulation.
    """
    
    def __init__(self, matrix, layout_manager, config=None):
        """Initialize the Game of Life with visualization capabilities."""
        super().__init__(matrix, layout_manager, config)
        
        # Game state
        self.grid = [[0 for _ in range(64)] for _ in range(64)]
        self.buffer = ""  # Text input buffer
        self.cursor_pos = (32, 32)  # Current cursor position for pattern insertion
        self.text_cursor = 0  # Position in text visualization
        self.insertion_delay = 0.2  # Seconds between character insertions
        self.last_insert_time = 0
        self.waiting_for_input = True
        
        # Game settings
        self.is_paused = False
        self.speed = 10  # Updates per second
        self.color_scheme = "DEFAULT"
        self.input_mode = "DIRECT"  # DIRECT or BUFFER mode
        
        # Visualization
        self.text_display = ""  # Text being visualized (scrolling)
        self.current_message = ""  # Full current message
        self.age_grid = [[0 for _ in range(64)] for _ in range(64)]  # Track cell age for coloring
        
        # Randomize initially
        self._randomize_cells(0.2)
        
    def initialize(self):
        """Set up the game when launched."""
        super().initialize()
        print("[Game of Life] Initialized. Type to feed patterns into the simulation!")
        self.is_paused = False
        
    def update(self, dt):
        """Update the game state."""
        if not self.running:
            return
            
        current_time = time.time()
        
        # Only update at the specified speed when not paused
        if not self.is_paused:
            # Update simulation based on the speed setting
            if hasattr(self, 'last_update_time'):
                time_since_update = current_time - self.last_update_time
                if time_since_update > 1.0 / self.speed:
                    self._update_simulation()
                    self.last_update_time = current_time
            else:
                self.last_update_time = current_time
                
        # Process any waiting characters from buffer in BUFFER mode
        if self.input_mode == "BUFFER" and self.buffer and current_time - self.last_insert_time > self.insertion_delay:
            self._process_next_character()
            self.last_insert_time = current_time
            
    def draw(self):
        """Draw the current state to the display."""
        if not self.running or not self.layout_manager:
            return
            
        # Get colors from current scheme
        colors = COLORS[self.color_scheme]
            
        # Draw to main area
        main_canvas = self.layout_manager.get_main_area_canvas()
        main_draw = ImageDraw.Draw(main_canvas)
        
        # Fill background
        main_draw.rectangle((0, 0, self.layout_manager.main_area_width, self.layout_manager.main_area_height), 
                          fill=colors["BACKGROUND"])
        
        # Draw cells
        max_age = 10  # Maximum age to track for color gradient
        for y in range(min(64, self.layout_manager.main_area_height)):
            for x in range(min(64, self.layout_manager.main_area_width)):
                if self.grid[y][x]:
                    # Color based on cell age
                    age = self.age_grid[y][x]
                    if age > 0:
                        # Gradient effect based on age
                        age_factor = min(1.0, age / max_age)
                        r = int(colors["ALIVE"][0] * (1 - age_factor * 0.5))
                        g = int(colors["ALIVE"][1] * (1 - age_factor * 0.3))
                        b = int(colors["ALIVE"][2])
                        cell_color = (r, g, b)
                    else:
                        cell_color = colors["ALIVE"]
                        
                    main_draw.point((x, y), fill=cell_color)
        
        # Draw text input at the bottom
        text_y = self.layout_manager.main_area_height - 12
        input_text = f"> {self.buffer}"
        main_draw.text((2, text_y), input_text, fill=colors["TEXT"])
        
        # Draw current message being visualized
        if self.current_message:
            visualization_text = f"Visualizing: {self.current_message}"
            main_draw.text((2, text_y - 12), visualization_text, fill=colors["TEXT"])
        
        # Draw to main area
        self.layout_manager.draw_to_main_area(main_canvas)
        
        # Draw title bar with controls
        title_canvas = self.layout_manager.get_title_area_canvas()
        title_draw = ImageDraw.Draw(title_canvas)
        
        # Title background
        title_draw.rectangle((0, 0, self.layout_manager.width, self.layout_manager.title_height), 
                            fill=colors["TITLE_BG"])
        
        # Mode and status information
        status = "RUNNING" if not self.is_paused else "PAUSED"
        mode = self.input_mode
        title_text = f"Game of Life ({status}) - Mode: {mode} - Type to interact!"
        title_draw.text((4, 2), title_text, fill=colors["TEXT"])
        
        self.layout_manager.draw_to_title_area(title_canvas)
        
    def handle_input(self, event):
        """Handle keyboard input to control the game and feed the simulation."""
        if not self.running:
            return
            
        # Handle control keys
        if event.key == 'p':
            # Toggle pause
            self.is_paused = not self.is_paused
            print(f"[Game of Life] {'Paused' if self.is_paused else 'Resumed'}")
        elif event.key == 'c':
            # Clear grid
            self._clear_cells()
            self.buffer = ""
            self.current_message = ""
            print("[Game of Life] Grid cleared")
        elif event.key == 'r':
            # Randomize grid
            self._randomize_cells()
            print("[Game of Life] Grid randomized")
        elif event.key == 's':
            # Change color scheme
            self._cycle_color_scheme()
        elif event.key == 'm':
            # Toggle input mode
            self.input_mode = "BUFFER" if self.input_mode == "DIRECT" else "DIRECT"
            print(f"[Game of Life] Input mode changed to {self.input_mode}")
        elif event.key == '+':
            # Increase speed
            self.speed = min(60, self.speed + 5)
            print(f"[Game of Life] Speed: {self.speed} updates/sec")
        elif event.key == '-':
            # Decrease speed
            self.speed = max(1, self.speed - 5)
            print(f"[Game of Life] Speed: {self.speed} updates/sec")
        elif event.key == 'enter':
            # Process buffer if in BUFFER mode
            if self.input_mode == "BUFFER":
                self.current_message = self.buffer
                print(f"[Game of Life] Processing: {self.buffer}")
                # Keep buffer for processing but reset cursor
                self.text_cursor = 0
            else:
                # In DIRECT mode, add a pattern at current cursor
                self._insert_pattern(self._get_random_pattern(), self.cursor_pos[0], self.cursor_pos[1])
        elif event.key == 'backspace':
            # Remove last character from buffer
            if self.buffer:
                self.buffer = self.buffer[:-1]
        else:
            # Handle character keys
            char = event.key.lower()
            if len(char) == 1 and ord(char) >= 32 and ord(char) <= 126:  # Printable ASCII
                self.buffer += char
                
                # In DIRECT mode, immediately insert the pattern
                if self.input_mode == "DIRECT":
                    self._insert_character(char)
                    
    def _process_next_character(self):
        """Process the next character from the buffer in BUFFER mode."""
        if not self.buffer or self.text_cursor >= len(self.buffer):
            return False
            
        # Get next character and insert its pattern
        char = self.buffer[self.text_cursor]
        self._insert_character(char)
        
        # Move to next character
        self.text_cursor += 1
        
        # Return True if more characters remain
        return self.text_cursor < len(self.buffer)
    
    def _insert_character(self, char):
        """Insert a character's pattern at the current cursor position."""
        pattern = self._get_pattern_for_char(char)
        
        # Move cursor slightly for next insertion
        x, y = self.cursor_pos
        self._insert_pattern(pattern, x, y)
        
        # Move cursor position for next character
        self.cursor_pos = ((x + 5) % 60, (y + random.randint(-3, 3)) % 60)
        
    def _get_pattern_for_char(self, char):
        """Get the appropriate pattern for a character."""
        if char in PATTERNS:
            return PATTERNS[char]
        return PATTERNS['default']  # Use default pattern for unknown chars
        
    def _insert_pattern(self, pattern, x, y):
        """Insert a pattern at the specified coordinates."""
        height = len(pattern)
        width = len(pattern[0]) if height > 0 else 0
        
        for py in range(height):
            for px in range(width):
                if pattern[py][px]:
                    grid_y = (y + py) % 64
                    grid_x = (x + px) % 64
                    self.grid[grid_y][grid_x] = 1
                    self.age_grid[grid_y][grid_x] = 0  # Reset age for new cells
    
    def _update_simulation(self):
        """Update the Game of Life grid according to Conway's rules."""
        new_grid = [[0 for _ in range(64)] for _ in range(64)]
        
        # Apply Conway's Game of Life rules
        for y in range(64):
            for x in range(64):
                neighbors = self._count_neighbors(x, y)
                if self.grid[y][x]:
                    # Cell is alive
                    if neighbors in [2, 3]:
                        # Cell survives
                        new_grid[y][x] = 1
                        self.age_grid[y][x] = min(20, self.age_grid[y][x] + 1)  # Increment age
                    else:
                        # Cell dies
                        new_grid[y][x] = 0
                        self.age_grid[y][x] = 0
                else:
                    # Cell is dead
                    if neighbors == 3:
                        # Cell becomes alive
                        new_grid[y][x] = 1
                        self.age_grid[y][x] = 0  # New cell, age 0
        
        self.grid = new_grid
    
    def _count_neighbors(self, x, y):
        """Count the number of live neighboring cells."""
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % 64, (y + dy) % 64
                count += self.grid[ny][nx]
        return count
    
    def _randomize_cells(self, density=0.3):
        """Randomize the grid with the specified density of live cells."""
        self.grid = [[1 if random.random() < density else 0 for _ in range(64)] for _ in range(64)]
        self.age_grid = [[0 for _ in range(64)] for _ in range(64)]
        
    def _clear_cells(self):
        """Clear the grid."""
        self.grid = [[0 for _ in range(64)] for _ in range(64)]
        self.age_grid = [[0 for _ in range(64)] for _ in range(64)]
        
    def _cycle_color_scheme(self):
        """Cycle through available color schemes."""
        schemes = list(COLORS.keys())
        current_idx = schemes.index(self.color_scheme)
        next_idx = (current_idx + 1) % len(schemes)
        self.color_scheme = schemes[next_idx]
        print(f"[Game of Life] Color scheme: {self.color_scheme}")
        
    def _get_random_pattern(self):
        """Get a random predefined pattern."""
        pattern_keys = list(PATTERNS.keys())
        return PATTERNS[random.choice(pattern_keys)]
    
    def cleanup(self):
        """Clean up when exiting."""
        super().cleanup()
        print("[Game of Life] Cleaned up resources") 