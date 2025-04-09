import os
import time
import datetime
import subprocess
import random
import json
import math
from penphin_api_assistants import (
    call_coder_assistant,
    call_graphic_designer_assistant,
    call_game_title_generator,
    PIXEL_ART_DIR,
    show_error_symbol
)
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw
from io import BytesIO

# === DISPLAY SETUP ===
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

# Screen layout constants
TITLE_AREA_HEIGHT = 14
GAME_AREA_HEIGHT = 40
LIGHTING_AREA_HEIGHT = 10

# Screen area coordinates
TITLE_AREA = (0, TITLE_AREA_HEIGHT)
GAME_AREA = (TITLE_AREA_HEIGHT, TITLE_AREA_HEIGHT + GAME_AREA_HEIGHT)
LIGHTING_AREA = (TITLE_AREA_HEIGHT + GAME_AREA_HEIGHT, 64)

# === CONFIG ===
AUTOMATE_INPUT = False
BUTTONS_AVAILABLE = ["red", "green", "blue", "black"]
GAME_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Games")
PIXEL_ART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PixelArt")

# Ensure directories exist with proper permissions
def ensure_directory(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path, mode=0o777)
        else:
            # Ensure existing directory has correct permissions
            os.chmod(path, 0o777)
    except Exception as e:
        print(f"⚠️ Warning: Could not set permissions for {path}: {e}")
        print("Will continue in memory mode")
        return False
    return True

# Try to create directories, but continue even if it fails
ensure_directory(GAME_FOLDER)
ensure_directory(PIXEL_ART_DIR)

def parse_hex_color(hex_bright):
    hex_part, bright = hex_bright.split(":")
    r = int(hex_part[1:3], 16)
    g = int(hex_part[3:5], 16)
    b = int(hex_part[5:7], 16)
    brightness = int(bright)
    r = int(r * (brightness / 100))
    g = int(g * (brightness / 100))
    b = int(b * (brightness / 100))
    return r, g, b

def clean_up_pixel_art(img, size=(64, 64)):
    return img.convert("RGB").resize(size, Image.NEAREST)

def safe_load_image_from_response(response_content):
    try:
        img = Image.open(BytesIO(response_content))
        return clean_up_pixel_art(img)
    except Exception as e:
        print("❌ Failed to load image from response:", e)
        return Image.new("RGB", (64, 64), (255, 0, 0))  # Error tile

def show_visual_frames(image_path):
    try:
        img = Image.open(image_path)
        img = clean_up_pixel_art(img)
        for y in range(64):
            for x in range(64):
                r, g, b = img.getpixel((x, y))
                matrix.SetPixel(x, y, r, g, b)
        time.sleep(1)
    except Exception as e:
        print(f"❌ Error displaying image: {e}")
        show_error_symbol()

