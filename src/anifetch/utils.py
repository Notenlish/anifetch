# animfetch/utils.py

"""
Anifetch utility module for common functions used across the application.
"""

import pathlib
import re
import subprocess
import sys
from importlib.resources import files
from platformdirs import user_data_dir
from importlib.metadata import version, PackageNotFoundError
import shutil

appname = "anifetch"
appauthor = "anifetch"


def get_version_of_anifetch():
    try:
        return version("anifetch")
    except PackageNotFoundError:
        raise Exception("Anifetch package not found.")


def check_sound_flag_given(cmd):
    if "--sound" in cmd:
        return True
    return False


def print_verbose(verbose, *msg):
    if verbose:
        print(*msg)


def strip_ansi(text):
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def get_text_length_of_formatted_text(text: str):
    text = strip_ansi(text)
    return len(text)


def get_ext_from_codec(codec):
    codec_extension_map = {
        "aac": "m4a",
        "mp3": "mp3",
        "opus": "opus",
        "vorbis": "ogg",
        "pcm_s16le": "wav",
        "flac": "flac",
        "alac": "m4a",
    }
    if not codec or codec.lower() not in codec_extension_map:
        raise ValueError(f"Unsupported or unknown codec: {codec}")
    return codec_extension_map[codec.lower()]


def check_codec_of_file(file: str):
    try:
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
        codec = subprocess.check_output(ffprobe_cmd, text=True).strip()
        return codec
    except subprocess.CalledProcessError:
        print_verbose(True, f"Error: Unable to determine codec for file {file}.")
        return None


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
    try:
        subprocess.run(extract_cmd, check=True)
        return audio_file
    except subprocess.CalledProcessError:
        print_verbose(True, f"Error: Unable to extract audio from file {file}.")
        return None


def get_data_path():
    # on linux: /home/[username]/.local/share/anifetch
    # windows: C:\\Users\\[Username]\\AppData\\Local\\anifetch\\anifetch
    base = pathlib.Path(user_data_dir(appname, appauthor))
    base.mkdir(parents=True, exist_ok=True)
    return base


def default_asset_presence_check(asset_dir):
    if not any(asset_dir.iterdir()):
        packaged_asset = files("anifetch.assets") / "example.mp4"
        shutil.copy(str(packaged_asset), asset_dir / "example.mp4")


def get_neofetch_status():  # will still save the rendered chafa in cache in any case
    try:
        # check the result of running neofetch with --version
        result = subprocess.run(
            ["neofetch", "--version"], capture_output=True, text=True
        )
        output = result.stdout + result.stderr
        if (
            "fastfetch" in output.lower()
        ):  # if the output contains "fastfetch", return wrapper
            return "wrapper"
        else:
            return "neofetch"  # neofetch works
    except FileNotFoundError:
        return "uninstalled"  # neofetch is not installed


def render_frame(path, width, height, chafa_args: str) -> str:
    """
    Renders a single frame using chafa.

    Args:
        path (Path): Path to the image file.
        width (int): Target width for rendering.
        height (int): Target height for rendering.
        chafa_args (str): Additional CLI arguments for chafa (space-separated).

    Returns:
        str: Rendered frame as ASCII text.

    Raises:
        SystemExit: If chafa fails to render the frame.
    """
    chafa_cmd = [
        "chafa",
        *chafa_args.strip().split(),
        "--format",
        "symbols",  # Fix issue #1 by forcing consistent rendering
        f"--size={width}x{height}",
        path.as_posix(),
    ]

    try:
        return subprocess.check_output(chafa_cmd, text=True)
    except subprocess.CalledProcessError as e:
        print(
            f"[ERROR] chafa rendering failed.\nCommand: {' '.join(chafa_cmd)}\nError: {e.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)


def get_video_dimensions(filename):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        filename,
    ]
    try:
        output = subprocess.check_output(
            cmd, text=True, stderr=subprocess.STDOUT
        ).strip()
        # print("OUTPUT OF GET VIDEO DIMENSIONS:", output)
        width_str, height_str = output.split("x")
        return int(width_str), int(height_str)
    except subprocess.CalledProcessError as e:
        print("FFPROBE FAILED WITH OUTPUT:", e.output)
        raise RuntimeError(f"Failed to get video dimensions: {filename}")
