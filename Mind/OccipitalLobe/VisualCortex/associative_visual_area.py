"""
Neurological Terms:
    - V3 (Visual Area 3): Dynamic form processing
    - V4 (Visual Area 4): Color processing and form recognition
    - V5/MT (Middle Temporal): Motion processing
    - Extrastriate Visual Cortex
    - Brodmann Areas 19, 37

Neurological Function:
    Associative Visual Area System:
    - Visual pattern recognition
    - Object identification
    - Visual memory integration
    - Spatial awareness
    - Visual feedback
    - Error handling
    - State management

Project Function:
    Handles complex visual processing:
    - Pattern recognition
    - Object identification
    - Visual memory
    - Spatial awareness
    - Visual feedback
"""

from typing import Dict, Any, Optional, Tuple, List, NamedTuple
from enum import Enum
import logging
from ...config import CONFIG
import math
import asyncio
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
import time
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class Expression(Enum):
    """Standard expressions for Penphin"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    CONTEMPT = "contempt"

class Size(Enum):
    """Standard size presets for Penphin"""
    SMALL = 16
    MEDIUM = 32
    LARGE = 48
    XLARGE = 64

class MenuItem:
    """Represents a menu item"""
    def __init__(self, text: str, action: str, icon: Optional[str] = None):
        journaling_manager.recordScope("MenuItem.__init__", text=text, action=action, icon=icon)
        self.text = text
        self.action = action
        self.icon = icon
        self.selected = False
        journaling_manager.recordDebug(f"Created menu item: {text}")

# Logo colors in RGB
class LogoColors:
    """Color constants for the logo"""
    DOLPHIN = (64, 200, 255)  # Cyan/Light blue
    DOLPHIN_HIGHLIGHT = (255, 255, 255)  # White
    PENGUIN = (255, 223, 128)  # Gold/Yellow
    BACKGROUND = (48, 32, 64)  # Dark purple
    
class Point(NamedTuple):
    """2D point representation"""
    x: int
    y: int

class AssociativeVisualArea:
    """Handles complex visual processing and effects"""
    
    def __init__(self):
        """Initialize the associative visual area"""
        journaling_manager.recordScope("AssociativeVisualArea.__init__")
        try:
            self.current_expression = Expression.NEUTRAL
            self.current_x = 0
            self.current_y = 0
            self.current_size = Size.MEDIUM
            self.is_listening = False
            self.menu_items: List[MenuItem] = []
            self.selected_index = -1
            self.animation_task = None
            journaling_manager.recordDebug("Initialized associative visual area")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing associative visual area: {e}")
            raise
            
    async def initialize(self) -> None:
        """Initialize the visual area"""
        journaling_manager.recordScope("AssociativeVisualArea.initialize")
        try:
            # Initialize visual components
            journaling_manager.recordInfo("Visual area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing visual area: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the visual area"""
        journaling_manager.recordScope("AssociativeVisualArea.cleanup")
        try:
            if self.animation_task:
                self.animation_task.cancel()
            journaling_manager.recordInfo("Visual area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up visual area: {e}")
            raise
            
    async def show_gear_animation(self, duration: float = 1.0, color: Optional[tuple] = None) -> None:
        """Show a gear animation"""
        journaling_manager.recordScope("AssociativeVisualArea.show_gear_animation", duration=duration, color=color)
        try:
            if self.animation_task:
                self.animation_task.cancel()
                
            self.animation_task = asyncio.create_task(
                self._animate_gear(duration, color)
            )
            journaling_manager.recordDebug(f"Started gear animation for {duration} seconds")
            
        except Exception as e:
            journaling_manager.recordError(f"Error showing gear animation: {e}")
            raise
            
    async def set_expression(self, expression: Expression) -> None:
        """Set the current expression"""
        journaling_manager.recordScope("AssociativeVisualArea.set_expression", expression=expression)
        try:
            self.current_expression = expression
            journaling_manager.recordDebug(f"Set expression to: {expression}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting expression: {e}")
            raise
            
    async def set_size(self, size: Size) -> None:
        """Set the current size"""
        journaling_manager.recordScope("AssociativeVisualArea.set_size", size=size)
        try:
            self.current_size = size
            journaling_manager.recordDebug(f"Set size to: {size}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting size: {e}")
            raise
            
    async def add_menu_item(self, text: str, action: str, icon: Optional[str] = None) -> None:
        """Add a menu item"""
        journaling_manager.recordScope("AssociativeVisualArea.add_menu_item", text=text, action=action, icon=icon)
        try:
            item = MenuItem(text, action, icon)
            self.menu_items.append(item)
            journaling_manager.recordDebug(f"Added menu item: {text}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error adding menu item: {e}")
            raise
            
    async def select_menu_item(self, index: int) -> None:
        """Select a menu item"""
        journaling_manager.recordScope("AssociativeVisualArea.select_menu_item", index=index)
        try:
            if 0 <= index < len(self.menu_items):
                self.selected_index = index
                for i, item in enumerate(self.menu_items):
                    item.selected = (i == index)
                journaling_manager.recordDebug(f"Selected menu item at index: {index}")
            else:
                journaling_manager.recordError(f"Invalid menu item index: {index}")
                raise ValueError(f"Invalid menu item index: {index}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error selecting menu item: {e}")
            raise
            
    async def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a pixel color"""
        journaling_manager.recordScope("AssociativeVisualArea.set_pixel", x=x, y=y, r=r, g=g, b=b)
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_pixel",
                "x": x,
                "y": y,
                "color": (r, g, b)
            })
            journaling_manager.recordDebug(f"Drew pixel at ({x}, {y}) with color RGB({r}, {g}, {b})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting pixel: {e}")
            raise
            
    async def update(self) -> None:
        """Update the visual display"""
        journaling_manager.recordScope("AssociativeVisualArea.update")
        try:
            # Implementation for updating display
            journaling_manager.recordDebug("Updated visual display")
            
        except Exception as e:
            journaling_manager.recordError(f"Error updating display: {e}")
            raise
            
    async def _animate_gear(self, duration: float, color: Optional[tuple] = None) -> None:
        """Animate a gear"""
        journaling_manager.recordScope("AssociativeVisualArea._animate_gear", duration=duration, color=color)
        try:
            # Implementation for gear animation
            journaling_manager.recordDebug(f"Animated gear for {duration} seconds")
            
        except Exception as e:
            journaling_manager.recordError(f"Error animating gear: {e}")
            raise

    async def process_patterns(self, visual_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process visual patterns in the input data
        
        Args:
            visual_data: Dictionary containing visual data to process
            
        Returns:
            Dict[str, Any]: Processing result containing pattern analysis
        """
        journaling_manager.recordScope("AssociativeVisualArea.process_patterns", visual_data=visual_data)
        try:
            journaling_manager.recordDebug("Starting pattern processing")
            
            # Process visual data
            result = {"status": "ok", "message": "Patterns processed"}
            
            journaling_manager.recordInfo("Successfully processed visual patterns")
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing patterns: {e}")
            return {"status": "error", "message": str(e)}
        
    async def draw_penphin(
        self,
        expression: Expression = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        size: Optional[Size] = None,
        is_listening: bool = None,
        rotation: float = 0.0
    ) -> None:
        """
        Draw Penphin with specified parameters
        
        Args:
            expression: Emotional expression to display
            x: X coordinate (0 to screen width)
            y: Y coordinate (0 to screen height)
            size: Size preset (SMALL, MEDIUM, LARGE, XLARGE)
            is_listening: Whether to show listening state
            rotation: Rotation angle in degrees
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea.draw_penphin",
            expression=expression,
            x=x,
            y=y,
            size=size,
            is_listening=is_listening,
            rotation=rotation
        )
        try:
            # Update state if parameters provided
            if expression:
                self.current_expression = expression
                journaling_manager.recordDebug(f"Updated expression to: {expression}")
                
            if x is not None:
                self.current_x = max(0, min(CONFIG.visual_width, x))
                journaling_manager.recordDebug(f"Updated x position to: {self.current_x}")
                
            if y is not None:
                self.current_y = max(0, min(CONFIG.visual_height, y))
                journaling_manager.recordDebug(f"Updated y position to: {self.current_y}")
                
            if size:
                self.current_size = size
                journaling_manager.recordDebug(f"Updated size to: {size}")
                
            if is_listening is not None:
                self.is_listening = is_listening
                journaling_manager.recordDebug(f"Updated listening state to: {is_listening}")
                
            # Draw body
            await self._draw_penphin_body(
                self.current_x,
                self.current_y,
                self.current_size.value,
                rotation
            )
            journaling_manager.recordDebug("Drew Penphin body")
            
            # Draw expression
            await self._draw_expression(
                self.current_x,
                self.current_y,
                self.current_size.value,
                rotation
            )
            journaling_manager.recordDebug("Drew Penphin expression")
            
            # Draw ears if listening
            if self.is_listening:
                await self._draw_listening_ears(
                    self.current_x,
                    self.current_y,
                    self.current_size.value,
                    rotation
                )
                journaling_manager.recordDebug("Drew listening ears")
                
            journaling_manager.recordInfo("Successfully drew Penphin")
                
        except Exception as e:
            journaling_manager.recordError(f"Error drawing Penphin: {e}")
            raise

    async def move_to(
        self,
        target_x: int,
        target_y: int,
        duration: float = 0.5,
        easing: str = "linear"
    ) -> None:
        """
        Animate Penphin moving to a target position
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            duration: Animation duration in seconds
            easing: Easing function ("linear", "ease_in", "ease_out", "ease_in_out")
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea.move_to",
            target_x=target_x,
            target_y=target_y,
            duration=duration,
            easing=easing
        )
        try:
            start_x, start_y = self.current_x, self.current_y
            steps = int(duration * CONFIG.visual_animation_fps)
            journaling_manager.recordDebug(f"Starting movement from ({start_x}, {start_y}) to ({target_x}, {target_y})")
            
            for i in range(steps):
                t = i / steps
                if easing == "linear":
                    current_x = start_x + (target_x - start_x) * t
                    current_y = start_y + (target_y - start_y) * t
                elif easing == "ease_in":
                    t = t * t
                    current_x = start_x + (target_x - start_x) * t
                    current_y = start_y + (target_y - start_y) * t
                elif easing == "ease_out":
                    t = 1 - (1 - t) * (1 - t)
                    current_x = start_x + (target_x - start_x) * t
                    current_y = start_y + (target_y - start_y) * t
                elif easing == "ease_in_out":
                    t = 0.5 - 0.5 * math.cos(t * math.pi)
                    current_x = start_x + (target_x - start_x) * t
                    current_y = start_y + (target_y - start_y) * t
                else:
                    journaling_manager.recordError(f"Invalid easing function: {easing}")
                    raise ValueError(f"Invalid easing function: {easing}")
                    
                await self.draw_penphin(x=int(current_x), y=int(current_y))
                await asyncio.sleep(1 / CONFIG.visual_animation_fps)
                
            journaling_manager.recordDebug(f"Completed movement to ({target_x}, {target_y})")
            journaling_manager.recordInfo("Movement animation completed successfully")
                
        except Exception as e:
            journaling_manager.recordError(f"Error moving Penphin: {e}")
            raise
        
    async def _draw_penphin_body(
        self,
        x: int,
        y: int,
        size: int,
        rotation: float
    ) -> None:
        """
        Draw Penphin's body shape
        
        Args:
            x: Center X coordinate
            y: Center Y coordinate
            size: Size of the body
            rotation: Rotation angle in degrees
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_penphin_body",
            x=x,
            y=y,
            size=size,
            rotation=rotation
        )
        try:
            # Convert rotation to radians
            angle = math.radians(rotation)
            journaling_manager.recordDebug(f"Converted rotation {rotation}° to radians")
            
            # Define body points (normalized coordinates)
            body_points = [
                Point(-0.3, 0.1),   # Start at nose
                Point(-0.2, 0.0),   # Upper curve
                Point(-0.1, -0.1),  # Head top
                Point(0.0, -0.1),   # Body top
                Point(0.1, 0.0),    # Tail start
                Point(0.2, 0.2),    # Tail tip
                Point(0.1, 0.1),    # Tail bottom
                Point(0.0, 0.0),    # Body bottom
                Point(-0.2, 0.1),   # Back to nose
            ]
            
            # Draw body outline
            await self._draw_curved_shape(
                points=body_points,
                center_x=x,
                center_y=y,
                scale=size,
                color=LogoColors.DOLPHIN,
                highlight_color=LogoColors.DOLPHIN_HIGHLIGHT
            )
            journaling_manager.recordDebug("Drew body outline")
            
            # Draw fin
            fin_points = [
                Point(-0.1, 0.0),   # Fin base
                Point(0.0, -0.15),  # Fin tip
                Point(0.1, 0.0),    # Fin back
            ]
            
            await self._draw_curved_shape(
                points=fin_points,
                center_x=x,
                center_y=y,
                scale=size,
                color=LogoColors.DOLPHIN,
                highlight_color=LogoColors.DOLPHIN_HIGHLIGHT
            )
            journaling_manager.recordDebug("Drew fin")
            
            journaling_manager.recordInfo("Successfully drew Penphin body")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing Penphin body: {e}")
            raise
        
    async def _draw_expression(
        self,
        x: int,
        y: int,
        size: int,
        rotation: float
    ) -> None:
        """Draw current expression"""
        # Implementation for drawing expression
        pass
        
    async def _draw_listening_ears(
        self,
        x: int,
        y: int,
        size: int,
        rotation: float
    ) -> None:
        """Draw animated listening ears"""
        # Implementation for drawing ears
        pass
        
    async def show_splash_screen(self) -> None:
        """
        Display the PenphinMind splash screen with logo and loading animation
        """
        journaling_manager.recordScope("AssociativeVisualArea.show_splash_screen")
        try:
            journaling_manager.recordDebug("Starting splash screen display")
            
            # Clear screen
            await self._clear_screen()
            journaling_manager.recordDebug("Cleared screen for splash")
            
            # Draw logo
            await self._draw_logo()
            journaling_manager.recordDebug("Drew PenphinMind logo")
            
            # Animate loading bar
            await self._animate_loading_bar()
            journaling_manager.recordDebug("Completed loading bar animation")
            
            # Fade to main screen
            await self._fade_transition()
            journaling_manager.recordDebug("Completed fade transition")
            
            journaling_manager.recordInfo("Splash screen displayed successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error showing splash screen: {e}")
            raise
            
    async def _draw_logo(self) -> None:
        """Draw the PenphinMind logo on the LED matrix"""
        journaling_manager.recordScope("AssociativeVisualArea._draw_logo")
        try:
            # Center the logo
            center_x = CONFIG.visual_width // 2
            center_y = CONFIG.visual_height // 2
            scale = min(CONFIG.visual_width, CONFIG.visual_height) // 2
            journaling_manager.recordDebug(f"Logo centered at ({center_x}, {center_y}) with scale {scale}")
            
            # Set background
            await self._set_background(*LogoColors.BACKGROUND)
            journaling_manager.recordDebug("Set logo background")
            
            # Draw dolphin outline
            dolphin_points = [
                Point(-0.3, 0.1),   # Start at nose
                Point(-0.2, 0.0),   # Upper curve
                Point(-0.1, -0.1),  # Head top
                Point(0.0, -0.1),   # Body top
                Point(0.1, 0.0),    # Tail start
                Point(0.2, 0.2),    # Tail tip
                Point(0.1, 0.1),    # Tail bottom
                Point(0.0, 0.0),    # Body bottom
                Point(-0.2, 0.1),   # Back to nose
            ]
            
            # Draw dolphin
            await self._draw_curved_shape(
                points=dolphin_points,
                center_x=center_x - scale//4,
                center_y=center_y,
                scale=scale,
                color=LogoColors.DOLPHIN,
                highlight_color=LogoColors.DOLPHIN_HIGHLIGHT
            )
            journaling_manager.recordDebug("Drew dolphin outline")
            
            # Draw dolphin fin
            fin_points = [
                Point(-0.1, 0.0),   # Fin base
                Point(0.0, -0.15),  # Fin tip
                Point(0.1, 0.0),    # Fin back
            ]
            
            await self._draw_curved_shape(
                points=fin_points,
                center_x=center_x - scale//4,
                center_y=center_y,
                scale=scale,
                color=LogoColors.DOLPHIN,
                highlight_color=LogoColors.DOLPHIN_HIGHLIGHT
            )
            journaling_manager.recordDebug("Drew dolphin fin")
            
            # Draw penguin outline
            penguin_points = [
                Point(0.2, 0.1),    # Start at beak
                Point(0.1, 0.0),    # Head top
                Point(0.0, 0.0),    # Body top
                Point(-0.1, 0.1),   # Back
                Point(0.0, 0.2),    # Bottom
                Point(0.1, 0.15),   # Front
                Point(0.2, 0.1),    # Back to beak
            ]
            
            # Draw penguin
            await self._draw_curved_shape(
                points=penguin_points,
                center_x=center_x + scale//4,
                center_y=center_y,
                scale=scale,
                color=LogoColors.PENGUIN,
                highlight_color=None
            )
            journaling_manager.recordDebug("Drew penguin outline")
            
            # Draw eye details
            await self._draw_pixel(
                center_x - scale//3,
                center_y - scale//6,
                0, 0, 0  # Black for dolphin eye
            )
            await self._draw_pixel(
                center_x + scale//4,
                center_y - scale//8,
                0, 0, 0  # Black for penguin eye
            )
            journaling_manager.recordDebug("Drew eye details")
            
            journaling_manager.recordInfo("Successfully drew PenphinMind logo")
                
        except Exception as e:
            journaling_manager.recordError(f"Error drawing logo: {e}")
            raise
            
    async def _draw_curved_shape(
        self,
        points: List[Point],
        center_x: int,
        center_y: int,
        scale: int,
        color: Tuple[int, int, int],
        highlight_color: Optional[Tuple[int, int, int]] = None
    ) -> None:
        """
        Draw a curved shape using points
        
        Args:
            points: List of normalized points (-1 to 1)
            center_x: Center X coordinate
            center_y: Center Y coordinate
            scale: Size scale
            color: RGB color tuple
            highlight_color: Optional highlight color
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_curved_shape",
            points=points,
            center_x=center_x,
            center_y=center_y,
            scale=scale,
            color=color,
            highlight_color=highlight_color
        )
        try:
            # Convert normalized points to screen coordinates
            screen_points = []
            for point in points:
                x = center_x + int(point.x * scale)
                y = center_y + int(point.y * scale)
                screen_points.append(Point(x, y))
            journaling_manager.recordDebug(f"Converted {len(points)} points to screen coordinates")
                
            # Draw main shape
            for i in range(len(screen_points) - 1):
                p1 = screen_points[i]
                p2 = screen_points[i + 1]
                
                # Draw line segment
                await self._draw_antialiased_line(
                    p1.x, p1.y,
                    p2.x, p2.y,
                    color
                )
                
                # Draw highlight if specified
                if highlight_color:
                    # Offset highlight slightly
                    await self._draw_antialiased_line(
                        p1.x - 1, p1.y - 1,
                        p2.x - 1, p2.y - 1,
                        highlight_color
                    )
                    
            journaling_manager.recordDebug(f"Drew curved shape with {len(screen_points)} points")
            journaling_manager.recordInfo("Successfully drew curved shape")
                    
        except Exception as e:
            journaling_manager.recordError(f"Error drawing curved shape: {e}")
            raise

    async def _draw_antialiased_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: Tuple[int, int, int]
    ) -> None:
        """
        Draw an anti-aliased line using Xiaolin Wu's algorithm
        
        Args:
            x1, y1: Start point
            x2, y2: End point
            color: RGB color tuple
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_antialiased_line",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            color=color
        )
        try:
            # Implementation of Xiaolin Wu's line algorithm
            dx = x2 - x1
            dy = y2 - y1
            
            if abs(dx) > abs(dy):
                # Horizontal-ish line
                if x2 < x1:
                    x1, x2 = x2, x1
                    y1, y2 = y2, y1
                    journaling_manager.recordDebug("Swapped endpoints for horizontal line")
                    
                gradient = dy / dx
                journaling_manager.recordDebug(f"Calculated gradient: {gradient}")
                
                # Handle first endpoint
                xend = round(x1)
                yend = y1 + gradient * (xend - x1)
                xgap = 1 - ((x1 + 0.5) - int(x1))
                
                xpxl1 = xend
                ypxl1 = int(yend)
                
                await self._plot_pixel(xpxl1, ypxl1, color, xgap * (1 - (yend - int(yend))))
                await self._plot_pixel(xpxl1, ypxl1 + 1, color, xgap * (yend - int(yend)))
                
                intery = yend + gradient
                
                # Handle second endpoint
                xend = round(x2)
                yend = y2 + gradient * (xend - x2)
                xgap = (x2 + 0.5) - int(x2)
                
                xpxl2 = xend
                ypxl2 = int(yend)
                
                await self._plot_pixel(xpxl2, ypxl2, color, xgap * (1 - (yend - int(yend))))
                await self._plot_pixel(xpxl2, ypxl2 + 1, color, xgap * (yend - int(yend)))
                
                # Main loop
                for x in range(xpxl1 + 1, xpxl2):
                    await self._plot_pixel(x, int(intery), color, 1 - (intery - int(intery)))
                    await self._plot_pixel(x, int(intery) + 1, color, intery - int(intery))
                    intery += gradient
                    
            else:
                # Vertical-ish line
                if y2 < y1:
                    x1, x2 = x2, x1
                    y1, y2 = y2, y1
                    journaling_manager.recordDebug("Swapped endpoints for vertical line")
                    
                gradient = dx / dy
                journaling_manager.recordDebug(f"Calculated gradient: {gradient}")
                
                # Similar implementation for vertical lines...
                # (Implementation follows same pattern as horizontal case)
                pass
                
            journaling_manager.recordDebug(f"Drew anti-aliased line from ({x1}, {y1}) to ({x2}, {y2})")
            journaling_manager.recordInfo("Successfully drew anti-aliased line")
                
        except Exception as e:
            journaling_manager.recordError(f"Error drawing anti-aliased line: {e}")
            raise

    async def _plot_pixel(
        self,
        x: int,
        y: int,
        color: Tuple[int, int, int],
        brightness: float
    ) -> None:
        """
        Plot a pixel with given brightness
        
        Args:
            x, y: Pixel coordinates
            color: RGB color tuple
            brightness: Brightness factor (0-1)
        """
        journaling_manager.recordScope(
            "AssociativeVisualArea._plot_pixel",
            x=x,
            y=y,
            color=color,
            brightness=brightness
        )
        try:
            if 0 <= x < CONFIG.visual_width and 0 <= y < CONFIG.visual_height:
                r = int(color[0] * brightness)
                g = int(color[1] * brightness)
                b = int(color[2] * brightness)
                await self._draw_pixel(x, y, r, g, b)
                journaling_manager.recordDebug(f"Plotted pixel at ({x}, {y}) with brightness {brightness}")
            else:
                journaling_manager.recordError(f"Pixel coordinates out of bounds: ({x}, {y})")
                raise ValueError(f"Pixel coordinates out of bounds: ({x}, {y})")
                
        except Exception as e:
            journaling_manager.recordError(f"Error plotting pixel: {e}")
            raise
        
    async def _animate_loading_bar(self) -> None:
        """
        Animate loading bar during splash screen with neural synapse-inspired effect
        """
        journaling_manager.recordScope("AssociativeVisualArea._animate_loading_bar")
        try:
            # Loading bar dimensions
            bar_width = int(CONFIG.visual_width * 0.8)  # 80% of screen width
            bar_height = 3  # 3 pixels high
            bar_x = (CONFIG.visual_width - bar_width) // 2  # Centered
            bar_y = int(CONFIG.visual_height * 0.8)  # Near bottom
            
            journaling_manager.recordDebug(f"Loading bar dimensions: {bar_width}x{bar_height} at ({bar_x}, {bar_y})")
            
            # Colors
            empty_color = (32, 32, 48)  # Dark background
            fill_color = LogoColors.DOLPHIN  # Match dolphin color
            pulse_color = LogoColors.DOLPHIN_HIGHLIGHT  # White pulse
            
            # Draw empty bar background
            for x in range(bar_width):
                for y in range(bar_height):
                    await self._draw_pixel(
                        bar_x + x,
                        bar_y + y,
                        *empty_color
                    )
            journaling_manager.recordDebug("Drew empty bar background")
            
            # Animate fill with neural pulse effect
            steps = 50  # Total animation steps
            pulse_width = 10  # Width of the bright pulse
            
            journaling_manager.recordDebug(f"Starting animation with {steps} steps and pulse width {pulse_width}")
            
            for step in range(steps):
                # Calculate fill position
                fill_percent = step / steps
                fill_x = int(bar_width * fill_percent)
                
                # Draw filled portion
                for x in range(fill_x):
                    for y in range(bar_height):
                        # Calculate distance from pulse center
                        dist_from_pulse = abs(x - fill_x)
                        
                        if dist_from_pulse < pulse_width:
                            # Create pulse effect
                            pulse_factor = 1 - (dist_from_pulse / pulse_width)
                            color = self._blend_colors(
                                fill_color,
                                pulse_color,
                                pulse_factor
                            )
                        else:
                            color = fill_color
                            
                        await self._draw_pixel(
                            bar_x + x,
                            bar_y + y,
                            *color
                        )
                
                # Add neural synapse dots above and below
                if step % 5 == 0:  # Every 5th step
                    synapse_y_offsets = [-2, 4]  # Dots above and below
                    for y_offset in synapse_y_offsets:
                        if 0 <= bar_y + y_offset < CONFIG.visual_height:
                            await self._draw_pixel(
                                bar_x + fill_x,
                                bar_y + y_offset,
                                *pulse_color
                            )
                
                # Pause for animation
                await asyncio.sleep(0.05)
                
            journaling_manager.recordDebug("Completed main animation loop")
            
            # Final pulse across the whole bar
            for pulse_step in range(bar_width):
                for x in range(bar_width):
                    dist_from_pulse = abs(x - pulse_step)
                    if dist_from_pulse < pulse_width:
                        pulse_factor = 1 - (dist_from_pulse / pulse_width)
                        color = self._blend_colors(
                            fill_color,
                            pulse_color,
                            pulse_factor
                        )
                        
                        for y in range(bar_height):
                            await self._draw_pixel(
                                bar_x + x,
                                bar_y + y,
                                *color
                            )
                
                await asyncio.sleep(0.01)
                
            journaling_manager.recordDebug("Completed final pulse animation")
            journaling_manager.recordInfo("Loading bar animation completed successfully")
                
        except Exception as e:
            journaling_manager.recordError(f"Error animating loading bar: {e}")
            raise
        
    def _blend_colors(
        self,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int],
        factor: float
    ) -> Tuple[int, int, int]:
        """Blend two colors with a factor between 0 and 1"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._blend_colors",
            color1=color1,
            color2=color2,
            factor=factor
        )
        try:
            blended = tuple(
                int(c1 + (c2 - c1) * factor)
                for c1, c2 in zip(color1, color2)
            )
            journaling_manager.recordDebug(f"Blended colors: {color1} + {color2} = {blended}")
            return blended
            
        except Exception as e:
            journaling_manager.recordError(f"Error blending colors: {e}")
            raise
        
    async def _fade_transition(self) -> None:
        """Fade transition effect"""
        journaling_manager.recordScope("AssociativeVisualArea._fade_transition")
        try:
            # Fade out duration
            fade_duration = 0.5  # seconds
            steps = 20  # Number of fade steps
            step_duration = fade_duration / steps
            
            journaling_manager.recordDebug(f"Starting fade transition with {steps} steps over {fade_duration} seconds")
            
            # Fade out current screen
            for step in range(steps):
                # Calculate fade factor (1 to 0)
                fade_factor = 1 - (step / steps)
                
                # Apply fade to all pixels
                for x in range(CONFIG.visual_width):
                    for y in range(CONFIG.visual_height):
                        # Get current pixel color
                        current_color = await self._get_pixel_color(x, y)
                        
                        # Apply fade
                        faded_color = tuple(
                            int(c * fade_factor)
                            for c in current_color
                        )
                        
                        await self._draw_pixel(x, y, *faded_color)
                
                # Update display
                await self.update()
                await asyncio.sleep(step_duration)
                
            journaling_manager.recordDebug("Completed fade out")
            
            # Clear screen completely
            await self._clear_screen()
            journaling_manager.recordDebug("Cleared screen")
            
            # Fade in new screen
            for step in range(steps):
                # Calculate fade factor (0 to 1)
                fade_factor = step / steps
                
                # Apply fade to all pixels
                for x in range(CONFIG.visual_width):
                    for y in range(CONFIG.visual_height):
                        # Get target pixel color
                        target_color = await self._get_target_pixel_color(x, y)
                        
                        # Apply fade
                        faded_color = tuple(
                            int(c * fade_factor)
                            for c in target_color
                        )
                        
                        await self._draw_pixel(x, y, *faded_color)
                
                # Update display
                await self.update()
                await asyncio.sleep(step_duration)
                
            journaling_manager.recordDebug("Completed fade in")
            journaling_manager.recordInfo("Fade transition completed successfully")
                
        except Exception as e:
            journaling_manager.recordError(f"Error during fade transition: {e}")
            raise
            
    async def _get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get current color of a pixel"""
        try:
            # Implementation would get current pixel color
            return (0, 0, 0)  # Placeholder
        except Exception as e:
            journaling_manager.recordError(f"Error getting pixel color: {e}")
            raise
            
    async def _get_target_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get target color for a pixel"""
        try:
            # Implementation would get target pixel color
            return (0, 0, 0)  # Placeholder
        except Exception as e:
            journaling_manager.recordError(f"Error getting target pixel color: {e}")
            raise
        
    async def play_penguin_animation(self) -> None:
        """Play the penguin character animation"""
        journaling_manager.recordScope("AssociativeVisualArea.play_penguin_animation")
        try:
            # Implementation for penguin animation
            journaling_manager.recordDebug("Starting penguin animation")
            
            # Draw penguin body
            await self._draw_penphin_body(
                self.current_x,
                self.current_y,
                self.current_size.value,
                0.0  # No rotation
            )
            
            # Draw penguin expression
            await self._draw_expression(
                self.current_x,
                self.current_y,
                self.current_size.value,
                0.0
            )
            
            journaling_manager.recordDebug("Completed penguin animation")
            journaling_manager.recordInfo("Penguin animation played successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error playing penguin animation: {e}")
            raise
            
    async def play_dolphin_animation(self) -> None:
        """Play the dolphin character animation"""
        journaling_manager.recordScope("AssociativeVisualArea.play_dolphin_animation")
        try:
            # Implementation for dolphin animation
            journaling_manager.recordDebug("Starting dolphin animation")
            
            # Draw dolphin body
            await self._draw_penphin_body(
                self.current_x,
                self.current_y,
                self.current_size.value,
                0.0  # No rotation
            )
            
            # Draw dolphin expression
            await self._draw_expression(
                self.current_x,
                self.current_y,
                self.current_size.value,
                0.0
            )
            
            journaling_manager.recordDebug("Completed dolphin animation")
            journaling_manager.recordInfo("Dolphin animation played successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error playing dolphin animation: {e}")
            raise
            
    async def draw_menu(self, items: List[MenuItem]) -> None:
        """
        Draw the menu system
        
        Args:
            items: List of menu items to display
        """
        journaling_manager.recordScope("AssociativeVisualArea.draw_menu", num_items=len(items))
        try:
            self.menu_items = items
            self.selected_index = 0
            
            # Clear screen
            await self._clear_screen()
            journaling_manager.recordDebug("Cleared screen for menu")
            
            # Draw menu background
            await self._draw_menu_background()
            journaling_manager.recordDebug("Drew menu background")
            
            # Draw menu items
            for i, item in enumerate(items):
                await self._draw_menu_item(item.text, i, item.selected)
                journaling_manager.recordDebug(f"Drew menu item {i+1}/{len(items)}")
                
            # Draw navigation hints
            await self._draw_menu_navigation()
            journaling_manager.recordDebug("Drew menu navigation")
            
            journaling_manager.recordInfo("Menu drawn successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu: {e}")
            raise

    async def _draw_menu_background(self) -> None:
        """Draw menu background"""
        # Implementation for menu background
        pass
        
    async def _draw_menu_item(
        self,
        text: str,
        index: int,
        is_selected: bool = False
    ) -> None:
        """Draw a menu item on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu_item",
            text=text,
            index=index,
            is_selected=is_selected
        )
        try:
            # Calculate position
            x = 2  # Left margin
            y = 8 + (index * 6)  # Start below title
            
            # Draw selection indicator
            if is_selected:
                await self._draw_menu_selection(x, y)
                
            # Draw text
            await self._draw_text(text, x + 4, y, 255, 255, 255)
            
            journaling_manager.recordDebug(
                f"Drew menu item '{text}' at index {index}, "
                f"selected={is_selected}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu item: {e}")
            raise
        
    async def _draw_menu_navigation(self) -> None:
        """Draw menu navigation hints"""
        journaling_manager.recordScope("AssociativeVisualArea._draw_menu_navigation")
        try:
            # Draw up/down arrows for navigation
            await self._draw_text("^", CONFIG.visual_width // 2, 0, 255, 255, 255)
            await self._draw_text("v", CONFIG.visual_width // 2, CONFIG.visual_height - 8, 255, 255, 255)
            
            # Draw selection hint
            await self._draw_text(">", 2, CONFIG.visual_height - 8, 255, 255, 255)
            
            journaling_manager.recordDebug("Drew menu navigation hints")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu navigation: {e}")
            raise
        
    async def navigate_menu(self, direction: int) -> None:
        """
        Navigate the menu
        
        Args:
            direction: 1 for down, -1 for up
        """
        journaling_manager.recordScope("AssociativeVisualArea.navigate_menu", direction=direction)
        try:
            if not self.menu_items:
                journaling_manager.recordDebug("No menu items to navigate")
                return
                
            self.selected_index = (
                (self.selected_index + direction) % len(self.menu_items)
            )
            
            # Update selection state
            for i, item in enumerate(self.menu_items):
                item.selected = (i == self.selected_index)
                
            journaling_manager.recordDebug(f"Navigated menu to index {self.selected_index}")
            
            # Redraw menu with new selection
            await self.draw_menu(self.menu_items)
            
        except Exception as e:
            journaling_manager.recordError(f"Error navigating menu: {e}")
            raise
            
    async def select_menu_item(self) -> str:
        """
        Select the current menu item
        
        Returns:
            str: Action associated with selected item
        """
        journaling_manager.recordScope("AssociativeVisualArea.select_menu_item")
        try:
            if not self.menu_items:
                journaling_manager.recordDebug("No menu items to select")
                return ""
                
            selected_item = self.menu_items[self.selected_index]
            journaling_manager.recordDebug(f"Selected menu item: {selected_item.text}")
            return selected_item.action
            
        except Exception as e:
            journaling_manager.recordError(f"Error selecting menu item: {e}")
            raise

    async def _clear_screen(self) -> None:
        """Clear the LED matrix screen"""
        journaling_manager.recordScope("AssociativeVisualArea._clear_screen")
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "clear"
            })
            journaling_manager.recordDebug("Cleared LED matrix screen")
            journaling_manager.recordInfo("Screen cleared successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error clearing screen: {e}")
            raise
            
    async def _set_background(self, r: int, g: int, b: int) -> None:
        """Set the background color of the LED matrix"""
        journaling_manager.recordScope("AssociativeVisualArea._set_background", r=r, g=g, b=b)
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "set_background",
                "color": (r, g, b)
            })
            journaling_manager.recordDebug(f"Set background color to RGB({r}, {g}, {b})")
            journaling_manager.recordInfo("Background color set successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting background: {e}")
            raise
            
    async def _draw_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Draw a single pixel on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_pixel",
            x=x,
            y=y,
            r=r,
            g=g,
            b=b
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_pixel",
                "x": x,
                "y": y,
                "color": (r, g, b)
            })
            journaling_manager.recordDebug(f"Drew pixel at ({x}, {y}) with color RGB({r}, {g}, {b})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing pixel: {e}")
            raise

    async def show_gear_animation(self, duration: float = 5.0, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Show a rotating gear animation"""
        journaling_manager.recordScope("AssociativeVisualArea.show_gear_animation", duration=duration, color=color)
        try:
            start_time = time.time()
            r, g, b = color
            
            while time.time() - start_time < duration:
                # Calculate gear position
                self._gear_rotation = (self._gear_rotation + 0.1) % (2 * math.pi)
                
                # Draw gear teeth
                for i in range(8):
                    angle = self._gear_rotation + (i * math.pi / 4)
                    x = int(32 + 12 * math.cos(angle))
                    y = int(16 + 12 * math.sin(angle))
                    await self.set_pixel(x, y, r, g, b)
                    
                # Draw center
                await self.set_pixel(32, 16, r, g, b)
                
                # Update display
                await self.update()
                time.sleep(0.05)
                
            journaling_manager.recordDebug("Gear animation completed")
            
        except Exception as e:
            journaling_manager.recordError(f"Error showing gear animation: {e}")
            raise

    async def set_expression(self, expression: Expression) -> None:
        """Set the current expression"""
        journaling_manager.recordScope("AssociativeVisualArea.set_expression", expression=expression)
        try:
            self.current_expression = expression
            journaling_manager.recordDebug(f"Expression set to: {expression.value}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting expression: {e}")
            raise
            
    async def set_size(self, size: Size) -> None:
        """Set the current size"""
        journaling_manager.recordScope("AssociativeVisualArea.set_size", size=size)
        try:
            self.current_size = size
            journaling_manager.recordDebug(f"Size set to: {size.value}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting size: {e}")
            raise
            
    async def add_menu_item(self, text: str, action: str, icon: Optional[str] = None) -> None:
        """Add a menu item"""
        journaling_manager.recordScope("AssociativeVisualArea.add_menu_item", text=text, action=action, icon=icon)
        try:
            item = MenuItem(text, action, icon)
            self.menu_items.append(item)
            journaling_manager.recordDebug(f"Added menu item: {text}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error adding menu item: {e}")
            raise
            
    async def select_menu_item(self, index: int) -> None:
        """Select a menu item"""
        journaling_manager.recordScope("AssociativeVisualArea.select_menu_item", index=index)
        try:
            if 0 <= index < len(self.menu_items):
                self.selected_index = index
                for i, item in enumerate(self.menu_items):
                    item.selected = (i == index)
                journaling_manager.recordDebug(f"Selected menu item: {self.menu_items[index].text}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error selecting menu item: {e}")
            raise
            
    async def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """Set a pixel color"""
        journaling_manager.recordScope("AssociativeVisualArea.set_pixel", x=x, y=y, r=r, g=g, b=b)
        try:
            # Implementation would go here
            pass
            
        except Exception as e:
            journaling_manager.recordError(f"Error setting pixel: {e}")
            raise
            
    async def update(self) -> None:
        """Update the display"""
        journaling_manager.recordScope("AssociativeVisualArea.update")
        try:
            current_time = time.time()
            if current_time - self._last_update >= 1.0 / 30.0:  # 30 FPS
                self._last_update = current_time
                self.animation_frame = (self.animation_frame + 1) % 30
                
        except Exception as e:
            journaling_manager.recordError(f"Error updating display: {e}")
            raise

    async def _draw_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        r: int,
        g: int,
        b: int
    ) -> None:
        """Draw a line on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_line",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            r=r,
            g=g,
            b=b
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_line",
                "start": (x1, y1),
                "end": (x2, y2),
                "color": (r, g, b)
            })
            journaling_manager.recordDebug(f"Drew line from ({x1}, {y1}) to ({x2}, {y2}) with color RGB({r}, {g}, {b})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing line: {e}")
            raise

    async def _draw_circle(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        r: int,
        g: int,
        b: int,
        fill: bool = False
    ) -> None:
        """Draw a circle on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_circle",
            center_x=center_x,
            center_y=center_y,
            radius=radius,
            r=r,
            g=g,
            b=b,
            fill=fill
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_circle",
                "center": (center_x, center_y),
                "radius": radius,
                "color": (r, g, b),
                "fill": fill
            })
            journaling_manager.recordDebug(
                f"Drew circle at ({center_x}, {center_y}) with radius {radius}, "
                f"color RGB({r}, {g}, {b}), fill={fill}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing circle: {e}")
            raise

    async def _draw_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        r: int,
        g: int,
        b: int,
        fill: bool = False
    ) -> None:
        """Draw a rectangle on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_rectangle",
            x=x,
            y=y,
            width=width,
            height=height,
            r=r,
            g=g,
            b=b,
            fill=fill
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_rectangle",
                "position": (x, y),
                "size": (width, height),
                "color": (r, g, b),
                "fill": fill
            })
            journaling_manager.recordDebug(
                f"Drew rectangle at ({x}, {y}) with size {width}x{height}, "
                f"color RGB({r}, {g}, {b}), fill={fill}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing rectangle: {e}")
            raise

    async def _draw_text(
        self,
        text: str,
        x: int,
        y: int,
        r: int,
        g: int,
        b: int,
        font_size: int = 1,
        font_name: str = "default"
    ) -> None:
        """Draw text on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_text",
            text=text,
            x=x,
            y=y,
            r=r,
            g=g,
            b=b,
            font_size=font_size,
            font_name=font_name
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_text",
                "text": text,
                "position": (x, y),
                "color": (r, g, b),
                "font_size": font_size,
                "font_name": font_name
            })
            journaling_manager.recordDebug(
                f"Drew text '{text}' at ({x}, {y}) with color RGB({r}, {g}, {b}), "
                f"font_size={font_size}, font_name={font_name}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing text: {e}")
            raise

    async def _draw_image(
        self,
        image_data: List[List[Tuple[int, int, int]]],
        x: int,
        y: int,
        scale: float = 1.0
    ) -> None:
        """Draw an image on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_image",
            x=x,
            y=y,
            scale=scale,
            image_size=f"{len(image_data)}x{len(image_data[0])}"
        )
        try:
            await SynapticPathways.transmit_command({
                "command_type": "visual",
                "operation": "draw_image",
                "image_data": image_data,
                "position": (x, y),
                "scale": scale
            })
            journaling_manager.recordDebug(
                f"Drew image at ({x}, {y}) with scale {scale}, "
                f"size {len(image_data)}x{len(image_data[0])}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing image: {e}")
            raise

    async def _draw_animation(
        self,
        frames: List[List[List[Tuple[int, int, int]]]],
        x: int,
        y: int,
        duration: float = 1.0,
        loop: bool = True
    ) -> None:
        """Draw an animation on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_animation",
            x=x,
            y=y,
            duration=duration,
            loop=loop,
            num_frames=len(frames)
        )
        try:
            frame_duration = duration / len(frames)
            journaling_manager.recordDebug(f"Starting animation with {len(frames)} frames, duration {duration}s")
            
            while True:
                for i, frame in enumerate(frames):
                    await self._draw_image(frame, x, y)
                    journaling_manager.recordDebug(f"Drew frame {i+1}/{len(frames)}")
                    await asyncio.sleep(frame_duration)
                
                if not loop:
                    break
                    
            journaling_manager.recordInfo("Animation completed successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing animation: {e}")
            raise

    async def _draw_progress_bar(
        self,
        progress: float,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Tuple[int, int, int] = (255, 255, 255),
        background_color: Tuple[int, int, int] = (0, 0, 0),
        show_percentage: bool = True
    ) -> None:
        """Draw a progress bar on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_progress_bar",
            progress=progress,
            x=x,
            y=y,
            width=width,
            height=height,
            color=color,
            background_color=background_color,
            show_percentage=show_percentage
        )
        try:
            # Draw background
            await self._draw_rectangle(x, y, width, height, *background_color, fill=True)
            
            # Draw progress
            fill_width = int(width * progress)
            if fill_width > 0:
                await self._draw_rectangle(x, y, fill_width, height, *color, fill=True)
                
            # Draw percentage text if enabled
            if show_percentage:
                percentage_text = f"{progress:.0%}"
                text_width = len(percentage_text) * 4  # Approximate width
                text_x = x + (width - text_width) // 2
                text_y = y + (height - 4) // 2
                await self._draw_text(percentage_text, text_x, text_y, *color)
                
            journaling_manager.recordDebug(
                f"Drew progress bar at ({x}, {y}) with progress {progress:.2%}, "
                f"size {width}x{height}, show_percentage={show_percentage}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing progress bar: {e}")
            raise

    async def _draw_menu(
        self,
        title: str,
        items: List[str],
        selected_index: int = 0,
        scroll_offset: int = 0,
        max_visible_items: int = 5
    ) -> None:
        """Draw a menu on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu",
            title=title,
            num_items=len(items),
            selected_index=selected_index,
            scroll_offset=scroll_offset,
            max_visible_items=max_visible_items
        )
        try:
            # Draw title
            await self._draw_menu_title(title)
            
            # Draw menu items
            visible_items = items[scroll_offset:scroll_offset + max_visible_items]
            for i, item in enumerate(visible_items):
                is_selected = (i + scroll_offset) == selected_index
                await self._draw_menu_item(item, i, is_selected)
                
            # Draw scroll indicators if needed
            if scroll_offset > 0:
                await self._draw_menu_scroll("up")
            if scroll_offset + max_visible_items < len(items):
                await self._draw_menu_scroll("down")
                
            journaling_manager.recordDebug(
                f"Drew menu '{title}' with {len(items)} items, "
                f"selected={selected_index}, scroll={scroll_offset}"
            )
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu: {e}")
            raise

    async def _draw_menu_selection(self, x: int, y: int) -> None:
        """Draw a selection indicator for a menu item"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu_selection",
            x=x,
            y=y
        )
        try:
            # Draw selection arrow
            await self._draw_text(">", x, y, 255, 255, 255)
            journaling_manager.recordDebug(f"Drew selection indicator at ({x}, {y})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu selection: {e}")
            raise

    async def _draw_menu_scroll(self, direction: str) -> None:
        """Draw a scroll indicator for a menu"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu_scroll",
            direction=direction
        )
        try:
            if direction == "up":
                # Draw up arrow at top
                await self._draw_text("^", CONFIG.visual_width // 2, 0, 255, 255, 255)
            elif direction == "down":
                # Draw down arrow at bottom
                await self._draw_text("v", CONFIG.visual_width // 2, CONFIG.visual_height - 8, 255, 255, 255)
                
            journaling_manager.recordDebug(f"Drew scroll indicator in {direction} direction")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu scroll: {e}")
            raise

    async def _draw_menu_title(self, title: str) -> None:
        """Draw a menu title on the LED matrix"""
        journaling_manager.recordScope(
            "AssociativeVisualArea._draw_menu_title",
            title=title
        )
        try:
            # Draw title at top center
            title_width = len(title) * 4  # Approximate width
            x = (CONFIG.visual_width - title_width) // 2
            y = 2  # Top margin
            
            await self._draw_text(title, x, y, 255, 255, 255)
            journaling_manager.recordDebug(f"Drew menu title '{title}' at ({x}, {y})")
            
        except Exception as e:
            journaling_manager.recordError(f"Error drawing menu title: {e}")
            raise 