def list_existing_folders(base_path):
    return [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

def get_latest_attempt(folder):
    attempts = sorted(
        [f for f in os.listdir(folder) if f.startswith("v") and f.endswith(".py") or f.endswith(".json")],
        reverse=True
    )
    return attempts[0] if attempts else None

def get_description(folder):
    desc_path = os.path.join(folder, "description.txt")
    if os.path.exists(desc_path):
        with open(desc_path, 'r') as f:
            return f.read().strip()
    return "(No description)"

def save_description(folder, title, description):
    desc_path = os.path.join(folder, "description.txt")
    date = datetime.datetime.now().strftime("%b %d %Y")
    with open(desc_path, 'w') as f:
        f.write(f"🕹️ {title}  —  {date}\n\n{description}\n")

def create_animation():
    print("\n✨ Create New or Load Existing Pixel Art:")
    print("1. Create New")
    print("2. Load Existing")
    choice = input("Choose an option: ").strip()

    if choice == '2':
        folders = list_existing_folders(PIXEL_ART_DIR)
        if not folders:
            print("No existing pixel art found.")
            return
        print("\n📂 Existing Pixel Art:")
        for i, name in enumerate(folders):
            latest = get_latest_attempt(os.path.join(PIXEL_ART_DIR, name))
            desc = get_description(os.path.join(PIXEL_ART_DIR, name))
            print(f"{i + 1}. {name} [{latest}] → {desc[:50]}...")
        idx = int(input("Choose a folder: ").strip()) - 1
        folder = folders[idx]
        latest = get_latest_attempt(os.path.join(PIXEL_ART_DIR, folder))
        if latest:
            show_visual_frames(os.path.join(PIXEL_ART_DIR, folder, latest))
        return

    prompt = input("\nDescribe an animation: ").strip()
    print("\n🎨 Generating animation JSON...\n")
    result = call_graphic_designer_assistant(prompt)
    
    # Show the frames immediately after generation
    show_visual_frames(result)
    
    print("\n✨ Naming your animation...")
    title, description = call_game_title_generator(prompt)
    
    # Try to save, but continue even if it fails
    folder = os.path.join(PIXEL_ART_DIR, title)
    try:
        ensure_directory(folder)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"v1_{timestamp}.json"
        with open(os.path.join(folder, filename), 'w') as f:
            f.write(result)
        save_description(folder, title, description)
        print(f"\n✨ Animation saved to {folder}")
    except Exception as e:
        print(f"⚠️ Warning: Could not save animation: {e}")
        print("Continuing with in-memory display...")
    
    input("\nPress Enter to return to menu.")

def show_refinement_prompt():
    print("\n🔄 Would you like to refine the game?")
    print("1. Yes, make improvements")
    print("2. No, continue playing")
    choice = input("Choose an option: ").strip()
    if choice == '1':
        print("\n💡 What would you like to improve?")
        print("1. Game mechanics")
        print("2. Visual effects")
        print("3. Performance")
        print("4. Fix specific issue")
        improvement_type = input("Choose an option: ").strip()
        
        if improvement_type == '1':
            prompt = input("\nDescribe the game mechanics changes you want (e.g., 'Make the ball bounce more randomly'): ").strip()
            return "game_mechanics", prompt
        elif improvement_type == '2':
            prompt = input("\nDescribe the visual changes you want (e.g., 'Add particle effects'): ").strip()
            return "visual_effects", prompt
        elif improvement_type == '3':
            prompt = input("\nDescribe the performance improvements you want (e.g., 'Optimize collision detection'): ").strip()
            return "performance", prompt
        elif improvement_type == '4':
            prompt = input("\nDescribe the specific issue to fix: ").strip()
            return "fix_issue", prompt
    return None, None

def refine_game(current_code, error=None, improvement_type=None, prompt=None):
    if not improvement_type or not prompt:
        improvement_type, prompt = show_refinement_prompt()
        if not improvement_type:
            return current_code
    
    print("\n🔄 Generating improvements...")
    return call_coder_assistant(
        f"Refine this game code based on: {prompt}\n\n"
        f"IMPORTANT RULES:\n"
        f"- Game must run automatically (no user input required)\n"
        f"- Previous game state must be cleared before new game starts\n"
        f"- Screen sections:\n"
        f"  - Top {TITLE_AREA_HEIGHT} pixels: Title area\n"
        f"  - Middle {GAME_AREA_HEIGHT} pixels: Main game area\n"
        f"  - Bottom {LIGHTING_AREA_HEIGHT} pixels: Lighting effects\n\n"
        f"Current code:\n{current_code}"
    )

def show_loading_animation(is_graphic_designer=False, progress_text=None):
    # Set default text based on type
    if progress_text is None:
        progress_text = "DESIGNING..." if is_graphic_designer else "CODING..."
    
    # Game of Life setup
    cells = [[random.random() < 0.3 for _ in range(64)] for _ in range(64)]
    
    # Text setup - in title area (first 17 rows)
    text_y = 8  # Moved down from 5 to 8
    text_x = (64 - len(progress_text) * 4) // 2 + 2  # Moved right by adding 2 pixels
    
    # Simple 5x3 font for each character
    font = {
        'C': [[1,1,1], [1,0,0], [1,0,0], [1,0,0], [1,1,1]],
        'R': [[1,1,1], [1,0,1], [1,1,1], [1,1,0], [1,0,1]],
        'E': [[1,1,1], [1,0,0], [1,1,1], [1,0,0], [1,1,1]],
        'A': [[0,1,0], [1,0,1], [1,1,1], [1,0,1], [1,0,1]],
        'T': [[1,1,1], [0,1,0], [0,1,0], [0,1,0], [0,1,0]],
        'I': [[1,1,1], [0,1,0], [0,1,0], [0,1,0], [1,1,1]],
        'N': [[1,0,1], [1,1,1], [1,1,1], [1,0,1], [1,0,1]],
        'G': [[1,1,1], [1,0,0], [1,0,1], [1,0,1], [1,1,1]],
        'O': [[1,1,1], [1,0,1], [1,0,1], [1,0,1], [1,1,1]],
        'D': [[1,1,0], [1,0,1], [1,0,1], [1,0,1], [1,1,0]],
        'S': [[1,1,1], [1,0,0], [1,1,1], [0,0,1], [1,1,1]],
        'F': [[1,1,1], [1,0,0], [1,1,1], [1,0,0], [1,0,0]],
        '.': [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,1,0]]
    }
    
    # Draw initial frame immediately
    matrix.Clear()
    
    try:
        while not loading_stop_event.is_set():  # Check for stop event
            # Update Game of Life
            new_cells = [[False for _ in range(64)] for _ in range(64)]
            for y in range(64):
                for x in range(64):
                    # Skip the title area to keep it clear
                    if y < 17:
                        continue
                        
                    # Count neighbors
                    neighbors = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = (x + dx) % 64, (y + dy) % 64
                            if cells[ny][nx]:
                                neighbors += 1
                    
                    # Apply rules
                    if cells[y][x]:
                        new_cells[y][x] = neighbors in [2, 3]
                    else:
                        new_cells[y][x] = neighbors == 3
                    
                    # Draw cell
                    if new_cells[y][x]:
                        if is_graphic_designer:
                            r = random.randint(0, 255)
                            g = random.randint(0, 255)
                            b = random.randint(0, 255)
                        else:
                            r = random.randint(0, 50)
                            g = random.randint(0, 100)
                            b = random.randint(0, 50)
                        matrix.SetPixel(x, y, r, g, b)
                    else:
                        matrix.SetPixel(x, y, 0, 0, 0)
            
            cells = new_cells
            
            # Draw pulsing text
            pulse = 0.5 + 0.5 * math.sin(time.time() * 3)  # Pulsing effect
            intensity = int(255 * pulse)
            
            # Clear the title area
            for y in range(17):
                for x in range(64):
                    matrix.SetPixel(x, y, 0, 0, 0)
            
            # Draw each character
            for i, char in enumerate(progress_text):
                char_data = font.get(char.upper(), font['.'])  # Use dot for unknown chars
                for y in range(5):  # Character height
                    for x in range(3):  # Character width
                        if char_data[y][x]:  # Only draw if the pixel should be on
                            matrix.SetPixel(text_x + i*4 + x, text_y + y, intensity, intensity, intensity)
            
            time.sleep(0.05)  # Faster animation update
            
    except Exception as e:
        print(f"⚠️ Error in loading animation: {str(e)}")
        show_error_symbol()
    finally:
        # Clear the matrix when animation stops
        matrix.Clear()

