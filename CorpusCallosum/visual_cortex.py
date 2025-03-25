#!/usr/bin/env python3
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from typing import Optional, Tuple, List, Dict, Any
import platform
from config import CONFIG
from PreFrontalCortex.behavior_manager import SystemState

logger = logging.getLogger(__name__)

class MockRGBMatrix:
    """Mock implementation for non-Raspberry Pi systems"""
    def __init__(self, options=None):
        self.brightness = 50
        self.width = CONFIG.led_cols
        self.height = CONFIG.led_rows
        logger.info("Initialized Mock RGB Matrix for development")
        
    def SetImage(self, image):
        """Mock setting image"""
        pass
        
    def Clear(self):
        """Mock clearing display"""
        pass

class MockRGBMatrixOptions:
    """Mock options for non-Raspberry Pi systems"""
    def __init__(self):
        self.rows = 32
        self.cols = 32
        self.brightness = 50
        self.gpio_slowdown = 1
        self.chain_length = 1
        self.parallel = 1
        self.pwm_bits = 11
        self.scan_mode = 0
        self.pwm_lsb_nanoseconds = 130
        self.rgb_sequence = "RGB"

# Try to import real RGB matrix, fall back to mock if not available
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    IS_RASPBERRY_PI = True
except ImportError:
    RGBMatrix = MockRGBMatrix
    RGBMatrixOptions = MockRGBMatrixOptions
    IS_RASPBERRY_PI = False
    logger.warning("Using mock RGB Matrix implementation (non-Raspberry Pi system detected)")

