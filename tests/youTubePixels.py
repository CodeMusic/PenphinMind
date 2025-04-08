
import random
import os
import cv2
from PIL import Image
from yt_dlp import YoutubeDL

def download_video(youtube_url, output_path="temp_video.mp4"):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    return output_path

def extract_frames(video_path, max_frames=2):
    cap = cv2.VideoCapture(video_path)
    frames = []
    count = 0
    while cap.isOpened() and count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (64, 64))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_frame = Image.fromarray(frame)
        frames.append(pil_frame)
        count += 1
    cap.release()
    return frames

def frame_to_pixel_string(pil_img):
    pixels = pil_img.load()
    output = []
    for y in range(64):
        row = []
        for x in range(64):
            r, g, b = pixels[x, y]
            brightness = max(r, g, b) * 100 // 255
            row.append(f"#{r:02X}{g:02X}{b:02X}:{brightness}")
        output.append(" ".join(row))
    return output

def main():
    RANDOM_YOUTUBE_VIDEOS = [
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtu.be/fC_q9KPczAg",
        "https://youtu.be/jfKfPfyJRdk"
    ]

    try:
        youtube_url = input("🎥 Enter YouTube video URL (or press Enter for a surprise): ").strip()
        if not youtube_url:
            youtube_url = random.choice(RANDOM_YOUTUBE_VIDEOS)
            print(f"🎲 Surprise! Using: {youtube_url}")

        print("📥 Downloading video...")
        video_path = download_video(youtube_url)

        print("🎞️ Extracting frames...")
        frames = extract_frames(video_path)

        print("🧼 Converting to 64x64 format...")
        for i, frame in enumerate(frames):
            print(f"\n=== FRAME {i + 1} ===")
            for row in frame_to_pixel_string(frame):
                print(row)

    finally:
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
            print("🗑️ Temporary video file removed.")

if __name__ == "__main__":
    main()
