import time
import random
import math
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw

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

WIDTH, HEIGHT = matrix.width, matrix.height
STATUS_BAR_HEIGHT = 17
MAIN_HEIGHT = HEIGHT - STATUS_BAR_HEIGHT
CHAR_RADIUS = 2
TRAIL_LENGTH = 40

# === COLOR UTILS ===
def hue_to_rgb(hue):
    h = float(hue) / 60.0
    c = 255
    x = int((1 - abs(h % 2 - 1)) * c)
    h = int(h)
    return [
        (c, x, 0), (x, c, 0), (0, c, x),
        (0, x, c), (x, 0, c), (c, 0, x)
    ][h % 6]

def color_distance(h1, h2):
    return min(abs(h1 - h2), 360 - abs(h1 - h2))

def attraction_strength(h1, h2):
    return max(0.1, 1 - color_distance(h1, h2) / 180)

# === LIFEFORM ===
class LifeForm:
    def __init__(self, x, y, hue):
        self.x = x
        self.y = y
        self.hue = hue
        self.original_hue = hue
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.path = []

    def rgb(self):
        return hue_to_rgb(self.hue)

    def update_heading(self, target):
        dx = target.x - self.x
        dy = target.y - self.y

        # Wrap-around distance
        if abs(dx) > WIDTH / 2:
            dx -= math.copysign(WIDTH, dx)
        if abs(dy) > MAIN_HEIGHT / 2:
            dy -= math.copysign(MAIN_HEIGHT, dy)

        # Normalize attraction vector
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx /= dist
        dy /= dist

        # Get attraction weight
        weight = attraction_strength(self.hue, target.hue) * 0.05

        # Apply attraction + noise
        self.vx = 0.95 * self.vx + weight * dx + random.uniform(-0.02, 0.02)
        self.vy = 0.95 * self.vy + weight * dy + random.uniform(-0.02, 0.02)

        # Limit speed
        mag = math.hypot(self.vx, self.vy)
        if mag > 1.5:
            self.vx *= 1.5 / mag
            self.vy *= 1.5 / mag

    def move(self):
        self.x = (self.x + self.vx) % WIDTH
        self.y = STATUS_BAR_HEIGHT + ((self.y + self.vy - STATUS_BAR_HEIGHT) % MAIN_HEIGHT)
        
        # Turn purple in the title area (temporary effect)
        if self.y < STATUS_BAR_HEIGHT:
            self.hue = 270  # Purple
        else:
            self.hue = self.original_hue
            
        self.path.append((int(self.x), int(self.y), self.hue))
        if len(self.path) > TRAIL_LENGTH:
            self.path.pop(0)

# === CONSTRUCTION GRID ===
class ConstructGrid:
    def __init__(self, width, height):
        self.grid = [[None for _ in range(width)] for _ in range(height)]

    def seed_path(self, path):
        for x, y, hue in path:
            if STATUS_BAR_HEIGHT <= y < HEIGHT and 0 <= x < WIDTH:
                self.grid[y][x] = {'hue': hue, 'age': 0}

    def step(self):
        new_grid = [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]
        for y in range(STATUS_BAR_HEIGHT, HEIGHT):
            for x in range(WIDTH):
                neighbors = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx = (x + dx) % WIDTH
                        ny = STATUS_BAR_HEIGHT + ((y + dy - STATUS_BAR_HEIGHT) % MAIN_HEIGHT)
                        n = self.grid[ny][nx]
                        if n:
                            neighbors.append(n)

                current = self.grid[y][x]
                count = len(neighbors)
                if current and count in [2, 3]:
                    new_grid[y][x] = {'hue': current['hue'], 'age': current['age'] + 1}
                elif not current and count == 3:
                    hue_avg = sum(n['hue'] for n in neighbors) / 3
                    new_grid[y][x] = {'hue': hue_avg % 360, 'age': 0}
        self.grid = new_grid

    def draw(self, draw):
        for y in range(STATUS_BAR_HEIGHT, HEIGHT):
            for x in range(WIDTH):
                cell = self.grid[y][x]
                if cell:
                    draw.point((x, y), fill=hue_to_rgb(int(cell['hue'])))

# === INIT ===
red = LifeForm(10, STATUS_BAR_HEIGHT + MAIN_HEIGHT // 2, 0)
violet = LifeForm(WIDTH - 10, STATUS_BAR_HEIGHT + MAIN_HEIGHT // 2, 270)
construct = ConstructGrid(WIDTH, HEIGHT)

# === MAIN LOOP ===
tick = 0
try:
    while True:
        img = Image.new("RGB", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(img)

        # Draw title bar with light purple background
        for y in range(STATUS_BAR_HEIGHT):
            for x in range(WIDTH):
                draw.point((x, y), fill=(180, 160, 220))  # Light purple background

        # Draw PENPHIN text in gold at top
        gold_color = (255, 215, 0)  # Gold color
        draw.text((12, 5), "PENPHIN", fill=gold_color)
        
        # Draw MIND text in gold at bottom
        draw.text((20, HEIGHT - 12), "MIND", fill=gold_color)

        # Update headings & movement
        red.update_heading(violet)
        violet.update_heading(red)
        red.move()
        violet.move()

        # Update field
        construct.seed_path(red.path + violet.path)
        construct.step()
        construct.draw(draw)

        # Draw lifeforms
        draw.ellipse((red.x - CHAR_RADIUS, red.y - CHAR_RADIUS, red.x + CHAR_RADIUS, red.y + CHAR_RADIUS), fill=red.rgb())
        draw.ellipse((violet.x - CHAR_RADIUS, violet.y - CHAR_RADIUS, violet.x + CHAR_RADIUS, violet.y + CHAR_RADIUS), fill=violet.rgb())

        # Rotate image 180 degrees
        img = img.rotate(180)
        
        # Display
        matrix.SetImage(img)
        time.sleep(0.05)
        tick += 1

except KeyboardInterrupt:
    matrix.Clear()
    print("🧠 Life ended.")