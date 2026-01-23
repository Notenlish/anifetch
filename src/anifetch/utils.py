# animfetch/utils.py

"""
Anifetch utility module for common functions used across the application.
"""

import pathlib
import json
import re
import subprocess
import os
import sys
from importlib.resources import files
from importlib.metadata import version, PackageNotFoundError
import shutil
from copy import deepcopy
from hashlib import sha256
from typing import Literal
import errno


from platformdirs import user_data_dir
import wcwidth

appname = "anifetch"
appauthor = "anifetch"

# Source - https://stackoverflow.com/a
# Posted by James Spencer, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-21, License - CC BY-SA 4.0

if os.name == "nt":
    import msvcrt
    import ctypes

    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int), ("visible", ctypes.c_byte)]


def clear_screen():
    """Clears screen using cls or clear depending on OS."""
    _ = os.system("cls" if os.name == "nt" else "clear")
    # sys.stdout.write("\x1b[2J")
    # sys.stdout.flush()


def disable_autowrap():
    """Returns whether it was able to disable autowrap."""
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[?7l")
        sys.stdout.flush()
        return True
    return False


def enable_autowrap():
    """Returns whether it was able to enable autowrap."""
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[?7h")
        sys.stdout.flush()
        return True
    return False


def tput_cup(row: int, col: int):
    """Moves the cursor to positions row and col.
    https://man7.org/linux/man-pages/man1/tput.1.html

    Does not flush.
    """
    sys.stdout.write(f"\x1b[{row + 1};{col + 1}H")
    # sys.stdout.flush()  # not needed appearently


def tput_el():  # tput clear to end of the line
    """Clears from the cursor to the end of the line."""
    sys.stdout.write("\x1b[K")
    sys.stdout.flush()


def get_terminal_width():
    """Returns terminal width(columns)"""
    return os.get_terminal_size().columns


def get_terminal_height():
    """Returns terminal height(lines)"""
    return os.get_terminal_size().lines


def hide_cursor():
    if os.name == "nt":
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == "posix":
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


def show_cursor():
    if os.name == "nt":
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = True
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.name == "posix":
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def clean_ansi(raw_text: str):
    return ANSI_RE.sub("", raw_text)


def get_character_width(raw: str):
    """Gives the raw terminal width of a particular string by stripping ANSI codes, removing \n \t \r and using wcwidth to get the actual character width."""
    return wcwidth.wcswidth(
        clean_ansi(raw).replace("\n", "").replace("\r", "").replace("\t", "")
    )


def truncate_line(line: str, max_width: int):
    """Does not keep the trailing \n"""
    if max_width <= 0 or not line:
        return ""

    # Remove ANSI codes to get visible text length
    visible_length = get_character_width(line)

    total_output = ""
    if visible_length <= max_width:
        total_output = f"{line}\r"
    else:
        out: list[str] = []
        width = 0
        i = 0

        while i < len(line) and width < max_width:
            # if ansi sequence starts, copy it to out
            m = ANSI_RE.match(line, i)
            if m:
                out.append(m.group(0))
                i = m.end()
                continue
            ch = line[i]
            i += 1

            w: int = wcwidth.wcwidth(ch)
            if w < 0:
                w = 0

            if width + w > max_width:
                break
            out.append(ch)
            width += w
        out.append("\x1b[0m")
        total_output = "".join(out)
    total_output = total_output.replace("\n", "")
    total_output = total_output.replace("\r", "")
    return total_output


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


def get_fetch_output(
    use_fastfetch: bool,
    neofetch_status: Literal["neofetch", "uninstalled", "wrapper"],
    force_neofetch: bool,
):
    fetch_output: list[str]
    if not use_fastfetch:
        if (
            neofetch_status == "wrapper" and force_neofetch
        ) or neofetch_status == "neofetch":
            # Get Neofetch Output
            fetch_output = subprocess.check_output(
                ["neofetch", "--off"], text=True
            ).splitlines()

        elif neofetch_status == "uninstalled":
            print(
                "Neofetch is not installed. Please install Neofetch or Fastfetch.",
                file=sys.stderr,
            )
            sys.exit(1)

        else:
            print(
                "Neofetch is deprecated. Try fastfetch using '-ff' argument or force neofetch to run using '--force' argument.",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        try:
            fetch_output = subprocess.check_output(
                ["fastfetch", "--logo", "none", "--pipe", "false"], text=True
            ).splitlines()
        except FileNotFoundError as e:
            if e.errno == errno.ENOENT:
                print(
                    "The command Fastfetch was not found. You probably forgot to install it. You can install it by going to here: https://github.com/fastfetch-cli/fastfetch?tab=readme-ov-file#installation\n If you installed Fastfetch but it still doesn't work, check your PATH."
                )
                raise SystemExit
            else:
                raise Exception(e)
    return fetch_output


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
        "symbols",  # Fixes https://github.com/Notenlish/anifetch/issues/1
        f"--size={width}x{height}",
        path.as_posix(),
    ]

    p = subprocess.run(
        chafa_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if p.returncode != 0:
        print(
            f"[ERROR] chafa rendering failed.\nCommand: {' '.join(chafa_cmd)}\nError: {p.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)
    return p.stdout


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


if __name__ == "__main__":
    a = "                                                [m[1m[33mGPU 2[m: [mNVIDIA GeForce RTX 3050 Ti Laptop GPU @ 2.10 GHz (3.87 GiB) [Discrete]\n"
    print(a)
    b = truncate_line(a, 111)
    print(b)
