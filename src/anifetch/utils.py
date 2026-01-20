# animfetch/utils.py

"""
Anifetch utility module for common functions used across the application.
"""

import pathlib
import json
import re
import subprocess
import sys
from importlib.resources import files
from platformdirs import user_data_dir
from importlib.metadata import version, PackageNotFoundError
import shutil
from copy import deepcopy
from hashlib import sha256

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


def extract_audio_from_file(CACHE_PATH, file: str, extension):
    audio_file = CACHE_PATH / f"output_audio.{extension}"
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
        # if the output contains "fastfetch", return wrapper
        if "fastfetch" in output.lower():
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


def clean_cache_args(cache_args: dict) -> dict:
    """Removes unimportant caching args that don't matter when caching/checking caches. Returns the cleaned dict."""
    args_to_remove = (
        "playback_rate",
        "verbose",
        "fast_fetch",
        "benchmark",
        "force_render",
    )
    cleaned = deepcopy(cache_args)  # need to deepcopy to not modify original dict.
    for key in args_to_remove:
        if key in cleaned:
            del cleaned[key]
    return cleaned


def check_args_hash_same(args1: dict, args2: dict):
    for a in (args1, args2):
        if a.get("hash", None) is None:
            raise KeyError(f"{args1} doesn't have a hash!")
    if args1["hash"] == args2["hash"]:
        return True
    return False


def find_corresponding_cache(args: dict, all_saved_caches_list: list[dict]):
    corresponding = None
    for saved_cache_dict in all_saved_caches_list:
        if check_args_hash_same(args, saved_cache_dict):
            corresponding = saved_cache_dict
    if corresponding is None:
        raise LookupError("Couldn't find corresponding dict in all saved caches.")
    return corresponding


def hash_dict(d: dict):
    json_str = json.dumps(d, sort_keys=True, ensure_ascii=False)
    encoded = json_str.encode("utf-8")
    hashed = sha256(encoded)
    return hashed.hexdigest()


def hash_of_cache_args(args: dict):
    """Takes in the cleaned dictionary consisting of all the arguments for caching and generates an hash. If a 'hash' key already exists raises an KeyError."""
    if "hash" in args.keys():
        raise KeyError("Hash already exists for this cache args dictionary.")

    hash = hash_dict(args)
    return hash


def get_caches_json(CACHE_LIST_PATH):
    if (CACHE_LIST_PATH).exists():
        with open(CACHE_LIST_PATH, "r") as f:
            caches_data: list[dict] = json.load(f)
        return caches_data
    return []


def save_caches_json(CACHE_LIST_PATH, data):
    with open(CACHE_LIST_PATH, "w") as f:
        json.dump(data, f, indent=2)


def args_checker(allowed_alternatives, args):
    if args.filename is None and not any(
        getattr(args, key) for key in allowed_alternatives
    ):
        raise ValueError(
            "Missing input. Use a filename or a cache monitoring argument.\nUse --help for help."
        )


def threaded_chafa_frame_gen(
    i: int,
    f: str,
    VIDEO_DIR: pathlib.Path,
    OUTPUT_DIR: pathlib.Path,
    WIDTH: int,
    HEIGHT: int,
    chafa_args: str,
    centered: bool,
    len_fetch: int,
    fetch_output: list[str],
    frames: dict[int, str],
) -> list[str] | None:
    # f = 00001.png
    path = VIDEO_DIR / f
    frame = render_frame(path, WIDTH, HEIGHT, chafa_args)

    chafa_lines = frame.splitlines()
    fetch_lines: list[str] | None = None

    if centered:  # TODO: should i check for i == 0?
        # centering the fetch output or the chafa animation if needed.
        len_chafa = len(chafa_lines)

        if (
            len_chafa < len_fetch
        ):  # if the chafa animation is shorter than the fetch output
            pad = (len_fetch - len_chafa) // 2
            remind = (len_fetch - len_chafa) % 2
            chafa_lines.pop()  # don't ask me why, the last line always seems to be empty
            chafa_lines = (
                [" " * WIDTH] * pad + chafa_lines + [" " * WIDTH] * (pad + remind)
            )

        elif (
            len_fetch < len_chafa
            and i == 0  # I only need one thread to update the fetch_lines(template)
        ):  # if the chafa animation is longer than the fetch output
            pad = (len_chafa - len_fetch) // 2
            remind = (len_chafa - len_fetch) % 2
            fetch_lines = (
                [" " * WIDTH] * pad + fetch_output + [" " * WIDTH] * (pad + remind)
            )

        if i == 0:
            # updating the HEIGHT variable from the first frame
            HEIGHT = len(chafa_lines)
    else:
        if i == 0:
            len_chafa = len(chafa_lines)
            pad = abs(len_fetch - len_chafa) // 2
            remind = abs(len_fetch - len_chafa) % 2
            HEIGHT = len(chafa_lines) + (2 * pad + remind) * WIDTH

    out = "\n".join(chafa_lines)

    if i == 0:
        frames[i] = out
    with open((OUTPUT_DIR / f).with_suffix(".txt"), "w") as file:
        file.write(out)

    return fetch_lines
