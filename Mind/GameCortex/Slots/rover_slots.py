"""
RoverSlots - A slot machine game featuring Rover the dog.
"""

from .base_slots_game import BaseSlotsGame, play_sound, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, SILVER, GOLD, ORANGE, PURPLE, MARGIN, TOP_MARGIN, VISIBLE_HEIGHT
from PIL import ImageDraw
import time

# === ROVER SPECIFIC CONFIG ===
ROVER_SYMBOLS = ["🦴", "🐾", "🎾", "7", "ROVER", "💰"]
ROVER_SYMBOL_COLORS = {
    "🦴": WHITE,
    "🐾": ORANGE,
    "🎾": GREEN,
    "7": RED,
    "ROVER": GOLD,
    "💰": YELLOW,
}
ROVER_CONFIG = {
    'title': "ROVERSLOTS",
    'symbols': ROVER_SYMBOLS,
    'symbol_colors': ROVER_SYMBOL_COLORS,
    'start_bank': 50.0, # Give Rover a bit more start money
    'win_multiplier': 15, # Higher payout for Rover!
    'title_color': PURPLE,  # Changed from BLUE to PURPLE
    'background_color': ORANGE,  # Changed from PURPLE to ORANGE
    'border_color': GOLD,
    'sound_file': "front_center_fixed.wav",
    # Inherits reel config, timings etc from base defaults unless specified here
    'width': 64, # Pass dimensions needed for drawing
    'height': 64,
    'visible_height': VISIBLE_HEIGHT,
    'margin': MARGIN,
    'top_margin': TOP_MARGIN
}

