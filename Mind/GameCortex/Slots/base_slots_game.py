"""
Base class for all slot machine games.
"""

import time
import random
import math
import numpy as np
from PIL import Image, ImageDraw
import subprocess
import os

# Import BaseModule instead of defining BaseGame
from ..base_module import BaseModule 

# === SHARED CONSTANTS (can be moved to a config or shared location) ===
WIDTH, HEIGHT = 64, 64
MARGIN = 3  
TOP_MARGIN = 0
VISIBLE_HEIGHT = 60

# === COLORS ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
SILVER = (192, 192, 192)
GOLD = (255, 215, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Default Audio Config
SOUND_FILE = "front_center_fixed.wav" # Default sound, can be overridden
AUDIO_DEVICE = "plughw:0,0"

# --- Audio Playback Function (Shared) ---
def play_sound(sound_file=SOUND_FILE, audio_device=AUDIO_DEVICE):
    """Play the specified sound file."""
    if not os.path.exists(sound_file):
        print(f"Warning: Sound file {sound_file} not found")
        return
        
    success = False
    try:
        print(f"Attempting audio playback of {sound_file}...")
        
        # First, try playing the sound file directly
        try:
            print(f"Playing sound file on {audio_device}")
            os.system(f"aplay -D {audio_device} {sound_file} &")
            print("Sound playback initiated")
            success = True
        except Exception as e:
            print(f"Sound playback failed: {e}")
            
        # Fallback to speaker-test if aplay failed
        if not success:
            try:
                print(f"Using speaker-test on {audio_device} as fallback")
                subprocess.Popen(
                    ['speaker-test', '-D', audio_device, '-t', 'sine', '-f', '1000', '-l', '1'], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                time.sleep(0.5)
                subprocess.run(['pkill', 'speaker-test'], check=False)
                print("Speaker test successful")
            except Exception as e:
                print(f"Speaker test fallback failed: {e}")
    except Exception as e:
        print(f"Error in audio playback function: {e}")

# --- Base Slots Game Logic ---
class BaseSlotsGame(BaseModule):
    """Provides the core logic and drawing for slot machines."""
    
    def __init__(self, matrix, layout_manager, config=None):
        # Initialize BaseModule first
        super().__init__(matrix, layout_manager, config)
        
        # Game-specific initializations using self.config
        self.reels = []
        self.positions = [0] * self.config.get('reel_count', 3)
        self.target_positions = [0] * self.config.get('reel_count', 3)
        self.spinning = False
        self.win = False
        self.bank = self.config.get('start_bank', 25.0)
        self.bet = self.config.get('bet_amount', 0.25)
        self.last_time = time.time() # Move last_time initialization here
        self.state_timer = 0
        self.current_state = self.config.get('initial_state', 'INTRO') # INTRO, IDLE, SPINNING, RESULT, GAME_OVER
        self.symbols = self.config.get('symbols', ["?", "?", "?"])
        self.symbol_colors = self.config.get('symbol_colors', {})
        self.win_multiplier = self.config.get('win_multiplier', 10)
        self.title = self.config.get('title', 'SLOTS')
        self.title_color = self.config.get('title_color', BLUE)
        self.background_color = self.config.get('background_color', PURPLE)
        self.border_color = self.config.get('border_color', GOLD)
        self.reel_config = {
            'count': self.config.get('reel_count', 3),
            'height': self.config.get('reel_height', 20),
            'width': self.config.get('reel_width', 13),
            'margin': self.config.get('reel_margin', 3)
        }
        self.intro_display_time = self.config.get('intro_time', 3.0)
        self.result_display_time = self.config.get('result_time', 3.0)
        self.sound_file = self.config.get('sound_file', SOUND_FILE)
        
        self._setup_reels()
        
    def initialize(self):
        """Initialize game state."""
        super().initialize() # Call BaseModule initialize
        self.last_time = time.time() # Reset timer on initialize
        self.state_timer = 0
        self.current_state = 'INTRO' # Start with intro
        play_sound(self.sound_file) # Play sound on game start
        
    def _setup_reels(self):
        """Initializes the content of each reel."""
        self.reels = []
        reel_symbols = self.symbols * 3 # Ensure enough symbols
        for _ in range(self.reel_config['count']):
            self.reels.append(random.sample(reel_symbols, 10))
        
    def spin(self):
        """Attempts to start spinning the reels."""
        if self.bank < self.bet:
            print("Not enough money to spin!")
            # Optionally show a message on screen
            return False
            
        self.bank -= self.bet
        self.spinning = True
        self.win = False
        self.positions = [0] * self.reel_config['count'] # Reset visual position
        for i in range(self.reel_config['count']):
            self.target_positions[i] = random.randint(10, 25) # Spin longer
        play_sound(self.sound_file) # Play sound on spin start
        return True
        
    def update_reels(self, dt):
        """Updates the position of the spinning reels."""
        if not self.spinning:
            return
            
        still_spinning = False
        for i in range(self.reel_config['count']):
            if self.positions[i] < self.target_positions[i]:
                progress = self.positions[i] / self.target_positions[i] if self.target_positions[i] > 0 else 1
                # Make spin slower and more consistent
                speed = 10.0 + (5.0 * (1.0 - progress)**2) # Adjusted speed curve
                self.positions[i] += speed * dt
                # Ensure we don't overshoot
                if self.positions[i] >= self.target_positions[i]:
                     self.positions[i] = self.target_positions[i]
                else:
                     still_spinning = True 
            # If it reached target, it stays there.
                
        if not still_spinning:
            self.spinning = False
            self.check_win()
            
    def check_win(self):
        """Checks if the current reel combination is a win."""
        visible_symbols = []
        for i in range(self.reel_config['count']):
            # Ensure position calculation wraps correctly
            pos = int(round(self.positions[i])) % len(self.reels[i]) 
            visible_symbols.append(self.reels[i][pos])
            
        # Winning condition: all visible symbols are identical
        if len(set(visible_symbols)) == 1:
            winning_amount = self.bet * self.win_multiplier
            self.bank += winning_amount
            self.win = True
            print(f"WINNER! Symbols: {visible_symbols[0]}, Won ${winning_amount:.2f}")
            play_sound(self.sound_file) # Play sound on win
        else:
            self.win = False
            
    def update(self, dt):
        """Main update loop managing game states."""
        if not self.running:
            return
            
        self.state_timer += dt
        
        if self.current_state == 'INTRO':
            if self.state_timer >= self.intro_display_time:
                self.current_state = 'IDLE' 
                self.state_timer = 0
        elif self.current_state == 'IDLE':
            # In a real game, wait for input here
            # For demo, auto-spin after a short delay
            if self.state_timer >= 1.5: 
                 if self.bank >= self.bet:
                     if self.spin(): # Attempt to spin
                        self.current_state = 'SPINNING'
                        self.state_timer = 0
                 else: # Not enough money
                     self.current_state = 'GAME_OVER' 
                     self.state_timer = 0
                     play_sound(self.sound_file) # Play a sound for game over?
        elif self.current_state == 'SPINNING':
            self.update_reels(dt)
            if not self.spinning:
                self.current_state = 'RESULT'
                self.state_timer = 0
        elif self.current_state == 'RESULT':
            if self.state_timer >= self.result_display_time:
                 # If won, maybe show intro/celebration again?
                 if self.win:
                     self.current_state = 'INTRO' # Or a specific WIN state
                     self.state_timer = 0
                     play_sound(self.sound_file) # Play win sound again?
                 else:
                     self.current_state = 'IDLE' # Go back to waiting for spin
                     self.state_timer = 0
        elif self.current_state == 'GAME_OVER':
            if self.state_timer >= 5.0: # Show for 5 seconds
                self.running = False # End the game
                
    # --- Drawing Methods (Placeholders / To be overridden) ---
    def draw_intro(self, draw):
        """Draws the intro screen."""
        draw.text((10, 25), "Welcome!", fill=WHITE)
        
    def draw_game_over(self, draw):
        """Draws the game over screen."""
        draw.text((10, 25), "GAME OVER", fill=RED)
        draw.text((10, 35), f"Bank: ${self.bank:.2f}", fill=WHITE)
        
    def draw_logo(self, draw, x, y, size):
         """Draws a small logo in the title bar."""
         draw.rectangle((x-size, y-size, x+size, y+size), fill=YELLOW)

    # --- Main Draw Method --- 
    def draw(self):
        """Draws the current state of the game using the layout manager."""
        if not self.running or not self.layout_manager:
            return
            
        # Clear the whole layout manager canvas first (optional, depends on desired effect)
        # self.layout_manager.clear_all()
        
        if self.current_state == 'INTRO':
            # Intro screen might use the full main area
            intro_canvas = self.layout_manager.get_main_area_canvas()
            intro_draw = ImageDraw.Draw(intro_canvas)
            self.draw_intro(intro_draw)
            self.layout_manager.draw_to_main_area(intro_canvas)
            # Optionally clear or draw specific title/ambient/sides for intro
            title_canvas = self.layout_manager.get_title_area_canvas()
            ImageDraw.Draw(title_canvas).rectangle((0,0,self.layout_manager.width, self.layout_manager.title_height), fill=BLACK) # Black title bar during intro
            self.layout_manager.draw_to_title_area(title_canvas)
            
        elif self.current_state == 'GAME_OVER':
            # Game Over screen might use the full main area
            game_over_canvas = self.layout_manager.get_main_area_canvas()
            game_over_draw = ImageDraw.Draw(game_over_canvas)
            self.draw_game_over(game_over_draw)
            self.layout_manager.draw_to_main_area(game_over_canvas)
            # Optionally clear or draw specific title/ambient/sides
            title_canvas = self.layout_manager.get_title_area_canvas()
            ImageDraw.Draw(title_canvas).rectangle((0,0,self.layout_manager.width, self.layout_manager.title_height), fill=BLACK) # Black title bar
            self.layout_manager.draw_to_title_area(title_canvas)
            
        else: # Draw the main slot machine interface (IDLE, SPINNING, RESULT)
            # 1. Draw Title Area
            title_canvas = self.layout_manager.get_title_area_canvas()
            title_draw = ImageDraw.Draw(title_canvas)
            title_bottom = self.layout_manager.title_height # y-coordinate is relative to this canvas
            title_draw.rectangle((0, 0, self.layout_manager.width, title_bottom), fill=self.title_color)
            # Title text
            title_text_y = 3
            for i, char in enumerate(self.title):
                x = MARGIN + 5 + i * 4
                title_draw.text((x, title_text_y), char, fill=GOLD if i % 2 == 0 else WHITE)
            # Draw Logo using coordinates relative to title canvas
            self.draw_logo(title_draw, self.layout_manager.width - MARGIN - 8, title_bottom // 2, 5) 
            self.layout_manager.draw_to_title_area(title_canvas)
            
            # 2. Draw Main Area (Reels and Info)
            main_canvas = self.layout_manager.get_main_area_canvas()
            main_draw = ImageDraw.Draw(main_canvas)
            # Main background (only for the main area dimensions)
            main_draw.rectangle((0, 0, self.layout_manager.main_area_width, self.layout_manager.main_area_height), 
                                fill=self.background_color, outline=self.border_color)
            
            # Divide main area into top half (reels) and bottom half (status)
            reels_section_height = self.layout_manager.main_area_height // 2
            status_section_y = reels_section_height
            status_section_height = self.layout_manager.main_area_height - reels_section_height
            
            # Draw separator line between reels and status sections
            main_draw.line([(0, reels_section_height), 
                          (self.layout_manager.main_area_width, reels_section_height)], 
                          fill=self.border_color, width=1)
            
            # Reels - coordinates relative to main_canvas, positioned in top half
            reel_margin_top = 3  # Space from top of reels section
            reel_height = reels_section_height - (2 * reel_margin_top)
            
            total_reel_width = self.reel_config['count'] * self.reel_config['width'] + (self.reel_config['count'] - 1) * self.reel_config['margin']
            left_offset = (self.layout_manager.main_area_width - total_reel_width) // 2
            
            # Update reel height in config to match available space
            self.reel_config['height'] = reel_height
            
            for i in range(self.reel_config['count']):
                x = left_offset + i * (self.reel_config['width'] + self.reel_config['margin'])
                y = reel_margin_top
                
                # Draw reel background
                main_draw.rectangle((x, y, x + self.reel_config['width'], y + self.reel_config['height']), 
                                   fill=BLACK, outline=SILVER)
                
                # Draw symbol in reel
                pos = int(round(self.positions[i])) % len(self.reels[i])
                symbol = self.reels[i][pos]
                symbol_color = self.symbol_colors.get(symbol, WHITE) 
                
                symbol_x = x + self.reel_config['width'] // 2 - 2
                symbol_y = y + self.reel_config['height'] // 2 - 4
                main_draw.text((symbol_x, symbol_y), symbol, fill=symbol_color)
                
            # Status section - bottom half of main area
            status_section_margin = 3
            status_x = status_section_margin
            status_width = self.layout_manager.main_area_width - (2 * status_section_margin)
            
            # Draw status box
            main_draw.rectangle((status_x, status_section_y + status_section_margin, 
                                status_x + status_width, 
                                status_section_y + status_section_height - status_section_margin), 
                                fill=(0, 0, 0, 128), outline=SILVER)
            
            # Betting Info - positioned in status section
            bet_text_y = status_section_y + status_section_margin + 5
            bank_text_y = bet_text_y + 10
            bet_text = f"BET: ${self.bet:.2f}"
            bank_text = f"BANK: ${self.bank:.2f}"
            main_draw.text((status_x + 5, bet_text_y), bet_text, fill=WHITE)
            main_draw.text((status_x + 5, bank_text_y), bank_text, fill=WHITE)
            
            # Winner display - in status section when winning
            if self.win and self.current_state == 'RESULT':
                win_box_y = bank_text_y + 15
                win_box_h = 12
                win_box_w = status_width - 10
                win_box_x = status_x + 5
                main_draw.rectangle((win_box_x, win_box_y, 
                                    win_box_x + win_box_w, win_box_y + win_box_h), 
                                    fill=RED, outline=GOLD)
                                    
                # Center text within the red box
                winner_text = "WINNER!"
                text_x = win_box_x + (win_box_w - (len(winner_text) * 6)) // 2  # Estimate text width
                text_y = win_box_y + 2
                for i, char in enumerate(winner_text):
                    main_draw.text((text_x + i * 6, text_y), char, fill=GOLD)
                    
            self.layout_manager.draw_to_main_area(main_canvas)
            
            # 3. Draw Ambient and Side Columns (Optional - Add animations here)
            # Example: Fill ambient area
            ambient_canvas = self.layout_manager.get_ambient_area_canvas()
            ImageDraw.Draw(ambient_canvas).rectangle((0,0, self.layout_manager.width, self.layout_manager.ambient_height), fill=BLACK)
            self.layout_manager.draw_to_ambient_area(ambient_canvas)
            
            # Example: Fill side columns
            left_canvas = self.layout_manager.get_left_column_canvas()
            ImageDraw.Draw(left_canvas).rectangle((0,0, self.layout_manager.side_column_width, self.layout_manager.height), fill=BLACK)
            self.layout_manager.draw_to_left_column(left_canvas)
            
            right_canvas = self.layout_manager.get_right_column_canvas()
            ImageDraw.Draw(right_canvas).rectangle((0,0, self.layout_manager.side_column_width, self.layout_manager.height), fill=BLACK)
            self.layout_manager.draw_to_right_column(right_canvas)
            
    def cleanup(self):
        """Clean up game resources."""
        super().cleanup() # Call BaseModule cleanup
        print(f"Cleaning up slot game {self.__class__.__name__}")

    # Needs layout_manager.update_display() called in the main loop 