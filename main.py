import os
import random
from datetime import datetime
import yt_dlp
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from moviepy.editor import VideoFileClip
from googleapiclient.http import MediaFileUpload

# -------------------------------------------------------------
# Environment Secrets & Target Channels
# -------------------------------------------------------------
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")

TARGET_CHANNELS = [
    "https://www.youtube.com/@HardToonz22",
    "https://www.youtube.com/@Lilyash",
    "https://www.youtube.com/@tiny.farming",
    "https://www.youtube.com/@Lala_Loops"
]

def get_youtube_service():
    creds = Credentials(
        None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def download_latest_video(channel_url, is_short=True):
    print(f"🎬 Checking content from: {channel_url}")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloaded_video.%(ext)s',
        'quiet': True,
        'playlistend': 5
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            target_url = f"{channel_url}/shorts" if is_short else f"{channel_url}/videos"
            info = ydl.extract_info(target_url, download=False)
            entries = info.get('entries', [])
            if not entries:
                return None, None
            
            selected_video = random.choice(entries)
            video_url = selected_video.get('webpage_url')
            title = selected_video.get('title', 'Fun Animation Story')
            
            ydl.download([video_url])
            return "downloaded_video.mp4", title
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None, None

def process_video_for_cloning(input_file):
    print("✂️ Modifying video parameters (1.05x speed boost) to prevent reuse detection...")
    clip = VideoFileClip(input_file)
    modified_clip = clip.speedx(1.05)
    output_file = "processed_cloned_video.mp4"
    modified_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    modified_clip.close()
    return output_file

def upload_to_youtube(video_file, title, is_short=True):
    youtube = get_youtube_service()
    hashtag = "#Shorts #Animation #ToonTalesStudio #Viral #Cartoons" if is_short else "#Animation #Cartoon #ToonTalesStudio #Stories"
    
    body = {
        "snippet": {
            "title": f"{title} {hashtag}",
            "description": f"{title}\n\nWelcome to Toon & Tales Studio! Enjoy amazing animations and 3D cartoon stories.\n\n{hashtag}",
            "tags": ["Animation", "3D Cartoons", "ToonTalesStudio", "Viral", "Shorts"],
            "categoryId": "1"  # Film & Animation
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading... {int(status.progress() * 100)}%")
            
    print(f"🎉 Upload successful! Video ID: {response.get('id')}")

if __name__ == "__main__":
    current_hour = datetime.utcnow().hour
    # Schedule check: BD time 8 AM & 5 PM (Shorts), 8 PM (Long video)
    is_short = True if current_hour in [2, 11] else False
    
    selected_channel = random.choice(TARGET_CHANNELS)
    raw_video, video_title = download_latest_video(selected_channel, is_short=is_short)
    
    if raw_video and os.path.exists(raw_video):
        final_video = process_video_for_cloning(raw_video)
        upload_to_youtube(final_video, video_title, is_short=is_short)
        
        # Clean up files after upload
        if os.path.exists("downloaded_video.mp4"):
            os.remove("downloaded_video.mp4")
        if os.path.exists("processed_cloned_video.mp4"):
            os.remove("processed_cloned_video.mp4")
    else:
        print("⚠️ No valid video found for processing at this time.")
        
