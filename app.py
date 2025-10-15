"""
TERMINAL VIDEO DOWNLOADER WEB (DEBUG-FRIENDLY)
- Uses temp folders (no persistent 'downloads' folder)
- Checks cookies.txt and returns clear error messages when download fails
"""

from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import re
import tempfile
import zipfile
import shutil
import platform
import traceback

app = Flask(__name__)

# Auto-detect FFmpeg path
if platform.system() == "Windows":
    FFMPEG_PATH = r"C:\Users\tempu\Desktop\TERMINAL VIDEO DOWNLOADER\ffmpeg\bin\ffmpeg.exe"
else:
    FFMPEG_PATH = "/usr/bin/ffmpeg"  # for Render or Linux

COOKIES_FILE = "cookies.txt"  # must be placed in same folder as app.py if required

def download_media(url, download_choice, temp_dir, use_cookies=True):
    """Download a single media file into the temp folder.
       Returns (filepath, None) on success or (None, error_message) on failure.
    """
    output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    common_opts = {
        'outtmpl': output_template,
        'ffmpeg_location': FFMPEG_PATH,
        'quiet': True,
        'noprogress': True,
        'nooverwrites': True,
        'restrictfilenames': True,
    }

    # Add cookies only if file exists and use_cookies True
    if use_cookies and os.path.exists(COOKIES_FILE):
        common_opts['cookies'] = COOKIES_FILE

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_choice == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"
        return filename, None

    except Exception as e:
        # Return traceback string for debugging (you can shorten this)
        tb = traceback.format_exc()
        return None, f"yt-dlp error for {url}: {str(e)}\n{tb}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    urls_input = request.form.get("urls", "")
    download_choice = request.form.get("type", "audio")
    urls = [u.strip() for u in re.split(r'[\n,]+', urls_input) if u.strip()]

    if not urls:
        return "❌ No URLs provided!", 400

    # If cookies.txt is missing, inform user (but still attempt without cookies)
    cookies_present = os.path.exists(COOKIES_FILE)
    if not cookies_present:
        # warn user but allow trying without cookies for public videos
        warning = ("⚠️ cookies.txt not found. "
                   "YouTube may block downloads with HTTP 429 or 'Sign in' errors. "
                   "Place a valid cookies.txt next to app.py and redeploy.")
    else:
        warning = None

    temp_dir = tempfile.mkdtemp()
    downloaded_files = []
    errors = []

    for url in urls:
        file_path, err = download_media(url, download_choice, temp_dir, use_cookies=cookies_present)
        if file_path:
            downloaded_files.append(file_path)
        else:
            errors.append(err)

    # If there were errors and no files downloaded, return error details
    if len(downloaded_files) == 0:
        # cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        return (f"❌ All downloads failed.\n"
                f"{warning + '\\n' if warning else ''}"
                f"Errors:\n" + "\n\n".join(errors)), 500

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
