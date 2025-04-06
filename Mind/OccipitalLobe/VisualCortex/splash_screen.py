"""
Splash Screen - Handles startup visualization and loading animations.

This module is responsible for displaying the startup splash screen and 
loading animations before the main system initializes.
"""

import asyncio
import logging
import time
from PIL import Image, ImageDraw, ImageFont
import random
from config import CONFIG
import math

logger = logging.getLogger(__name__)

class SplashScreenManager:
    """
    Manages the display of splash screens and loading animations.
    This class provides methods to show various splash screens with
    loading indicators and progress updates based on real system events.
    """
    
    def __init__(self, matrix=None):
        """
        Initialize the splash screen manager with a matrix display.
        
        Args:
            matrix: The RGB matrix or visual area to display on
        """
        self._matrix = matrix
        self._width = 64
        self._height = 64
        self._loading_progress = 0  # 0-100 percentage
        self._loading_text = "Starting..."
        self._running = False
        self._task = None
        self._completed_events = set()
        self._current_step = 0
        
        # Load settings from config
        self._load_config()
    
    def _load_config(self):
        """Load splash screen configuration from CONFIG"""
        splash_config = getattr(CONFIG, 'splash_screen', {})
        
        # Set defaults if config not available
        if not splash_config:
            self._enabled = True
            self._bg_color = (0, 0, 32)  # Dark blue
            self._text_color = (255, 255, 255)  # White
            self._accent_color = (100, 180, 255)  # Light blue
            self._header_text = "PENPHIN"
            self._subheader_text = "MIND"
            self._show_circuit = True
            self._loading_steps = [
                {"event": "visual_init", "progress": 10, "text": "Loading visual cortex..."},
                {"event": "matrix_init", "progress": 25, "text": "Initializing LED matrix..."},
                {"event": "connection", "progress": 40, "text": "Connecting components..."},
                {"event": "synaptic_init", "progress": 60, "text": "Starting synaptic pathways..."},
                {"event": "neural_init", "progress": 80, "text": "Preparing neural networks..."},
                {"event": "mind_init", "progress": 95, "text": "Starting mind processes..."},
                {"event": "complete", "progress": 100, "text": "System ready"}
            ]
            self._symbols = ["☰", "⚙", "✓", "⚡", "🧠"]
            self._completion_color = (0, 32, 0)  # Dark green
            self._completion_text = ["SYSTEM", "READY"]
        else:
            # Load from config
            self._enabled = splash_config.get("enabled", True)
            self._bg_color = splash_config.get("background_color", (0, 0, 32))
            self._text_color = splash_config.get("text_color", (255, 255, 255))
            self._accent_color = splash_config.get("accent_color", (100, 180, 255))
            self._header_text = splash_config.get("header_text", "PENPHIN")
            self._subheader_text = splash_config.get("subheader_text", "MIND")
            self._show_circuit = splash_config.get("show_circuit_pattern", True)
            self._loading_steps = splash_config.get("loading_steps", [])
            self._symbols = splash_config.get("symbols", ["☰", "⚙", "✓", "⚡", "🧠"])
            self._completion_color = splash_config.get("completion_color", (0, 32, 0))
            self._completion_text = splash_config.get("completion_text", ["SYSTEM", "READY"])
    
    async def initialize(self, matrix):
        """
        Initialize with the provided matrix
        
        Args:
            matrix: RGB matrix or visual cortex primary area
        """
        self._matrix = matrix
        
    async def show_startup_splash(self, duration=3.0):
        """
        Display the initial startup splash screen before any connection.
        
        Args:
            duration: How long to display the splash screen in seconds
        
        Returns:
            bool: True if displayed successfully
        """
        if not self._matrix or not self._enabled:
            logger.error("Cannot show splash: no matrix available or splash disabled")
            return False
            
        try:
            # Create a startup splash screen image
            image = Image.new("RGB", (self._width, self._height), self._bg_color)
            
            # Draw logo and text
            draw = ImageDraw.Draw(image)
            
            # PenphinMind text
            draw.text((10, 10), self._header_text, fill=self._text_color)
            draw.text((10, 22), self._subheader_text, fill=self._accent_color)
            
            # Draw a simple circuit board pattern if enabled
            if self._show_circuit:
                for i in range(10):
                    x = random.randint(0, self._width)
                    y = random.randint(30, self._height)
                    length = random.randint(5, 15)
                    direction = random.choice(["h", "v"])
                    
                    # Generate a color in the accent color family
                    r, g, b = self._accent_color
                    color = (max(0, r-100), min(255, g+random.randint(-50, 50)), min(255, b+random.randint(-50, 50)))
                    
                    if direction == "h":
                        draw.line([(x, y), (x + length, y)], fill=color, width=1)
                    else:
                        draw.line([(x, y), (x, y + length)], fill=color, width=1)
            
            # Set the image on the matrix
            if hasattr(self._matrix, 'set_image'):
                result = await self._matrix.set_image(image)
            else:
                # Direct matrix access
                self._matrix.SetImage(image)
                result = True
                
            # Wait for the duration
            await asyncio.sleep(duration)
            return result
            
        except Exception as e:
            logger.error(f"Error displaying startup splash: {e}")
            return False
    
    async def start_loading_animation(self, initial_text="Initializing..."):
        """
        Start an animated loading sequence in the background.
        
        Args:
            initial_text: The initial loading message to display
        """
        if not self._enabled:
            logger.info("Splash screen disabled in config, skipping loading animation")
            return
            
        if self._task and not self._task.done():
            logger.warning("Loading animation already running")
            return
            
        self._running = True
        self._loading_text = initial_text
        self._loading_progress = 0
        self._completed_events = set()
        self._current_step = 0
        
        # Find first step's progress
        if self._loading_steps:
            self._loading_progress = self._loading_steps[0].get("progress", 0)
        
        # Create background task for animation
        self._task = asyncio.create_task(self._run_loading_animation())
        
    async def _run_loading_animation(self):
        """Background task that updates the loading animation."""
        try:
            # How often to update the animation (seconds)
            update_interval = 0.1
            frame = 0
            
            while self._running:
                await self._draw_loading_frame(frame)
                frame = (frame + 1) % 10  # 10 animation frames
                await asyncio.sleep(update_interval)
                
        except Exception as e:
            logger.error(f"Error in loading animation: {e}")
        finally:
            logger.debug("Loading animation stopped")
            
    async def _draw_loading_frame(self, frame):
        """
        Draw a single frame of the loading animation.
        
        Args:
            frame: Current animation frame number
        """
        if not self._matrix:
            return
            
        try:
            # Create the loading screen image
            image = Image.new("RGB", (self._width, self._height), self._bg_color)
            draw = ImageDraw.Draw(image)
            
            # PenphinMind text
            draw.text((10, 5), self._header_text, fill=self._text_color)
            draw.text((10, 17), self._subheader_text, fill=self._accent_color)
            
            # Loading text
            draw.text((5, 32), self._loading_text, fill=(200, 200, 200))
            
            # Progress bar
            progress_width = int(54 * (self._loading_progress / 100))
            draw.rectangle((5, 42, 59, 47), outline=(100, 100, 100))
            draw.rectangle((5, 42, 5 + progress_width, 47), fill=(0, 200, 0))
            
            # Loading animation dots
            dot_positions = [(10, 52), (20, 52), (30, 52), (40, 52), (50, 52)]
            active_dots = frame % len(dot_positions) + 1
            
            for i, pos in enumerate(dot_positions):
                if i < active_dots:
                    color = (0, 255, 0)  # Active dot
                else:
                    color = (50, 50, 50)  # Inactive dot
                draw.ellipse((pos[0], pos[1], pos[0] + 5, pos[1] + 5), fill=color)
            
            # Draw loading step symbols with their specific colors and positions
            y_pos = 58
            x_spacing = 12
            x_start = 8
            
            # Find the current active loading step
            current_step_event = None
            current_step_progress = 0
            for step in self._loading_steps:
                step_progress = step.get("progress", 0)
                if step_progress <= self._loading_progress and step_progress >= current_step_progress:
                    current_step_event = step.get("event")
                    current_step_progress = step_progress
            
            # Go through each step and draw its symbol
            for i, step in enumerate(self._loading_steps):
                if i < len(self._loading_steps):
                    event = step.get("event", "")
                    step_progress = step.get("progress", 0)
                    symbol = step.get("symbol", self._symbols[i] if i < len(self._symbols) else "•")
                    
                    # Get custom color for this step if available
                    if "symbol_color" in step:
                        base_color = step.get("symbol_color")
                    else:
                        # Fall back to default logic based on progress
                        base_color = (0, 255, 0) if step_progress <= self._loading_progress else (100, 100, 100)
                    
                    # Make the current step's symbol brighter and pulsating
                    if event == current_step_event:
                        # Create a pulsating effect for the current step
                        pulse_factor = 0.7 + 0.3 * abs(math.sin(time.time() * 5))
                        r = min(255, int(base_color[0] * pulse_factor))
                        g = min(255, int(base_color[1] * pulse_factor))
                        b = min(255, int(base_color[2] * pulse_factor))
                        color = (r, g, b)
                        
                        # Make the symbol slightly larger
                        font_size = 14
                    elif step_progress <= self._loading_progress:
                        # Completed step - show in normal color
                        color = base_color
                        font_size = 12
                    else:
                        # Future step - dimmer
                        r = max(30, base_color[0] // 3)
                        g = max(30, base_color[1] // 3)
                        b = max(30, base_color[2] // 3)
                        color = (r, g, b)
                        font_size = 12
                    
                    # Calculate x position to space the symbols evenly
                    x_pos = x_start + i * x_spacing
                    
                    # Draw the symbol
                    draw.text((x_pos, y_pos), symbol, fill=color)
            
            # Set the image on the matrix
            if hasattr(self._matrix, 'set_image'):
                await self._matrix.set_image(image)
            else:
                # Direct matrix access
                self._matrix.SetImage(image)
                
        except Exception as e:
            logger.error(f"Error drawing loading frame: {e}")
    
    async def handle_event(self, event_name):
        """
        Handle a system event, updating the progress based on configuration.
        
        Args:
            event_name: Name of the system event (must match events in config)
            
        Returns:
            bool: True if the event was handled, False if not found
        """
        if not self._enabled or not self._running:
            return False
            
        # Add to completed events
        self._completed_events.add(event_name)
        
        # Find the step for this event
        for step in self._loading_steps:
            if step.get("event") == event_name:
                self._loading_progress = step.get("progress", 0)
                self._loading_text = step.get("text", "Loading...")
                logger.info(f"Splash screen event: {event_name} - Progress: {self._loading_progress}%")
                
                # If event is "complete", prepare to stop animation
                if event_name == "complete":
                    # Wait a moment to show 100%
                    await asyncio.sleep(1.0)
                    await self.stop_loading_animation()
                    await self.show_complete_splash()
                
                return True
                
        return False
    
    async def update_loading_progress(self, progress, text=None):
        """
        Update the loading progress and optionally the loading text.
        This can be called manually to update progress if not tied to events.
        
        Args:
            progress: Loading percentage (0-100)
            text: Optional new loading text
        """
        if not self._enabled or not self._running:
            return
            
        self._loading_progress = min(100, max(0, progress))
        if text:
            self._loading_text = text
            
    async def stop_loading_animation(self):
        """Stop the loading animation and clean up."""
        if not self._running:
            return
            
        self._running = False
        
        if self._task and not self._task.done():
            # Wait for the task to finish
            try:
                await asyncio.wait_for(self._task, timeout=0.5)
            except asyncio.TimeoutError:
                # Cancel if it doesn't finish in time
                self._task.cancel()
                
            self._task = None
    
    async def show_complete_splash(self, duration=2.0):
        """
        Show the completion splash screen.
        
        Args:
            duration: How long to show the completion screen
        """
        if not self._matrix or not self._enabled:
            return False
            
        try:
            # Create completion splash image
            image = Image.new("RGB", (self._width, self._height), self._completion_color)
            draw = ImageDraw.Draw(image)
            
            # System ready message
            if len(self._completion_text) >= 2:
                draw.text((5, 10), self._completion_text[0], fill=self._text_color)
                draw.text((20, 22), self._completion_text[1], fill=(0, 255, 0))
            else:
                draw.text((5, 15), "READY", fill=(0, 255, 0))
            
            # Add checkmark
            check_points = [(15, 35), (25, 45), (45, 20)]
            draw.line(check_points, fill=(0, 255, 0), width=3)
            
            # Draw all the completed step symbols as a visual summary
            y_start = 50
            x_spacing = 8
            
            # Draw a horizontal line to separate the checkmark from symbols
            draw.line([(5, y_start-3), (59, y_start-3)], fill=(100, 200, 100), width=1)
            
            # Calculate how many symbols we have to properly space them
            num_symbols = len(self._loading_steps)
            available_width = self._width - 14  # 7px margin on each side
            if num_symbols > 0:
                x_spacing = min(x_spacing, available_width / num_symbols)
            
            # Draw all symbols from completed steps
            for i, step in enumerate(self._loading_steps):
                symbol = step.get("symbol", "•")
                # Get the symbol color, using the defined color if available
                if "symbol_color" in step:
                    color = step.get("symbol_color")
                else:
                    # Default to green for completed symbols
                    color = (0, 255, 0)
                
                # Calculate position
                x_pos = 7 + (i * x_spacing * 1.8)
                
                # Draw the symbol slightly smaller
                draw.text((x_pos, y_start), symbol, fill=color)
            
            # Set the image on the matrix
            if hasattr(self._matrix, 'set_image'):
                await self._matrix.set_image(image)
            else:
                # Direct matrix access
                self._matrix.SetImage(image)
                
            # Wait for the duration
            await asyncio.sleep(duration)
            return True
            
        except Exception as e:
            logger.error(f"Error displaying completion splash: {e}")
            return False 