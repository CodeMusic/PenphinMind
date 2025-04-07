import time
import random
import math
from PIL import Image, ImageDraw
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# === MATRIX SETUP ===
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'
options.brightness = 30
options.disable_hardware_pulsing = True
matrix = RGBMatrix(options=options)

WIDTH, HEIGHT = 64, 64
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
ROTATE = 180  # set to 90/180/270 if your panel is flipped

# === LAYOUT ===
HEADER_HEIGHT = 16
MAIN_HEIGHT = 40
AMBIENT_HEIGHT = 10

# === EMOTIONS ===
EMOTION_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),         # Passion
    "green": (0, 255, 0),       # Growth
    "blue": (0, 0, 255),        # Serenity
    "orange": (255, 165, 0),    # Creativity
    "yellow": (255, 255, 0),    # Connection
    "indigo": (20, 30, 180),    # Intuition - deeper blue with less purple
    "violet": (148, 0, 211),    # Flow
}

# Emotion word associations - using shorter terms for some emotions
EMOTION_WORDS = {
    "white": "LOGIC",
    "red": "PASSION",
    "green": "GROWTH",
    "blue": "CALM",  # Shorter than SERENITY
    "violet": "FLOW",
    "orange": "INVENT",  # Shorter than CREATIVITY
    "yellow": "CONNECT", # Shorter than CONNECTION
    "indigo": "INSIGHT"  # Alternative to INTUITION
}

PRIMARY = {"red", "green", "blue"}
DISCOVERED = ["black", "white"]
emotion_regions = {}
notification_queue = []  # Queue of emotions to display notifications for
notification_timer = 0   # Timer for current notification
current_notification = None  # Current emotion being displayed

# Define numeric values for each color
COLOR_VALUES = {
    "white": 0,
    "red": 1,
    "orange": 2,
    "yellow": 3,
    "green": 4,
    "blue": 5,
    "indigo": 6,
    "violet": 7
}

def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return (int(v*255),)*3
    i = int(h*6.)
    f = h*6. - i
    i %= 6
    v, p, q, t = int(255*v), int(255*v*(1-s)), int(255*v*(1-s*f)), int(255*v*(1-s*(1-f)))
    return [(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)][i]

