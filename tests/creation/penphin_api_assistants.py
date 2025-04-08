import openai
import datetime
import json
import random
import time
import os
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import threading
from threading import Event
from PIL import Image
import math

# === CONFIG ===
API_KEY = ""
DEBUG_MODE = True  # Enable debug mode by default

# Get the current script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ERROR_LOG_DIR = os.path.join(SCRIPT_DIR, "error_logs")
PIXEL_ART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))), "PixelArt")

# Ensure directories exist
os.makedirs(ERROR_LOG_DIR, exist_ok=True, mode=0o755)
os.makedirs(PIXEL_ART_DIR, exist_ok=True, mode=0o755)

# Cache for OpenAI client
_client = None

def get_openai_client():
    global _client
    if _client is None:
        print("\n🔌 Initializing OpenAI client...")
        _client = openai.OpenAI(api_key=API_KEY)
        # Warm up the client with a simple request
        try:
            _client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            print("✅ Client initialized successfully")
        except Exception as e:
            print(f"⚠️ Warning: Client warm-up failed: {str(e)}")
    return _client

# Initialize client on import
client = get_openai_client()

# === SYSTEM PROMPTS ===

CODE_ASSISTANT_MSG = (
    "You are a creative Python game designer for RGB LED matrices (64x64) using the `PIL.Image` system "
    "and `matrix.SetImage()` to render.\n\n"
    "Design **mini games** that run automatically (no input required), using large 8x8 or bigger sprites. "
    "The display has 3 sections:\n"
    "- TITLE_AREA: (0–14) — shows score/title/status.\n"
    "- GAME_AREA: (14–54) — the main gameplay zone.\n"
    "- AMBIENT_AREA: (54–64) — for ambient color effects.\n\n"
    "IMPORTANT RULES:\n"
    "1. ALL sprites and assets MUST be created directly in the code using PIL.Image.new()\n"
    "2. NO external files or resources can be used\n"
    "3. Each sprite must be created as a new Image with its own pixels set\n"
    "4. Example sprite creation:\n"
    "   sprite = Image.new('RGB', (8, 8), (0, 0, 0))\n"
    "   pixels = sprite.load()\n"
    "   pixels[0,0] = (255, 0, 0)  # Set individual pixels\n"
    "5. Animate visibly within GAME_AREA\n"
    "6. Feature player, enemy, or moving objects\n"
    "7. Track score or game state\n"
    "8. End after a time limit or trigger\n"
    "9. Use automatic logic to play itself\n"
    "10. Rotate display for VR (flip via image.rotate(180))\n"
    "11. Include startup and cleanup code\n\n"
    "Use this display setup at the top of every script:\n\n"
    "from rgbmatrix import RGBMatrix, RGBMatrixOptions\n"
    "from PIL import Image\n"
    "import time, random\n\n"
    "options = RGBMatrixOptions()\n"
    "options.rows = 64\n"
    "options.cols = 64\n"
    "options.chain_length = 1\n"
    "options.parallel = 1\n"
    "options.hardware_mapping = 'regular'\n"
    "options.brightness = 30\n"
    "options.disable_hardware_pulsing = True\n"
    "matrix = RGBMatrix(options=options)\n\n"
    "Now create the game. ONLY output valid Python code. DO NOT wrap in markdown or explain anything."
)
VISUAL_ASSISTANT_MSG = (
    "You are a visual AI named PenphinEyes. You respond ONLY with raw visual frame data that SYMBOLICALLY represents the prompt. "
    "Each frame must consist of 64 lines. Each line must have 64 pixel values. "
    "Each pixel value must be in the format '#RRGGBB' (hex color only). "
    "If you want to show a second frame, separate it using the line:\n"
    "=== FRAME BREAK ===\n\n"
    "IMPORTANT RULES:\n"
    "1. The visual MUST symbolically represent the prompt's meaning\n"
    "2. Use colors and patterns that convey the prompt's essence\n"
    "3. Create meaningful visual metaphors\n"
    "4. No explanations, text, or formatting—only pure frame data\n"
    "5. Each frame should tell a story or convey an emotion"
)

