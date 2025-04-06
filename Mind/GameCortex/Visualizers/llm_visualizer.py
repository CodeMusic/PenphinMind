"""
LLM Visualizer - Converts text input to visual patterns, with or without LLM connectivity.
"""

import random
import time
import math
import colorsys
import asyncio
from PIL import Image, ImageDraw, ImageFont
from Mind.GameCortex.base_module import BaseModule
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class TextVisualizer(BaseModule):
    """
    A module that visualizes text as colorful patterns on the LED matrix.
    Can connect to LLM for input if available, or accept direct user text input.
    """
    
    def __init__(self, matrix, layout_manager, config=None):
        """Initialize the text visualizer."""
        super().__init__(matrix, layout_manager, config)
        
        # Character-to-color mapping
        self.char_map = {}
        self._initialize_char_colors()
        
        # State variables
        self.buffer = ""           # Text input buffer
        self.visualization_text = ""  # Current text being visualized
        self.current_col = 0       # Current column
        self.current_row = 0       # Current row
        self.has_llm = False       # Whether LLM is connected
        self.input_mode = "Direct" # Direct or LLM mode
        self.last_update_time = 0  # Last visualization update
        self.visualization_speed = 0.1  # Seconds between char visual updates
        self.background_color = (0, 0, 40)  # Dark blue background
        self.pixels = None
        self.image = None
        self.display_width = 64
        self.display_height = 64
        
        # Animation settings
        self.animation_mode = "Rainfall"  # Rainfall, Spiral, Radial
        self.fade_enabled = True          # Whether old characters fade over time
        self.fade_grid = [[1.0 for _ in range(self.display_width)] for _ in range(self.display_height)]
        
        # Create initial image
        self.create_visualization_image()
        
    def create_visualization_image(self):
        """Create a new visualization image."""
        self.image = Image.new("RGB", (self.display_width, self.display_height), self.background_color)
        self.pixels = self.image.load()
        
    def _initialize_char_colors(self):
        """Initialize character-to-color mapping using a spectrum."""
        chars = "abcdefghijklmnopqrstuvwxyz0123456789 !?.,;:\"'`~@#$%^&*()-_=+[]{}\\|<>/\n\t"
        spectrum_size = len(chars)
        
        # Create colors around the hue spectrum
        for i, char in enumerate(chars):
            # Map to a hue value (0-1) based on position in spectrum
            hue = i / spectrum_size
            # Convert HSV to RGB (S and V at 100% for vibrant colors)
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            # Convert to 8-bit color values
            color = tuple(int(c * 255) for c in rgb)
            self.char_map[char] = color
        
        # Special colors for certain characters
        self.char_map[" "] = (0, 0, 50)    # Dark blue for spaces
        self.char_map["\n"] = (100, 100, 100)  # Gray for newlines
        self.char_map["\t"] = (50, 50, 100)    # Light blue for tabs
        
    def initialize(self):
        """Initialize when the visualizer is started."""
        super().initialize()
        print("[TextVisualizer] Initialized. Type to visualize!")
        
        # Try to check for LLM
        self._check_llm_connection()
        
    def _check_llm_connection(self):
        """Check if LLM is available through Mind's neural connectors."""
        try:
            # Try to import & check SynapticPathways, which is Mind's neural connector
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            if hasattr(SynapticPathways, 'is_initialized') and SynapticPathways.is_initialized():
                self.has_llm = True
                journaling_manager.recordInfo("[TextVisualizer] LLM connection detected.")
                print("[TextVisualizer] LLM connection available, can use LLM input mode.")
            else:
                journaling_manager.recordInfo("[TextVisualizer] SynapticPathways exist but not initialized.")
                self.has_llm = False
        except ImportError:
            journaling_manager.recordInfo("[TextVisualizer] SynapticPathways not available.")
            self.has_llm = False
            
        if not self.has_llm:
            print("[TextVisualizer] No LLM connection detected. Using direct input mode only.")
            
    def update(self, dt):
        """Update visualizer state."""
        if not self.running:
            return
            
        current_time = time.time()
        
        # Check if it's time to process a character
        if self.visualization_text and current_time - self.last_update_time > self.visualization_speed:
            # Process next character in visualization text
            if self.visualization_text:
                # Get next character
                char = self.visualization_text[0].lower()
                self.visualization_text = self.visualization_text[1:]
                
                # Visualize it
                self._visualize_character(char)
                
                # Update last visual time
                self.last_update_time = current_time

        # Apply fade effect if enabled
        if self.fade_enabled:
            self._apply_fade_effect()
            
    def _apply_fade_effect(self):
        """Apply fade effect to existing pixels."""
        # Only fade every few frames for performance
        if random.random() > 0.2:
            return
            
        # Fade all pixels slightly towards background
        fade_factor = 0.99  # How much color remains after fade
        for y in range(self.display_height):
            for x in range(self.display_width):
                r, g, b = self.pixels[x, y]
                bg_r, bg_g, bg_b = self.background_color
                
                # Fade toward background
                new_r = int(r * fade_factor + bg_r * (1 - fade_factor))
                new_g = int(g * fade_factor + bg_g * (1 - fade_factor))
                new_b = int(b * fade_factor + bg_b * (1 - fade_factor))
                
                self.pixels[x, y] = (new_r, new_g, new_b)
                    
    def _visualize_character(self, char):
        """Visualize a character based on current animation mode."""
        if char not in self.char_map:
            char = 'a'  # Default fallback
            
        color = self.char_map[char]
        
        if self.animation_mode == "Rainfall":
            self._rainfall_visualization(char, color)
        elif self.animation_mode == "Spiral":
            self._spiral_visualization(char, color)
        elif self.animation_mode == "Radial":
            self._radial_visualization(char, color)
    
    def _rainfall_visualization(self, char, color):
        """Rainfall animation - characters flow from top to bottom."""
        # Characters fall from top at random horizontal positions
        x = random.randint(0, self.display_width - 1)
        y = 0
        
        # Brighter colors for key characters
        if char in "aeiou":  # Vowels
            color = self._brighten_color(color, 1.3)
        elif char in ".,!?":  # Punctuation
            color = self._brighten_color(color, 1.5)
            
        # Draw character as a colored pixel with surrounding glow
        self._draw_glow_pixel(x, y, color, 2)
        
        # Track where in the visualization we are
        self.current_col = x
        self.current_row = y
    
    def _spiral_visualization(self, char, color):
        """Spiral animation - characters form a growing spiral."""
        # Parameters for the spiral
        max_radius = 30
        total_points = max_radius * 8
        
        # Calculate position on spiral
        t = (time.time() * 10) % total_points
        radius = t / total_points * max_radius
        angle = t * 0.5
        
        # Convert to coordinates
        x = int(self.display_width / 2 + radius * math.cos(angle))
        y = int(self.display_height / 2 + radius * math.sin(angle))
        
        # Make sure within bounds
        x = max(0, min(self.display_width - 1, x))
        y = max(0, min(self.display_height - 1, y))
        
        # Draw with modified color based on char
        modified_color = self._modify_color_by_char(color, char)
        self._draw_glow_pixel(x, y, modified_color, 2)
        
        # Track position
        self.current_col = x
        self.current_row = y
    
    def _radial_visualization(self, char, color):
        """Radial animation - characters expand from center in waves."""
        # Convert character to a position in the alphabet (0-25)
        char_pos = ord(char.lower()) - ord('a') if 'a' <= char.lower() <= 'z' else 0
        
        # Calculate angle based on character
        angle = (char_pos / 26.0) * 2 * math.pi
        
        # Calculate distance from center based on time
        t = time.time() * 0.5
        radius = 10 + (t % 20)  # Expands outward
        
        # Calculate position
        center_x = self.display_width // 2
        center_y = self.display_height // 2
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        
        # Ensure within bounds
        x = max(0, min(self.display_width - 1, x))
        y = max(0, min(self.display_height - 1, y))
        
        # Draw with brightness based on distance from center
        brightness = 1.0 - (radius / 30.0) * 0.5
        modified_color = self._brighten_color(color, brightness)
        self._draw_glow_pixel(x, y, modified_color, 3)
        
        # Track position
        self.current_col = x
        self.current_row = y
    
    def _draw_glow_pixel(self, x, y, color, glow_radius=2):
        """Draw a glowing pixel at the specified position."""
        for dy in range(-glow_radius, glow_radius + 1):
            for dx in range(-glow_radius, glow_radius + 1):
                # Calculate position with wrap-around
                draw_x = (x + dx) % self.display_width
                draw_y = (y + dy) % self.display_height
                
                # Calculate distance from center
                distance = math.sqrt(dx**2 + dy**2)
                if distance <= glow_radius:
                    # Calculate intensity based on distance (1.0 at center, 0.0 at radius)
                    intensity = 1.0 - (distance / glow_radius)
                    
                    # Get current color
                    r, g, b = color
                    
                    # Apply intensity
                    glow_r = int(r * intensity)
                    glow_g = int(g * intensity)
                    glow_b = int(b * intensity)
                    
                    # Set pixel with some blending with existing color
                    current = self.pixels[draw_x, draw_y]
                    blended = self._blend_colors(current, (glow_r, glow_g, glow_b), 0.7)
                    self.pixels[draw_x, draw_y] = blended
    
    def _blend_colors(self, color1, color2, factor):
        """Blend two colors with the given factor (0.0 to 1.0)."""
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        r = int(r1 * (1 - factor) + r2 * factor)
        g = int(g1 * (1 - factor) + g2 * factor)
        b = int(b1 * (1 - factor) + b2 * factor)
        return (r, g, b)
    
    def _brighten_color(self, color, factor):
        """Brighten a color by the given factor."""
        r, g, b = color
        return (
            min(255, int(r * factor)),
            min(255, int(g * factor)),
            min(255, int(b * factor))
        )
    
    def _modify_color_by_char(self, color, char):
        """Modify color based on character type."""
        r, g, b = color
        
        if char in "aeiou":  # Vowels
            return (min(255, int(r * 1.2)), g, b)
        elif char in "bcdfghjklmnpqrstvwxyz":  # Consonants
            return (r, min(255, int(g * 1.2)), b)
        elif char in "0123456789":  # Numbers
            return (r, g, min(255, int(b * 1.2)))
        elif char in ".,!?;:":  # Punctuation
            return (min(255, int(r * 1.3)), min(255, int(g * 1.3)), min(255, int(b * 1.3)))
        else:
            return color
    
    async def _get_llm_input(self):
        """Try to get input from LLM if connected."""
        if not self.has_llm:
            return None
            
        try:
            # Try to use SynapticPathways to get LLM output
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Generate a prompt for the LLM
            prompts = [
                "Describe a colorful scene in a few sentences.",
                "What is your favorite visualization pattern?",
                "Tell me a short poem about colors and light.",
                "How would you describe the feeling of synesthesia?",
                "Generate a random sequence of letters that would create a beautiful pattern."
            ]
            prompt = random.choice(prompts)
            
            # Try to get response from LLM
            response = await SynapticPathways.send_text_request(prompt)
            if response and "response" in response:
                return response["response"]
            return None
        except Exception as e:
            journaling_manager.recordError(f"Error getting LLM input: {e}")
            self.has_llm = False  # Disable LLM mode on error
            return None
    
    def draw(self):
        """Draw the current visualization to the display."""
        if not self.running or not self.layout_manager:
            return
            
        # Get canvases from layout manager
        main_canvas = self.layout_manager.get_main_area_canvas()
        title_canvas = self.layout_manager.get_title_area_canvas()
        
        # Draw visualization to main area
        # Copy our visualization image to the main canvas
        main_canvas.paste(self.image)
        
        # Draw input line at bottom
        draw = ImageDraw.Draw(main_canvas)
        draw.text((2, self.layout_manager.main_area_height - 10), f"> {self.buffer}", fill=(255, 255, 255))
        
        # Draw title
        title_draw = ImageDraw.Draw(title_canvas)
        title_draw.rectangle((0, 0, self.layout_manager.width, self.layout_manager.title_height), fill=(0, 0, 64))
        
        # Show status in title
        mode_text = f"LLM" if self.input_mode == "LLM" else "Direct"
        anim_text = self.animation_mode
        title_draw.text((4, 2), f"TextVisualizer - {mode_text} - {anim_text}", fill=(255, 255, 255))
        
        # Update display through layout manager
        self.layout_manager.draw_to_main_area(main_canvas)
        self.layout_manager.draw_to_title_area(title_canvas)
        
    def handle_input(self, event):
        """Handle keyboard input for the visualizer."""
        if not self.running:
            return
            
        # Control keys
        if event.key == 'c':
            # Clear screen
            self.create_visualization_image()
            print("[TextVisualizer] Screen cleared")
        elif event.key == 'a':
            # Toggle animation mode
            modes = ["Rainfall", "Spiral", "Radial"]
            current_idx = modes.index(self.animation_mode)
            self.animation_mode = modes[(current_idx + 1) % len(modes)]
            print(f"[TextVisualizer] Animation mode: {self.animation_mode}")
        elif event.key == 'f':
            # Toggle fade
            self.fade_enabled = not self.fade_enabled
            print(f"[TextVisualizer] Fade effect: {'Enabled' if self.fade_enabled else 'Disabled'}")
        elif event.key == 'm':
            # Toggle input mode
            if self.has_llm:
                self.input_mode = "LLM" if self.input_mode == "Direct" else "Direct"
                print(f"[TextVisualizer] Input mode: {self.input_mode}")
                
                # If switching to LLM mode, try to get initial input
                if self.input_mode == "LLM":
                    asyncio.create_task(self._llm_input_loop())
            else:
                print("[TextVisualizer] LLM mode not available - no connection detected")
        elif event.key == '+':
            # Speed up visualization
            self.visualization_speed = max(0.01, self.visualization_speed - 0.01)
            print(f"[TextVisualizer] Speed: {1/self.visualization_speed:.2f} chars/sec")
        elif event.key == '-':
            # Slow down visualization
            self.visualization_speed = min(0.5, self.visualization_speed + 0.01)
            print(f"[TextVisualizer] Speed: {1/self.visualization_speed:.2f} chars/sec")
        elif event.key == 'enter':
            # Process buffer
            if self.buffer:
                self.visualization_text += self.buffer
                print(f"[TextVisualizer] Visualizing: {self.buffer}")
                self.buffer = ""  # Clear buffer after sending
        elif event.key == 'backspace':
            # Remove last character from buffer
            if self.buffer:
                self.buffer = self.buffer[:-1]
        else:
            # Handle character keys
            char = event.key.lower()
            if len(char) == 1 and ord(char) >= 32 and ord(char) <= 126:  # Printable ASCII
                self.buffer += char
                
    async def _llm_input_loop(self):
        """Background task to periodically get input from LLM."""
        if not self.has_llm or self.input_mode != "LLM":
            return
            
        print("[TextVisualizer] Starting LLM input loop...")
        
        while self.running and self.input_mode == "LLM":
            # Get input from LLM
            llm_text = await self._get_llm_input()
            
            if llm_text:
                # Truncate very long responses
                if len(llm_text) > 200:
                    llm_text = llm_text[:200] + "..."
                    
                print(f"[TextVisualizer] LLM generated: {llm_text}")
                self.visualization_text += llm_text
            
            # Wait before getting more input
            await asyncio.sleep(10)  # 10 seconds between LLM inputs
    
    def cleanup(self):
        """Clean up resources when stopping."""
        super().cleanup()
        print("[TextVisualizer] Cleaned up resources") 