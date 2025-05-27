import os
import json
import subprocess
import requests
from gtts import gTTS
from keybert import KeyBERT
from dotenv import load_dotenv

load_dotenv()
OUTPUT_DIR = "media/output"
VOICE_PATH = f"{OUTPUT_DIR}/voice.mp3"
VIDEO_PATH = f"{OUTPUT_DIR}/video.mp4"
LOOPED_VIDEO_PATH = f"{OUTPUT_DIR}/video_looped.mp4"
CAPTION_PATH = f"{OUTPUT_DIR}/caption.txt"
FINAL_VIDEO_PATH = f"{OUTPUT_DIR}/final.mp4"

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_keyword(text, num_keywords=3):
    kw_model = KeyBERT()
    keywords = kw_model.extract_keywords(text, stop_words="english", top_n=num_keywords)
    return keywords[0][0] if keywords else "technology"

def download_pexels_video(query, api_key, out_path):
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": 1}
    res = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    res.raise_for_status()
    videos = res.json().get("videos", [])
    if not videos:
        raise Exception("No videos found.")
    video_url = videos[0]["video_files"][0]["link"]
    video_data = requests.get(video_url).content
    with open(out_path, "wb") as f:
        f.write(video_data)

def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    duration = float(json.loads(result.stdout)["format"]["duration"])
    return duration

def loop_video_to_duration(video_in, duration, video_out):
    loop_count = int(duration // 10) + 1
    subprocess.run([
        "ffmpeg", "-stream_loop", str(loop_count),
        "-i", video_in,
        "-t", str(duration + 1),
        "-c", "copy", video_out
    ], check=True)

def generate_final_video(text):
    # Step 1: Extract keyword
    keyword = extract_keyword(text)

    # Step 2: Download video
    download_pexels_video(keyword, PEXELS_API_KEY, VIDEO_PATH)

    # Step 3: Generate audio
    tts = gTTS(text)
    tts.save(VOICE_PATH)

    # Step 4: Get duration
    duration = get_audio_duration(VOICE_PATH)

    # Step 5: Loop video
    loop_video_to_duration(VIDEO_PATH, duration, LOOPED_VIDEO_PATH)

    # Step 6: Save captions
    with open(CAPTION_PATH, "w") as f:
        f.write(text)

    # Step 7: Combine everything
    cmd = [
        "ffmpeg",
        "-i", LOOPED_VIDEO_PATH,
        "-i", VOICE_PATH,
        "-vf",
        f"drawtext=textfile={CAPTION_PATH}:fontcolor=white:fontsize=14:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-100",
        "-c:a", "aac",
        "-shortest",
        FINAL_VIDEO_PATH
    ]
    subprocess.run(cmd, check=True)

    return FINAL_VIDEO_PATH