TITLE_GENERATOR_MSG = (
    "You are a creative naming agent for visual pixel games and artworks. Respond ONLY in JSON format.\n\n"
    "Response format:\n"
    "{\n"
    "  \"title\": \"UniqueGameTitle\",  # Max 30 chars, CamelCase, no spaces\n"
    "  \"description\": \"Brief summary of the concept (max 100 characters)\"\n"
    "}\n\n"
    "RULES:\n"
    "1. Title must be UNIQUE and use CamelCase (no spaces, no symbols).\n"
    "2. Description should clearly express the theme, motion, or emotion of the creation.\n"
    "3. Do NOT include explanation or markdown—only valid JSON."
)

# === MATRIX SETUP ===
matrix_options = RGBMatrixOptions()
matrix_options.rows = 64
matrix_options.cols = 64
matrix_options.chain_length = 1
matrix_options.parallel = 1
matrix_options.hardware_mapping = 'regular'
matrix_options.brightness = 30
matrix_options.disable_hardware_pulsing = True
matrix_options.led_rgb_sequence = "RGB"
matrix = RGBMatrix(options=matrix_options)

# Rotation constant (0=0°, 1=90°, 2=180°, 3=270°)
ROTATE = 2

# Add after matrix setup
loading_stop_event = Event()

def log_error(error_type, prompt, response, error_message, target_dir=None):
    try:
        # Use the script's error log directory if no target directory specified
        if target_dir:
            error_dir = os.path.join(target_dir, "error_logs")
        else:
            error_dir = ERROR_LOG_DIR
        
        os.makedirs(error_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = os.path.join(error_dir, f"error_{timestamp}.json")
        
        error_data = {
            "timestamp": timestamp,
            "error_type": error_type,
            "error_message": str(error_message),
            "prompt": prompt,
            "response": response
        }
        
        with open(error_file, 'w') as f:
            json.dump(error_data, f, indent=2)
        print(f"⚠️ Error logged to: {error_file}")
        
        if DEBUG_MODE:
            print("\n🔍 Debug Information:")
            print(f"Error Type: {error_type}")
            print(f"Error Message: {error_message}")
            print("\nRequest:")
            print(json.dumps({"prompt": prompt}, indent=2))
            print("\nResponse:")
            print(json.dumps({"response": response}, indent=2))
            
    except Exception as e:
        print(f"❌ Failed to log error: {str(e)}")
        if DEBUG_MODE:
            print(f"Error occurred in log_error: {str(e)}")

def extract_json_from_response(response_text):
    try:
        # First try to parse the entire response as JSON
        try:
            data = json.loads(response_text)
            # Validate the structure
            if "frames" in data and isinstance(data["frames"], list):
                # Ensure each frame has 64 rows
                for frame in data["frames"]:
                    if len(frame) != 64:
                        raise ValueError(f"Invalid frame height: {len(frame)} rows (expected 64)")
                    # Ensure each row has 64 pixels
                    for row in frame:
                        if len(row) != 64:
                            raise ValueError(f"Invalid row width: {len(row)} pixels (expected 64)")
                return data
        except json.JSONDecodeError:
            pass
        
        # If that fails, try to find JSON within the text
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start == -1 or end == 0:
            return None
        
        json_str = response_text[start:end]
        try:
            data = json.loads(json_str)
            # Validate the structure
            if "frames" in data and isinstance(data["frames"], list):
                # Ensure each frame has 64 rows
                for frame in data["frames"]:
                    if len(frame) != 64:
                        raise ValueError(f"Invalid frame height: {len(frame)} rows (expected 64)")
                    # Ensure each row has 64 pixels
                    for row in frame:
                        if len(row) != 64:
                            raise ValueError(f"Invalid row width: {len(row)} pixels (expected 64)")
                return data
        except json.JSONDecodeError as e:
            log_error("JSON_EXTRACTION", response_text, None, str(e))
            return None
    except Exception as e:
        log_error("JSON_EXTRACTION", response_text, None, str(e))
        return None

def show_random_animation(is_graphic_designer=False, progress=0.0):
    # Calculate the shrinking area based on progress
    width = int(64 * (1 - progress))
    height = int(64 * (1 - progress))
    start_x = (64 - width) // 2
    start_y = (64 - height) // 2
    
    for _ in range(5):  # Show 5 frames of random animation
        for y in range(64):
            for x in range(64):
                if start_x <= x < start_x + width and start_y <= y < start_y + height:
                    if is_graphic_designer:
                        # Colorful randomness for graphic designer
                        r = random.randint(0, 255)
                        g = random.randint(0, 255)
                        b = random.randint(0, 255)
                    else:
                        # Dark green/black for coder
                        r = random.randint(0, 50)
                        g = random.randint(0, 100)
                        b = random.randint(0, 50)
                    matrix.SetPixel(x, y, r, g, b)
                else:
                    # Show game of life in the stabilized areas
                    if random.random() < 0.3:
                        intensity = int(255 * (1 - progress))
                        matrix.SetPixel(x, y, intensity, intensity, intensity)
                    else:
                        matrix.SetPixel(x, y, 0, 0, 0)
        time.sleep(0.1)

def show_structured_animation(progress):
    # Game of Life style animation that becomes more structured as progress increases
    cells = [[random.random() < 0.3 for _ in range(64)] for _ in range(64)]
    
    for _ in range(5):  # Show 5 frames
        new_cells = [[False for _ in range(64)] for _ in range(64)]
        for y in range(64):
            for x in range(64):
                # Count neighbors
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = (x + dx) % 64, (y + dy) % 64
                        if cells[ny][nx]:
                            neighbors += 1
                
                # Apply rules with progress-based mutation
                if cells[y][x]:
                    new_cells[y][x] = neighbors in [2, 3] or random.random() < (1 - progress)
                else:
                    new_cells[y][x] = neighbors == 3 or random.random() < (1 - progress)
                
                # Display with progress-based color
                if new_cells[y][x]:
                    intensity = int(255 * progress)
                    matrix.SetPixel(x, y, intensity, intensity, intensity)
                else:
                    matrix.SetPixel(x, y, 0, 0, 0)
        
        cells = new_cells
        time.sleep(0.1)

def show_error_symbol(error_message=None):
    """
    Display a stylized error symbol with optional error message.
    
    Args:
        error_message (str, optional): Error message to display in the title area
        
    The display includes:
    - A pulsing red X with glow effect
    - An inner circle
    - Optional error message in the title area
    """
    # Clear the matrix first
    matrix.Clear()
    
    try:
        # Draw a stylized X with glow effect
        for frame in range(20):  # Show for 20 frames
            # Calculate pulse intensity
            pulse = 0.5 + 0.5 * math.sin(time.time() * 5)
            intensity = int(255 * pulse)
            
            # Clear the matrix
            matrix.Clear()
            
            # Draw outer glow
            for i in range(64):
                for j in range(64):
                    # Calculate distance from center
                    dx = abs(i - 31.5)
                    dy = abs(j - 31.5)
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    # Create a circular glow effect
                    if dist < 30:
                        glow_intensity = int(intensity * (1 - dist/30))
                        matrix.SetPixel(i, j, glow_intensity, 0, 0)
            
            # Draw stylized X
            for i in range(64):
                # Main X with thickness
                for offset in range(-1, 2):
                    # Main diagonal
                    if 0 <= i+offset < 64 and 0 <= i+offset < 64:
                        matrix.SetPixel(i+offset, i+offset, intensity, 0, 0)
                    # Anti-diagonal
                    if 0 <= 63-i+offset < 64 and 0 <= i+offset < 64:
                        matrix.SetPixel(63-i+offset, i+offset, intensity, 0, 0)
            
            # Draw inner circle
            for angle in range(0, 360, 5):
                rad = math.radians(angle)
                x = int(31.5 + 10 * math.cos(rad))
                y = int(31.5 + 10 * math.sin(rad))
                if 0 <= x < 64 and 0 <= y < 64:
                    matrix.SetPixel(x, y, intensity, 0, 0)
            
            # Display error message if provided
            if error_message:
                display_error_text(error_message, intensity)
            
            time.sleep(0.05)  # 20fps animation
        
        # Keep the error displayed for 2 seconds
        time.sleep(2)
        
    except Exception as e:
        print(f"⚠️ Error in error display: {str(e)}")
    finally:
        matrix.Clear()

def display_error_text(error_message, intensity):
    """
    Display error message text in the title area.
    
    Args:
        error_message (str): Error message to display
        intensity (int): Current pulse intensity for the text
    """
    # Simple 3x5 font for error message
    error_font = {
        'A': [[1,1,1], [1,0,1], [1,1,1], [1,0,1], [1,0,1]],
        'B': [[1,1,0], [1,0,1], [1,1,0], [1,0,1], [1,1,0]],
        'C': [[1,1,1], [1,0,0], [1,0,0], [1,0,0], [1,1,1]],
        'D': [[1,1,0], [1,0,1], [1,0,1], [1,0,1], [1,1,0]],
        'E': [[1,1,1], [1,0,0], [1,1,1], [1,0,0], [1,1,1]],
        'F': [[1,1,1], [1,0,0], [1,1,1], [1,0,0], [1,0,0]],
        'G': [[1,1,1], [1,0,0], [1,0,1], [1,0,1], [1,1,1]],
        'H': [[1,0,1], [1,0,1], [1,1,1], [1,0,1], [1,0,1]],
        'I': [[1,1,1], [0,1,0], [0,1,0], [0,1,0], [1,1,1]],
        'J': [[0,0,1], [0,0,1], [0,0,1], [1,0,1], [1,1,1]],
        'K': [[1,0,1], [1,1,0], [1,0,0], [1,1,0], [1,0,1]],
        'L': [[1,0,0], [1,0,0], [1,0,0], [1,0,0], [1,1,1]],
        'M': [[1,0,1], [1,1,1], [1,1,1], [1,0,1], [1,0,1]],
        'N': [[1,0,1], [1,1,1], [1,1,1], [1,0,1], [1,0,1]],
        'O': [[1,1,1], [1,0,1], [1,0,1], [1,0,1], [1,1,1]],
        'P': [[1,1,1], [1,0,1], [1,1,1], [1,0,0], [1,0,0]],
        'Q': [[1,1,1], [1,0,1], [1,0,1], [1,1,1], [0,0,1]],
        'R': [[1,1,1], [1,0,1], [1,1,1], [1,1,0], [1,0,1]],
        'S': [[1,1,1], [1,0,0], [1,1,1], [0,0,1], [1,1,1]],
        'T': [[1,1,1], [0,1,0], [0,1,0], [0,1,0], [0,1,0]],
        'U': [[1,0,1], [1,0,1], [1,0,1], [1,0,1], [1,1,1]],
        'V': [[1,0,1], [1,0,1], [1,0,1], [0,1,0], [0,1,0]],
        'W': [[1,0,1], [1,0,1], [1,1,1], [1,1,1], [1,0,1]],
        'X': [[1,0,1], [0,1,0], [0,1,0], [0,1,0], [1,0,1]],
        'Y': [[1,0,1], [0,1,0], [0,1,0], [0,1,0], [0,1,0]],
        'Z': [[1,1,1], [0,0,1], [0,1,0], [1,0,0], [1,1,1]],
        ' ': [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]],
        ':': [[0,0,0], [0,1,0], [0,0,0], [0,1,0], [0,0,0]],
        '.': [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,1,0]],
        '_': [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [1,1,1]]
    }
    
    # Display error message in title area
    error_text = f"ERR: {error_message[:20]}"  # Limit to 20 chars
    text_x = 2
    text_y = 2
    
    for i, char in enumerate(error_text.upper()):
        char_data = error_font.get(char, error_font[' '])
        for y in range(5):
            for x in range(3):
                if char_data[y][x]:
                    if ROTATE == 2:  # 180 degrees
                        matrix.SetPixel(63 - (text_x + i*4 + x), 63 - (text_y + y), intensity, 0, 0)
                    else:
                        matrix.SetPixel(text_x + i*4 + x, text_y + y, intensity, 0, 0)

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
                    
                    # Draw cell (rotated)
                    if new_cells[y][x]:
                        if is_graphic_designer:
                            r = random.randint(0, 255)
                            g = random.randint(0, 255)
                            b = random.randint(0, 255)
                        else:
                            r = random.randint(0, 50)
                            g = random.randint(0, 100)
                            b = random.randint(0, 50)
                        # Apply rotation
                        if ROTATE == 2:  # 180 degrees
                            matrix.SetPixel(63-x, 63-y, r, g, b)
                        else:
                            matrix.SetPixel(x, y, r, g, b)
                    else:
                        # Apply rotation
                        if ROTATE == 2:  # 180 degrees
                            matrix.SetPixel(63-x, 63-y, 0, 0, 0)
                        else:
                            matrix.SetPixel(x, y, 0, 0, 0)
            
            cells = new_cells
            
            # Draw pulsing text
            pulse = 0.5 + 0.5 * math.sin(time.time() * 3)  # Pulsing effect
            intensity = int(255 * pulse)
            
            # Clear the title area
            for y in range(17):
                for x in range(64):
                    if ROTATE == 2:  # 180 degrees
                        matrix.SetPixel(63-x, 63-y, 0, 0, 0)
                    else:
                        matrix.SetPixel(x, y, 0, 0, 0)
            
            # Draw each character
            for i, char in enumerate(progress_text):
                char_data = font.get(char.upper(), font['.'])  # Use dot for unknown chars
                for y in range(5):  # Character height
                    for x in range(3):  # Character width
                        if char_data[y][x]:  # Only draw if the pixel should be on
                            # Apply rotation
                            if ROTATE == 2:  # 180 degrees
                                rot_x = 63 - (text_x + i*4 + x)
                                rot_y = 63 - (text_y + y)
                            else:
                                rot_x = text_x + i*4 + x
                                rot_y = text_y + y
                            matrix.SetPixel(rot_x, rot_y, intensity, intensity, intensity)
            
            time.sleep(0.05)  # Faster animation update
            
    except Exception as e:
        print(f"⚠️ Error in loading animation: {str(e)}")
        show_error_symbol()
    finally:
        # Clear the matrix when animation stops
        matrix.Clear()

