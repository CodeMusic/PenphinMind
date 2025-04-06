"""
CodeMusAI's Symbols - A slot machine game featuring coding and AI symbols.
"""

from .base_slots_game import BaseSlotsGame, play_sound, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, SILVER, GOLD, ORANGE, PURPLE, MARGIN, TOP_MARGIN, VISIBLE_HEIGHT
from PIL import ImageDraw

# === CODEMUSAI SPECIFIC CONFIG ===
CODEMUSAI_SYMBOLS = ["</>", "AI", "🧠", "🤖", "💻", "⚙️"]
CODEMUSAI_SYMBOL_COLORS = {
    "</>": BLUE,
    "AI": GREEN,
    "🧠": PURPLE,
    "🤖": SILVER,
    "💻": WHITE,
    "⚙️": ORANGE,
}
CODEMUSAI_CONFIG = {
    'title': "CODEMUSAI",
    'symbols': CODEMUSAI_SYMBOLS,
    'symbol_colors': CODEMUSAI_SYMBOL_COLORS,
    'start_bank': 75.0,  # More starting money
    'win_multiplier': 20,  # Higher payout for CodeMusAI
    'title_color': GREEN,
    'background_color': BLACK,
    'border_color': BLUE,
    'sound_file': "front_center_fixed.wav",
    # Inherits reel config, timings etc from base defaults
    'width': 64,
    'height': 64,
    'visible_height': VISIBLE_HEIGHT,
    'margin': MARGIN,
    'top_margin': TOP_MARGIN
}

class CodeMusAISlots(BaseSlotsGame):
    """Implements the CodeMusAI themed slot game."""
    
    def __init__(self, matrix, layout_manager, config=None):
        # Merge base config with CodeMusAI specific config
        full_config = CODEMUSAI_CONFIG.copy()
        if config:
            full_config.update(config)
        # Pass matrix and layout_manager to the BaseSlotsGame constructor
        super().__init__(matrix, layout_manager, full_config)
        
    # --- CodeMusAI Specific Drawing --- 
    def draw_code_symbol(self, draw, x_center, y_center, size):
        """Draws a coding symbol at a specific location and size."""
        # Draw a code bracket
        bracket_width = size * 0.7
        bracket_height = size * 1.2
        line_width = max(1, int(size * 0.1))
        
        # Left bracket
        left_x = x_center - bracket_width // 2
        draw.line([(left_x, y_center - bracket_height // 2), 
                  (left_x - bracket_width // 4, y_center - bracket_height // 2),
                  (left_x - bracket_width // 4, y_center + bracket_height // 2),
                  (left_x, y_center + bracket_height // 2)], 
                  fill=BLUE, width=line_width)
        
        # Right bracket
        right_x = x_center + bracket_width // 2
        draw.line([(right_x, y_center - bracket_height // 2), 
                  (right_x + bracket_width // 4, y_center - bracket_height // 2),
                  (right_x + bracket_width // 4, y_center + bracket_height // 2),
                  (right_x, y_center + bracket_height // 2)], 
                  fill=BLUE, width=line_width)
        
        # Slash
        draw.line([(x_center - bracket_width // 4, y_center - bracket_height // 4),
                  (x_center + bracket_width // 4, y_center + bracket_height // 4)],
                  fill=GREEN, width=line_width)
        
    def draw_intro(self, draw):
        """Draws the CodeMusAI intro screen using the provided draw context."""
        # Draw background
        draw.rectangle((0, 0, 
                        self.layout_manager.main_area_width, 
                        self.layout_manager.main_area_height), 
                       fill=self.background_color, outline=self.border_color)
                       
        # Draw code symbol centered
        self.draw_code_symbol(draw, self.layout_manager.main_area_width//2, 
                             self.layout_manager.main_area_height//2, 20)
        draw.text((10, self.layout_manager.main_area_height - 10), "CodeMusAI Slots!", fill=GREEN)
        
    def draw_game_over(self, draw):
        """Draws the game over screen."""
        self.draw_intro(draw)  # Reuse intro screen background
        # Draw GAME OVER box
        box_width = self.layout_manager.main_area_width - 20
        box_height = 20
        box_x = 10
        box_y = (self.layout_manager.main_area_height - box_height) // 2 - 5
        draw.rectangle((box_x, box_y, box_x + box_width, box_y + box_height), fill=BLACK, outline=GREEN)
        draw.text((box_x + 5, box_y + 3), "GAME OVER", fill=GREEN)
        draw.text((box_x + 5, box_y + 13), f"BANK: ${self.bank:.2f}", fill=WHITE)
        
    def draw_logo(self, draw, x, y, size):
         """Draws a small CodeMusAI logo."""
         # Coordinates are relative to the canvas passed in (title canvas)
         self.draw_code_symbol(draw, x, y, size) 