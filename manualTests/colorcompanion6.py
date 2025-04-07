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

# === EMOTION COLORS ===
EMOTION_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),         # Passion
    "green": (0, 255, 0),       # Growth
    "blue": (0, 0, 255),        # Calm
    "orange": (255, 165, 0),    # Invent
    "yellow": (255, 255, 0),    # Connect
    "indigo": (20, 30, 180),    # Insight
    "violet": (148, 0, 211),    # Flow
}

EMOTION_WORDS = {
    "white": "LOGIC",
    "red": "PASSION",
    "green": "GROWTH",
    "blue": "CALM",
    "violet": "FLOW",
    "orange": "INVENT",
    "yellow": "CONNECT",
    "indigo": "INSIGHT"
}

def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return (int(v*255),)*3
    i = int(h*6.)
    f = h*6. - i
    i %= 6
    v, p, q, t = int(255*v), int(255*v*(1-s)), int(255*v*(1-s*f)), int(255*v*(1-s*(1-f)))
    return [(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)][i]

# === ANIMATION FUNCTIONS ===
def draw_pulsing_circle(draw, color, x, y, radius, pulse_speed=0.1):
    # Make sure radius is an integer
    radius = int(radius)
    
    # Add gentle pulsing effect
    pulse = 0.8 + 0.2 * math.sin(time.time() * pulse_speed * 5)
    
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        for r in range(1, radius + 1):
            # Apply pulse to radius
            actual_r = r * pulse
            px = int(x + math.cos(rad) * actual_r)
            py = int(y + math.sin(rad) * actual_r)
            
            # Skip if outside bounds
            if not (0 <= px < WIDTH and 0 <= py < HEIGHT):
                continue
                
            draw.point((px, py), fill=EMOTION_COLORS[color])

def draw_ambient_waves(draw, tick, colors):
    # Create flowing wave effect at bottom of screen
    wave_height = 12
    start_y = HEIGHT - wave_height
    
    for y in range(start_y, HEIGHT):
        for x in range(WIDTH):
            # Create wave pattern
            wave1 = math.sin(x * 0.1 + tick * 0.05) * 0.5 + 0.5
            wave2 = math.sin(x * 0.05 - tick * 0.03 + y * 0.1) * 0.5 + 0.5
            wave = (wave1 + wave2) / 2.0
            
            # Use multiple colors
            color_idx = int(wave * len(colors))
            color_idx = min(color_idx, len(colors) - 1)
            color = colors[color_idx]
            
            # Add intensity variation
            intensity = 0.7 + 0.3 * wave
            r = int(color[0] * intensity)
            g = int(color[1] * intensity)
            b = int(color[2] * intensity)
            
            draw.point((x, y), fill=(r, g, b))