def parse_raw_frames(raw_data):
    """Parse raw hex color data into a list of frames"""
    frames = []
    current_frame = [[(0, 0, 0) for _ in range(64)] for _ in range(64)]  # Initialize 64x64 grid with black
    pixel_count = 0
    
    # Process each line
    for line in raw_data.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check for frame break
        if line == "=== FRAME BREAK ===":
            # Add current frame if we have any pixels
            if pixel_count > 0:
                frames.append(current_frame)
                # Initialize new frame
                current_frame = [[(0, 0, 0) for _ in range(64)] for _ in range(64)]
                pixel_count = 0
            continue
            
        # Remove commas and split on #
        hex_colors = line.replace(',', '').split('#')[1:]  # Skip first empty element
        
        for hex_color in hex_colors:
            try:
                # Calculate x,y coordinates (0-based)
                x = pixel_count % 64
                y = pixel_count // 64
                
                # If we've filled the current frame, start a new one
                if y >= 64:
                    frames.append(current_frame)
                    current_frame = [[(0, 0, 0) for _ in range(64)] for _ in range(64)]
                    pixel_count = 0
                    x = 0
                    y = 0
                
                # Ensure we have 6 characters
                hex_color = hex_color.strip()
                if len(hex_color) < 6:
                    hex_color = hex_color.ljust(6, '0')
                elif len(hex_color) > 6:
                    hex_color = hex_color[:6]
                
                # Parse RGB values
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                
                # Set the pixel
                current_frame[y][x] = (r, g, b)
                pixel_count += 1
                
            except:
                # If parsing fails, skip this pixel
                pixel_count += 1
                continue
    
    # Add the last frame if it has any pixels
    if pixel_count > 0:
        frames.append(current_frame)
        
    # Log frame information
    total_pixels = sum(len(frame) * len(frame[0]) for frame in frames)
    print(f"📊 Processed {len(frames)} frames with {total_pixels} total pixels")
    if total_pixels < len(frames) * 64 * 64:
        print(f"⚠️ Warning: Some frames are incomplete")
        
    return frames

