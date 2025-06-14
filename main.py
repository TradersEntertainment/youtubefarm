# MrBeast TikTok Bot with Turkish Subtitles & CAPTCHA bypass

import os
import subprocess
import whisper
import yt_dlp
import openai
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from playwright.sync_api import sync_playwright
import time
import uuid

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME")
TIKTOK_PASSWORD = os.getenv("TIKTOK_PASSWORD")
CHANNEL_URL = "https://www.youtube.com/@MrBeast/videos"
VIDEO_LENGTH_LIMIT = 60

TEMP_DIR = "temp"
OUTPUT_DIR = "output"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_latest_video():
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio/best',
        'outtmpl': f'{TEMP_DIR}/video.%(ext)s',
        'noplaylist': False,
        'quiet': True,
        'no_warnings': True,
        'playlist_items': '1'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=True)
        print("🎬 Video indirildi:", info.get("title"))
        return f"{TEMP_DIR}/video.mp4"

def transcribe_video(video_path):
    model = whisper.load_model("base.en")
    result = model.transcribe(video_path)
    return result['segments']

def translate_segments(segments):
    openai.api_key = OPENAI_API_KEY
    for seg in segments:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Aşağıdaki cümleyi Türkçeye çevir:\n{seg['text']}"}]
        )
        seg['text'] = response['choices'][0]['message']['content']
    return segments

def find_best_clip(segments):
    keywords = ["won", "crazy", "insane", "unbelievable"]
    for seg in segments:
        if any(kw in seg['text'].lower() for kw in keywords):
            return seg['start'], min(seg['end'], seg['start'] + VIDEO_LENGTH_LIMIT)
    return segments[0]['start'], segments[0]['start'] + VIDEO_LENGTH_LIMIT

def create_clip(video_path, start, end, segments):
    clip = VideoFileClip(video_path).subclip(start, end)
    w, h = clip.size
    crop_width = int(h * 9 / 16)
    x_center = (w - crop_width) // 2
    clip = clip.crop(x1=x_center, x2=x_center + crop_width)
    clip = clip.resize(height=1920)
    
    subtitle_text = " ".join(seg['text'] for seg in segments if start <= seg['start'] <= end)
    subtitle = TextClip(subtitle_text, fontsize=48, color='white', size=clip.size)
    subtitle = subtitle.set_duration(clip.duration).set_position(('center', 'bottom'))
    final = CompositeVideoClip([clip, subtitle])
    out_path = os.path.join(OUTPUT_DIR, f"clip_{uuid.uuid4()}.mp4")
    final.write_videofile(out_path, codec='libx264', audio_codec='aac')
    return out_path, subtitle_text

def generate_caption(prompt):
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Aşağıdaki video için kısa, dikkat çekici bir TikTok başlığı ve 2 Türkçe hashtag öner:\n{prompt}"}]
    )
    return response['choices'][0]['message']['content']

def manual_login_and_save_session():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.tiktok.com/login")
        print("🚨 Lütfen TikTok girişini tamamlayın ve CAPTCHA'yı çözün.\nTamamlandığında ENTER'a basın.")
        input()
        context.storage_state(path="state.json")
        browser.close()

def upload_to_tiktok(video_path, caption):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="state.json")
        page = context.new_page()
        page.goto("https://www.tiktok.com/upload")
        time.sleep(5)
        page.set_input_files("input[type='file']", video_path)
        time.sleep(5)
        page.fill("[placeholder='Videonu açıkla']", caption)
        time.sleep(1)
        page.click("text=Yükle")
        time.sleep(10)
        context.close()
        browser.close()

def main():
    if not os.path.exists("state.json"):
        manual_login_and_save_session()
    video_path = download_latest_video()
    segments = transcribe_video(video_path)
    segments = translate_segments(segments)
    start, end = find_best_clip(segments)
    clip_path, transcript = create_clip(video_path, start, end, segments)
    caption = generate_caption(transcript)
    upload_to_tiktok(clip_path, caption)

if __name__ == '__main__':
    main()
