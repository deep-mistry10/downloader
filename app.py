"""
==============================================================
 TERMINAL VIDEO DOWNLOADER WEB
 Copyright (c) 2025 Deep Mistry
 Author: Deep Mistry
 License: All Rights Reserved
 Version: 2.0.0
 Description:
 A stable, web-based YouTube & media downloader using yt-dlp + FFmpeg.
 Optimized for both local (Windows) and Render hosting.
==============================================================
"""

from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import re
import tempfile
import zipfile
import shutil
from pathlib import Path
import platform

app = Flask(__name__)

# ✅ Auto-detect FFmpeg path (works on both PC and Render)
if platform.system() == "Windows":
    FFMPEG_PATH = r"/usr/bin/ffmpeg"
else:
    FFMPEG_PATH = "/usr/bin/ffmpeg"  # default on Render/Linux

def sanitize_filename(name):
    """Remove illegal characters from file names."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_media(url, download_choice, temp_dir):
    """Download a single media file and return its final path."""
    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    if download_choice == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'ffmpeg_location': FFMPEG_PATH,
            'quiet': True,
            'noprogress': True
            'cookies': 'cookies.txt'
        }
    else:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'ffmpeg_location': FFMPEG_PATH,
            'quiet': True,
            'noprogress': True
            'cookies': 'cookies.txt'
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Determine correct filename
        if download_choice == "audio":
            filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        else:
            filename = ydl.prepare_filename(info)

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

    temp_dir = tempfile.mkdtemp()
    downloaded_files = []

    for url in urls:
        try:
            file_path = download_media(url, download_choice, temp_dir)
            downloaded_files.append(file_path)
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")

    # ✅ Send single file directly
    if len(downloaded_files) == 1:
        file_path = downloaded_files[0]
        filename = os.path.basename(file_path)
        response = send_file(file_path, as_attachment=True, download_name=filename)
        # cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        return response

    # ✅ Zip multiple files
    zip_path = os.path.join(temp_dir, "downloads.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in downloaded_files:
            zipf.write(file, os.path.basename(file))

    response = send_file(zip_path, as_attachment=True, download_name="downloads.zip")
    # cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