def show_visual_frames(raw_data):
    """
    Display visual frames from raw hex color data and collect user feedback.
    
    Args:
        raw_data (str): Raw hex color data containing frame information
        
    Returns:
        tuple: (improvement_type, improvement_prompt) if user wants changes,
               (None, None) if no changes needed or on error
    """
    try:
        frames = parse_raw_frames(raw_data)
        
        if not frames:
            print("⚠️ No valid frames found in data.")
            return None, None
            
        # Display each frame with proper rotation
        for frame in frames:
            matrix.Clear()
            for y, row in enumerate(frame):
                for x, (r, g, b) in enumerate(row):
                    if ROTATE == 2:  # 180 degrees
                        matrix.SetPixel(63-x, 63-y, r, g, b)
                    else:
                        matrix.SetPixel(x, y, r, g, b)
            time.sleep(1)
            
        # Keep the last frame displayed until user input
        print("\nPress Enter to continue...")
        input()
        
        # Only clear the display if no error occurred
        matrix.Clear()
        
        # Collect user feedback
        print("\n💭 What would you like to improve?")
        print("1. Visual effects")
        print("2. Animation timing")
        print("3. Color scheme")
        print("4. Overall design")
        print("5. No changes needed")
        
        while True:
            choice = input("\nChoose an option (1-5): ").strip()
            
            if choice in ['1', '2', '3', '4']:
                improvement_type = {
                    '1': 'visual effects',
                    '2': 'animation timing',
                    '3': 'color scheme',
                    '4': 'overall design'
                }[choice]
                
                prompt = input(f"\nDescribe the {improvement_type} changes you want: ").strip()
                if prompt:  # Only return if we have a valid prompt
                    return improvement_type, prompt
                else:
                    print("Please provide a description of the changes you want.")
                    continue
                    
            elif choice == '5':
                return None, None
                
            else:
                print("Invalid choice. Please select 1-5.")
                continue
                
    except Exception as e:
        print(f"❌ Error displaying visual frames: {e}")
        # Keep the last frame displayed until user input
        print("\nPress Enter to continue...")
        input()
        return None, None