class VisualCortex:
    """Handles visual output through RGB LED Matrix"""
    
    def __init__(self):
        """Initialize the visual cortex with RGB matrix"""
        self.logger = logging.getLogger(__name__)
        self.matrix: Optional[RGBMatrix] = None
        self.image: Optional[Image] = None
        self.draw: Optional[ImageDraw] = None
        self._initialize_matrix()
        
    def _initialize_matrix(self) -> None:
        """Initialize the RGB matrix with configuration"""
        try:
            options = RGBMatrixOptions()
            options.rows = CONFIG.led_rows
            options.cols = CONFIG.led_cols
            options.brightness = CONFIG.led_max_brightness
            options.gpio_slowdown = CONFIG.led_gpio_slowdown
            options.chain_length = CONFIG.led_chain_length
            options.parallel = CONFIG.led_parallel
            options.pwm_bits = CONFIG.led_pwm_bits
            options.scan_mode = CONFIG.led_scan_mode
            options.pwm_lsb_nanoseconds = CONFIG.led_pwm_lsb_nanoseconds
            options.rgb_sequence = CONFIG.led_rgb_sequence
            
            self.matrix = RGBMatrix(options=options)
            self.image = Image.new('RGB', (CONFIG.led_cols, CONFIG.led_rows))
            self.draw = ImageDraw.Draw(self.image)
            
            if IS_RASPBERRY_PI:
                self.logger.info("RGB Matrix initialized successfully on Raspberry Pi")
            else:
                self.logger.info("Mock RGB Matrix initialized for development")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RGB Matrix: {e}")
            raise
            
    def on_state_change(self, new_state: SystemState) -> None:
        """Handle system state changes"""
        if not self.matrix:
            return
            
        if new_state == SystemState.INITIALIZING:
            self.show_splash_screen()
            if not IS_RASPBERRY_PI:
                self.logger.info("Splash screen would show on real hardware")
        elif new_state == SystemState.THINKING:
            self._start_thinking_animation()
            if not IS_RASPBERRY_PI:
                self.logger.info("Thinking animation would show on real hardware")
        elif new_state == SystemState.LISTENING:
            self._start_listening_animation()
            if not IS_RASPBERRY_PI:
                self.logger.info("Listening animation would show on real hardware")
        elif new_state == SystemState.SPEAKING:
            self._start_speaking_animation()
            if not IS_RASPBERRY_PI:
                self.logger.info("Speaking animation would show on real hardware")
        elif new_state == SystemState.ERROR:
            self._start_error_animation()
            if not IS_RASPBERRY_PI:
                self.logger.info("Error animation would show on real hardware")
        elif new_state == SystemState.SHUTDOWN:
            self.clear()
            if not IS_RASPBERRY_PI:
                self.logger.info("Display would clear on real hardware")
            
    def _start_thinking_animation(self) -> None:
        """Start thinking animation"""
        if not IS_RASPBERRY_PI:
            return
        brightness = int(50 + 50 * np.sin(time.time() * 2))
        self.matrix.brightness = brightness
        
    def _start_listening_animation(self) -> None:
        """Start listening animation"""
        if not IS_RASPBERRY_PI:
            return
        wave = int(50 + 50 * np.sin(time.time() * 4))
        self.matrix.brightness = wave
        
    def _start_speaking_animation(self) -> None:
        """Start speaking animation"""
        if not IS_RASPBERRY_PI:
            return
        pattern = int(50 + 50 * np.sin(time.time() * 3))
        self.matrix.brightness = pattern
        
    def _start_error_animation(self) -> None:
        """Start error animation"""
        if not IS_RASPBERRY_PI:
            return
        flash = int(100 if int(time.time() * 8) % 2 else 0)
        self.matrix.brightness = flash
            
    def clear(self) -> None:
        """Clear the display"""
        if not IS_RASPBERRY_PI:
            return
        if self.draw:
            self.draw.rectangle([(0, 0), (CONFIG.led_cols-1, CONFIG.led_rows-1)], fill=(0, 0, 0))
            self.matrix.SetImage(self.image)
            
    def show_splash_screen(self) -> None:
        """Display the splash screen animation"""
        if not IS_RASPBERRY_PI:
            self.logger.info("Splash screen animation would show: Penguin -> Dolphin -> PenphinOS text")
            return
            
        try:
            # Create frames for animation
            frames = self._create_splash_frames()
            
            # Display each frame
            for frame in frames:
                self.matrix.SetImage(frame)
                time.sleep(0.5)  # Frame duration
                
            # Clear the display
            self.clear()
            
        except Exception as e:
            self.logger.error(f"Error showing splash screen: {e}")
            self.clear()
            
    def _create_splash_frames(self) -> list[Image.Image]:
        """Create frames for the splash screen animation"""
        frames = []
        
        # Frame 1: Penguin
        penguin = Image.new('RGB', (CONFIG.led_cols, CONFIG.led_rows), (0, 0, 0))
        draw = ImageDraw.Draw(penguin)
        
        # Draw penguin body (simple oval)
        draw.ellipse([20, 20, 44, 44], fill=(255, 255, 255))
        # Draw head
        draw.ellipse([35, 15, 50, 30], fill=(255, 255, 255))
        # Draw beak
        draw.polygon([(45, 22), (55, 22), (45, 25)], fill=(255, 165, 0))
        # Draw feet
        draw.ellipse([25, 40, 35, 45], fill=(255, 165, 0))
        draw.ellipse([35, 40, 45, 45], fill=(255, 165, 0))
        
        frames.append(penguin)
        
        # Frame 2: Dolphin
        dolphin = Image.new('RGB', (CONFIG.led_cols, CONFIG.led_rows), (0, 0, 0))
        draw = ImageDraw.Draw(dolphin)
        
        # Draw dolphin body (curved shape)
        draw.arc([10, 20, 54, 40], 0, 180, fill=(0, 150, 255), width=5)
        # Draw tail
        draw.polygon([(10, 30), (0, 20), (0, 40)], fill=(0, 150, 255))
        # Draw fin
        draw.polygon([(30, 20), (35, 10), (40, 20)], fill=(0, 150, 255))
        
        frames.append(dolphin)
        
        # Frame 3: Text "PenphinOS"
        text = Image.new('RGB', (CONFIG.led_cols, CONFIG.led_rows), (0, 0, 0))
        draw = ImageDraw.Draw(text)
        
        # Draw text (scaled to fit)
        draw.text((10, 25), "PenphinOS", fill=(255, 255, 255))
        
        frames.append(text)
        
        return frames
        
    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
        """Set a single pixel color"""
        if not IS_RASPBERRY_PI:
            return
        if 0 <= x < CONFIG.led_cols and 0 <= y < CONFIG.led_rows:
            self.draw.point([(x, y)], fill=color)
            self.matrix.SetImage(self.image)
            
    def set_brightness(self, brightness: int) -> None:
        """Set the matrix brightness (0-100)"""
        if not IS_RASPBERRY_PI:
            return
        if 0 <= brightness <= 100:
            self.matrix.brightness = brightness
            
    def cleanup(self) -> None:
        """Clean up resources"""
        if not IS_RASPBERRY_PI:
            return
        if self.matrix:
            self.clear()
            self.matrix.Clear()
            self.matrix = None