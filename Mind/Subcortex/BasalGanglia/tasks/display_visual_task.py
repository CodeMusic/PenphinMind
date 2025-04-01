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