def draw_color_merge(draw, tick, color1, color2, result_color, progress):
    # Draw animation of two colors merging to form a new color
    center_y = HEIGHT // 2
    
    # Draw source colors (shrinking as progress increases)
    r1 = 10 * (1 - progress * 0.5)
    draw_pulsing_circle(draw, color1, WIDTH // 3, center_y, r1)
    draw_pulsing_circle(draw, color2, 2 * WIDTH // 3, center_y, r1)
    
    # Draw result color (growing as progress increases)
    if progress > 0.3:
        r3 = progress * 15
        draw_pulsing_circle(draw, result_color, WIDTH // 2, center_y, r3)
    
    # Draw connecting lines with flowing particles
    num_particles = 20
    for i in range(num_particles):
        # Calculate position along path based on progress and particle index
        t = (i / num_particles + tick * 0.01) % 1.0
        
        # Path from color1 to result
        x1 = WIDTH // 3 + (WIDTH // 2 - WIDTH // 3) * t
        y1 = center_y
        
        # Path from color2 to result
        x2 = 2 * WIDTH // 3 - (2 * WIDTH // 3 - WIDTH // 2) * t
        y2 = center_y
        
        # Only draw if within bounds
        if 0 <= x1 < WIDTH and 0 <= y1 < HEIGHT:
            # Blend colors along path
            c1 = EMOTION_COLORS[color1]
            cr = EMOTION_COLORS[result_color]
            r = int(c1[0] * (1-t) + cr[0] * t)
            g = int(c1[1] * (1-t) + cr[1] * t)
            b = int(c1[2] * (1-t) + cr[2] * t)
            draw.point((int(x1), int(y1)), fill=(r, g, b))
        
        if 0 <= x2 < WIDTH and 0 <= y2 < HEIGHT:
            c2 = EMOTION_COLORS[color2]
            cr = EMOTION_COLORS[result_color]
            r = int(c2[0] * (1-t) + cr[0] * t)
            g = int(c2[1] * (1-t) + cr[1] * t)
            b = int(c2[2] * (1-t) + cr[2] * t)
            draw.point((int(x2), int(y2)), fill=(r, g, b))

def draw_emotion_notification(draw, emotion):
    # Draw notification with emotion color and name
    draw.rectangle((0, 0, WIDTH - 1, 15), fill=EMOTION_COLORS[emotion])
    
    # Get emotion word
    word = EMOTION_WORDS[emotion]
    
    # Choose text color based on background
    text_color = (0, 0, 0) if emotion in ["yellow", "green", "white"] else (255, 255, 255)
    
    # Center the text
    text_width = len(word) * 6  # Approximate pixel width
    text_x = (WIDTH - text_width) // 2
    
    draw.text((text_x, 4), word, fill=text_color)

def draw_emotion_circles(draw, tick, emotions):
    # Draw circles for each emotion in harmonious arrangement
    num_emotions = len(emotions)
    center_y = HEIGHT // 2
    
    for i, emotion in enumerate(emotions):
        # Calculate position in circular arrangement
        angle = i * (2 * math.pi / num_emotions)
        distance = 20  # Distance from center
        x = CENTER_X + math.cos(angle) * distance
        y = center_y + math.sin(angle) * distance
        
        # Add subtle movement
        x += math.sin(tick * 0.02 + i * 0.5) * 2
        y += math.cos(tick * 0.03 + i * 0.5) * 2
        
        # Determine size (pulsing)
        base_size = 7
        pulse_offset = i * 0.7  # Different timing for each emotion
        size = base_size + math.sin(tick * 0.05 + pulse_offset) * 2
        
        draw_pulsing_circle(draw, emotion, x, y, size)

# === MAIN ANIMATION ===
def run_animation():
    tick = 0
    current_phase = 0
    phase_progress = 0
    discovered_emotions = ["white"]  # Start with Logic
    
    # Phases of animation
    phases = [
        {"name": "logic_intro", "duration": 3},           # Phase 0: Logic appears
        {"name": "primary_emotions", "duration": 6},      # Phase 1: Primary emotions emerge (red, green, blue)
        {"name": "emotion_mixing", "duration": 12},       # Phase 2: Emotions mix to form secondary emotions
        {"name": "harmony", "duration": 5},               # Phase 3: All emotions in harmony
        {"name": "integration", "duration": 4},           # Phase 4: Emotions integrate
        {"name": "restart", "duration": 2}                # Phase 5: Cycle back to start
    ]
    
    # Specific color mixes to discover
    mixes = [
        {"color1": "red", "color2": "blue", "result": "violet", "triggered": False},
        {"color1": "red", "color2": "green", "result": "yellow", "triggered": False},
        {"color1": "blue", "color2": "green", "result": "indigo", "triggered": False},
        {"color1": "red", "color2": "yellow", "result": "orange", "triggered": False}
    ]
    
    # Emotion notifications queue
    notification_queue = ["white"]  # Start with Logic
    current_notification = None
    notification_timer = 0
    
    try:
        while True:
            # Create new frame
            img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Calculate phase duration and progress
            phase_duration = phases[current_phase]["duration"] * 20  # 20 ticks per second
            phase_progress = (tick % phase_duration) / phase_duration
            
            # Handle notification display
            if notification_timer > 0:
                notification_timer -= 1
                draw_emotion_notification(draw, current_notification)
            elif notification_queue and not current_notification:
                current_notification = notification_queue.pop(0)
                notification_timer = 20  # Show for 1 second
                draw_emotion_notification(draw, current_notification)
            else:
                current_notification = None
            
            # Phase 0: Logic Intro
            if phases[current_phase]["name"] == "logic_intro":
                # Growing white circle
                radius = 3 + phase_progress * 10
                draw_pulsing_circle(draw, "white", CENTER_X, CENTER_Y, radius)
                
                # Add ambient waves with just white
                draw_ambient_waves(draw, tick, [EMOTION_COLORS["white"]])
                
            # Phase 1: Primary Emotions
            elif phases[current_phase]["name"] == "primary_emotions":
                # White remains in center
                draw_pulsing_circle(draw, "white", CENTER_X, CENTER_Y, 8)
                
                # Add primary emotions if not already discovered
                primaries = ["red", "green", "blue"]
                for i, color in enumerate(primaries):
                    if phase_progress > (i * 0.2 + 0.2) and color not in discovered_emotions:
                        discovered_emotions.append(color)
                        notification_queue.append(color)
                
                # Draw the discovered primary emotions
                for i, color in enumerate([c for c in primaries if c in discovered_emotions]):
                    angle = i * (2 * math.pi / 3)
                    distance = 15 * min(1.0, (phase_progress - 0.2) * 2)
                    x = CENTER_X + math.cos(angle) * distance
                    y = CENTER_Y + math.sin(angle) * distance
                    draw_pulsing_circle(draw, color, x, y, 7)
                
                # Update ambient waves with discovered colors
                wave_colors = [EMOTION_COLORS[c] for c in discovered_emotions]
                draw_ambient_waves(draw, tick, wave_colors)
            
            # Phase 2: Emotion Mixing
            elif phases[current_phase]["name"] == "emotion_mixing":
                # Draw all discovered emotions
                draw_emotion_circles(draw, tick, discovered_emotions)
                
                # Trigger emotion mixes at specific points in the phase
                segment_size = 1.0 / len(mixes)
                for i, mix in enumerate(mixes):
                    segment_start = i * segment_size
                    segment_end = (i + 1) * segment_size
                    
                    # Check if we should start this mix
                    if (segment_start <= phase_progress < segment_end and 
                        not mix["triggered"] and
                        mix["color1"] in discovered_emotions and 
                        mix["color2"] in discovered_emotions and
                        mix["result"] not in discovered_emotions):
                        
                        # Mark as triggered
                        mix["triggered"] = True
                        
                        # Discover the new emotion
                        discovered_emotions.append(mix["result"])
                        notification_queue.append(mix["result"])
                        
                        # Show the specific mix animation
                        mix_progress = (phase_progress - segment_start) / (segment_end - segment_start)
                        draw_color_merge(draw, tick, mix["color1"], mix["color2"], 
                                         mix["result"], mix_progress)
                
                # Update ambient waves with discovered colors
                wave_colors = [EMOTION_COLORS[c] for c in discovered_emotions]
                draw_ambient_waves(draw, tick, wave_colors)
            
            # Phase 3: Harmony
            elif phases[current_phase]["name"] == "harmony":
                # Draw all emotions in harmony
                draw_emotion_circles(draw, tick, discovered_emotions)
                
                # Update ambient waves with all colors
                wave_colors = [EMOTION_COLORS[c] for c in discovered_emotions]
                draw_ambient_waves(draw, tick, wave_colors)
            
            # Phase 4: Integration
            elif phases[current_phase]["name"] == "integration":
                # Draw emotions moving toward center
                for i, emotion in enumerate(discovered_emotions):
                    angle = i * (2 * math.pi / len(discovered_emotions))
                    # Start from outer positions and move inward
                    distance = 20 * (1 - phase_progress)
                    x = CENTER_X + math.cos(angle) * distance
                    y = CENTER_Y + math.sin(angle) * distance
                    
                    # Shrink as they approach center
                    size = 7 * (1 - phase_progress * 0.7)
                    draw_pulsing_circle(draw, emotion, x, y, size)
                
                # White grows in center as emotions integrate
                white_size = 5 + 15 * phase_progress
                draw_pulsing_circle(draw, "white", CENTER_X, CENTER_Y, white_size)
                
                # Update ambient waves with all colors
                wave_colors = [EMOTION_COLORS[c] for c in discovered_emotions]
                draw_ambient_waves(draw, tick, wave_colors)
            
            # Phase 5: Restart
            elif phases[current_phase]["name"] == "restart":
                # White fades out
                white_size = 20 * (1 - phase_progress)
                draw_pulsing_circle(draw, "white", CENTER_X, CENTER_Y, white_size)
                
                # Transition ambient waves to darkness
                fade = 1 - phase_progress
                white_color = tuple(int(c * fade) for c in EMOTION_COLORS["white"])
                draw_ambient_waves(draw, tick, [white_color])
            
            # Update the display with the RGB matrix
            matrix.SetImage(img.rotate(ROTATE) if ROTATE else img)
            
            # Update tick and phase
            tick += 1
            if phase_progress >= 0.99:
                # Move to next phase
                current_phase = (current_phase + 1) % len(phases)
                tick = 0
                
                # Reset mix triggers when restarting the cycle
                if current_phase == 0:
                    discovered_emotions = ["white"]
                    notification_queue.append("white")
                    for mix in mixes:
                        mix["triggered"] = False
            
            # Small delay (50ms for 20fps)
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        # Clean up on exit
        matrix.Clear()
        print("🧠 Simulation Ended.")

# Run the animation
run_animation() 