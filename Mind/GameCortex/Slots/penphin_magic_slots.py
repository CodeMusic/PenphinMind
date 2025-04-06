"""
Penphin's Magic - A magical-themed slot machine game for PenphinMind.
"""

from .base_slots_game import BaseSlotsGame, play_sound, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, SILVER, GOLD, ORANGE, PURPLE, MARGIN, TOP_MARGIN, VISIBLE_HEIGHT
from PIL import ImageDraw

# === PENPHIN MAGIC SPECIFIC CONFIG ===
MAGIC_SYMBOLS = ["✨", "🔮", "🧙", "🪄", "🌟", "🎩"]
MAGIC_SYMBOL_COLORS = {
    "✨": YELLOW,  # Sparkles are yellow
    "🔮": PURPLE,  # Crystal ball is purple
    "🧙": BLUE,    # Wizard is blue
    "🪄": WHITE,   # Magic wand is white
    "🌟": GOLD,    # Star is gold
    "🎩": BLACK,   # Magic hat is black
}
MAGIC_CONFIG = {
    'title': "PENPHIN MAGIC",
    'symbols': MAGIC_SYMBOLS,
    'symbol_colors': MAGIC_SYMBOL_COLORS,
    'start_bank': 100.0,  # More starting money for magic
    'win_multiplier': 25,  # Higher payout for magic symbols
    'title_color': PURPLE,
    'background_color': (32, 0, 64),  # Deep magic purple
    'border_color': (128, 0, 255),    # Bright purple
    'sound_file': "front_center_fixed.wav",
    'width': 64,
    'height': 64,
    'visible_height': VISIBLE_HEIGHT,
    'margin': MARGIN,
    'top_margin': TOP_MARGIN
}

class PenphinMagicSlots(BaseSlotsGame):
    """Implements the Penphin's Magic themed slot game."""
    
    def __init__(self, matrix, layout_manager, config=None):
        # Merge base config with Magic specific config
        full_config = MAGIC_CONFIG.copy()
        if config:
            full_config.update(config)
        # Pass matrix and layout_manager to the BaseSlotsGame constructor
        super().__init__(matrix, layout_manager, full_config)
        
    # --- Magic Specific Drawing ---
    def draw_magic_wand(self, draw, x_center, y_center, size):
        """Draws a magic wand at a specific location and size."""
        # Wand body (white rectangle)
        wand_length = size * 1.5
        wand_width = size * 0.2
        wand_angle = 30  # Degrees
        
        # Calculate points for rotated wand
        import math
        rad_angle = math.radians(wand_angle)
        dx = math.cos(rad_angle) * wand_length / 2
        dy = math.sin(rad_angle) * wand_length / 2
        
        # Center point of wand
        center_x = x_center
        center_y = y_center
        
        # End points of wand
        end1_x = center_x - dx
        end1_y = center_y - dy
        end2_x = center_x + dx
        end2_y = center_y + dy
        
        # Draw wand body
        draw.line([(end1_x, end1_y), (end2_x, end2_y)], fill=WHITE, width=int(wand_width))
        
        # Draw wand tip (star)
        star_size = size * 0.4
        star_x = end2_x
        star_y = end2_y
        
        # Draw 5-point star
        points = []
        for i in range(10):
            # Alternating between outer and inner points
            point_angle = math.radians(i * 36)
            radius = star_size if i % 2 == 0 else star_size * 0.4
            px = star_x + radius * math.sin(point_angle)
            py = star_y - radius * math.cos(point_angle)
            points.append((px, py))
        
        draw.polygon(points, fill=YELLOW)
        
        # Draw sparkles around the wand
        self._draw_sparkles(draw, center_x, center_y, size)
        
    def _draw_sparkles(self, draw, x, y, size):
        """Draw sparkles around a point"""
        import random
        
        # Draw 5 random sparkles
        for _ in range(5):
            # Random offset from center
            offset_x = random.randint(-int(size), int(size))
            offset_y = random.randint(-int(size), int(size))
            
            # Skip if too close to center
            if abs(offset_x) < size/2 and abs(offset_y) < size/2:
                continue
                
            # Draw sparkle (simple star)
            sparkle_x = x + offset_x
            sparkle_y = y + offset_y
            sparkle_size = size * 0.2
            
            # Small 4-point star
            draw.line([(sparkle_x - sparkle_size, sparkle_y),
                      (sparkle_x + sparkle_size, sparkle_y)], fill=YELLOW, width=1)
            draw.line([(sparkle_x, sparkle_y - sparkle_size),
                      (sparkle_x, sparkle_y + sparkle_size)], fill=YELLOW, width=1)
        
    def draw_intro(self, draw):
        """Draws the Penphin's Magic intro screen."""
        # Draw magic background
        draw.rectangle((0, 0, 
                        self.layout_manager.main_area_width, 
                        self.layout_manager.main_area_height), 
                       fill=self.background_color, outline=self.border_color)
                       
        # Draw magic wand centered
        self.draw_magic_wand(draw, self.layout_manager.main_area_width//2, 
                            self.layout_manager.main_area_height//2, 15)
                            
        # Draw title
        draw.text((5, self.layout_manager.main_area_height - 10), 
                 "Penphin's Magic!", fill=PURPLE)
        
    def draw_game_over(self, draw):
        """Draws the game over screen."""
        self.draw_intro(draw)  # Reuse intro screen background
        # Draw GAME OVER box
        box_width = self.layout_manager.main_area_width - 20
        box_height = 20
        box_x = 10
        box_y = (self.layout_manager.main_area_height - box_height) // 2 - 5
        
        # Draw fancier game over box with gradient fill
        for i in range(box_height):
            # Gradient from purple to black
            color_val = int(255 * (1 - i/box_height))
            color = (color_val//2, 0, color_val)
            draw.line([(box_x, box_y + i), (box_x + box_width, box_y + i)], fill=color)
            
        # Border
        draw.rectangle((box_x, box_y, box_x + box_width, box_y + box_height), 
                      fill=None, outline=PURPLE)
                      
        # Text
        draw.text((box_x + 5, box_y + 3), "MAGIC OVER", fill=GOLD)
        draw.text((box_x + 5, box_y + 13), f"BANK: ${self.bank:.2f}", fill=WHITE)
        
    def draw_logo(self, draw, x, y, size):
         """Draws a small magic logo for the title area."""
         # Draw a small magic hat
         hat_width = size * 1.2
         hat_height = size * 0.8
         hat_brim_height = size * 0.2
         
         # Hat top (trapezoid)
         draw.polygon([
             (x - hat_width/4, y - hat_height/2 + hat_brim_height),  # Left bottom of hat top
             (x + hat_width/4, y - hat_height/2 + hat_brim_height),  # Right bottom of hat top
             (x + hat_width/6, y - hat_height/2 - hat_height),       # Right top
             (x - hat_width/6, y - hat_height/2 - hat_height)        # Left top
         ], fill=BLACK, outline=PURPLE)
         
         # Hat brim (ellipse)
         draw.ellipse([
             (x - hat_width/2, y - hat_height/2),
             (x + hat_width/2, y - hat_height/2 + hat_brim_height*2)
         ], fill=BLACK, outline=PURPLE) 