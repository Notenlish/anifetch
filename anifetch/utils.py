# animfetch/utils.py

'''
    Anifetch utility module for common functions used across the application.
'''

import os
import pathlib
import re
import subprocess
import sys


def print_verbose(verbose, *msg):
    if verbose:
        print(*msg)


def strip_ansi(text):
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def get_text_length_of_formatted_text(text: str):
    text = strip_ansi(text)
    return len(text)


def get_ext_from_codec(codec: str):
    codec_extension_map = {
        "aac": "m4a",
        "mp3": "mp3",
        "opus": "opus",
        "vorbis": "ogg",
        "pcm_s16le": "wav",
        "flac": "flac",
        "alac": "m4a",
    }
    return codec_extension_map.get(codec, "bin")


def check_codec_of_file(file: str):
    ffprobe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name",
        "-of",
        "default=nokey=1:noprint_wrappers=1",
        file,
    ]
    codec = str(subprocess.check_output(ffprobe_cmd, text=True).strip())
    return codec


def extract_audio_from_file(BASE_PATH, file: str, extension):
    audio_file = BASE_PATH / f"output_audio.{extension}"
    extract_cmd = [
        "ffmpeg",
        "-i",
        file,
        "-y",
        "-vn",
        "-c:a",
        "copy",
        "-loglevel",
        "quiet",
        audio_file,
    ]
    subprocess.call(extract_cmd)
    return audio_file


def get_data_path():
    xdg_data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    data_path = os.path.join(xdg_data_home, "anifetch")
    os.makedirs(data_path, exist_ok=True)
    return pathlib.Path(data_path)


def check_sound_flag():
    if "--sound" in sys.argv or "-s" in sys.argv:
        return True
    return False

def check_chroma_flag():
    if "--chroma" in sys.argv:
        return True
    return False

def get_neofetch_status():  # will still save the rendered chafa in cache in any case
    try:
        # check the result of running neofetch with --version
        result = subprocess.run(["neofetch", "--version"], capture_output=True, text=True)
        output = result.stdout + result.stderr
        if "fastfetch" in output.lower(): # if the output contains "fastfetch", return wrapper
            return "wrapper"
        else:
            return "neofetch"  # neofetch works
    except FileNotFoundError:
        return "uninstalled"  # neofetch is not installed
    
def get_video_dimensions(filename):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        filename
    ]
    output = subprocess.check_output(cmd, text=True).strip()
    width_str, height_str = output.split('x')
    return int(width_str), int(height_str)