import time
import random
import hashlib
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

# === COLOR DEFINITIONS ===
ROYGBIV = [
    (255, 0, 0),       # Red
    (255, 127, 0),     # Orange
    (255, 255, 0),     # Yellow
    (0, 255, 0),       # Green
    (0, 0, 255),       # Blue
    (75, 0, 130),      # Indigo
    (148, 0, 211)      # Violet
]

COLOR_TOLERANCE = 60

# === CELL STRUCTURE ===
class Cell:
    def __init__(self):
        self.alive = False
        self.color = (0, 0, 0)
        self.age = 0
        self.structure_id = None


grid = [[Cell() for _ in range(WIDTH)] for _ in range(HEIGHT)]
structure_counter = 1
structure_history = {}
structure_stability = {}
structure_color = {}

# === INIT ===
def seed_random_cells(count=400):
    for _ in range(count):
        x, y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)
        grid[y][x].alive = True

# === UTILITY ===
def neighbors(x, y):
    coords = [(x+dx, y+dy) for dx in (-1,0,1) for dy in (-1,0,1) if not (dx==0 and dy==0)]
    return [(cx % WIDTH, cy % HEIGHT) for cx, cy in coords]

def color_distance(c1, c2):
    return sum((a-b)**2 for a,b in zip(c1,c2)) ** 0.5

def average_color(c1, c2):
    return tuple((a + b) // 2 for a, b in zip(c1, c2))

def get_structure_hash(cells):
    return hashlib.md5("".join(f"{x},{y}" for x, y in sorted(cells)).encode()).hexdigest()

def flood_fill_structure(x, y, visited):
    stack = [(x, y)]
    cluster = set()
    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))
        cell = grid[cy][cx]
        if cell.alive:
            cluster.add((cx, cy))
            for nx, ny in neighbors(cx, cy):
                stack.append((nx, ny))
    return cluster

# === AUTOMATA CORE ===
def update():
    global grid, structure_counter
    new_grid = [[Cell() for _ in range(WIDTH)] for _ in range(HEIGHT)]
    id_assignment = {}
    visited = set()

    # Assign structure IDs to clusters
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if grid[y][x].alive and (x, y) not in visited:
                cluster = flood_fill_structure(x, y, visited)
                hash_val = get_structure_hash(cluster)
                existing_id = None
                for sid, h in structure_history.items():
                    if h == hash_val:
                        existing_id = sid
                        break
                sid = existing_id if existing_id else structure_counter
                if not existing_id:
                    structure_counter += 1
                structure_history[sid] = hash_val
                structure_stability[sid] = structure_stability.get(sid, 0) + 1
                if structure_stability[sid] > 15 and sid not in structure_color:
                    structure_color[sid] = random.choice(ROYGBIV)
                for cx, cy in cluster:
                    id_assignment[(cx, cy)] = sid

    # Apply Game of Life rules
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = grid[y][x]
            alive_neighbors = 0
            same_color_neighbors = 0
            neighbor_colors = []

            for nx, ny in neighbors(x, y):
                n_cell = grid[ny][nx]
                if n_cell.alive:
                    neighbor_colors.append(n_cell.color)
                    alive_neighbors += 1

            if cell.alive:
                if alive_neighbors in (2,3):
                    new_grid[y][x].alive = True
                    new_grid[y][x].age = cell.age + 1
            else:
                if alive_neighbors == 3:
                    new_grid[y][x].alive = True
                    new_grid[y][x].age = 1

    # Color update pass
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if new_grid[y][x].alive:
                sid = id_assignment.get((x, y))
                new_grid[y][x].structure_id = sid
                if sid in structure_color:
                    new_grid[y][x].color = structure_color[sid]
                else:
                    new_grid[y][x].color = (255, 255, 255)

    # Emit colored pixel from matured structures
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = new_grid[y][x]
            sid = cell.structure_id
            if cell.alive and sid in structure_color and cell.age > 15:
                if random.random() < 0.01:
                    dx, dy = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
                    ex, ey = (x + dx) % WIDTH, (y + dy) % HEIGHT
                    if not new_grid[ey][ex].alive:
                        new_grid[ey][ex].alive = True
                        new_grid[ey][ex].color = structure_color[sid]
                        new_grid[ey][ex].structure_id = sid

    # Color merging on overlap
    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = new_grid[y][x]
            if not cell.alive or not cell.structure_id:
                continue
            sid = cell.structure_id
            for nx, ny in neighbors(x, y):
                neighbor = new_grid[ny][nx]
                if neighbor.alive and neighbor.structure_id and neighbor.structure_id != sid:
                    c1 = structure_color.get(sid)
                    c2 = structure_color.get(neighbor.structure_id)
                    if c1 and c2:
                        merged = average_color(c1, c2)
                        structure_color[sid] = merged
                        structure_color[neighbor.structure_id] = merged

    grid = new_grid

# === DRAW ===
def draw():
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = grid[y][x]
            if cell.alive:
                draw.point((x, y), fill=cell.color)
            else:
                draw.point((x, y), fill=(0, 0, 0))

    matrix.SetImage(img)

# === MAIN LOOP ===
seed_random_cells()
try:
    while True:
        update()
        draw()
        time.sleep(0.05)
except KeyboardInterrupt:
    matrix.Clear()
