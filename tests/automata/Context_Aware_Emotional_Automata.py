import time
import random
import hashlib
from PIL import Image, ImageDraw
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import collections

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
EMOTION_COLORS = {
    "red": (255, 0, 0),        # Passion
    "orange": (255, 127, 0),   # Creativity
    "yellow": (255, 255, 0),   # Connection
    "green": (0, 255, 0),      # Growth
    "blue": (0, 0, 255),       # Calm
    "indigo": (75, 0, 130),    # Insight
    "violet": (148, 0, 211),   # Flow
}
GREY = (40, 40, 40)  # Emotionally numb but alive

# === CELL STRUCTURE ===
class Cell:
    def __init__(self):
        self.alive = False
        self.color = (0, 0, 0)
        self.age = 0
        self.structure_id = None
        self.emotions = {k: 0.0 for k in EMOTION_COLORS}

    def dominant_emotion(self):
        nonzero = [(k, v) for k, v in self.emotions.items() if v > 0.5]
        if not nonzero:
            return None
        max_val = max(nonzero, key=lambda x: x[1])[1]
        top = [EMOTION_COLORS[k] for k, v in nonzero if v == max_val]
        return tuple(sum(c[i] for c in top) // len(top) for i in range(3))

    def update_emotions(self, event, context=None):
        if event == "isolation":
            self.emotions["yellow"] = max(0, self.emotions["yellow"] - 2)
            self.emotions["blue"] = min(10, self.emotions["blue"] + 1)
        elif event == "conflict":
            self.emotions["green"] = max(0, self.emotions["green"] - 2)
            self.emotions["red"] = min(10, self.emotions["red"] + 2)
        elif event == "crowded":
            self.emotions["orange"] = min(10, self.emotions["orange"] + 1)
            self.emotions["indigo"] = min(10, self.emotions["indigo"] + 1)
        elif event == "aged":
            self.emotions["green"] = min(10, self.emotions["green"] + 1)
            self.emotions["violet"] = min(10, self.emotions["violet"] + 1)

        # Passive decay
        for k in self.emotions:
            self.emotions[k] = max(0.0, self.emotions[k] - 0.1)

# === GRID INIT ===
grid = [[Cell() for _ in range(WIDTH)] for _ in range(HEIGHT)]

def neighbors(x, y):
    coords = [(x+dx, y+dy) for dx in (-1,0,1) for dy in (-1,0,1) if not (dx==0 and dy==0)]
    return [((cx + WIDTH) % WIDTH, (cy + HEIGHT) % HEIGHT) for cx, cy in coords]

def seed_random_cells(count=400):
    for _ in range(count):
        x, y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)
        grid[y][x].alive = True
        for k in grid[y][x].emotions:
            grid[y][x].emotions[k] = random.uniform(0, 3)

def update():
    global grid
    new_grid = [[Cell() for _ in range(WIDTH)] for _ in range(HEIGHT)]

    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = grid[y][x]
            alive_neighbors = sum(1 for nx, ny in neighbors(x, y) if grid[ny][nx].alive)

            if cell.alive:
                if alive_neighbors in (2, 3):
                    new_grid[y][x].alive = True
                    new_grid[y][x].emotions = cell.emotions.copy()
                    new_grid[y][x].age = cell.age + 1

                    if alive_neighbors <= 1:
                        new_grid[y][x].update_emotions("isolation")
                    elif alive_neighbors >= 6:
                        new_grid[y][x].update_emotions("crowded")
                    if cell.age > 20:
                        new_grid[y][x].update_emotions("aged")
                else:
                    new_grid[y][x].update_emotions("conflict")
            else:
                if alive_neighbors == 3:
                    new_grid[y][x].alive = True
                    e = {k: 0.0 for k in EMOTION_COLORS}
                    for nx, ny in neighbors(x, y):
                        for k in e:
                            e[k] += grid[ny][nx].emotions[k]
                    for k in e:
                        e[k] = min(10, e[k] / 3)

                    # Mutation layer
                    for k in random.sample(list(EMOTION_COLORS.keys()), 2):
                        e[k] += random.uniform(0.3, 1.2)

                    new_grid[y][x].emotions = e

    grid = new_grid

def draw():
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    emotion_counter = collections.Counter()
    alive_count = 0

    for y in range(HEIGHT):
        for x in range(WIDTH):
            cell = grid[y][x]
            screen_y = HEIGHT - 1 - y
            if cell.alive:
                alive_count += 1
                dominant = cell.dominant_emotion()
                if dominant:
                    cell.color = dominant
                    for emotion, value in cell.emotions.items():
                        if value == max(cell.emotions.values()):
                            emotion_counter[emotion] += 1
                else:
                    cell.color = GREY
                draw.point((x, screen_y), fill=cell.color)
            else:
                draw.point((x, screen_y), fill=(0, 0, 0))

    matrix.SetImage(img)

    # Console Output
    print(f"\n🧬 Alive Cells: {alive_count}")
    for emotion in EMOTION_COLORS:
        print(f"{emotion.capitalize():<8}: {emotion_counter[emotion]}")
    print("-" * 40)

# === MAIN LOOP ===
seed_random_cells()
try:
    while True:
        update()
        draw()
        time.sleep(0.1)
except KeyboardInterrupt:
    matrix.Clear()