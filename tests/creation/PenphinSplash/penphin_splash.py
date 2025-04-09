from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import time

# === LED Matrix Setup ===
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'
options.brightness = 50
options.disable_hardware_pulsing = True
matrix = RGBMatrix(options=options)

# === Load Image ===
image = Image.open("penphin_64x64.jpg").convert("RGB")
image = image.resize((64, 64))

# === Display Image ===
for y in range(64):
    for x in range(64):
        r, g, b = image.getpixel((x, y))
        matrix.SetPixel(x, y, r, g, b)

# === Hold splash screen ===
time.sleep(5)  # Keep it on screen for 5 seconds
matrix.Clear()