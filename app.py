"""
==============================================================
 TERMINAL VIDEO DOWNLOADER WEB (CLEAN VERSION)
==============================================================
No 'downloads' folder will be created.
Each download happens in a temp folder, then deleted automatically.
"""

from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import re
import tempfile
import zipfile
import shutil
import platform

app = Flask(__name__)

# Auto-detect FFmpeg path
if platform.system() == "Windows":
    FFMPEG_PATH = r"C:\Users\tempu\Desktop\TERMINAL VIDEO DOWNLOADER\ffmpeg\bin\ffmpeg.exe"
else:
    FFMPEG_PATH = "/usr/bin/ffmpeg"  # for Render or Linux

def sanitize_filename(name):
    """Remove illegal filename characters."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_media(url, download_choice, temp_dir):
    """Download a single media file into the temp folder."""
    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    # Common yt-dlp options
    common_opts = {
        'outtmpl': output_template,
        'ffmpeg_location': FFMPEG_PATH,
        'quiet': True,
        'noprogress': True,
        'cookies': 'cookies.txt',
        'nooverwrites': True,
        'restrictfilenames': True,
    }

    if download_choice == "audio":
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        }
    else:
        ydl_opts = {
            **common_opts,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if download_choice == "audio":
            filename = os.path.splitext(filename)[0] + ".mp3"

    return filename


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    urls_input = request.form.get("urls", "")
    download_choice = request.form.get("type", "audio")
    urls = [u.strip() for u in re.split(r'[\n,]+', urls_input) if u.strip()]

    if not urls:
        return "❌ No URLs provided!"

    # Create a temporary directory (deleted after download)
    temp_dir = tempfile.mkdtemp()
    downloaded_files = []

    for url in urls:
        try:
            print(f"Downloading: {url}")
            file_path = download_media(url, download_choice, temp_dir)
            downloaded_files.append(file_path)
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")

    # Single file → send directly
    if len(downloaded_files) == 1:
        file_path = downloaded_files[0]
        filename = os.path.basename(file_path)
        response = send_file(file_path, as_attachment=True, download_name=filename)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return response

    # Multiple files → zip them
    zip_path = os.path.join(temp_dir, "downloads.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in downloaded_files:
            zipf.write(file, os.path.basename(file))

    response = send_file(zip_path, as_attachment=True, download_name="downloads.zip")
    shutil.rmtree(temp_dir, ignore_errors=True)
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
