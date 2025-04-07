import time
import random
import math
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw

# === LED Matrix Setup ===
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'
options.brightness = 30
options.disable_hardware_pulsing = True
matrix = RGBMatrix(options=options)

WIDTH = matrix.width
HEIGHT = matrix.height

# === Layout Constants ===
TITLE_HEIGHT = 16
FOOTER_HEIGHT = 8
MAIN_HEIGHT = HEIGHT - TITLE_HEIGHT - FOOTER_HEIGHT

# === Game Constants ===
FOOD_COUNT = 10
MANA_ITEM_COUNT = 3
FOOD_RADIUS = 1
CHAR_RADIUS = 2
SPEED = 1
LIFE_UPDATE_INTERVAL = 10  # Update Game of Life every 10 frames

# === Utilities ===
def hue_to_rgb(hue):
    h = float(hue) / 60.0
    c = 255
    x = int((1 - abs(h % 2 - 1)) * c)
    h = int(h)
    return [
        (c, x, 0), (x, c, 0), (0, c, x),
        (0, x, c), (x, 0, c), (c, 0, x)
    ][h % 6]

def blend_rgb(rgb1, rgb2, t):
    return tuple(int((1 - t) * a + t * b) for a, b in zip(rgb1, rgb2))

def color_distance(h1, h2):
    return min(abs(h1 - h2), 360 - abs(h1 - h2))

# === Classes ===
class Character:
    def __init__(self, name, x, y, hue):
        self.name = name
        self.x = x
        self.y = y
        self.hue = hue
        self.target_food = None
        self.synchronized = False
        self.partner = None
        self.mana = 100
        self.path = []

    def rgb(self):
        return hue_to_rgb(self.hue)

    def move_towards(self, tx, ty):
        dx = tx - self.x
        dy = ty - self.y
        dist = max(1, math.hypot(dx, dy))
        self.x += SPEED * dx / dist
        self.y += SPEED * dy / dist
        self.path.append((int(self.x), int(self.y), self.rgb()))
        if len(self.path) > 40:
            self.path.pop(0)

    def move(self, foods):
        if not foods:
            return
        if self.synchronized and self.partner:
            hue_diff = color_distance(self.hue, self.partner.hue)
            if hue_diff > 0:
                self.hue += 1 if self.hue < self.partner.hue else -1
                self.hue %= 360
        if not self.target_food or self.target_food not in foods:
            self.target_food = min(foods, key=lambda f: math.hypot(self.x - f[0], self.y - f[1]))
        self.move_towards(*self.target_food)

    def check_food(self, foods):
        for food in foods:
            if math.hypot(self.x - food[0], self.y - food[1]) < FOOD_RADIUS + CHAR_RADIUS:
                self.hue += 20 if self.name == "Red" else -20
                self.hue %= 360
                foods.remove(food)
                return

    def check_mana(self, mana_items):
        for item in mana_items:
            if math.hypot(self.x - item[0], self.y - item[1]) < CHAR_RADIUS + 1:
                self.mana = min(150, self.mana + 10)
                mana_items.remove(item)
                return

    def try_sync(self, other):
        if color_distance(self.hue, other.hue) <= 60:
            self.synchronized = True
            self.partner = other

# === Game of Life ===
class GameOfLife:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]

    def seed(self, points):
        for x, y in points:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y][x] = 1

    def step(self):
        new_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                neighbors = sum(
                    self.grid[(y + dy) % self.height][(x + dx) % self.width]
                    for dy in [-1, 0, 1] for dx in [-1, 0, 1]
                    if (dx, dy) != (0, 0)
                )
                if self.grid[y][x] == 1 and neighbors in [2, 3]:
                    new_grid[y][x] = 1
                elif self.grid[y][x] == 0 and neighbors == 3:
                    new_grid[y][x] = 1
        self.grid = new_grid

    def draw(self, draw, color):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1:
                    draw.point((x, y), fill=color)

# === Initialization ===
red = Character("Red", 10, TITLE_HEIGHT + MAIN_HEIGHT // 2, 0)
violet = Character("Violet", WIDTH - 10, TITLE_HEIGHT + MAIN_HEIGHT // 2, 270)
characters = [red, violet]
foods = [(random.randint(0, WIDTH), random.randint(TITLE_HEIGHT, HEIGHT - FOOTER_HEIGHT)) for _ in range(FOOD_COUNT)]
mana_items = [(random.randint(0, WIDTH), random.randint(HEIGHT - FOOTER_HEIGHT, HEIGHT - 1)) for _ in range(MANA_ITEM_COUNT)]

life = GameOfLife(WIDTH, HEIGHT)
frame_count = 0
pulse = 0

# === Main Loop ===
try:
    while True:
        img = Image.new("RGB", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(img)

        # === Update Characters ===
        for char in characters:
            char.move(foods)
            char.check_food(foods)
            char.check_mana(mana_items)

except KeyboardInterrupt:
    # Clean up on exit
    matrix.Clear()
    print("🧠 Simulation Ended.")