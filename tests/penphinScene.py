import time
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageChops
from rgbmatrix import RGBMatrix, RGBMatrixOptions

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

WIDTH, HEIGHT = 64, 64
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
font = ImageFont.load_default()

# === COLOR UTILITIES ===
def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return (int(v*255),) * 3
    i = int(h*6.)
    f = (h*6.) - i
    p = int(255 * v * (1. - s))
    q = int(255 * v * (1. - s*f))
    t = int(255 * v * (1. - s*(1.-f)))
    v = int(255*v)
    i = i % 6
    return [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]

def scale_brightness(color, intensity):
    r, g, b = color
    return (int(r * intensity), int(g * intensity), int(b * intensity))

# === DAY COLORS ===
DAY_COLOR_MAP = {
    6: (255, 0, 0),        # Sunday
    0: (255, 165, 0),      # Monday
    1: (255, 255, 0),      # Tuesday
    2: (0, 255, 0),        # Wednesday
    3: (0, 0, 255),        # Thursday
    4: (75, 0, 130),       # Friday
    5: (148, 0, 211),      # Saturday
}

# === GLOBAL LAYOUT DATA ===
seaweed_layout = [] # Stores (x_base, base_y, height) tuples

# === HELPER TO INITIALIZE LAYOUT ===
def initialize_seaweed():
    global seaweed_layout
    if seaweed_layout: # Only run once
        return

    print("Initializing seaweed layout...") # Debug print
    rock_y_start = 49 # Rocks start here (15px tall)
    temp_img = Image.new("RGB", (1,1)) # Dummy image needed for Draw object if needed
    # Simulate rock heights to anchor seaweed realistically
    simulated_rock_tops = {}
    for rx in range(0, WIDTH, 5):
        rock_height = random.randint(4, 10)
        simulated_rock_tops[rx] = 63 - rock_height

    for rx in range(0, WIDTH, 5):
        if random.random() < 0.35: # Chance for seaweed (slightly increased)
            rock_top_y = simulated_rock_tops.get(rx, rock_y_start)
            seaweed_height = random.randint(5, 12)
            # Anchor near rock top or base line
            seaweed_base_y = max(rock_y_start, rock_top_y + random.randint(-1, 2)) 
            seaweed_base_y = min(63, seaweed_base_y) # Clamp to bottom
            seaweed_layout.append((rx + 2, seaweed_base_y, seaweed_height))
    print(f"Initialized {len(seaweed_layout)} seaweed plants.") # Debug print

# === HELPER FUNCTION FOR ROTATION ===
def set_rotated_image(img):
    matrix.SetImage(img.transpose(Image.Transpose.ROTATE_180))