def call_coder_assistant(prompt, model="gpt-3.5-turbo"):
    try:
        print("\n💻 Starting code generation...")
        # Reset the stop event
        loading_stop_event.clear()
        # Start loading animation in a separate thread
        loading_thread = threading.Thread(
            target=show_loading_animation,
            args=(False, "CODING...")
        )
        loading_thread.daemon = True
        loading_thread.start()
        
        print("🧠 Processing code concepts...")
        messages = [
            {"role": "system", "content": CODE_ASSISTANT_MSG},
            {"role": "user", "content": prompt}
        ]
        
        if DEBUG_MODE:
            print("\n🔍 Request:")
            print(json.dumps({"messages": messages}, indent=2))
        
        response = get_openai_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.6,
            max_tokens=1500
        )
        
        if DEBUG_MODE:
            print("\n🔍 Response:")
            print(response.choices[0].message.content)
        
        # Stop loading animation
        loading_stop_event.set()
        loading_thread.join()
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"⚠️ Error in code generation: {str(e)}")
        # Stop loading animation and show error
        loading_stop_event.set()
        show_error_symbol()
        log_error("CODE_GENERATION", prompt, None, str(e))
        return f"# ERROR: {str(e)}"

def call_graphic_designer_assistant(prompt, model="gpt-3.5-turbo"):
    try:
        print("\n🎨 Starting visual generation...")
        # Reset the stop event
        loading_stop_event.clear()
        # Start loading animation in a separate thread
        loading_thread = threading.Thread(
            target=show_loading_animation,
            args=(True, "DESIGNING...")
        )
        loading_thread.daemon = True
        loading_thread.start()
        
        print("🧠 Processing visual concepts...")
        messages = [
            {"role": "system", "content": VISUAL_ASSISTANT_MSG},
            {"role": "user", "content": prompt}
        ]
        
        if DEBUG_MODE:
            print("\n🔍 Request:")
            print(json.dumps({"messages": messages}, indent=2))
        
        response = get_openai_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )
        
        if DEBUG_MODE:
            print("\n🔍 Response:")
            print(response.choices[0].message.content)
        
        print("📝 Processing visual data...")
        raw_data = response.choices[0].message.content
        
        # Clean up the raw data
        # Remove any JSON markers or other non-frame data
        if raw_data.startswith('{"frames":'):
            try:
                data = json.loads(raw_data)
                if "frames" in data:
                    raw_data = data["frames"]
            except:
                pass
                
        # Ensure we have a string
        if isinstance(raw_data, str):
            # Remove any leading/trailing whitespace and newlines
            raw_data = raw_data.strip()
            # Remove any JSON markers
            raw_data = raw_data.replace('{"frames":', '').replace('}', '')
            # Remove any markdown code blocks
            raw_data = raw_data.replace('```', '')
            # Remove any other non-hex characters except # and newlines
            raw_data = ''.join(c for c in raw_data if c.isalnum() or c in ['#', '\n'])
        
        # Stop loading animation
        loading_stop_event.set()
        loading_thread.join()
        
        # Show the frames immediately
        improvement_type, improvement_prompt = show_visual_frames(raw_data)
        
        return improvement_type, improvement_prompt
        
    except Exception as e:
        print(f"⚠️ Error in visual generation: {str(e)}")
        # Stop loading animation but don't show error symbol to preserve the display
        loading_stop_event.set()
        loading_thread.join()
        # Keep the last frame displayed until user input
        print("\nPress Enter to continue...")
        input()
        if not isinstance(e, Exception):
            log_error("VISUAL_GENERATION", prompt, None, str(e))
        return None, None

