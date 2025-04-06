"""
Base class for all runnable modules within the Mind, like Games or Visualizers.
"""

class BaseModule:
    """Abstract base for runnable modules managed by a cortex (e.g., GameCortex)."""
    
    def __init__(self, matrix, layout_manager, config=None):
        """Initializes the module with necessary hardware/layout interfaces."""
        self.matrix = matrix # Direct matrix access (optional, layout manager preferred)
        self.layout_manager = layout_manager
        self.config = config or {}
        self.running = False
        print(f"BaseModule initialized for {self.__class__.__name__}")
        
    def initialize(self):
        """Called once when the module is launched."""
        self.running = True
        print(f"Initializing {self.__class__.__name__}")
        
    def update(self, dt):
        """Called every frame to update the module's state. dt is delta time in seconds."""
        pass
        
    def draw(self):
        """Called every frame to draw the module's visuals using the layout manager."""
        # Base draw does nothing, subclasses must implement
        pass
        
    def handle_input(self, event):
        """Handles input events (e.g., button presses)."""
        pass
        
    def cleanup(self):
        """Called once when the module is stopped."""
        self.running = False
        print(f"Cleaning up {self.__class__.__name__}") 