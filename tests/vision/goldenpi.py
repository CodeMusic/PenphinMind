#!/usr/bin/env python3

import time
import math
import numpy as np
from rgbmatrix import RGBMatrix, RGBMatrixOptions

class FractalConsciousness:
    """
    Creates a visual representation of consciousness as a fractal pattern
    using mathematical constants and cellular automata.
    """
    
    def __init__(self):
        """
        Initialize the perceptual framework for fractal generation.
        """
        # Matrix configuration for visual stimulus representation
        self.options = RGBMatrixOptions()
        self.options.rows = 64
        self.options.cols = 64
        self.options.chain_length = 1
        self.options.parallel = 1
        self.options.hardware_mapping = 'regular'
        self.options.brightness = 30
        self.options.disable_hardware_pulsing = True
        
        # Collective consciousness canvas
        self.matrix = RGBMatrix(options=self.options)
        
        # Archetype constants that shape natural patterns
        self.phi = (1 + math.sqrt(5)) / 2  # Golden ratio (1.618...)
        self.pi = math.pi
        
        # Cellular memory grid (for Game of Life)
        self.grid = np.zeros((self.options.rows, self.options.cols), dtype=np.int8)
        self.next_grid = np.zeros((self.options.rows, self.options.cols), dtype=np.int8)
        
        # Seed the initial pattern based on mathematical constants
        self._seed_initial_state()
    
    def _seed_initial_state(self):
        """
        Creates the initial cognitive state using mathematical constants.
        """
        # Use pi digits to create initial patterns
        pi_str = str(self.pi).replace('.', '')
        
        for i in range(min(len(pi_str), self.options.rows * self.options.cols)):
            row = i // self.options.cols
            col = i % self.options.cols
            # Convert digit to binary (0 or 1) with threshold at 5
            self.grid[row, col] = 1 if int(pi_str[i]) >= 5 else 0
            
        # Add some pattern based on golden ratio positions
        for i in range(20):
            pos = int((self.phi * i * 10) % (self.options.rows * self.options.cols))
            row = pos // self.options.cols
            col = pos % self.options.cols
            self.grid[row, col] = 1
    
    def _update_life_cycle(self):
        """
        Updates the cellular consciousness through one Game of Life generation.
        """
        for i in range(self.options.rows):
            for j in range(self.options.cols):
                # Count neighbors (wrapping at boundaries for toroidal universe)
                neighbors = 0
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        if di == 0 and dj == 0:
                            continue
                        ni = (i + di) % self.options.rows
                        nj = (j + dj) % self.options.cols
                        neighbors += self.grid[ni, nj]
                
                # Apply Game of Life rules
                if self.grid[i, j] == 1:
                    # Cell lives on if it has 2 or 3 neighbors
                    self.next_grid[i, j] = 1 if neighbors in [2, 3] else 0
                else:
                    # Cell is born if it has exactly 3 neighbors
                    self.next_grid[i, j] = 1 if neighbors == 3 else 0
        
        # Update grid for next generation
        self.grid, self.next_grid = self.next_grid.copy(), np.zeros_like(self.grid)
    
    def _get_color(self, row, col, generation):
        """
        Determines color based on position, cell state, and mathematical constants.
        """
        if self.grid[row, col] == 0:
            return (0, 0, 0)  # Dead cells are black
        
        # Use golden ratio and pi to create color variations
        angle = (row / self.options.rows + col / self.options.cols) * 2 * self.pi
        phi_factor = (self.phi * generation) % 1.0
        
        # Create a circular gradient using sin/cos waves
        r = int(128 + 127 * math.sin(angle + generation * 0.05))
        g = int(128 + 127 * math.sin(self.phi * angle + generation * 0.08))
        b = int(128 + 127 * math.cos(self.pi * angle + generation * 0.12))
        
        # Apply golden ratio intensity modulation
        intensity = 0.5 + 0.5 * math.sin(generation * 0.01 * self.phi)
        r = int(r * intensity)
        g = int(g * intensity)
        b = int(b * intensity)
        
        return (r % 256, g % 256, b % 256)
    
    def _render_collective_perception(self, generation):
        """
        Renders the current state to the LED matrix with fractal-inspired colors.
        """
        for row in range(self.options.rows):
            for col in range(self.options.cols):
                r, g, b = self._get_color(row, col, generation)
                self.matrix.SetPixel(col, row, r, g, b)
    
    def manifest_fractal_consciousness(self):
        """
        Main loop to generate and display the evolving fractal pattern.
        """
        try:
            generation = 0
            while True:
                self._render_collective_perception(generation)
                self._update_life_cycle()
                generation += 1
                time.sleep(0.1)  # Control speed of evolution
        except KeyboardInterrupt:
            # Graceful exit on Ctrl+C
            self.matrix.Clear()

if __name__ == "__main__":
    fractal_mind = FractalConsciousness()
    fractal_mind.manifest_fractal_consciousness()
