# === Streamed Playback Pipeline for LED Matrix (64x64) ===

import subprocess
import numpy as np
import cv2
import time
from PIL import Image, ImageDraw, ImageFont
from yt_dlp import YoutubeDL
from rgbmatrix import RGBMatrix, RGBMatrixOptions

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

# === Get Live Stream URL ===
def get_stream_url(youtube_url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]',
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info['url'], info.get('title', 'Unknown'), info.get('uploader', 'Unknown')

# === Display on Matrix ===
def display_frame(video_frame, title_text, author_text):
    full_image = Image.new("RGB", (64, 64))
    draw = ImageDraw.Draw(full_image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 6)

    # Title Area (0-17)
    draw.rectangle([0, 0, 63, 17], fill=(0, 0, 0))
    draw.text((1, 2), title_text[:25], font=font, fill=(255, 255, 255))
    draw.text((1, 9), author_text[:25], font=font, fill=(100, 100, 100))

    # Game Area (18–57)
    full_image.paste(video_frame, (0, 18))

    # Ambient (58–63)
    bar = video_frame.crop((0, 39, 64, 40))
    pixels = bar.getdata()
    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[1] for p in pixels) // len(pixels)
    b = sum(p[2] for p in pixels) // len(pixels)
    for y in range(58, 64):
        for x in range(64):
            full_image.putpixel((x, y), (r, g, b))

    matrix.SetImage(full_image.rotate(180))

# === Main Stream Display Loop ===
def stream_video(youtube_url):
    stream_url, title, author = get_stream_url(youtube_url)

    print(f"🎥 Streaming: {title} by {author}")
    command = [
        'ffmpeg', '-i', stream_url,
        '-f', 'image2pipe',
        '-pix_fmt', 'rgb24',
        '-vcodec', 'rawvideo', '-']

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    frame_width, frame_height = 640, 360  # Native input
    raw_frame_size = frame_width * frame_height * 3
    last_display = time.time()
    frame_delay = 0.12  # Increase delay between frames for smoother playback

    try:
        while True:
            raw = process.stdout.read(raw_frame_size)
            if len(raw) != raw_frame_size:
                break

            frame = np.frombuffer(raw, dtype=np.uint8).reshape((frame_height, frame_width, 3))
            frame = cv2.resize(frame, (64, 40), interpolation=cv2.INTER_AREA)
            pil_frame = Image.fromarray(frame)

            now = time.time()
            if now - last_display >= frame_delay:
                display_frame(pil_frame, title, author)
                last_display = now
            else:
                time.sleep(0.01)  # prevent CPU overuse

    except KeyboardInterrupt:
        print("🛑 Stream interrupted.")
    finally:
        matrix.Clear()
        process.terminate()
        process.wait()

# === Entry Point ===
if __name__ == "__main__":
    url = input("📺 Enter YouTube URL to stream: ").strip()
    if not url:
        url = "https://youtu.be/dQw4w9WgXcQ"
    stream_video(url)