def blend_colors(c1, c2):
    return tuple((c1[i] + c2[i]) // 2 for i in range(3))

def closest_emotion(color):
    for name, val in EMOTION_COLORS.items():
        if color == val:
            return name
    return None

# === GAME OF LIFE HEADER - Enhanced with Contextual Feedback Model ===
# Each cell now has state (emotion color), memory (past emotions), and context sensitivity

class CellularAutomatonCell:
    def __init__(self, color="black"):
        self.state = color  # Current emotion/color
        self.memory = [color, color, color]  # Recent emotional history
        self.context_score = 0.5  # Sensitivity to environment (0.0-1.0)
        self.alive = color != "black"  # Cell is alive if it has a color
    
    def update_memory(self):
        """Shift memory and store current state at front"""
        self.memory.pop()  # Remove oldest memory
        self.memory.insert(0, self.state)  # Add current state to front

# Initialize CFCA grid for header
header_cells = [[CellularAutomatonCell() for _ in range(WIDTH)] for _ in range(HEADER_HEIGHT)]
header_update_counter = 0

def initialize_header_cells():
    """Initialize the CFCA with structured patterns based on available emotions"""
    global header_cells
    
    # Reset all cells to black/dead
    header_cells = [[CellularAutomatonCell() for _ in range(WIDTH)] for _ in range(HEADER_HEIGHT)]
    
    # Get available colors
    unlocked_colors = [color for color in DISCOVERED if color not in ["black"]]
    complexity = len(unlocked_colors)
    
    # For initial state, start with standard Game of Life patterns
    if complexity <= 1:  # Only white/logic is available
        # Add a single small pattern in center (block)
        center_x, center_y = WIDTH // 2, HEADER_HEIGHT // 2
        
        # Create a 2x2 block (stable pattern)
        for dx in range(2):
            for dy in range(2):
                x, y = center_x - 1 + dx, center_y - 1 + dy
                if 0 <= x < WIDTH and 0 <= y < HEADER_HEIGHT:
                    header_cells[y][x].state = "white"
                    header_cells[y][x].memory = ["white", "white", "white"]
                    header_cells[y][x].alive = True
    else:
        # Multiple colors available - create more interesting patterns
        patterns = [
            # Block (stable)
            [(0,0), (0,1), (1,0), (1,1)],
            
            # Blinker (period 2 oscillator)
            [(0,0), (0,1), (0,2)],
            
            # Glider (moving pattern)
            [(0,1), (1,2), (2,0), (2,1), (2,2)],
            
            # Beacon (period 2 oscillator)
            [(0,0), (0,1), (1,0), (2,3), (3,2), (3,3)],
            
            # Toad (period 2 oscillator)
            [(1,1), (1,2), (1,3), (2,0), (2,1), (2,2)]
        ]
        
        # Place patterns with different colors
        num_patterns = min(complexity + 1, len(patterns))
        for i in range(num_patterns):
            pattern = patterns[i]
            
            # Choose color for this pattern
            if i < len(unlocked_colors):
                color = unlocked_colors[i]
            else:
                color = random.choice(unlocked_colors)
            
            # Place at random location
            start_x = random.randint(5, WIDTH - 10)
            start_y = random.randint(2, HEADER_HEIGHT - 4)
            
            # Create pattern
            for dx, dy in pattern:
                x, y = (start_x + dx) % WIDTH, (start_y + dy) % HEADER_HEIGHT
                header_cells[y][x].state = color
                header_cells[y][x].memory = [color, color, color]
                header_cells[y][x].alive = True
                header_cells[y][x].context_score = 0.7  # Higher initial context

def update_header_cells(tick):
    """Update the header CFCA based on the Contextual Feedback Model"""
    global header_cells, header_update_counter
    
    # Calculate update interval based on emotional complexity
    unlocked_colors = [color for color in DISCOVERED if color not in ["black"]]
    complexity = len(unlocked_colors)
    
    # Update interval decreases (faster updates) with more emotions
    update_interval = max(2, 5 - complexity // 2)
    
    # Only update cells at calculated interval
    header_update_counter += 1
    if header_update_counter < update_interval:
        return
    
    header_update_counter = 0
    
    # Create copy of current state for update
    new_cells = [[CellularAutomatonCell() for _ in range(WIDTH)] for _ in range(HEADER_HEIGHT)]
    for y in range(HEADER_HEIGHT):
        for x in range(WIDTH):
            new_cells[y][x].state = header_cells[y][x].state
            new_cells[y][x].memory = header_cells[y][x].memory.copy()
            new_cells[y][x].context_score = header_cells[y][x].context_score
            new_cells[y][x].alive = header_cells[y][x].alive
    
    # Calculate emotion distribution for balanced evolution
    emotion_counts = {}
    for color in unlocked_colors + ["black", "white"]:
        emotion_counts[color] = 0
    
    live_cells = 0
    for y in range(HEADER_HEIGHT):
        for x in range(WIDTH):
            if header_cells[y][x].alive:
                live_cells += 1
                color = header_cells[y][x].state
                if color in emotion_counts:
                    emotion_counts[color] += 1
    
    # Normalize counts
    if live_cells > 0:
        for color in emotion_counts:
            emotion_counts[color] /= live_cells
    
    # Ensure minimum cell activity - add new patterns if too few cells
    if live_cells < WIDTH * HEADER_HEIGHT * 0.1 and random.random() < 0.3:
        # Add new seed patterns when field gets too empty
        # Instead of calling add_seed_pattern, inline the code here
        if not unlocked_colors:
            unlocked_colors = ["white"]
        
        # Choose a random pattern to inject
        pattern = random.choice([
            # Block (stable)
            [(0,0), (0,1), (1,0), (1,1)],
            
            # Blinker (period 2 oscillator)
            [(0,0), (0,1), (0,2)],
            
            # Glider (moving pattern)
            [(0,1), (1,2), (2,0), (2,1), (2,2)]
        ])
        
        # Choose random color and position
        color = random.choice(unlocked_colors)
        start_x = random.randint(5, WIDTH - 10)
        start_y = random.randint(2, HEADER_HEIGHT - 4)
        
        # Create pattern
        for dx, dy in pattern:
            x, y = (start_x + dx) % WIDTH, (start_y + dy) % HEADER_HEIGHT
            new_cells[y][x].alive = True
            new_cells[y][x].state = color
            new_cells[y][x].memory = [color, color, color]
            new_cells[y][x].context_score = 0.7  # Higher initial context
    
    # Update each cell based on CFM principles
    for y in range(HEADER_HEIGHT):
        for x in range(WIDTH):
            current_cell = header_cells[y][x]
            new_cell = new_cells[y][x]
            
            # Count neighbors and gather context influences
            neighbors = []
            neighbor_colors = []
            total_context = 0
            
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    nx, ny = (x + dx) % WIDTH, (y + dy) % HEADER_HEIGHT
                    neighbor = header_cells[ny][nx]
                    
                    if neighbor.alive:
                        neighbors.append(neighbor)
                        neighbor_colors.append(neighbor.state)
                    
                    # Add context influence from all neighbors
                    total_context += neighbor.context_score
            
            # Live neighbors count
            live_neighbor_count = len(neighbors)
            
            # Calculate dominant emotion in neighborhood
            color_frequency = {}
            for color in neighbor_colors:
                if color not in color_frequency:
                    color_frequency[color] = 0
                color_frequency[color] += 1
            
            dominant_color = "black"
            dominant_count = 0
            for color, count in color_frequency.items():
                if count > dominant_count:
                    dominant_count = count
                    dominant_color = color
            
            # Calculate neighbor context average (higher values = more sensitive cell)
            avg_context = total_context / 8  # 8 neighbors total
            
            # Update context score based on CFM principles (environment influences context)
            # Higher complexity = more dramatic context adjustments
            context_adjust_rate = 0.05 + (complexity / 25)  # 0.05 to 0.15
            harmony = dominant_count / max(1, live_neighbor_count)  # How uniform are neighbors?
            
            # Context adjustment based on neighborhood harmony
            new_cell.context_score = (new_cell.context_score * (1 - context_adjust_rate) + 
                                     (avg_context * 0.5 + harmony * 0.5) * context_adjust_rate)
            
            # Ensure context stays in reasonable range
            new_cell.context_score = max(0.1, min(0.9, new_cell.context_score))
            
            # Apply CFCA rules based on current phase (emotion complexity)
            # === PHASE 0: Basic Game of Life (white/black only) ===
            if complexity <= 1:
                # Classic Conway rules with context influence
                if current_cell.alive:  # Cell is alive
                    # Cell survives with 2-3 neighbors (context can add slight variation)
                    context_bonus = int(current_cell.context_score * 2) - 1  # -1 to +1
                    survival = 2 <= (live_neighbor_count + context_bonus) <= 3
                    
                    if survival:
                        new_cell.alive = True
                        new_cell.state = "white"  # Only white in phase 0
                    else:
                        new_cell.alive = False
                        new_cell.state = "black"
                else:  # Cell is dead
                    # Birth with exactly 3 neighbors
                    birth = live_neighbor_count == 3
                    
                    if birth:
                        new_cell.alive = True
                        new_cell.state = "white"  # Only white in phase 0
                    else:
                        new_cell.alive = False
                        new_cell.state = "black"
            
            # === PHASE 1+: Emotion-Aware Rules ===
            else:
                # More complex rules that depend on emotions and context
                if current_cell.alive:  # Cell is alive
                    # Base survival still follows Conway, but with color-specific modifications
                    current_color = current_cell.state
                    
                    # Context-adjusted survival threshold
                    min_neighbors = 2
                    max_neighbors = 3
                    
                    # Emotion-specific survival rules
                    if current_color == "red" and complexity >= 2:  # PASSION: more energetic
                        # Red cells are more resilient but need energy
                        survival = live_neighbor_count >= 1 and live_neighbor_count <= 4
                        # Red can occasionally ignite nearby cells
                        if random.random() < 0.1 and live_neighbor_count >= 2:
                            # Mark a random dead neighbor for birth
                            empty_neighbors = []
                            for dy in [-1, 0, 1]:
                                for dx in [-1, 0, 1]:
                                    if dx == 0 and dy == 0:
                                        continue
                                    nx, ny = (x + dx) % WIDTH, (y + dy) % HEADER_HEIGHT
                                    if not header_cells[ny][nx].alive:
                                        empty_neighbors.append((nx, ny))
                            
                            if empty_neighbors and random.random() < 0.3:
                                nx, ny = random.choice(empty_neighbors)
                                new_cells[ny][nx].alive = True
                                new_cells[ny][nx].state = "red"
                    
                    elif current_color == "blue" and complexity >= 3:  # CALM: more stable
                        # Blue cells are more stable in harmonious areas
                        if harmony > 0.6:  # Most neighbors are same color
                            max_neighbors = 4  # Can survive with more neighbors
                        survival = min_neighbors <= live_neighbor_count <= max_neighbors
                    
                    elif current_color == "green" and complexity >= 3:  # GROWTH: spreads easily
                        # Green cells thrive and spread
                        survival = live_neighbor_count >= 2  # Need less to survive
                        # Can sometimes reproduce even when isolated
                        if random.random() < 0.05 and not survival:
                            survival = True
                    
                    elif current_color == "violet" and complexity >= 4:  # FLOW: harmonious
                        # Violet thrives in mixed environments
                        color_diversity = len(color_frequency)
                        if color_diversity >= 2:  # Multiple colors present
                            survival = live_neighbor_count >= 2  # Easier survival in diverse area
                        else:
                            survival = 2 <= live_neighbor_count <= 3  # Normal rules
                    
                    elif current_color == "yellow" and complexity >= 4:  # CONNECTION: join others
                        # Yellow creates connections between cells
                        if live_neighbor_count >= 3:
                            # Will try to bridge between cells of same type
                            same_color_count = color_frequency.get(current_color, 0)
                            survival = same_color_count >= 2  # Survives if connecting same colors
                        else:
                            survival = live_neighbor_count == 2  # Normal survival
                    
                    elif current_color == "indigo" and complexity >= 5:  # INSIGHT: perceptive
                        # Indigo has high awareness of surroundings
                        context_bonus = int(current_cell.context_score * 3) - 1  # -1 to +2
                        survival = (1 <= live_neighbor_count + context_bonus <= 4)
                    
                    elif current_color == "orange" and complexity >= 5:  # CREATION: unpredictable
                        # Orange has chaotic, creative patterns
                        if random.random() < 0.2:  # 20% chance of defying normal rules
                            survival = not (2 <= live_neighbor_count <= 3)  # Opposite of normal
                        else:
                            survival = 2 <= live_neighbor_count <= 3  # Normal rules
                    
                    else:  # Default or white - standard rules
                        # Context-adjusted survival
                        context_bonus = int(current_cell.context_score * 2) - 1  # -1 to +1
                        survival = min_neighbors <= (live_neighbor_count + context_bonus) <= max_neighbors
                    
                    # Apply survival outcome
                    if survival:
                        new_cell.alive = True
                        
                        # Memory system - colors can change based on dominant neighbors
                        # High context cells are more influenced by neighbors
                        if live_neighbor_count >= 3 and random.random() < current_cell.context_score:
                            if dominant_color != "black" and dominant_count >= 3:
                                # Color transforms to match dominant neighbor
                                new_cell.state = dominant_color
                    else:
                        new_cell.alive = False
                        new_cell.state = "black"
                
                else:  # Cell is dead
                    # Birth rules with color inheritance and context sensitivity
                    base_birth = live_neighbor_count == 3  # Classic rule
                    
                    # Context and complexity add possibility for varied birth conditions
                    birth_probability = 0.0
                    
                    if live_neighbor_count == 3:
                        # Standard birth has high probability
                        birth_probability = 0.95
                    elif live_neighbor_count == 2 and complexity >= 3:
                        # With enough complexity, births can happen with 2 neighbors
                        birth_probability = 0.1 + current_cell.context_score * 0.2  # 0.1 to 0.3
                    elif live_neighbor_count == 4 and complexity >= 5:
                        # High complexity allows occasional crowded births
                        birth_probability = 0.05 + current_cell.context_score * 0.1  # 0.05 to 0.15
                    
                    # Special birth rules for higher emotions
                    if "violet" in unlocked_colors and dominant_color == "violet":
                        # Violet promotes harmony - easier births
                        birth_probability += 0.1
                    
                    if "orange" in unlocked_colors and random.random() < 0.1:
                        # Orange adds creative randomness
                        birth_probability += 0.15
                    
                    # Apply birth rule
                    birth = random.random() < birth_probability
                    
                    if birth:
                        new_cell.alive = True
                        
                        # Choose color for new cell with weighted probabilities
                        if complexity <= 1:
                            # Only white available
                            new_cell.state = "white"
                        else:
                            # Choose color with weighted probability:
                            # 1. Dominant neighbor color has high influence
                            # 2. Underrepresented colors get a boost
                            # 3. Context affects color selection
                            
                            # Start with neighbor influence
                            color_weights = {}
                            for color in unlocked_colors:
                                # Start with small base weight
                                color_weights[color] = 0.1
                            
                            # Add weight from neighbor frequency
                            for color, count in color_frequency.items():
                                if color in color_weights:
                                    color_weights[color] += count * 0.5
                            
                            # Boost underrepresented colors
                            for color in color_weights:
                                distribution = emotion_counts.get(color, 0)
                                # Lower global count = higher boost
                                balance_factor = 1.0 - min(0.8, distribution * 2)
                                color_weights[color] *= balance_factor
                            
                            # Normalize weights
                            total_weight = sum(color_weights.values()) or 1
                            for color in color_weights:
                                color_weights[color] /= total_weight
                            
                            # Choose color with weighted probability
                            r = random.random()
                            cumulative = 0
                            chosen_color = unlocked_colors[0]  # Default to first color
                            
                            for color, weight in color_weights.items():
                                cumulative += weight
                                if r <= cumulative:
                                    chosen_color = color
                                    break
                            
                            new_cell.state = chosen_color
                    else:
                        new_cell.alive = False
                        new_cell.state = "black"
            
            # Update memory
            new_cell.update_memory()
    
    # Apply enhanced patterns for higher complexity
    if complexity >= 4:
        enhance_patterns(new_cells, complexity, unlocked_colors)
    
    # Update cells
    header_cells = new_cells

def enhance_patterns(cells, complexity, unlocked_colors):
    """Add structured patterns based on complexity level"""
    
    # Calculate pattern enhancement probability based on complexity
    enhancement_chance = min(0.8, complexity * 0.15)  # Increases with complexity
    
    # Find and enhance existing structures
    for y in range(1, HEADER_HEIGHT-1):
        for x in range(1, WIDTH-1):
            # Skip dead cells for efficiency
            if not cells[y][x].alive:
                continue
            
            # Get cell's color
            cell_color = cells[y][x].state
            
            # Emotion-specific enhancements with increasing complexity
            
            # PASSION (Red): Creates energetic explosions
            if "red" in unlocked_colors and cell_color == "red" and random.random() < enhancement_chance * 0.3:
                # Create explosive pattern in random direction
                direction = random.choice([(0,1), (1,0), (0,-1), (-1,0)])
                dx, dy = direction
                
                # Create flame-like pattern
                for i in range(1, 3 + min(3, complexity // 2)):
                    nx, ny = x + dx * i, y + dy * i
                    if 0 <= nx < WIDTH and 0 <= ny < HEADER_HEIGHT:
                        # Add with decreasing probability
                        if random.random() < (4 - i) / 4:
                            cells[ny][nx].alive = True
                            cells[ny][nx].state = "red"
                            cells[ny][nx].memory = ["red", "red", "red"]
                            cells[ny][nx].context_score = 0.7
            
            # CONNECTION (Yellow): Creates bridges
            if "yellow" in unlocked_colors and complexity >= 3:
                # Check for isolated cells that could be connected
                h_line = (x > 1 and x < WIDTH-2 and 
                         cells[y][x-2].alive and not cells[y][x-1].alive and 
                         cells[y][x].alive and not cells[y][x+1].alive and cells[y][x+2].alive)
                         
                v_line = (y > 1 and y < HEADER_HEIGHT-2 and 
                         cells[y-2][x].alive and not cells[y-1][x].alive and 
                         cells[y][x].alive and not cells[y+1][x].alive and cells[y+2][x].alive)
                
                # Create bridges with yellow
                if h_line and random.random() < enhancement_chance * 0.4:
                    cells[y][x-1].alive = True
                    cells[y][x-1].state = "yellow"
                    cells[y][x+1].alive = True
                    cells[y][x+1].state = "yellow"
                
                if v_line and random.random() < enhancement_chance * 0.4:
                    cells[y-1][x].alive = True
                    cells[y-1][x].state = "yellow"
                    cells[y+1][x].alive = True
                    cells[y+1][x].state = "yellow"
            
            # GROWTH (Green): Creates organic growth
            if "green" in unlocked_colors and cell_color == "green" and complexity >= 3:
                if random.random() < enhancement_chance * 0.25:
                    # Choose a random neighbor
                    neighbors = []
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < WIDTH and 0 <= ny < HEADER_HEIGHT and not cells[ny][nx].alive:
                                neighbors.append((nx, ny))
                    
                    # Grow in random available direction
                    if neighbors:
                        nx, ny = random.choice(neighbors)
                        cells[ny][nx].alive = True
                        cells[ny][nx].state = "green"
                        cells[ny][nx].memory = ["green", "green", "green"]
                        cells[ny][nx].context_score = 0.6
            
            # FLOW (Violet): Creates swirls
            if "violet" in unlocked_colors and complexity >= 5:
                if random.random() < enhancement_chance * 0.2:
                    # Create swirl pattern around this cell
                    points = [
                        (x-1, y-1), (x, y-1), (x+1, y-1),
                        (x-1, y),               (x+1, y),
                        (x-1, y+1), (x, y+1), (x+1, y+1)
                    ]
                    # Randomly select 3-5 points to create swirl
                    selected = random.sample(points, min(len(points), random.randint(3, 5)))
                    
                    for nx, ny in selected:
                        if 0 <= nx < WIDTH and 0 <= ny < HEADER_HEIGHT:
                            # Create swirl with violet
                            if not cells[ny][nx].alive or random.random() < 0.3:
                                cells[ny][nx].alive = True
                                cells[ny][nx].state = "violet"
                                cells[ny][nx].memory = ["violet", "violet", "violet"]
                                cells[ny][nx].context_score = 0.8
            
            # PERCEPTION (Indigo): Creates stable patterns at edges
            if "indigo" in unlocked_colors and complexity >= 6:
                # Check if this is an edge of a pattern
                is_edge = False
                live_neighbors = 0
                dead_neighbors = 0
                
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < WIDTH and 0 <= ny < HEADER_HEIGHT:
                            if cells[ny][nx].alive:
                                live_neighbors += 1
                            else:
                                dead_neighbors += 1
                
                # Edge cells have both live and dead neighbors
                is_edge = live_neighbors > 0 and dead_neighbors > 0
                
                if is_edge and random.random() < enhancement_chance * 0.3:
                    # Transform to indigo
                    cells[y][x].state = "indigo"
                    cells[y][x].memory = ["indigo", "indigo", "indigo"]
                    cells[y][x].context_score = 0.9  # High perception
            
            # CREATION (Orange): Adds chaos and unpredictability
            if "orange" in unlocked_colors and complexity >= 7 and random.random() < enhancement_chance * 0.15:
                # Create a completely random pattern nearby
                for _ in range(random.randint(2, 5)):
                    dx = random.randint(-3, 3)
                    dy = random.randint(-3, 3)
                    nx, ny = x + dx, y + dy
                    
                    if 0 <= nx < WIDTH and 0 <= ny < HEADER_HEIGHT:
                        # 50% chance to set alive, 50% to set dead (true chaos)
                        if random.random() < 0.5:
                            cells[ny][nx].alive = True
                            cells[ny][nx].state = "orange"
                            cells[ny][nx].memory = ["orange", "orange", "orange"]
                            cells[ny][nx].context_score = 0.5
                        else:
                            cells[ny][nx].alive = False
                            cells[ny][nx].state = "black"

def add_seed_pattern(cells, unlocked_colors):
    """Add a new seed pattern to revitalize the field"""
    if not unlocked_colors:
        unlocked_colors = ["white"]
    
    # Choose pattern based on available colors
    if len(unlocked_colors) <= 2:
        patterns = [
            # Basic patterns for early phases
            [(0,0), (0,1), (1,0), (1,1)],  # Block
            [(0,0), (0,1), (0,2)],         # Blinker
            [(0,1), (1,2), (2,0), (2,1), (2,2)]  # Glider
        ]
    else:
        # More complex patterns for later phases
        patterns = [
            # Glider gun components
            [(0,0), (0,1), (1,0), (1,1), (2,2), (2,3), (3,2), (3,3)],  # Two blocks
            [(0,2), (1,0), (1,4), (2,5), (3,0), (3,5), (4,1), (4,2), (4,3), (4,4)],  # Ship
            [(0,0), (0,1), (0,2), (1,0), (2,1), (3,0), (3,2), (4,0)]  # Complex
        ]
    
    # Choose random pattern and color
    pattern = random.choice(patterns)
    color = random.choice(unlocked_colors)
    
    # Place at random position
    start_x = random.randint(5, WIDTH - 10)
    start_y = random.randint(2, HEADER_HEIGHT - 5)
    
    # Create pattern
    for dx, dy in pattern:
        x, y = (start_x + dx) % WIDTH, (start_y + dy) % HEADER_HEIGHT
        cells[y][x].alive = True
        cells[y][x].state = color
        cells[y][x].memory = [color, color, color]
        cells[y][x].context_score = 0.7  # Higher initial context

def draw_header(draw):
    """Draw the header with Game of Life and notifications"""
    global notification_timer, current_notification
    
    # Check if we should display a notification or update Game of Life
    if current_notification or notification_queue:
        # Handle notification display
        if notification_timer <= 0 and notification_queue:
            # Get next notification
            current_notification = notification_queue.pop(0)
            notification_timer = 20  # Show for 1 second (20 ticks at 0.05s per tick)
            
        if current_notification:
            # Draw notification background with emotion color
            draw.rectangle((0, 0, WIDTH - 3, HEADER_HEIGHT - 1), 
                         fill=EMOTION_COLORS[current_notification])
            
            # Draw emotion word in contrasting color
            word = EMOTION_WORDS.get(current_notification, "UNLOCKED")
            text_width = len(word) * 6  # Approximate width
            text_x = (WIDTH - 3 - text_width) // 2
            
            # Use black text on bright colors
            text_color = EMOTION_COLORS["black"] if current_notification in ["yellow", "orange", "green"] else EMOTION_COLORS["white"]
            draw.text((text_x, 4), word, fill=text_color)
            
            # Update timer
            notification_timer -= 1
            if notification_timer <= 0:
                current_notification = None
            
            return
    
    # Draw the CFCA cells
    for y in range(HEADER_HEIGHT):
        for x in range(WIDTH - 2):  # Avoid rightmost two columns
            cell = header_cells[y][x]
            if cell.alive:
                # Calculate color based on cell's state and context
                base_color = EMOTION_COLORS[cell.state]
                
                # Apply subtle animation based on context score - higher context = more animated
                pulse = 0.8 + 0.2 * math.sin(tick * 0.1 + x * 0.05 + y * 0.05) * cell.context_score
                
                # Apply memory effect - cells with consistent history are more stable in color
                memory_stability = 1.0
                if cell.memory[0] == cell.memory[1] == cell.memory[2]:
                    memory_stability = 1.2  # Boost brightness for stable memory
                
                # Calculate final color with all effects
                r = min(255, int(base_color[0] * pulse * memory_stability))
                g = min(255, int(base_color[1] * pulse * memory_stability))
                b = min(255, int(base_color[2] * pulse * memory_stability))
                
                # Draw cell with calculated color
                draw.point((x, y), fill=(r, g, b))
                
                # For higher context cells, add subtle glow
                if cell.context_score > 0.7 and random.random() < 0.3:
                    # Choose a random neighbor for glow
                    dx, dy = random.choice([(-1,0), (1,0), (0,-1), (0,1)])
                    nx, ny = x + dx, y + dy
                    
                    # Make sure neighbor is within bounds
                    if 0 <= nx < WIDTH - 2 and 0 <= ny < HEADER_HEIGHT:
                        # Only draw glow if neighbor is not alive
                        if not header_cells[ny][nx].alive:
                            # Semi-transparent glow effect
                            glow_r = int(base_color[0] * 0.4)
                            glow_g = int(base_color[1] * 0.4)
                            glow_b = int(base_color[2] * 0.4)
                            draw.point((nx, ny), fill=(glow_r, glow_g, glow_b))

def draw_emotion_region(draw, name, cx, cy, r):
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        x = int(cx + math.cos(rad) * r) % WIDTH
        y = int(cy + math.sin(rad) * r) % HEIGHT
        draw.point((x, y), fill=EMOTION_COLORS[name])

def discover_mix(color1, color2):
    pair = {color1, color2}
    if pair == {"red", "blue"}: return "violet"
    if pair == {"red", "green"}: return "yellow"
    if pair == {"blue", "green"}: return "indigo"
    if pair == {"red", "yellow"}: return "orange"
    return None

def draw_ambient(draw, tick):
    # More pronounced and FASTER flowing effect using unlocked colors (avoiding rightmost 2 columns)
    unlocked = [color for color in DISCOVERED if color not in ["black", "white"]]
    if not unlocked:
        unlocked = ["white"]  # Default if no colors unlocked yet
    
    # Use multiple colors with smooth transitions
    color_count = len(unlocked)
    
    for y in range(HEIGHT - AMBIENT_HEIGHT, HEIGHT):
        # Create horizontal waves of color that move MUCH faster
        for x in range(WIDTH - 2):
            # Create flowing gradients based on sin waves with increased speed
            dx = x - CENTER_X
            dy = y - (HEIGHT - AMBIENT_HEIGHT // 2)
            dist = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            
            # Create more pronounced and FASTER wave patterns that change over time
            # Increased speed multipliers from 0.05/0.03 to 0.12/0.08
            wave1 = math.sin(dist * 0.25 - tick * 0.12 + angle * 2.0)  # Faster movement
            wave2 = math.sin(dist * 0.18 - tick * 0.08 - angle * 1.5)  # Faster and different direction
            wave3 = math.cos(dist * 0.12 + tick * 0.15 + angle * 0.8)  # Third wave component for more complexity
            wave = (wave1 + wave2 + wave3) / 3  # Combine three waves for more complex pattern
            
            # Color transition based on position and time - FASTER movement
            # Create smooth transitions between colors with increased speed
            base_t = (x / (WIDTH - 2) + tick * 0.025) % 1.0  # 2.5x speed increase from 0.01 to 0.025
            
            # Determine which two colors to blend between
            color_index1 = int(base_t * color_count)
            color_index2 = (color_index1 + 1) % color_count
            
            # How much to blend (0.0 to 1.0)
            blend_amount = (base_t * color_count) % 1.0
            
            # Get the two colors
            color1 = EMOTION_COLORS[unlocked[color_index1]]
            color2 = EMOTION_COLORS[unlocked[color_index2]]
            
            # Blend between them with more dynamic movement
            r = int(color1[0] * (1-blend_amount) + color2[0] * blend_amount)
            g = int(color1[1] * (1-blend_amount) + color2[1] * blend_amount)
            b = int(color1[2] * (1-blend_amount) + color2[2] * blend_amount)
            
            # Apply stronger wave effect and more intensity
            r = min(255, max(0, r + int(wave * 70)))  # Increased from 50 to 70
            g = min(255, max(0, g + int(wave * 70)))  # Increased from 50 to 70
            b = min(255, max(0, b + int(wave * 70)))  # Increased from 50 to 70
            
            # Add occasional "flow particles" for more dynamic visual
            if random.random() < 0.01:  # 1% chance per pixel
                # Create small bright particle
                particle_intensity = random.uniform(0.7, 1.0)
                pr = min(255, int(r * particle_intensity + 40))
                pg = min(255, int(g * particle_intensity + 40))
                pb = min(255, int(b * particle_intensity + 40))
                
                draw.point((x, y), fill=(pr, pg, pb))
            else:
                draw.point((x, y), fill=(r, g, b))

# === COLOR STATUS INDICATOR ===
def draw_color_status(draw, img):
    """Draw a vertical status bar showing unlocked colors in the rightmost two columns with pulsing effect"""
    # Define the status bar position
    status_x_start = WIDTH - 2  # Rightmost two columns
    status_y_end = HEIGHT - 1   # Bottom of screen
    
    # Color order from top to bottom as specified
    color_order = ["violet", "indigo", "blue", "green", "yellow", "orange", "red", "white"]
    
    # Get unlocked colors
    unlocked_colors = [color for color in color_order if color in DISCOVERED]
    unlocked_count = len(unlocked_colors)
    total_colors = len(color_order)
    
    # Fill background of status area (all black)
    for y in range(HEIGHT):
        for x in range(status_x_start, WIDTH):
            img.putpixel((x, y), EMOTION_COLORS["black"])
    
    # Draw unlocked colors with smooth transitions between them
    segment_height = 8
    
    # First pass: Draw base color segments with pulsing fill effect
    for i, color in enumerate(color_order):
        if color in DISCOVERED:
            # Calculate position for this color based on its fixed position in color_order
            position = color_order.index(color)
            y_start = position * segment_height
            y_end = y_start + segment_height - 1
            
            # Pulsing intensity increases as we get closer to unlocking all colors
            progress_pulse = 0.5 + 0.5 * math.sin(tick * 0.2) * (unlocked_count / total_colors)
            fill_factor = 1.0 + progress_pulse * 0.3  # Makes the pulse stronger as we unlock more
            
            # Draw the color segment with pulsing effect
            for y in range(y_start, y_end + 1):
                if 0 <= y < HEIGHT:  # Ensure we're within valid range
                    # Add stronger pulsing animation to status bar - faster and more noticeable
                    wave = math.sin(y * 0.3 + tick * 0.2) * 0.4 + 0.7  # 0.3 to 1.1 range
                    # Additional pulsing based on how many colors are discovered
                    collection_pulse = 0.9 + 0.3 * math.sin(tick * 0.1) * (unlocked_count / total_colors)
                    
                    # Combined pulsing effect
                    combined_pulse = wave * collection_pulse * fill_factor
                    
                    # Get base color
                    base_color = EMOTION_COLORS[color]
                    
                    # Apply wave effect with more intensity
                    r = min(255, int(base_color[0] * combined_pulse))
                    g = min(255, int(base_color[1] * combined_pulse))
                    b = min(255, int(base_color[2] * combined_pulse))
                    
                    for x in range(status_x_start, WIDTH):
                        img.putpixel((x, y), (r, g, b))
    
    # Second pass: Blend between adjacent colors at segment boundaries
    if len(unlocked_colors) > 1:
        for i in range(len(unlocked_colors) - 1):
            top_color = unlocked_colors[i]
            bottom_color = unlocked_colors[i+1]
            
            # Find positions in color_order
            top_pos = color_order.index(top_color)
            bottom_pos = color_order.index(bottom_color)
            
            # Only blend adjacent colors
            if abs(top_pos - bottom_pos) == 1:
                # Calculate blending area
                blend_start = min(top_pos, bottom_pos) * segment_height + segment_height - 2
                blend_end = blend_start + 3  # 3 pixels of blending
                
                # Draw blended area
                for y in range(blend_start, blend_end + 1):
                    if 0 <= y < HEIGHT:
                        # Calculate blend amount (0.0 to 1.0)
                        blend = (y - blend_start) / (blend_end - blend_start)
                        
                        # Get colors
                        color1 = EMOTION_COLORS[top_color]
                        color2 = EMOTION_COLORS[bottom_color]
                        
                        # Blend colors
                        r = int(color1[0] * (1-blend) + color2[0] * blend)
                        g = int(color1[1] * (1-blend) + color2[1] * blend)
                        b = int(color1[2] * (1-blend) + color2[2] * blend)
                        
                        # Apply more intense wave animation
                        wave = math.sin(y * 0.4 + tick * 0.15) * 0.3 + 0.8  # 0.5 to 1.1 range
                        # Additional pulse based on collection progress
                        progress_pulse = 1.0 + 0.2 * math.sin(tick * 0.1) * (unlocked_count / total_colors)
                        
                        # Combined effect
                        r = int(r * wave * progress_pulse)
                        g = int(g * wave * progress_pulse)
                        b = int(b * wave * progress_pulse)
                        
                        for x in range(status_x_start, WIDTH):
                            img.putpixel((x, y), (r, g, b))
    
    # Add "filling up" visual effect at the bottom when not all colors unlocked
    if unlocked_count < total_colors:
        # Calculate how much is "filled" - increases with each color
        fill_ratio = unlocked_count / total_colors
        
        # Create a pulsing "liquid" at the bottom that rises higher with more colors
        max_fill_height = int(HEIGHT * 0.3)  # Maximum height of the liquid effect
        current_fill_height = int(max_fill_height * fill_ratio)
        
        # Add a pulsing wave to the fill height
        wave_height = int(3 * math.sin(tick * 0.2)) + current_fill_height
        
        # Draw the liquid effect at the bottom of the status bar
        for y in range(HEIGHT - wave_height, HEIGHT):
            if y >= 0:  # Ensure we're within bounds
                # Calculate a shifting color based on unlocked colors
                hue = (tick * 0.01) % 1.0
                sat = 0.8
                val = 0.8 + 0.2 * math.sin(y * 0.3 + tick * 0.2)
                
                r, g, b = hsv_to_rgb(hue, sat, val)
                
                for x in range(status_x_start, WIDTH):
                    # Get current color and blend with the fill color
                    current = img.getpixel((x, y))
                    
                    # Distance from bottom affects opacity
                    opacity = (HEIGHT - y) / wave_height * 0.5
                    
                    # Blend
                    new_r = int(current[0] * (1-opacity) + r * opacity)
                    new_g = int(current[1] * (1-opacity) + g * opacity)
                    new_b = int(current[2] * (1-opacity) + b * opacity)
                    
                    img.putpixel((x, y), (new_r, new_g, new_b))

# === ANIMATION CYCLE CONTROL ===
# Simpler cyclical animation sequence
CYCLE_PHASES = [
    "white_start",       # 0: LOGIC appears 
    "primaries_emerge",  # 1: PASSION, GROWTH, CALM emerge
    "colors_mixing",     # 2: Emotions mix to create secondary emotions
    "all_colors_active", # 3: All 7 colors/emotions active and moving
    "colors_swirl",      # 4: Emotions integrate together
    "white_return",      # 5: LOGIC emerges from integration
    "face_appears",      # 6: Smiling face appears in white
    "face_message",      # 7: "Hi I'm Penphin" message
    "fade_out"           # 8: Fade to black before repeating
]

# Each phase duration in seconds
PHASE_DURATIONS = {
    "white_start": 3,
    "primaries_emerge": 5,
    "colors_mixing": 10,
    "all_colors_active": 7,
    "colors_swirl": 5,
    "white_return": 3,
    "face_appears": 3,
    "face_message": 4,
    "fade_out": 2
}

# Function to control the animation cycle
def update_animation_cycle(current_tick):
    global current_phase, phase_timer, DISCOVERED, growing_colors, merging_colors
    global merge_progress, merge_result, final_swirl_counter
    
    # Calculate current time in seconds
    current_time = current_tick * 0.05
    
    # Update phase timer
    if phase_timer <= 0:
        # Move to next phase
        current_phase_idx = CYCLE_PHASES.index(current_phase)
        next_phase_idx = (current_phase_idx + 1) % len(CYCLE_PHASES)
        current_phase = CYCLE_PHASES[next_phase_idx]
        phase_timer = PHASE_DURATIONS[current_phase] * 20  # Convert to ticks (20 per second)
        
        # Handle phase transitions
        handle_phase_transition(current_phase)
        
        print(f"🔄 Phase change: {current_phase}")
    else:
        phase_timer -= 1
    
    # Update animation elements based on current phase
    phase_progress = 1.0 - (phase_timer / (PHASE_DURATIONS[current_phase] * 20))
    
    if current_phase == "primaries_emerge":
        update_primaries_emergence(phase_progress)
    elif current_phase == "colors_mixing":
        update_color_mixing(phase_progress)
    elif current_phase == "all_colors_active":
        update_colors_activity(phase_progress)
    elif current_phase == "colors_swirl":
        update_color_swirl(phase_progress)
    
    # Update any active color merging
    if merging_colors:
        update_color_merging()

# Handle transitions between phases
def handle_phase_transition(new_phase):
    global DISCOVERED, growing_colors, merging_colors, merge_progress, merge_result, notification_queue
    
    if new_phase == "white_start":
        # Reset to initial state
        DISCOVERED = ["black", "white"]
        growing_colors = {
            "white": {
                "pos": (CENTER_X, CENTER_Y),
                "size": 15,
                "target": (CENTER_X, CENTER_Y)
            }
        }
        merging_colors = []
        merge_progress = 0
        merge_result = None
        
        # Add notification for white/logic
        notification_queue.append("white")
        
    elif new_phase == "primaries_emerge":
        # Add primary colors but keep white
        for color in ["red", "green", "blue"]:
            if color not in DISCOVERED:
                DISCOVERED.append(color)
                # Add notification for each primary emotion
                notification_queue.append(color)
            
            # Position primaries at the corners of a triangle around white
            angle = {"red": 0, "green": 120, "blue": 240}[color]
            rad = math.radians(angle)
            distance = 15
            pos_x = CENTER_X + math.cos(rad) * distance
            pos_y = CENTER_Y + math.sin(rad) * distance
            
            growing_colors[color] = {
                "pos": (CENTER_X, CENTER_Y),  # Start at center (will move outward)
                "size": 1,  # Start small
                "target": (pos_x, pos_y)
            }
    
    elif new_phase == "colors_mixing":
        # Start with just primaries (will mix during this phase)
        secondaries = {"violet", "yellow", "indigo", "orange"}
        for color in secondaries:
            if color in growing_colors:
                del growing_colors[color]
            if color in DISCOVERED:
                DISCOVERED.remove(color)
    
    elif new_phase == "colors_swirl":
        # Ensure all 7 colors are discovered and start moving toward center
        all_colors = ["red", "green", "blue", "violet", "yellow", "indigo", "orange"]
        for color in all_colors:
            if color not in DISCOVERED:
                DISCOVERED.append(color)
                # Announce any newly discovered colors
                notification_queue.append(color)
            if color in growing_colors:
                # Start moving toward center
                growing_colors[color]["target"] = (CENTER_X, CENTER_Y)

# Update functions for each phase

def update_primaries_emergence(progress):
    # Gradually move primaries out from center and grow them
    for color in ["red", "green", "blue"]:
        if color in growing_colors:
            info = growing_colors[color]
            
            # Grow in size as they emerge
            target_size = 5 + 3 * progress  # 5 to 8
            info["size"] = min(target_size, info["size"] + 0.1)
            
            # Move from center to target position
            cx, cy = info["pos"]
            tx, ty = info["target"]
            
            # Move faster at beginning, slower at end
            move_speed = 0.05 * (1 - progress * 0.5)  
            
            # Update position
            info["pos"] = (
                cx + (tx - cx) * move_speed,
                cy + (ty - cy) * move_speed
            )

def update_color_mixing(progress):
    global merging_colors, merge_progress, merge_result
    
    # Generate all secondary colors through mixing
    # We'll trigger merges at specific points in the progress
    merge_triggers = {
        0.2: ("red", "blue", "violet"),    # Red + Blue = Violet at 20%
        0.4: ("red", "green", "yellow"),   # Red + Green = Yellow at 40% 
        0.6: ("green", "blue", "indigo"),  # Green + Blue = Indigo at 60%
        0.8: ("red", "yellow", "orange")   # Red + Yellow = Orange at 80%
    }
    
    # Check if we should start a new merge
    if not merging_colors:
        for trigger_point, (color1, color2, result) in merge_triggers.items():
            # Check if we've reached a trigger point but haven't added the result color yet
            if progress >= trigger_point and result not in DISCOVERED and color1 in growing_colors and color2 in growing_colors:
                merging_colors = [color1, color2]
                merge_progress = 0
                merge_result = result
                print(f"🔄 Starting merge: {color1} + {color2} = {result}")
                break

def update_color_merging():
    global merging_colors, merge_progress, merge_result, growing_colors, DISCOVERED, notification_queue
    
    # Continue ongoing merge
    merge_progress += 0.02  # Speed of merge
    
    # Complete merge phase
    if merge_progress >= 1.0:
        color1, color2 = merging_colors
        
        # Add the new color to discovered colors
        if merge_result not in DISCOVERED:
            DISCOVERED.append(merge_result)
            
            # Create notification message with emotion names - but don't display mixing details
            # Just show the resulting emotion notification
            notification_queue.append(merge_result)
            
            # Add the new emotion to the growing colors
            # Calculate position based on the two parent colors
            pos1 = growing_colors[color1]["pos"]
            pos2 = growing_colors[color2]["pos"]
            mid_x = (pos1[0] + pos2[0]) / 2
            mid_y = (pos1[1] + pos2[1]) / 2
            
            # Place slightly away from midpoint to avoid overlap
            angle = random.uniform(0, 2 * math.pi)
            offset_distance = 10
            target_x = mid_x + math.cos(angle) * offset_distance
            target_y = mid_y + math.sin(angle) * offset_distance
            
            growing_colors[merge_result] = {
                "pos": (mid_x, mid_y),  # Start at midpoint
                "size": 5,
                "target": (target_x, target_y)
            }
        
        # Reset for next merge
        merging_colors = []
        merge_progress = 0
        merge_result = None

def update_colors_activity(progress):
    # Keep colors moving in gentle patterns
    for color, info in growing_colors.items():
        # Add gentle drift to each color
        cx, cy = info["pos"]
        
        # Each color moves in a small circle pattern
        angle = tick * 0.03 + {"red": 0, "green": 2.1, "blue": 4.2, 
                        "violet": 0.7, "yellow": 2.8, 
                        "orange": 5.6, "indigo": 3.5}.get(color, 0)
        radius = 5 + 3 * math.sin(tick * 0.02 + color_hash(color))
        
        tx = CENTER_X + math.cos(angle) * radius * 2
        ty = CENTER_Y + math.sin(angle) * radius
        
        # Move gradually
        info["pos"] = (
            cx + (tx - cx) * 0.03,
            cy + (ty - cy) * 0.03
        )
        
        # Pulsate sizes
        base_size = 7
        pulse = math.sin(tick * 0.1 + color_hash(color)) * 2
        info["size"] = base_size + pulse

def update_color_swirl(progress):
    global final_swirl_counter
    
    # Inward spiral motion for all colors toward the center
    final_swirl_counter = int(progress * 100)  # 0 to 100
    
    # Update color positions - move toward center with increasing speed
    for color, info in growing_colors.items():
        if color == "white":
            continue  # Skip white
            
        cx, cy = info["pos"]
        tx, ty = (CENTER_X, CENTER_Y)
        
        # Accelerate toward center as progress increases
        move_speed = 0.02 + progress * 0.1
        
        # Update position
        info["pos"] = (
            cx + (tx - cx) * move_speed,
            cy + (ty - cy) * move_speed
        )
        
        # Gradually shrink as they approach center
        info["size"] = max(1, info["size"] * (1 - progress * 0.01))

# Help calculate consistent values for each color
def color_hash(color):
    color_values = {"red": 0, "green": 1, "blue": 2, "violet": 3, 
                    "yellow": 4, "orange": 5, "indigo": 6, "white": 7}
    return color_values.get(color, 0) * 1.5

# ===== MAIN ANIMATION FUNCTIONS =====

# Draw the main area with emotion colors
def draw_main_area(draw):
    global merging_colors, merge_progress, merge_result, final_swirl_counter
    
    center_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - AMBIENT_HEIGHT) // 2
    
    # Draw based on current phase
    if current_phase == "white_start":
        # Draw expanding white center
        phase_progress = 1.0 - (phase_timer / (PHASE_DURATIONS[current_phase] * 20))
        radius = int(20 * phase_progress)
        draw_pulsing_circle(draw, "white", CENTER_X, center_y, radius)
        
    elif current_phase in ["primaries_emerge", "colors_mixing", "all_colors_active"]:
        # Draw all active color centers
        for color, info in growing_colors.items():
            cx, cy = info["pos"]
            radius = int(info["size"])
            draw_pulsing_circle(draw, color, cx, cy, radius)
        
        # Draw any active color merging
        if merging_colors:
            draw_merging_colors(draw)
    
    elif current_phase == "colors_swirl":
        # Draw swirling colors moving to center
        draw_final_swirl(draw, final_swirl_counter)
    
    elif current_phase == "white_return":
        # White expands from center
        phase_progress = 1.0 - (phase_timer / (PHASE_DURATIONS[current_phase] * 20))
        radius = int(5 + 25 * phase_progress)
        draw_pulsing_circle(draw, "white", CENTER_X, center_y, radius)
    
    elif current_phase in ["face_appears", "face_message"]:
        # Draw a white background with face
        draw_face(draw, current_phase == "face_message")
    
    elif current_phase == "fade_out":
        # Fade to black
        phase_progress = 1.0 - (phase_timer / (PHASE_DURATIONS[current_phase] * 20))
        radius = int(30 * (1 - phase_progress))
        if radius > 0:
            draw_pulsing_circle(draw, "white", CENTER_X, center_y, radius)

# Draw a pulsing colored circle
def draw_pulsing_circle(draw, color, cx, cy, radius):
    # Ensure radius is an integer
    radius = int(radius)
    
    # Add gentle pulsing effect
    pulse = 0.8 + 0.2 * math.sin(tick * 0.1)
    
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        for r in range(1, radius + 1):
            # Apply pulse to radius
            actual_r = r * pulse
            x = int(cx + math.cos(rad) * actual_r)
            y = int(cy + math.sin(rad) * actual_r)
            
            # Skip if outside bounds of main area
            if not (0 <= x < WIDTH - 2 and HEADER_HEIGHT <= y < HEIGHT - AMBIENT_HEIGHT):
                continue
                
            draw.point((x, y), fill=EMOTION_COLORS[color])

# Draw the final swirl animation
def draw_final_swirl(draw, counter):
    center_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - AMBIENT_HEIGHT) // 2
    
    # Draw all color centers first
    for color, info in growing_colors.items():
        cx, cy = info["pos"]
        radius = max(1, int(info["size"]))
        
        for angle in range(0, 360, max(5, 15 - counter // 10)):
            rad = math.radians(angle)
            
            # Add spiral effect - more pronounced as counter increases
            spiral_factor = min(0.3, counter * 0.003)
            spiral_angle = rad + spiral_factor * radius
            
            for r in range(1, radius + 1):
                # Add spiral effect to position
                x = int(cx + math.cos(spiral_angle) * r)
                y = int(cy + math.sin(spiral_angle) * r)
                
                # Skip if outside bounds
                if not (0 <= x < WIDTH - 2 and HEADER_HEIGHT <= y < HEIGHT - AMBIENT_HEIGHT):
                    continue
                    
                draw.point((x, y), fill=EMOTION_COLORS[color])
    
    # Draw connecting beams between colors and center
    if counter > 20:
        # Calculate beam strength
        beam_strength = min(1.0, (counter - 20) / 60)
        
        for color, info in growing_colors.items():
            if color == "white":
                continue  # Skip white
                
            cx, cy = info["pos"]
            
            # Draw beam from color to center
            for t in range(0, 100, 10):
                t_val = t / 100
                
                # Position along beam
                x = cx + (CENTER_X - cx) * t_val
                y = cy + (center_y - cy) * t_val
                
                # Add spiral effect to beam
                spiral_factor = beam_strength * 0.1
                angle = t_val * math.pi * 6 + tick * 0.1
                
                beam_x = x + math.cos(angle) * spiral_factor * 10
                beam_y = y + math.sin(angle) * spiral_factor * 10
                
                # Skip if outside bounds
                if not (0 <= beam_x < WIDTH - 2 and HEADER_HEIGHT <= beam_y < HEIGHT - AMBIENT_HEIGHT):
                    continue
                
                # Draw beam with proper color
                draw.point((int(beam_x), int(beam_y)), fill=EMOTION_COLORS[color])
    
    # Draw white center emerging as colors converge
    if counter > 50:
        white_radius = int((counter - 50) / 5)
        if white_radius > 0:
            for angle in range(0, 360, 10):
                rad = math.radians(angle)
                for r in range(min(white_radius, 10)):
                    x = int(CENTER_X + math.cos(rad) * r)
                    y = int(center_y + math.sin(rad) * r)
                    
                    # Skip if outside bounds
                    if not (0 <= x < WIDTH - 2 and HEADER_HEIGHT <= y < HEIGHT - AMBIENT_HEIGHT):
                        continue
                        
                    draw.point((x, y), fill=EMOTION_COLORS["white"])

# Draw the color merging visualization 
def draw_merging_colors(draw):
    if not merging_colors or len(merging_colors) != 2:
        return
    
    center_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - AMBIENT_HEIGHT) // 2
    color1, color2 = merging_colors
    
    # Get positions of the two colors being merged
    pos1 = growing_colors[color1]["pos"]
    pos2 = growing_colors[color2]["pos"]
    
    # Calculate midpoint where the new color will appear
    mid_x = (pos1[0] + pos2[0]) / 2
    mid_y = (pos1[1] + pos2[1]) / 2
    
    # Get the result color
    result_color = merge_result
    
    # Calculate progress-based sizes
    size1 = growing_colors[color1]["size"] * (1.0 - merge_progress * 0.5)
    size2 = growing_colors[color2]["size"] * (1.0 - merge_progress * 0.5)
    result_size = 1.0 + merge_progress * 8.0  # Grows as merge progresses
    
    # Draw the original colors (diminishing)
    draw_pulsing_circle(draw, color1, pos1[0], pos1[1], size1)
    draw_pulsing_circle(draw, color2, pos2[0], pos2[1], size2)
    
    # Draw the result color (growing)
    if merge_progress > 0.3:  # Start showing result after 30% progress
        draw_pulsing_circle(draw, result_color, mid_x, mid_y, result_size)
    
    # Draw connecting beams between original colors and result
    beam_segments = 20
    for i in range(beam_segments):
        # First beam from color1 to result
        t1 = i / beam_segments
        x1 = pos1[0] + (mid_x - pos1[0]) * t1
        y1 = pos1[1] + (mid_y - pos1[1]) * t1
        
        # Second beam from color2 to result
        x2 = pos2[0] + (mid_x - pos2[0]) * t1
        y2 = pos2[1] + (mid_y - pos2[1]) * t1
        
        # Add pulsing animation effect
        wave = math.sin(t1 * math.pi * 3 + tick * 0.2) * 0.5 + 0.5  # 0.0 to 1.0 pulsing
        
        # Skip if outside bounds
        if (0 <= x1 < WIDTH - 2 and HEADER_HEIGHT <= y1 < HEIGHT - AMBIENT_HEIGHT):
            # Begin with first color and gradually shift to result color
            c1 = EMOTION_COLORS[color1]
            cr = EMOTION_COLORS[result_color] if result_color else (255, 255, 255)
            
            # Blend the colors based on position along beam and wave
            blend_amount = t1 * (0.5 + wave * 0.5)
            r = int(c1[0] * (1 - blend_amount) + cr[0] * blend_amount)
            g = int(c1[1] * (1 - blend_amount) + cr[1] * blend_amount)
            b = int(c1[2] * (1 - blend_amount) + cr[2] * blend_amount)
            
            # Draw with slight thickness
            draw.point((int(x1), int(y1)), fill=(r, g, b))
            
        if (0 <= x2 < WIDTH - 2 and HEADER_HEIGHT <= y2 < HEIGHT - AMBIENT_HEIGHT):
            # Begin with second color and gradually shift to result color
            c2 = EMOTION_COLORS[color2]
            cr = EMOTION_COLORS[result_color] if result_color else (255, 255, 255)
            
            # Blend the colors based on position along beam and wave
            blend_amount = t1 * (0.5 + wave * 0.5)
            r = int(c2[0] * (1 - blend_amount) + cr[0] * blend_amount)
            g = int(c2[1] * (1 - blend_amount) + cr[1] * blend_amount)
            b = int(c2[2] * (1 - blend_amount) + cr[2] * blend_amount)
            
            draw.point((int(x2), int(y2)), fill=(r, g, b))
    
    # Draw connecting circle with pulsing wave
    if merge_progress > 0.5:  # Show at 50% merge progress
        radius = 8 * merge_progress
        for angle in range(0, 360, 20):
            rad = math.radians(angle)
            # Variable radius based on angle creates wave effect
            wave_factor = 0.8 + 0.2 * math.sin(angle * 0.2 + tick * 0.3)
            wave_radius = radius * wave_factor
            
            x = int(mid_x + math.cos(rad) * wave_radius)
            y = int(mid_y + math.sin(rad) * wave_radius)
            
            # Skip if outside bounds
            if not (0 <= x < WIDTH - 2 and HEADER_HEIGHT <= y < HEIGHT - AMBIENT_HEIGHT):
                continue
                
            # Rainbow effect around the emerging emotion
            hue = (angle / 360 + tick * 0.01) % 1.0
            r, g, b = hsv_to_rgb(hue, 0.8, 0.8)
            draw.point((x, y), fill=(r, g, b))

# Draw the face animation
def draw_face(draw, show_message):
    center_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - AMBIENT_HEIGHT) // 2
    
    # Draw white background for face
    draw.rectangle((0, HEADER_HEIGHT, WIDTH - 3, HEIGHT - AMBIENT_HEIGHT - 1), fill=(30, 30, 50))
    draw.ellipse((CENTER_X - 20, center_y - 20, CENTER_X + 20, center_y + 20), fill=EMOTION_COLORS["white"])
    
    # Draw eyes
    eye_y = center_y - 5
    
    # Left eye
    left_eye_x = CENTER_X - 8
    draw.ellipse((left_eye_x - 3, eye_y - 3, left_eye_x + 3, eye_y + 3), fill=EMOTION_COLORS["black"])
    
    # Right eye
    right_eye_x = CENTER_X + 8
    draw.ellipse((right_eye_x - 3, eye_y - 3, right_eye_x + 3, eye_y + 3), fill=EMOTION_COLORS["black"])
    
    # Draw smile
    mouth_y = center_y + 8
    smile_width = 12
    
    # Draw curved smile
    for x in range(CENTER_X - smile_width, CENTER_X + smile_width + 1):
        # Calculate position along curve
        t = (x - (CENTER_X - smile_width)) / (smile_width * 2)
        y_offset = int(5 * math.sin(t * math.pi))
        draw.point((x, mouth_y + y_offset), fill=EMOTION_COLORS["black"])
        
        # Make smile thicker
        if y_offset > 0:
            draw.point((x, mouth_y + y_offset - 1), fill=EMOTION_COLORS["black"])
    
    # No message text - just show the face

# Simple header showing current phase
def draw_simple_header(draw):
    # Declare global variables
    global current_notification, notification_queue, notification_timer, current_phase, phase_timer
    
    # Fill header background
    draw.rectangle((0, 0, WIDTH - 3, HEADER_HEIGHT - 1), fill=(10, 10, 20))
    
    # Handle notification display
    if notification_timer <= 0 and notification_queue:
        # Get next notification
        current_notification = notification_queue.pop(0)
        notification_timer = 20  # Show for 1 second (20 ticks at 0.05s per tick)
        
    if current_notification:
        # Draw notification background with emotion color
        draw.rectangle((0, 0, WIDTH - 3, HEADER_HEIGHT - 1), 
                     fill=EMOTION_COLORS[current_notification])
        
        # Draw emotion word in contrasting color
        word = EMOTION_WORDS.get(current_notification, "UNLOCKED")
        text_width = len(word) * 6  # Approximate width
        text_x = (WIDTH - 3 - text_width) // 2
        
        # Use black text on bright colors
        text_color = EMOTION_COLORS["black"] if current_notification in ["yellow", "orange", "green"] else EMOTION_COLORS["white"]
        draw.text((text_x, 4), word, fill=text_color)
        
        # Update timer
        notification_timer -= 1
        if notification_timer <= 0:
            current_notification = None
    # No else clause - we don't show any text if no notification is active

# === MAIN LOOP ===
tick = 0
current_phase = "white_start"  # Start with white base
phase_timer = PHASE_DURATIONS[current_phase] * 20  # Convert to ticks (20 per second)
growing_colors = {"white": {"pos": (CENTER_X, CENTER_Y), "size": 0, "target": (CENTER_X, CENTER_Y)}}
merging_colors = []
merge_progress = 0
merge_result = None
final_swirl_counter = 0

try:
    # Main animation loop
    while True:
        # Create image and drawing context for this frame
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Update animation cycle
        update_animation_cycle(tick)
        
        # Draw the header (simplified version that shows current phase)
        draw_simple_header(draw)
        
        # Draw the main area with animation
        draw_main_area(draw)
        
        # Draw the ambient effect at the bottom
        draw_ambient(draw, tick)
        
        # Draw the color status indicator
        draw_color_status(draw, img)
        
        # Update the display with the RGB matrix
        matrix.SetImage(img.rotate(ROTATE) if ROTATE else img)
        
        # Increment tick and add small delay
        tick += 1
        time.sleep(0.05)

except KeyboardInterrupt:
    # Clean up on exit
    matrix.Clear()
    print("🧠 Emotion automaton ended.")