def generate_fallback_content(prompt):
    # Create a meaningful fallback title
    words = [word.capitalize() for word in prompt.split() if word.isalnum()]
    fallback_title = "".join(words[:3]) or "Game" + str(random.randint(1000, 9999))
    
    # Create a meaningful description
    fallback_desc = f"A game about {prompt.lower()}"
    
    # Create a simple but meaningful ASCII art
    fallback_ascii = """
    /\\
   /  \\
  /    \\
    @
    """
    
    return fallback_title, fallback_desc, fallback_ascii

def call_game_title_generator(prompt, model="gpt-3.5-turbo", target_dir=None):
    try:
        print("\n🧠 Generating game title...")
        
        messages = [
            {
                "role": "system",
                "content": TITLE_GENERATOR_MSG
            },
            {
                "role": "user",
                "content": f"Create a game title based on this prompt: {prompt}"
            }
        ]
        
        if DEBUG_MODE:
            print("\n🔍 Debug - Request:")
            print(json.dumps({"messages": messages}, indent=2))
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )
        
        response_content = response.choices[0].message.content
        print("\n🔍 Debug - Raw Response:")
        print(response_content)
        
        print("📝 Processing response...")
        result = extract_json_from_response(response_content)
        
        if not result:
            raise ValueError("Failed to extract valid JSON from response")
            
        # Validate and ensure all fields are present and meaningful
        if not all(key in result for key in ["title", "description"]):
            raise ValueError("Missing required fields in response")
            
        # Ensure title is valid
        if not result["title"] or len(result["title"]) > 30 or " " in result["title"]:
            result["title"] = "".join(word.capitalize() for word in prompt.split()[:3])
            
        # Ensure description is valid
        if not result["description"] or len(result["description"]) > 100:
            result["description"] = f"A game about {prompt.lower()}"
            
        print(f"\n✨ Title: {result['title']}")
        print(f"📄 Description: {result['description']}")
        
        return result["title"], result["description"]
    except Exception as e:
        print(f"⚠️ Error in title generation: {str(e)}")
        log_error("TITLE_GENERATION", prompt, response.choices[0].message.content if 'response' in locals() else None, str(e), target_dir)
        # Use the fallback generator
        fallback_title = "".join(word.capitalize() for word in prompt.split()[:3])
        fallback_desc = f"A game about {prompt.lower()}"
        return fallback_title, fallback_desc

# === EXAMPLE ===
if __name__ == "__main__":
    code = call_coder_assistant("Make a rainbow swirl with fading trails.")
    print("\n[CODE OUTPUT]\n")
    print(code)

    frames = call_graphic_designer_assistant("Draw a ripple effect in blue and indigo.")
    print("\n[GRAPHIC OUTPUT]\n")
    print(frames)
