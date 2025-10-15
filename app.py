"""
==============================================================
 TERMINAL VIDEO DOWNLOADER WEB
 Copyright (c) 2025 Deep Mistry. All Rights Reserved.
 Author: Deep Mistry
 License: All Rights Reserved
 Version: 1.0.0
 Description:
 A web-based YouTube & media downloader using yt-dlp and FFmpeg.
==============================================================
"""

from flask import Flask, render_template, request, send_file
import yt_dlp
import os
from pathlib import Path
import re
import tempfile
import zipfile

app = Flask(__name__)
FFMPEG_PATH = r"C:\Users\tempu\Desktop\TERMINAL VIDEO DOWNLOADER\ffmpeg\bin\ffmpeg.exe"

def sanitize_filename(name):
    """Remove illegal characters from file names."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_media(url, download_choice, temp_dir):
    """Download a single media file and return its final path."""
    if download_choice == "audio":
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'ffmpeg_location': FFMPEG_PATH
        }
    else:
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'ffmpeg_location': FFMPEG_PATH
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Fix: set the correct final file path
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
        return "No URLs provided!"

    temp_dir = tempfile.mkdtemp()
    downloaded_files = []

    # Download all URLs
    for url in urls:
        try:
            file_path = download_media(url, download_choice, temp_dir)
            downloaded_files.append(file_path)
        except Exception as e:
            print(f"Failed {url}: {e}")

    # If only one file, send directly
    if len(downloaded_files) == 1:
        file_path = downloaded_files[0]
        filename = os.path.basename(file_path)
        return send_file(file_path, as_attachment=True, download_name=filename)

    # If multiple files, zip them
    zip_path = os.path.join(temp_dir, "downloads.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in downloaded_files:
            zipf.write(file, os.path.basename(file))
    return send_file(zip_path, as_attachment=True, download_name="downloads.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