# === SCENE ===
def draw_scene_base(t=0):
    # Ensure seaweed layout is generated on first call
    initialize_seaweed()

    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    island_y_start, island_y_end = 12, 14 # Moved up 2px, shorter 2px
    water_y_start = island_y_end + 1 # Starts at 15
    water_y_end = 48 # Water ends before rocks start at 49
    rock_y_start = 49 # Rocks start here (15px tall)

    # --- Background --- 
    # Always draw normal Sky & Textured Water
    draw.rectangle((0, 0, WIDTH - 1, water_y_start -1), fill=(135, 206, 235))
    base_water_color = (0, 100, 200)
    draw.rectangle((0, water_y_start, 63, water_y_end), fill=base_water_color)
    for y in range(water_y_start, water_y_end + 1, 3):
        line_intensity = 0.9 + math.sin(y * 0.5 + t * 0.1) * 0.05
        line_color = scale_brightness(base_water_color, line_intensity)
        draw.line((0, y, 63, y), fill=line_color)
    # Normal Rocks
    # draw.rectangle((0, rock_y_start, 63, 63), fill=(50, 30, 20))

    # Detailed Rock/Seaweed Layer
    rock_base_color = (40, 20, 10) # Darker base
    draw.rectangle((0, rock_y_start, 63, 63), fill=rock_base_color)
    seaweed_color = (0, 100, 0) # Dark green

    # Draw ROCKS first
    for rx in range(0, WIDTH, 5):
        rock_height = random.randint(4, 10)
        rock_y = 63 - rock_height
        rock_width = random.randint(5, 12)
        rock_color_variation = random.randint(-15, 15)
        rock_color = (50 + rock_color_variation, 30 + rock_color_variation, 20 + rock_color_variation)
        if random.random() < 0.6:
             draw.ellipse((rx, rock_y, rx + rock_width, 63), fill=rock_color)
        else:
             draw.rounded_rectangle((rx, rock_y, rx + rock_width, 63), radius=2, fill=rock_color)

    # Draw persistent, wobbling SEAWEED from layout (on top of rocks)
    for x_base, base_y, height in seaweed_layout:
        top_y = base_y - height
        # Wobble calculation (same as before)
        wobble_factor = math.sin(t * 0.5 + x_base * 0.1)
        top_offset = wobble_factor * 0.8
        base_offset = wobble_factor * -0.3
        # Draw the wobbling line
        draw.line((x_base + base_offset, base_y, x_base + top_offset, top_y), fill=seaweed_color, width=1)

    # Birds (Periodically)
    bird_period = 150 # Approx frames for a bird cycle
    birds_to_draw = []
    base_t_for_birds = int(t * 0.8) # Slow down bird time slightly
    if (base_t_for_birds // bird_period) % 2 == 0: # Appear every other cycle
         num_birds = (base_t_for_birds % 3) + 1 # 1 to 3 birds
         for i in range(num_birds):
              # Calculate horizontal position based on time within the period
              bird_progress = (base_t_for_birds % bird_period) / bird_period
              start_x = -5 - i * 8 # Stagger start position
              bird_x = start_x + bird_progress * (WIDTH + 10)
              # Vertical position with slight variation/wave
              bird_y = 5 + i * 2 + math.sin(t * 0.1 + i) * 1
              if bird_x > -2 and bird_x < WIDTH + 2: # Only draw if on screen
                   birds_to_draw.append((bird_x, bird_y))

    # Clouds (Drawn AFTER sky/background, BEFORE birds)
    for cx in range(0, 64, 24):
        offset = int((t * 2 + cx) % 64)
        draw.ellipse((offset, 2, offset + 16, 8), fill=(255, 255, 255))

    # Draw Birds (on top of clouds/sky)
    bird_color = (40, 40, 40) # Dark grey/black
    for bx, by in birds_to_draw:
         draw.line((bx - 1, by + 1, bx, by), fill=bird_color)
         draw.line((bx, by, bx + 1, by + 1), fill=bird_color)

    # Island (sand bump) - Adjusted position/size
    draw.rounded_rectangle((20, island_y_start, 44, island_y_end), radius=3, fill=(244, 164, 96))

    # Palm Tree - Adjusted trunk base to new island top
    leaves_y_end = 9
    trunk_y_start = leaves_y_end
    island_y_top = island_y_start # Connects to y=12
    draw.rectangle((31, trunk_y_start, 33, island_y_top), fill=(139, 69, 19))
    draw.rounded_rectangle((26, -5, 38, leaves_y_end), radius=4, fill=(34, 139, 34))

    return img

# === CHARACTERS ===
def draw_fish(draw, x, y, color, t):
    wiggle = math.sin(t * 0.1 + x * 0.2) * 2
    draw.ellipse((x, y + wiggle, x + 4, y + 4 + wiggle), fill=color)
    draw.polygon([(x + 5, y + 2 + wiggle), (x + 8, y + wiggle), (x + 8, y + 4 + wiggle)], fill=color)
    draw.point((x + 1, y + 1 + wiggle), fill=(0, 0, 0))

def draw_dolphin(draw, x, y):
    # Body using arcs for a curved shape
    draw.arc((x, y - 3, x + 10, y + 8), 180, 0, fill=(100, 149, 237), width=2) # Light blue outline for top
    draw.arc((x, y - 1, x + 10, y + 6), 0, 180, fill=(100, 149, 237), width=2) # Bottom curve
    # Tail fin
    draw.polygon([(x - 2, y + 2), (x, y + 1), (x, y+3)], fill=(100, 149, 237))
    # Dorsal fin
    draw.polygon([(x + 5, y - 3), (x + 7, y - 1), (x + 6, y -1)], fill=(100, 149, 237))
    # Eye
    draw.point((x + 8, y + 1), fill=(0, 0, 0))

def draw_penguin(draw, x, y):
    body_color = (0, 0, 0) # Black body
    belly_color = (255, 255, 255)
    beak_feet_color = (255, 165, 0) # Orange

    # Body
    draw.ellipse((x, y, x + 5, y + 7), fill=body_color)
    # Belly
    draw.ellipse((x + 1, y + 1, x + 4, y + 6), fill=belly_color)
    # Eyes (two dots)
    draw.point((x + 2, y + 2), fill=(0, 0, 0))
    draw.point((x + 3, y + 2), fill=(0, 0, 0))
    # Beak
    draw.polygon([(x+2, y+3), (x+3, y+3), (x+2.5, y+4)], fill=beak_feet_color)
    # Feet (two rectangles)
    draw.rectangle((x + 1, y + 7, x + 2, y + 8), fill=beak_feet_color)
    draw.rectangle((x + 3, y + 7, x + 4, y + 8), fill=beak_feet_color)
    # Small ear tufts (optional, subtle)
    # draw.point((x+1, y), fill=body_color)
    # draw.point((x+4, y), fill=body_color)

def draw_penphin(draw, x, y, scale=1.0, hue_shift=0.0):
    # Base color adjusted for richer purple, less reliant on hue_shift
    base_hue = 0.75 + math.sin(hue_shift * 0.05) * 0.05 # Centered on purple, smaller shift
    main_color = hsv_to_rgb(base_hue % 1.0, 0.95, 0.95) # More saturated/brighter purple
    shadow_color = hsv_to_rgb(base_hue % 1.0, 0.85, 0.75) # Darker, slightly desaturated purple

    body_w = int(6 * scale)
    body_h = int(7 * scale)
    feet_h = int(2 * scale)

    eye_y = y + int(2 * scale)
    eye_x_offset = int(1 * scale)
    pupil_color = (0,0,0)
    eye_color = (255, 255, 255)
    beak_color = (255, 165, 0) # Orange
    feet_color = beak_color # Use same orange for feet

    # Shadow/Undertone (drawn first)
    shadow_offset_x = int(1 * scale)
    shadow_offset_y = int(1 * scale)
    draw.ellipse((x + shadow_offset_x, y + shadow_offset_y,
                  x + body_w, y + body_h), fill=shadow_color)

    # Main body (drawn over shadow)
    body_x_end = x + body_w
    body_y_end = y + body_h
    draw.ellipse((x, y, body_x_end - shadow_offset_x, body_y_end - shadow_offset_y), fill=main_color)

    # Eyes (White with black pupil)
    eye_x1 = x + eye_x_offset + 1
    eye_x2 = body_x_end - eye_x_offset - 1
    draw.point((eye_x1, eye_y), fill=eye_color)
    draw.point((eye_x2, eye_y), fill=eye_color)
    # Pupils (Now drawn)
    draw.point((eye_x1, eye_y), fill=pupil_color)
    draw.point((eye_x2, eye_y), fill=pupil_color)

    # Small Beak/Mouth
    beak_y = y + int(4 * scale)
    beak_x = x + body_w // 2
    draw.polygon([(beak_x - 1, beak_y), (beak_x + 1, beak_y), (beak_x, beak_y + 1)], fill=beak_color)

    # Feet (Ellipses)
    feet_y_top = body_y_end # Feet start below the body ellipse
    feet_y_end = feet_y_top + feet_h
    foot_w = int(2 * scale)
    foot_gap = int(1 * scale)
    foot1_x = x + (body_w - foot_w * 2 - foot_gap) // 2
    foot2_x = foot1_x + foot_w + foot_gap
    draw.ellipse((foot1_x, feet_y_top, foot1_x + foot_w, feet_y_end), fill=feet_color)
    draw.ellipse((foot2_x, feet_y_top, foot2_x + foot_w, feet_y_end), fill=feet_color)

# === GEM FX ===
def gemlike_merge_effect(frames=15): # This function is no longer called in the main sequence
    for t in range(frames):
        img = Image.new("RGB", (WIDTH, HEIGHT)) # Start fresh each frame
        draw = ImageDraw.Draw(img)
        # Draw base scene elements that should be underneath the effect (sky, island, rocks)
        # Clouds
        for cx in range(0, 64, 24):
            offset = int((t * 2 + cx) % 64) # Use internal time 't' for cloud movement
            draw.ellipse((offset, 2, offset + 16, 8), fill=(255, 255, 255))
        # Island
        draw.rounded_rectangle((20, 12, 44, 18), radius=3, fill=(230, 210, 160))
        # Palm Tree
        trunk_y_start = 7; island_y_top = 12
        draw.rectangle((31, trunk_y_start, 33, island_y_top), fill=(139, 69, 19))
        draw.rounded_rectangle((26, -5, 38, 7), radius=4, fill=(34, 139, 34))
        # Rock base
        draw.rectangle((0, 57, 63, 63), fill=(50, 30, 20))

        # Apply swirl ONLY to water area
        for y in range(17, 57): # Water area y=17 to 56 inclusive
            for x in range(WIDTH):
                dx = x - CENTER_X
                dy = y - CENTER_Y # Center effect calculation relative to screen center
                dist = math.sqrt(dx*dx + dy*dy)
                angle = math.atan2(dy, dx)
                # Use a different wave/hue calculation than the purple one
                wave = math.sin(dist * 0.4 - t * 0.2 + angle * 3)
                hue = (t * 0.02 + dist * 0.03 + wave * 0.15 + angle * 0.1) % 1.0
                val = max(0.3, 0.95 - abs(wave) * 0.5)
                rgb = hsv_to_rgb(hue, 1.0, val)
                img.putpixel((x, y), rgb) # Draw the swirl pixel

        set_rotated_image(img)
        time.sleep(0.04)

def gemlike_penphin_effect(frames=20):
    for t in range(frames):
        img = draw_scene_base(t)
        draw = ImageDraw.Draw(img)
        for y in range(17, 52):  # Water area
            for x in range(WIDTH):
                dx = x - CENTER_X
                dy = y - CENTER_Y
                dist = math.sqrt(dx*dx + dy*dy)
                wave = math.sin(dist * 0.2 - t * 0.1)
                hue = 0.85 + math.sin(wave * 2) * 0.05
                val = max(0.2, 0.6 + wave * 0.2)
                rgb = hsv_to_rgb(hue % 1.0, 1.0, val)
                img.putpixel((x, y), rgb)
        draw_penphin(draw, 28, 5, 1.0 + 0.05 * math.sin(t * 0.2), t)
        set_rotated_image(img)
        time.sleep(0.05)

    # === MERGE SEQUENCE ===
def merge_characters():
    for i in range(32):
        frame = draw_scene_base(i)
        draw = ImageDraw.Draw(frame)
        day_rgb = DAY_COLOR_MAP[datetime.datetime.now().weekday()]
        for fx in range(3):
            draw_fish(draw, 10 + i + fx * 10, 30 + (fx % 2) * 5, day_rgb, i)
        draw_dolphin(draw, i, 32)
        draw_penguin(draw, 63 - i, 32)
        set_rotated_image(frame)
        time.sleep(0.05)

    # Lightning burst
    #gemlike_merge_effect(15)

def penphin_rise():
    for y in range(32, 18, -1):
        frame = draw_scene_base()
        draw = ImageDraw.Draw(frame)
        draw_penphin(draw, 28, y)
        set_rotated_image(frame)
        time.sleep(0.1)

def penphin_rest_breathe():
    for t in range(40):
        frame = draw_scene_base(t)
        draw = ImageDraw.Draw(frame)
        scale = 1.0 + 0.05 * math.sin(t * 0.2)
        draw_penphin(draw, 28, 5, scale, t)
        set_rotated_image(frame)
        time.sleep(0.1)

def fade_out(img):
    for alpha in range(0, 255, 15):
        overlay = Image.new("RGB", img.size, (0, 0, 0))
        blend = Image.blend(img, overlay, alpha / 255.0)
        set_rotated_image(blend)
        time.sleep(0.05)

def fade_in():
    base = draw_scene_base()
    for alpha in range(255, 0, -25):
        overlay = Image.new("RGB", (64, 64), (0, 0, 0))
        blend = Image.blend(base, overlay, alpha / 255.0)
        set_rotated_image(blend)
        time.sleep(0.05)

# === ICONIC SCENE: SLOT MACHINE ===
def slot_machine_scene():
    symbols = ['cherry', 'star', 'fish', 'seven']
    colors = {'cherry': (255, 0, 0), 'star': (255, 255, 0),
              'fish': (0, 255, 255), 'seven': (255, 0, 255)}

    def draw_symbol(draw, symbol, x, y):
        if symbol == 'cherry':
            draw.ellipse((x, y, x+3, y+3), fill=(255, 0, 0))
            draw.ellipse((x+4, y, x+7, y+3), fill=(255, 0, 0))
            draw.line((x+3, y-1, x+4, y-2), fill=(0, 255, 0))
        elif symbol == 'star':
            for dx in [-1, 0, 1]:
                draw.point((x+3+dx, y+2), fill=(255, 255, 0))
                draw.point((x+3, y+2+dx), fill=(255, 255, 0))
        elif symbol == 'fish':
            draw.polygon([(x+2, y+1), (x+6, y+2), (x+2, y+3)], fill=(0, 255, 255))
        elif symbol == 'seven':
            draw.line((x, y, x+5, y), fill=(255, 0, 255))
            draw.line((x+5, y, x+2, y+5), fill=(255, 0, 255))

    for spin in range(10):
        frame = Image.new("RGB", (64, 64), (0, 0, 0))
        draw = ImageDraw.Draw(frame)
        for i in range(3):
            s = random.choice(symbols)
            draw_symbol(draw, s, 10 + i*18, 30)
        set_rotated_image(frame)
        time.sleep(0.1)

    # Final result
    result = [random.choice(symbols) for _ in range(3)]
    frame = Image.new("RGB", (64, 64), (0, 0, 0))
    draw = ImageDraw.Draw(frame)
    for i, s in enumerate(result):
        draw_symbol(draw, s, 10 + i*18, 30)
    set_rotated_image(frame)
    time.sleep(2)

    # Confetti burst
    for _ in range(15):
        fx = Image.new("RGB", (64, 64))
        draw = ImageDraw.Draw(fx)
        for _ in range(50):
            x, y = random.randint(0, 63), random.randint(0, 63)
            hue = random.random()
            color = hsv_to_rgb(hue, 1.0, 1.0)
            draw.point((x, y), fill=color)
        set_rotated_image(fx)
        time.sleep(0.05)

# === NEW ACTION: PENPHIN TRIES TO CATCH FISH ===
def penphin_tries_to_catch_fish(frames=80): # Increased frames for new actions
    fish_x, fish_y = random.randint(5, 55), random.randint(water_y_start + 2, water_y_end - 2)
    fish_caught = False
    fish_visible = True
    penphin_x, penphin_y = 28, 5 # Resting position Y=5
    target_x, target_y = penphin_x, penphin_y
    day_rgb = DAY_COLOR_MAP[datetime.datetime.now().weekday()]

    state = "seeking"
    fish_offset_x, fish_offset_y = 0, 0 # Offset when fish is caught
    eating_timer = 0

    for t in range(frames):
        frame = draw_scene_base(t)
        draw = ImageDraw.Draw(frame)

        # --- Fish Logic --- 
        if fish_visible:
            draw_fish(draw, fish_x, fish_y, day_rgb, t * 5)
        elif not fish_caught and state != "returning_fail": # Fish escaped and we are not already returning
            state = "returning_fail"
            target_x, target_y = 28, 5

        # --- Penphin State Machine & Movement --- 
        current_penphin_x, current_penphin_y = penphin_x, penphin_y # Base position for this frame
        scale = 1.0 # Base scale

        if state == "seeking":
            # Decide to lunge after some time
            if t > frames * 0.2 and target_x == 28:
                target_x = fish_x - 3
                target_y = fish_y - 10 # Aim above fish initially
                if target_y < water_y_start: target_y = water_y_start # Dont go below water surface
            
            # Move towards target if set
            if target_x != 28:
                if abs(penphin_x - target_x) > 1:
                    penphin_x += math.copysign(1, target_x - penphin_x)
                if abs(penphin_y - target_y) > 1:
                    penphin_y += math.copysign(1, target_y - penphin_y)

            # Check for catch
            if fish_visible:
                dist_sq = (penphin_x - fish_x)**2 + (penphin_y + 4 - fish_y)**2 # Check near beak Y
                if dist_sq < 25: # Close enough
                    fish_caught = True
                    # Don't make fish invisible yet
                    state = "returning_with_fish"
                    # Record offset relative to Penphin's current position
                    fish_offset_x = fish_x - penphin_x
                    fish_offset_y = fish_y - penphin_y
                    target_x, target_y = 28, 5 # Target back to rest
                # Check for escape (if not caught this frame)
                elif t > frames * 0.6 and random.random() < 0.05:
                    fish_visible = False # Fish escaped
                    # State will change to returning_fail on next iteration via Fish Logic check
            
            scale = 1.0 + 0.05 * math.sin(t * 0.2) # Normal breathing/bobbing

        elif state == "returning_with_fish" or state == "returning_fail":
            # Move Penphin back to rest
            moved = False
            if abs(penphin_x - target_x) > 1:
                penphin_x += math.copysign(1, target_x - penphin_x)
                moved = True
            if abs(penphin_y - target_y) > 1:
                # Allow movement even if close vertically, to ensure island arrival
                penphin_y += math.copysign(1, target_y - penphin_y)
                moved = True
            
            # Update fish position if carrying it
            if state == "returning_with_fish":
                fish_x = penphin_x + fish_offset_x
                fish_y = penphin_y + fish_offset_y

            if not moved: # Reached destination
                penphin_x, penphin_y = 28, 5 # Snap to position Y=5
                if state == "returning_with_fish":
                    fish_visible = False # Fish disappears now
                    state = "eating"
                    eating_timer = 15 # Eat for 15 frames
                else: # Failed catch
                     state = "done"
            scale = 1.0 + 0.05 * math.sin(t * 0.1) # Slower bob when returning

        elif state == "eating":
            eating_timer -= 1
            # Quick scale pulse/wiggle for "eating"
            scale = 1.0 + 0.1 * abs(math.sin(t * 0.9)) 
            if eating_timer <= 0:
                state = "done"
        
        elif state == "done":
            scale = 1.0 + 0.05 * math.sin(t * 0.2) # Resume gentle breathing
            pass # Do nothing, just wait for frames to end

        # Update current position AFTER state logic potentially changes penphin_x/y
        current_penphin_x, current_penphin_y = penphin_x, penphin_y

        # Draw Penphin with current position and scale
        draw_penphin(draw, current_penphin_x, current_penphin_y, scale, t)

        set_rotated_image(frame)
        time.sleep(0.07)

    # Optional: short pause at the very end
    time.sleep(0.3)

# === NEW ACTION: PENPHIN INTERACTS WITH TREE ===
def penphin_interacts_with_tree(frames=50):
    penphin_x, penphin_y = 28, 5 # Start at rest Y=5
    target_x, target_y = 30, 5 # Move near tree base (stay on Y=5)
    tree_interaction_done = False

    for t in range(frames):
        frame = draw_scene_base(t)
        draw = ImageDraw.Draw(frame)

        # Move Penphin towards tree
        if not tree_interaction_done:
            if abs(penphin_x - target_x) > 0:
                penphin_x += math.copysign(1, target_x - penphin_x)
            if abs(penphin_y - target_y) > 0:
                penphin_y += math.copysign(1, target_y - penphin_y)
            elif t > frames // 4: # Reached tree, start interaction
                # Simple peck/shake animation
                shake_offset = math.sin(t * 0.8) * 1
                penphin_x += shake_offset
                if t > frames * 3 // 4: # Interaction finished
                     tree_interaction_done = True
                     target_x, target_y = 28, 5 # Target back to rest Y=5
        else:
             # Move Penphin back to rest
            if abs(penphin_x - target_x) > 0:
                penphin_x += math.copysign(1, target_x - penphin_x)
            if abs(penphin_y - target_y) > 0:
                penphin_y += math.copysign(1, target_y - penphin_y)

        scale = 1.0 + 0.05 * math.sin(t * 0.2)
        draw_penphin(draw, penphin_x, penphin_y, scale, t)
        set_rotated_image(frame)
        time.sleep(0.07)
    time.sleep(0.3)

# === NEW ACTION: PENPHIN CANNONBALL ===
def penphin_cannonball(frames=70):
    penphin_x, penphin_y = 28, 5 # Start at rest Y=5
    jump_peak_y = -3 # Go higher relative to new start Y=5
    water_entry_y = 15 # Adjusted for new island height (water starts at 15)
    splash_radius = 0
    # Fish positions now store [x, y, scared_flag]
    fish_positions = [[random.randint(5, 55), random.randint(water_entry_y + 2, 45), False] for _ in range(3)]
    state = "prepare_jump"
    day_rgb = DAY_COLOR_MAP[datetime.datetime.now().weekday()]
    scare_speed = 3.0 # How fast fish flee

    for t in range(frames):
        frame = draw_scene_base(t)
        draw = ImageDraw.Draw(frame)

        # State machine for animation
        if state == "prepare_jump":
            penphin_y += 0.5 # Slight crouch/bob
            if t > frames * 0.1:
                state = "jumping"
                jump_start_t = t
        elif state == "jumping":
            jump_progress = (t - jump_start_t) / (frames * 0.4)
            penphin_y = 5 + (jump_peak_y - 5) * math.sin(jump_progress * math.pi) # Use Y=5 as base
            penphin_x += 0.2
            if jump_progress >= 1.0:
                state = "falling"
                fall_start_t = t
        elif state == "falling":
             fall_progress = (t - fall_start_t) / (frames * 0.2)
             penphin_y = jump_peak_y + (water_entry_y - jump_peak_y) * fall_progress**2
             if penphin_y >= water_entry_y:
                 state = "splash"
                 splash_start_t = t
                 penphin_y = water_entry_y
                 # Scare the fish!
                 for i in range(len(fish_positions)):
                     fish_positions[i][2] = True # Set scared flag
        elif state == "splash":
             splash_progress = (t - splash_start_t) / (frames * 0.15)
             splash_radius = 8 * math.sin(splash_progress * math.pi)
             if splash_progress >= 1.0:
                 state = "return_to_island"
                 target_x, target_y = 28, 5 # Target back to rest Y=5
        elif state == "return_to_island":
             if abs(penphin_x - target_x) > 1:
                 penphin_x += math.copysign(1, target_x - penphin_x)
             if abs(penphin_y - target_y) > 1:
                  penphin_y += math.copysign(1, target_y - penphin_y)
                  if penphin_y > water_entry_y: penphin_y = water_entry_y
             else:
                  penphin_y = 5 # Snap to rest y=5
                  state = "done"

        # Update and draw fish
        for i in range(len(fish_positions)):
            fx, fy, scared = fish_positions[i]

            if scared:
                # Calculate direction away from splash point (penphin_x, water_entry_y)
                dx = fx - penphin_x
                dy = fy - water_entry_y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0: # Avoid division by zero
                    flee_x = fx + (dx / dist) * scare_speed
                    flee_y = fy + (dy / dist) * scare_speed
                    # Update position in the list
                    fish_positions[i][0] = flee_x
                    fish_positions[i][1] = flee_y
                    fx, fy = flee_x, flee_y # Use updated position for drawing this frame
            
            # Only draw fish if they are roughly on screen
            if fx > -8 and fx < WIDTH + 8:
                draw_fish(draw, fx, fy, day_rgb, t * 5) # Use a time factor for wiggle

        # Draw splash effect
        if state == "splash" and splash_radius > 0:
            draw.ellipse((penphin_x - splash_radius, penphin_y - splash_radius // 2,
                           penphin_x + splash_radius, penphin_y + splash_radius // 2), fill=(200, 220, 255))

        # Draw Penphin unless fully submerged briefly during splash peak
        draw_penphin_condition = True
        if state == "splash":
            # Need splash_progress to check if submerged
            splash_progress = (t - splash_start_t) / (frames * 0.15)
            if splash_progress > 0.2 and splash_progress < 0.8:
                 draw_penphin_condition = False

        if draw_penphin_condition:
             scale = 1.0 + 0.05 * math.sin(t * 0.2)
             draw_penphin(draw, penphin_x, penphin_y, scale, t)

        set_rotated_image(frame)
        time.sleep(0.06)
    time.sleep(0.3)

# === NEW ACTION: COCONUT BONK ===
def penphin_coconut_bonk(frames=60):
    penphin_x, penphin_y = 28, 5 # Start at rest Y=5
    target_x = 32
    coconut_x, coconut_y = 32, 2 # Start higher in taller leaves
    coconut_visible = False
    coconut_hit = False
    stars_visible = False
    star_t_start = 0
    state = "walking_to_tree"

    for t in range(frames):
        frame = draw_scene_base(t)
        draw = ImageDraw.Draw(frame)

        # Penphin Movement & State
        if state == "walking_to_tree":
             if abs(penphin_x - target_x) > 0:
                 penphin_x += math.copysign(0.5, target_x - penphin_x)
             else:
                 state = "under_tree"
                 wait_start_t = t
        elif state == "under_tree":
             if t > wait_start_t + 10: # Wait briefly
                 state = "coconut_fall"
                 coconut_visible = True
        elif state == "coconut_fall":
            coconut_y += 1.5 # Fall speed
            # Check hit against new Penphin Y=5 and height (approx body_h=7)
            if coconut_y >= (penphin_y + 1) and coconut_y <= (penphin_y + 7) and not coconut_hit:
                coconut_y = penphin_y + 1 # Hit top of head (relative to body top Y)
                coconut_hit = True
                stars_visible = True
                star_t_start = t
                state = "seeing_stars"
        elif state == "seeing_stars":
            # Wobble penphin slightly
            penphin_x += math.sin(t * 1.5) * 0.5
            if t > star_t_start + 20: # Stars last 20 frames
                stars_visible = False
                coconut_visible = False # Coconut disappears after hit/stars
                state = "returning"
                target_x = 28 # Target back to rest Y=5
        elif state == "returning":
            if abs(penphin_x - target_x) > 0:
                 penphin_x += math.copysign(0.5, target_x - penphin_x)
            else:
                 state = "done"

        # Draw Coconut
        if coconut_visible:
            draw.ellipse((coconut_x-1, coconut_y-1, coconut_x+1, coconut_y+1), fill=(139, 69, 19))

        # Draw Penphin
        scale = 1.0 + 0.05 * math.sin(t * 0.1) # Slower breath when idle/walking
        draw_penphin(draw, penphin_x, penphin_y, scale, t)

        # Draw Stars
        if stars_visible:
            star_duration_progress = (t - star_t_start) / 20.0
            alpha = math.sin(star_duration_progress * math.pi) # Fade stars in/out
            star_color = (int(255*alpha), int(255*alpha), int(0*alpha))
            star_radius = 3
            for i in range(3):
                angle = (t * 0.2 + i * 2 * math.pi / 3)
                # Adjust star position relative to new penphin_y=5
                sx = penphin_x + 2 + math.cos(angle) * star_radius
                sy = penphin_y + 1 + math.sin(angle) * star_radius # Centered higher on head
                # Simple star shape (cross)
                draw.line((sx-1, sy, sx+1, sy), fill=star_color)
                draw.line((sx, sy-1, sx, sy+1), fill=star_color)

        set_rotated_image(frame)
        time.sleep(0.07)
    time.sleep(0.3)

# === Combined Swirl & Rise ===
def swirl_and_rise_sequence(total_frames=60):
    penphin_start_y = 30
    penphin_end_y = 5 # New resting Y = 5
    island_y_start = 12
    water_y_start = island_y_start + 1 # water starts at 15
    water_y_end = 48 # Water ends at 48

    # Swirl lasts whole time, rise happens during last part
    rise_start_frame = int(total_frames * 0.4) # Start rising later
    rise_frames = total_frames - rise_start_frame

    for t in range(total_frames):
        # Draw base scene with sky swirl ENABLED
        frame = draw_scene_base(t)
        draw = ImageDraw.Draw(frame)

        # --- Penphin Position --- 
        penphin_current_y = penphin_start_y
        if t >= rise_start_frame:
            rise_progress = (t - rise_start_frame) / rise_frames
            # Ensure y doesn't go below final resting position due to overshoot
            penphin_current_y = max(penphin_end_y, penphin_start_y + (penphin_end_y - penphin_start_y) * rise_progress)

        # --- Water Effect (Purple Swirl) --- 
        # Only apply swirl effect DURING the rise phase
        if t >= rise_start_frame:
            rise_progress = (t - rise_start_frame) / rise_frames
            fade_factor = max(0.0, 1.0 - rise_progress) # Fade linearly as Penphin rises, clamp at 0
            
            # Apply Purple Swirl to water (fading based on factor)
            for y in range(water_y_start, water_y_end + 1): # Use new water range
                for x in range(WIDTH):
                    dx = x - CENTER_X
                    dy = y - CENTER_Y
                    dist = math.sqrt(dx*dx + dy*dy)
                    wave = math.sin(dist * 0.2 - t * 0.1) # Keep swirl effect consistent
                    hue = 0.85 + math.sin(wave * 2) * 0.05
                    # Base water properties
                    base_water_rgb = (0, 100, 200)
                    base_hue, base_sat, base_val = 0.6, 1.0, 0.78 # Approx values for base water
                    # Swirl properties
                    swirl_hue = hue % 1.0
                    swirl_sat = 1.0
                    swirl_val = max(0.2, 0.6 + wave * 0.2)
                    
                    # Interpolate HSV towards base water color as fade_factor decreases
                    final_hue = swirl_hue * fade_factor + base_hue * (1 - fade_factor)
                    final_sat = swirl_sat * fade_factor + base_sat * (1 - fade_factor)
                    final_val = swirl_val * fade_factor + base_val * (1 - fade_factor)
                    
                    final_rgb = hsv_to_rgb(final_hue, final_sat, final_val)
                    # Only draw if y is within actual water bounds
                    if y >= water_y_start and y <= water_y_end:
                         frame.putpixel((x, y), final_rgb)
        # else: Water remains textured as drawn by draw_scene_base()

        # --- Draw Penphin --- 
        scale = 1.0 + 0.05 * math.sin(t * 0.2)
        draw_penphin(draw, 28, penphin_current_y, scale, t)

        set_rotated_image(frame)
        time.sleep(0.06)

# === MAIN LOOP ===
import datetime
initial_cycle_complete = False # Flag for first run
scene_cycle_duration = 60 # Target duration in seconds for each cycle
last_fade_time = time.time()
current_scene_image = Image.new("RGB", (WIDTH, HEIGHT)) # Initialize dummy image

# Define water boundaries for use in main loop fish placement
water_y_start = 15 # Water starts at 15
water_y_end = 48 # Water ends at 48

try:
    while True:
        current_time = time.time()
        # --- Check for Fade Out/In --- 
        if current_time - last_fade_time > scene_cycle_duration:
            fade_out(current_scene_image) # Fade out the last drawn frame
            fade_in()
            last_fade_time = current_time
            # Re-draw base after fade in if needed, or let the next action draw it
            current_scene_image = draw_scene_base() # Reset base image after fade
            draw = ImageDraw.Draw(current_scene_image)
            draw_penphin(draw, 28, 5, 1.0, 0) # Ensure Penphin is visible at rest Y=5
            set_rotated_image(current_scene_image)
            time.sleep(0.5) # Brief pause after fade in

        # --- Determine Action --- 
        if not initial_cycle_complete:
            # --- First cycle: Full sequence ---
            scene = draw_scene_base() # Use a fresh base for drawing
            draw = ImageDraw.Draw(scene)
            day_rgb = DAY_COLOR_MAP[datetime.datetime.now().weekday()]
            for i in range(6): # Draw more fish initially
                fish_y_pos = random.randint(water_y_start + 2, water_y_end - 2)
                while fish_y_pos == 32: # Keep check for merge sequence line
                    fish_y_pos = random.randint(water_y_start + 2, water_y_end - 2)
                draw_fish(draw, random.randint(5, 55), fish_y_pos, day_rgb, i)
            set_rotated_image(scene)
            time.sleep(2)

            merge_characters() # Characters merge
            swirl_and_rise_sequence() # Purple swirl starts, Penphin rises through it, water clears as Penphin lands
            initial_cycle_complete = True
            last_fade_time = time.time() # Start timer after first sequence
            # Get the final frame of the rise sequence for potential immediate fade
            current_scene_image = draw_scene_base()
            draw = ImageDraw.Draw(current_scene_image)
            draw_penphin(draw, 28, 5, 1.0, 0) # Draw Penphin at rest Y=5

        else:
            # --- Subsequent cycles: Random actions --- 
            action_choice = random.random()
            chosen_action = False

            if action_choice < 0.30:
                penphin_rest_breathe()
                chosen_action = True
            elif action_choice < 0.50:
                penphin_tries_to_catch_fish()
                chosen_action = True
            elif action_choice < 0.65:
                penphin_interacts_with_tree()
                chosen_action = True
            elif action_choice < 0.80:
                 penphin_cannonball()
                 chosen_action = True
            elif action_choice < 0.95:
                 penphin_coconut_bonk()
                 chosen_action = True
            # else: # Remaining % is implicit idle / slot machine chance

            if not chosen_action and random.random() < 0.1: # Small chance for slots if no other action ran
                 slot_machine_scene()
                 chosen_action = True # Count slots as an action

            # Update current_scene_image *after* the action completes
            current_scene_image = draw_scene_base()
            draw = ImageDraw.Draw(current_scene_image)
            draw_penphin(draw, 28, 5, 1.0, 0) # Draw Penphin at rest Y=5
            # No matrix.SetImage here, rely on next loop iteration or fade check

            # Add a small delay between actions if needed, prevents frantic switching
            if chosen_action:
                time.sleep(random.uniform(0.5, 1.5))
            else: # If no action chosen (idle state)
                 # Just show the base scene with Penphin
                 # Add a chance for a random fish to appear
                 if random.random() < 0.15:
                    f_img = current_scene_image.copy()
                    f_draw = ImageDraw.Draw(f_img)
                    f_day_rgb = DAY_COLOR_MAP[datetime.datetime.now().weekday()]
                    f_y = random.randint(water_y_start + 2, water_y_end - 2)
                    f_x = random.choice([-10, WIDTH + 1]) # Start off screen
                    f_speed = random.uniform(0.5, 1.5)
                    # Simple animation of fish swimming across
                    for fi in range(int(WIDTH * 1.5 / f_speed)):
                        fish_frame = f_img.copy()
                        fish_draw = ImageDraw.Draw(fish_frame)
                        current_fx = f_x + fi * f_speed * (1 if f_x < 0 else -1)
                        if current_fx > -8 and current_fx < WIDTH + 8:
                            draw_fish(fish_draw, current_fx, f_y, f_day_rgb, time.time() * 5)
                        set_rotated_image(fish_frame)
                        time.sleep(0.04)
                        if current_fx < -10 or current_fx > WIDTH + 10: break # stop if off screen
                 else:
                    # Standard idle pause
                    set_rotated_image(current_scene_image)
                    time.sleep(random.uniform(1.0, 3.0))

except KeyboardInterrupt:
    print("💤 Penphin returns to the deep...")
    matrix.Clear()
