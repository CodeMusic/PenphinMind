from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw
import time
import random

# === MATRIX SETUP ===
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'
options.brightness = 30
options.disable_hardware_pulsing = True
options.led_rgb_sequence = "RGB"
matrix = RGBMatrix(options=options)

# === TILE ENGINE CONFIG ===
TILE_SIZE = 4
GRID_ROWS = 10
GRID_COLS = 16
TOP_MARGIN = 14

# === COLORS ===
COLORS = {
    " ": (0, 0, 0),
    "C": (255, 255, 0),
    "O": (0, 0, 255),
    "X": (128, 128, 128),
    "@": (0, 255, 0),
}

# === SAMPLE LEVEL (mutable) ===
sample_level = [
    list("XXXXXXXXXXXXXXXX"),
    list("X     O       @X"),
    list("X              X"),
    list("X              X"),
    list("X   XXXXXX     X"),
    list("X        X     X"),
    list("X   C    X     X"),
    list("X        X     X"),
    list("X              X"),
    list("XXXXXXXXXXXXXXXX"),
]

# === DRAW FUNCTIONS ===
def draw_tile(draw, x, y, tile_char):
    color = COLORS.get(tile_char, (255, 0, 255))
    px = x * TILE_SIZE
    py = y * TILE_SIZE + TOP_MARGIN
    draw.rectangle([px, py, px + TILE_SIZE - 1, py + TILE_SIZE - 1], fill=color)

def draw_level(matrix, level):
    image = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(image)
    for y in range(GRID_ROWS):
        for x in range(GRID_COLS):
            draw_tile(draw, x, y, level[y][x])
    matrix.SetImage(image)

# === GAME FUNCTIONS ===
def find_player(level):
    for y, row in enumerate(level):
        for x, char in enumerate(row):
            if char == "C":
                return x, y
    return None, None

def move_player(level, dx, dy):
    x, y = find_player(level)
    if x is None:
        return
    new_x, new_y = x + dx, y + dy
    if level[new_y][new_x] == " ":
        level[y][x] = " "
        level[new_y][new_x] = "C"

def get_random_direction():
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # up, down, left, right
    return random.choice(directions)

# === MAIN LOOP ===
while True:
    # Random movement
    dx, dy = get_random_direction()
    move_player(sample_level, dx, dy)

    draw_level(matrix, sample_level)
    time.sleep(0.5)  # Slower movement for better visibility