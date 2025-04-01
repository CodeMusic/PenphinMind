import time
import random
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

# === MATRIX CONFIG ===
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'
options.brightness = 30
options.disable_hardware_pulsing = True

matrix = RGBMatrix(options=options)

# === GAME CONFIG ===
WIDTH, HEIGHT = 64, 64
grid = [[random.randint(0, 1) for _ in range(WIDTH)] for _ in range(HEIGHT)]

def count_neighbors(x, y):
    return sum(
        grid[(y + dy) % HEIGHT][(x + dx) % WIDTH]
        for dy in [-1, 0, 1]
        for dx in [-1, 0, 1]
        if not (dx == 0 and dy == 0)
    )

def update_grid():
    global grid
    new_grid = [[0]*WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            neighbors = count_neighbors(x, y)
            if grid[y][x] == 1:
                new_grid[y][x] = 1 if neighbors in [2, 3] else 0
            else:
                new_grid[y][x] = 1 if neighbors == 3 else 0
    grid = new_grid

def draw_grid():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if grid[y][x]:
                fitness = count_neighbors(x, y)  # 👈 basic "fitness" proxy
                color = (0, min(255, fitness * 40), 255 - fitness * 20)
                pixels[x, y] = color
    matrix.SetImage(image)

# === MAIN LOOP ===
try:
    while True:
        draw_grid()
        update_grid()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
    matrix.Clear()