class RoverSlots(BaseSlotsGame):
    """Implements the Rover-themed slot game."""
    
    def __init__(self, matrix, layout_manager, config=None):
        # Merge base config with Rover specific config
        full_config = ROVER_CONFIG.copy()
        if config:
            full_config.update(config)
        # Pass matrix and layout_manager to the BaseSlotsGame constructor
        super().__init__(matrix, layout_manager, full_config)
        
    # --- Rover Specific Drawing --- 
    
    def draw_rover(self, draw, x_center, y_center, size):
        """Draws Rover the dog at a specific location and size."""
        # White rectangle for face
        face_margin = size * 0.1
        draw.rectangle((x_center - size + face_margin, y_center - size + face_margin, 
                        x_center + size - face_margin, y_center + size - face_margin), fill=WHITE)
        
        # Silver rectangle for eyes (upper half)
        eye_panel_bottom = y_center - face_margin # Top half
        draw.rectangle((x_center - size + face_margin, y_center - size + face_margin, 
                        x_center + size - face_margin, eye_panel_bottom), fill=SILVER)
        
        # Eyes (two round eyes)
        eye_y = y_center - size*0.5
        eye_size_factor = 0.15
        left_eye_x = x_center - size*0.3
        right_eye_x = x_center + size*0.3
        
        draw.ellipse((left_eye_x - size*eye_size_factor, eye_y - size*eye_size_factor, 
                      left_eye_x + size*eye_size_factor, eye_y + size*eye_size_factor), fill=BLACK)
        draw.ellipse((right_eye_x - size*eye_size_factor, eye_y - size*eye_size_factor, 
                      right_eye_x + size*eye_size_factor, eye_y + size*eye_size_factor), fill=BLACK)
        
        # Triangle nose (pointing down)
        nose_top = eye_panel_bottom + size*0.1
        nose_width_factor = 0.3
        nose_height_factor = 0.2
        nose_points = [
            (x_center, nose_top + size*nose_height_factor),  # bottom point
            (x_center - size*nose_width_factor/2, nose_top), # left point
            (x_center + size*nose_width_factor/2, nose_top)  # right point
        ]
        draw.polygon(nose_points, fill=BLACK)
        
        # Line from nose to mouth
        mouth_top = nose_top + size*nose_height_factor
        mouth_bottom = mouth_top + size*0.2
        
        # Draw vertical line down from nose
        draw.line([(x_center, mouth_top), (x_center, mouth_bottom)], fill=BLACK, width=1)
        
        # Draw smile (curve up on right side)
        draw.arc((x_center - size*0.4, mouth_bottom - size*0.2, x_center + size*0.4, mouth_bottom + size*0.2), 
                 180, 0, fill=BLACK, width=1)
        
        # Triangle ears ABOVE the head, pointing down to connect
        ear_size_factor = 0.3
        left_ear_x = x_center - size*0.5
        right_ear_x = x_center + size*0.5
        ear_y = y_center - size*0.8 # Above the head
        
        # Left ear 
        draw.polygon([
            (left_ear_x, ear_y + size*ear_size_factor),  # bottom point (connects)
            (left_ear_x - size*ear_size_factor, ear_y), # top left
            (left_ear_x + size*ear_size_factor, ear_y)  # top right
        ], fill=WHITE, outline=BLACK)
        
        # Right ear
        draw.polygon([
            (right_ear_x, ear_y + size*ear_size_factor), # bottom point (connects)
            (right_ear_x - size*ear_size_factor, ear_y), # top left
            (right_ear_x + size*ear_size_factor, ear_y)  # top right
        ], fill=WHITE, outline=BLACK)
        
    def draw_intro(self, draw):
        """Draws the Rover intro screen using the provided draw context (for main area)."""
        # Draw background directly on the provided canvas (which is the main_area_canvas)
        draw.rectangle((0, 0, 
                        self.layout_manager.main_area_width, 
                        self.layout_manager.main_area_height), 
                       fill=self.background_color, outline=self.border_color)
                       
        # Draw Rover centered within the main area canvas
        self.draw_rover(draw, self.layout_manager.main_area_width//2, self.layout_manager.main_area_height//2, 20) 
        draw.text((10, self.layout_manager.main_area_height - 10), "RoverSlots!", fill=GOLD)
        
    def draw_game_over(self, draw):
        """Draws the game over screen using the provided draw context."""
        self.draw_intro(draw) # Reuse intro screen background on the main_area_canvas
        # Draw GAME OVER box relative to the main_area_canvas
        box_width = self.layout_manager.main_area_width - 20
        box_height = 20
        box_x = 10
        box_y = (self.layout_manager.main_area_height - box_height) // 2 - 5
        draw.rectangle((box_x, box_y, box_x + box_width, box_y + box_height), fill=BLACK, outline=RED)
        draw.text((box_x + 5, box_y + 3), "GAME OVER", fill=RED)
        draw.text((box_x + 5, box_y + 13), f"BANK: ${self.bank:.2f}", fill=WHITE)
        
    def draw_logo(self, draw, x, y, size):
        """Draws a small Rover logo using the provided draw context (for title area)."""
        # Coordinates x, y are relative to the canvas passed in (title canvas)
        self.draw_rover(draw, x, y, size)
        
    # Override the draw method to handle win notification in title section
    def draw(self):
        """Override the draw method to handle win notification in title section."""
        if not self.running or not self.layout_manager:
            return
            
        # Call the parent draw method first
        super().draw()
        
        # If we won, also update the title area to show the win
        if self.win and self.current_state == 'RESULT':
            # Get a fresh title canvas
            title_canvas = self.layout_manager.get_title_area_canvas()
            title_draw = ImageDraw.Draw(title_canvas)
            
            # Create a flashing effect by alternating colors
            flash_color = ORANGE if int(time.time() * 4) % 2 == 0 else PURPLE
            
            # Fill the title bar with the flash color
            title_draw.rectangle((0, 0, self.layout_manager.width, self.layout_manager.title_height), 
                                fill=flash_color)
            
            # Draw the win text
            win_amount = self.bet * self.win_multiplier
            win_text = f"WIN ${win_amount:.2f}!"
            
            # Draw each character with alternating colors for emphasis
            for i, char in enumerate(win_text):
                x = 5 + i * 5  # Adjust spacing for text
                y = 2
                char_color = GOLD if i % 2 == 0 else WHITE
                title_draw.text((x, y), char, fill=char_color)
                
            # Add the logo
            self.draw_logo(title_draw, self.layout_manager.width - 10, 
                          self.layout_manager.title_height // 2, 4)
                          
            # Update the title area
            self.layout_manager.draw_to_title_area(title_canvas)
            
        # Make sure to update the display
        self.layout_manager.update_display() 