def create_game(prompt=None, title=None):
    print("\n🎮 Create New or Load Existing Game:")
    print("1. Create New")
    print("2. Load Existing")
    choice = input("Choose an option: ").strip()

    if choice == '2':
        folders = list_existing_folders(GAME_FOLDER)
        if not folders:
            print("No existing games found.")
            return
        print("\n📂 Existing Games:")
        for i, name in enumerate(folders):
            latest = get_latest_attempt(os.path.join(GAME_FOLDER, name))
            desc = get_description(os.path.join(GAME_FOLDER, name))
            print(f"{i + 1}. {name} [{latest}] → {desc[:50]}...")
        idx = int(input("Choose a game folder: ").strip()) - 1
        folder = folders[idx]
        latest = get_latest_attempt(os.path.join(GAME_FOLDER, folder))
        if latest:
            # Run the game in the current VR environment
            game_path = os.path.join(GAME_FOLDER, folder, latest)
            try:
                # Execute the game in the current Python environment
                with open(game_path, 'r') as f:
                    game_code = f.read()
                exec(game_code, {'matrix': matrix, 'RGBMatrix': RGBMatrix, 'RGBMatrixOptions': RGBMatrixOptions})
            except Exception as e:
                print(f"❌ Error running game: {e}")
                show_error_symbol()
        return

    if not prompt:
        prompt = input("\nDescribe a game: ").strip()
    
    print("\n✨ Naming your game...")
    if not title:
        title, description = call_game_title_generator(prompt)
    else:
        description = f"A game about {prompt.lower()}"
    
    print(f"\n🎮 Making {title}...")
    
    # Generate the game code first
    print("\n💻 Generating game code...")
    result = call_coder_assistant(prompt)
    
    # Try to save, but continue even if it fails
    folder_path = os.path.join(GAME_FOLDER, title)
    try:
        ensure_directory(folder_path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"v1_{timestamp}.py"
        with open(os.path.join(folder_path, filename), 'w') as f:
            f.write(result)
        save_description(folder_path, title, description)
        print(f"\n✨ Game saved to {folder_path}")
    except Exception as e:
        print(f"⚠️ Warning: Could not save game: {e}")
        print("Continuing with in-memory execution...")
    
    print(f"📄 Description: {description}")
    
    # Launch the game in the current VR environment
    print("\n🚀 Launching game...")
    
    # Add retry logic for running the game
    max_consecutive_failures = 7
    consecutive_failures = 0
    last_error = None
    current_code = result
    successful_run = False
    
    while True:  # Keep trying until successful or user gives up
        while consecutive_failures < max_consecutive_failures:
            try:
                # Create a dictionary with all necessary imports and variables
                game_env = {
                    'matrix': matrix,
                    'RGBMatrix': RGBMatrix,
                    'RGBMatrixOptions': RGBMatrixOptions,
                    'random': random,
                    'time': time,
                    'Image': Image,
                    'PIL': Image,
                    # Screen section constants
                    'TITLE_AREA': (0, TITLE_AREA_HEIGHT),
                    'GAME_AREA': (TITLE_AREA_HEIGHT, TITLE_AREA_HEIGHT + GAME_AREA_HEIGHT),
                    'AMBIENT_AREA': (TITLE_AREA_HEIGHT + GAME_AREA_HEIGHT, 64),
                    'TITLE_AREA_HEIGHT': TITLE_AREA_HEIGHT,
                    'GAME_AREA_HEIGHT': GAME_AREA_HEIGHT,
                    'AMBIENT_AREA_HEIGHT': LIGHTING_AREA_HEIGHT
                }
                
                if consecutive_failures > 0:
                    print(f"\n🔄 Attempt {consecutive_failures + 1}/{max_consecutive_failures} - Fixing error: {last_error}")
                    # Send error and code to AI for complete fix
                    current_code = call_coder_assistant(
                        f"Fix this game code that has the following error: {last_error}\n\n"
                        f"IMPORTANT RULES:\n"
                        f"- Game must run automatically (no user input required)\n"
                        f"- Previous game state must be cleared before new game starts\n"
                        f"- Screen sections:\n"
                        f"  - Top {TITLE_AREA_HEIGHT} pixels: Title area\n"
                        f"  - Middle {GAME_AREA_HEIGHT}, pixels: Main game area\n"
                        f"  - Bottom {LIGHTING_AREA_HEIGHT} pixels: Lighting effects\n\n"
                        f"Current code with error:\n{current_code}"
                    )
                
                # Clear any previous game state
                matrix.Clear()
                
                # Execute the game in the current Python environment
                exec(current_code, game_env)
                
                # If we get here, the game ran successfully
                successful_run = True
                consecutive_failures = 0  # Reset failure counter on success
                break
                
            except Exception as e:
                last_error = str(e)
                print(f"❌ Error running game: {e}")
                show_error_symbol()
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print("\n❌ Max consecutive failures reached.")
                    break
                time.sleep(1)  # Brief pause before retry
        
        if successful_run:
            print("\n✅ Game completed successfully!")
            break
            
        # Ask if user wants to try again
        print("\n🔄 Would you like to try again?")
        print("1. Yes, try again")
        print("2. No, return to menu")
        choice = input("Choose an option: ").strip()
        
        if choice == '1':
            # Reset counters and try again
            consecutive_failures = 0
            last_error = None
            current_code = result
            successful_run = False
            print("\n🔄 Starting new attempt...")
        else:
            print("\n👋 Returning to menu...")
            break
    
    input("\nPress Enter to return to menu.")

def fix_list_index_error(code):
    """Automatically fix list index out of range errors"""
    # Add bounds checking for list accesses
    fixed_code = code.replace(
        "pixels[x, y] =",
        "if 0 <= x < 64 and 0 <= y < 64: pixels[x, y] ="
    )
    return fixed_code

def fix_undefined_variable(code):
    """Automatically fix undefined variable errors"""
    # Add missing variable initializations
    if "player_x" not in code:
        code = "player_x = 32\n" + code
    if "player_y" not in code:
        code = "player_y = 32\n" + code
    if "score" not in code:
        code = "score = 0\n" + code
    if "game_over" not in code:
        code = "game_over = False\n" + code
    return code

def fix_image_rotation(code):
    """Automatically fix image rotation issues"""
    # Ensure proper image rotation
    fixed_code = code.replace(
        "matrix.SetImage(image)",
        "matrix.SetImage(image.rotate(180))"
    )
    return fixed_code

def main():
    print("\n🎮✨ Welcome to the Penphin Creator ✨🎮")
    while True:
        print("\nMain Menu:")
        print("1. Create Game")
        print("2. Create Pixel Art")
        print("3. Exit")
        choice = input("Choose an option: ").strip()

        if choice == '1':
            create_game()
        elif choice == '2':
            create_animation()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()