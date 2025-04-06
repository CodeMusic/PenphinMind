"""
Manages the layout and drawing regions for the LED matrix display.
Located within the Occipital Lobe as it defines the Mind's visual output structure.
"""

from PIL import Image, ImageDraw
from rgbmatrix import RGBMatrix # For type hints

class VisualLayoutManager:
    """Handles screen regions and provides drawing canvases for each."""
    
    def __init__(self, visual_cortex=None, matrix=None):
        """
        Initialize with either a PrimaryVisualArea instance or a fallback RGBMatrix.
        
        Args:
            visual_cortex: PrimaryVisualArea instance from OccipitalLobe
            matrix: Direct RGBMatrix instance (fallback if visual_cortex not provided)
        """
        self.visual_cortex = visual_cortex
        self._direct_matrix = matrix
        
        if not visual_cortex and not matrix:
            raise ValueError("Either visual_cortex or matrix must be provided")
            
        # Determine dimensions from either visual_cortex or direct matrix
        if visual_cortex:
            # If visual_cortex provided, get the matrix from it
            if hasattr(visual_cortex, '_matrix'):
                self._matrix = visual_cortex._matrix
            else:
                raise ValueError("visual_cortex does not have a _matrix attribute")
                
            # Try to get dimensions from options
            if hasattr(visual_cortex, '_options'):
                self.width = visual_cortex._options.cols
                self.height = visual_cortex._options.rows
            else:
                # Default dimensions
                self.width = 64
                self.height = 64
                
            print(f"VisualLayoutManager using visual_cortex with matrix dimensions: {self.width}x{self.height}")
        else:
            # Fallback to direct matrix
            self._matrix = matrix
            # Get dimensions directly from the matrix object if possible
            self.width = getattr(matrix, 'width', 64)
            self.height = getattr(matrix, 'height', 64)
            print(f"VisualLayoutManager using direct matrix with dimensions: {self.width}x{self.height}")
        
        # Define Region Dimensions
        self.title_height = 11
        self.ambient_height = 10
        self.side_column_width = 3
        
        # Calculate Main Content Area Dimensions (Generic Name)
        self.main_area_x_start = self.side_column_width
        self.main_area_y_start = self.title_height
        self.main_area_width = self.width - (2 * self.side_column_width)
        self.main_area_height = self.height - self.title_height - self.ambient_height
        
        # Ensure calculated dimensions are not negative
        if self.main_area_width < 0 or self.main_area_height < 0:
            raise ValueError(f"Calculated main area dimensions are invalid ({self.main_area_width}x{self.main_area_height}). Check region sizes.")
            
        # Main canvas representing the full matrix display
        self.canvas = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.canvas)
        
        print(f"VisualLayoutManager initialized: W={self.width}, H={self.height}")
        print(f"  Title H: {self.title_height}, Ambient H: {self.ambient_height}, Side W: {self.side_column_width}")
        print(f"  Main Area: X={self.main_area_x_start}, Y={self.main_area_y_start}, W={self.main_area_width}, H={self.main_area_height}")

    def clear_all(self, color=(0, 0, 0)):
        """Clears the entire canvas with the specified color (default black)."""
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)

    def get_main_area_canvas(self) -> Image.Image:
        """Returns a new, blank PIL Image canvas for the main content area."""
        if self.main_area_width <= 0 or self.main_area_height <= 0:
             print("Warning: Requesting main area canvas with zero or negative dimensions!")
             return Image.new("RGB", (1, 1)) 
        return Image.new("RGB", (self.main_area_width, self.main_area_height))

    def draw_to_main_area(self, content_canvas: Image.Image):
        """Pastes the provided content canvas onto the main canvas in the main area region."""
        if self.main_area_width <= 0 or self.main_area_height <= 0:
            print("Warning: Cannot draw to main area with zero or negative dimensions.")
            return
            
        if content_canvas.width != self.main_area_width or content_canvas.height != self.main_area_height:
            print(f"Warning: Content canvas size ({content_canvas.width}x{content_canvas.height}) doesn't match main area ({self.main_area_width}x{self.main_area_height}). Resizing/clipping.")
            temp_canvas = Image.new("RGB", (self.main_area_width, self.main_area_height))
            temp_canvas.paste(content_canvas, (0,0))
            content_canvas = temp_canvas
            
        self.canvas.paste(content_canvas, (self.main_area_x_start, self.main_area_y_start))

    def get_title_area_canvas(self) -> Image.Image:
        """Returns a new, blank PIL Image canvas for the title area."""
        if self.width <= 0 or self.title_height <= 0:
            return Image.new("RGB", (1, 1))
        return Image.new("RGB", (self.width, self.title_height))

    def draw_to_title_area(self, title_canvas: Image.Image):
        """Pastes the provided title canvas onto the main canvas."""
        if self.width <= 0 or self.title_height <= 0:
            return
            
        if title_canvas.width != self.width or title_canvas.height != self.title_height:
             print(f"Warning: Title canvas size mismatch. Resizing/clipping.")
             temp_canvas = Image.new("RGB", (self.width, self.title_height))
             temp_canvas.paste(title_canvas, (0,0))
             title_canvas = temp_canvas
             
        self.canvas.paste(title_canvas, (0, 0))
            
    def get_ambient_area_canvas(self) -> Image.Image:
        """Returns a new, blank PIL Image canvas for the ambient area."""
        if self.width <= 0 or self.ambient_height <= 0:
            return Image.new("RGB", (1, 1))
        return Image.new("RGB", (self.width, self.ambient_height))

    def draw_to_ambient_area(self, ambient_canvas: Image.Image):
        """Pastes the provided ambient canvas onto the main canvas."""
        if self.width <= 0 or self.ambient_height <= 0:
             return
             
        if ambient_canvas.width != self.width or ambient_canvas.height != self.ambient_height:
             print(f"Warning: Ambient canvas size mismatch. Resizing/clipping.")
             temp_canvas = Image.new("RGB", (self.width, self.ambient_height))
             temp_canvas.paste(ambient_canvas, (0,0))
             ambient_canvas = temp_canvas
             
        y_pos = self.height - self.ambient_height
        self.canvas.paste(ambient_canvas, (0, y_pos))
             
    def get_left_column_canvas(self) -> Image.Image:
         """Returns a new, blank PIL Image canvas for the left column."""
         if self.side_column_width <= 0 or self.height <= 0:
             return Image.new("RGB", (1, 1))
         return Image.new("RGB", (self.side_column_width, self.height))
         
    def draw_to_left_column(self, column_canvas: Image.Image):
        """Pastes the provided canvas onto the main canvas's left column."""
        if self.side_column_width <= 0 or self.height <= 0:
             return
             
        if column_canvas.width != self.side_column_width or column_canvas.height != self.height:
             print(f"Warning: Left column canvas size mismatch. Resizing/clipping.")
             temp_canvas = Image.new("RGB", (self.side_column_width, self.height))
             temp_canvas.paste(column_canvas, (0,0))
             column_canvas = temp_canvas
             
        self.canvas.paste(column_canvas, (0, 0))
            
    def get_right_column_canvas(self) -> Image.Image:
         """Returns a new, blank PIL Image canvas for the right column."""
         if self.side_column_width <= 0 or self.height <= 0:
             return Image.new("RGB", (1, 1))
         return Image.new("RGB", (self.side_column_width, self.height))
         
    def draw_to_right_column(self, column_canvas: Image.Image):
        """Pastes the provided canvas onto the main canvas's right column."""
        if self.side_column_width <= 0 or self.height <= 0:
            return
            
        if column_canvas.width != self.side_column_width or column_canvas.height != self.height:
             print(f"Warning: Right column canvas size mismatch. Resizing/clipping.")
             temp_canvas = Image.new("RGB", (self.side_column_width, self.height))
             temp_canvas.paste(column_canvas, (0,0))
             column_canvas = temp_canvas

        x_pos = self.width - self.side_column_width
        self.canvas.paste(column_canvas, (x_pos, 0))

    def update_display(self, rotate_degrees: int = 270):
        """
        Rotates the final canvas if needed and sends it to the matrix.
        Uses visual_cortex if available, fallbacks to direct matrix.
        """
        if rotate_degrees == 0:
            final_image = self.canvas
        else:
            final_image = self.canvas.rotate(rotate_degrees, expand=False) 
            
        try:
            if final_image.width != self.width or final_image.height != self.height:
                 print(f"Error: Final image size ({final_image.width}x{final_image.height}) after rotation does not match matrix size ({self.width}x{self.height}). Resizing.")
                 final_image = final_image.resize((self.width, self.height))
                 
            # Use visual_cortex if available, otherwise direct matrix
            if self.visual_cortex and hasattr(self.visual_cortex, 'set_image'):
                # Use the async method if possible
                import asyncio
                try:
                    asyncio.get_event_loop().run_until_complete(self.visual_cortex.set_image(final_image))
                except:
                    # Fallback to direct method
                    self.visual_cortex.set_image(final_image)
            elif self._matrix:
                self._matrix.SetImage(final_image)
            else:
                print("Warning: No matrix available to update display")
        except Exception as e:
            print(f"Error updating matrix display: {e}") 