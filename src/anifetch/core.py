"""
Anifetch core module for running the animation.
"""

import json
import os
import pathlib
import shutil
import subprocess
import errno
import sys
import time
from .utils import (
    check_codec_of_file,
    extract_audio_from_file,
    get_text_length_of_formatted_text,
    get_ext_from_codec,
    get_data_path,
    default_asset_presence_check,
    get_video_dimensions,
    get_neofetch_status,
    render_frame,
    print_verbose,
    check_sound_flag_given,
)

GAP = 2
PAD_LEFT = 4


def run_anifetch(args):
    st = time.time()

    args.sound_flag_given = check_sound_flag_given(sys.argv)
    args.chroma_flag_given = args.chroma is not None
    neofetch_status = get_neofetch_status()

    BASE_PATH = get_data_path()

    VIDEO_DIR = BASE_PATH / "video"
    OUTPUT_DIR = BASE_PATH / "output"
    CACHE_PATH = BASE_PATH / "cache.json"
    ASSET_PATH = BASE_PATH / "assets"

    (ASSET_PATH).mkdir(parents=True, exist_ok=True)
    (VIDEO_DIR).mkdir(exist_ok=True)
    (OUTPUT_DIR).mkdir(exist_ok=True)

    default_asset_presence_check(ASSET_PATH)

    filename = pathlib.Path(args.filename)

    # If the filename is relative, check if it exists in the assets directory.
    if not filename.exists():
        candidate = ASSET_PATH / filename
        if candidate.exists():
            filename = candidate
            # print("EXISTS IN THE ASSET PATH", "candidate:", candidate)
        else:
            print(
                f"[ERROR] File not found: {args.filename}\nMake sure the file exists or that it is in the correct directory.",
                file=sys.stderr,
            )
            sys.exit(1)

    newpath = ASSET_PATH / filename.name

    try:
        shutil.copy(filename, newpath)
    except shutil.SameFileError:
        pass
    args.filename = str(newpath)

    if args.sound_flag_given:
        if args.sound:
            pass
        else:
            codec = check_codec_of_file(args.filename)
            try:
                ext = get_ext_from_codec(codec)
            except ValueError as e:
                print(f"[ERROR] {e}")
                sys.exit(1)

            args.sound_saved_path = str(BASE_PATH / f"output_audio.{ext}")

    if args.chroma and args.chroma.startswith("#"):
        print("[ERROR] Use '0x' prefix for chroma color, not '#'.", file=sys.stderr)
        sys.exit(1)

    # check cache
    should_update = False
    try:
        args_dict = {key: value for key, value in args._get_kwargs()}
        if args.force_render:
            should_update = True
        else:
            with open(CACHE_PATH, "r") as f:
                data = json.load(f)
            for key, value in args_dict.items():
                try:
                    cached_value = data[key]
                except KeyError:
                    should_update = True
                    break
                if value != cached_value:  # check if all options match
                    if key not in (
                        "playback_rate",
                        "verbose",
                        "center",
                        "fast_fetch",
                        "benchmark",
                        "force_render",
                    ):  # These arguments don't invalidate the cache.
                        print_verbose(  # TODO: this is a very ugly way of doing verbose debug printing
                            args.verbose,
                            f"{key} INVALID! Will cache again. Value:{value} Cache:{cached_value}",
                        )
                        should_update = True
    except FileNotFoundError:
        should_update = True

    if should_update:
        print("Caching...")

    WIDTH = args.width
    # automatically calculate height if not given
    if "--height" not in sys.argv and "-H" not in sys.argv:
        try:
            vid_w, vid_h = get_video_dimensions(ASSET_PATH / args.filename)
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)

        ratio = vid_h / vid_w
        HEIGHT = round(args.width * ratio)
    else:
        HEIGHT = args.height

    # Get the fetch output(neofetch/fastfetch)
    if not args.fast_fetch:
        if (
            neofetch_status == "wrapper" and args.force
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
                    "The command Fastfetch was not found. You probably forgot to install it. You can install it by going to here: https://github.com/fastfetch-cli/fastfetch\n If you installed Fastfetch but it still doesn't work, check your PATH."
                )
                raise SystemExit
            else:
                raise Exception(e)

    # put cached frames here
    frames: list[str] = []

    # copy the fetch output to the fetch_lines variable
    fetch_lines = fetch_output[:]
    len_fetch = len(fetch_lines)

    # cache is invalid, re-render
    if should_update:
        print_verbose(args.verbose, "SHOULD RENDER WITH CHAFA")

        # delete all old frames
        shutil.rmtree(VIDEO_DIR, ignore_errors=True)
        (VIDEO_DIR).mkdir(exist_ok=True)

        stdout = None if args.verbose else subprocess.DEVNULL
        stderr = None if args.verbose else subprocess.PIPE

        try:
            result_ffmpeg = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    f"{args.filename}",
                    "-vf",
                    f"fps={args.framerate},format=rgba",
                    str(BASE_PATH / "video/%05d.png"),
                ],
                stdout=stdout,
                stderr=stderr,
                text=True,
            )
        except FileNotFoundError as e:
            if e.errno == errno.ENOENT:
                print(
                    "The command Ffmpeg was not found. You probably forgot to install it. You can install it by going to here: https://ffmpeg.org/download.html\n If you installed Ffmpeg but it still doesn't work, check your PATH."
                )
                raise SystemExit
            else:
                raise
        else:
            if result_ffmpeg.returncode != 0:
                print(f"[ERROR] ffmpeg failed: {result_ffmpeg.stderr}")
                sys.exit(1)

        print_verbose(args.verbose, args.sound_flag_given)

        if args.sound_flag_given:
            if args.sound:  # sound file given
                print_verbose(args.verbose, "Sound file to use:", args.sound)
                source = pathlib.Path(args.sound)
                dest = BASE_PATH / source.with_name(f"output_audio{source.suffix}")
                shutil.copy(source, dest)
                args.sound_saved_path = str(dest)
            else:
                print_verbose(
                    args.verbose,
                    "No sound file specified, will attempt to extract it from video.",
                )
                codec = check_codec_of_file(args.filename)
                ext = get_ext_from_codec(codec)
                audio_file = extract_audio_from_file(BASE_PATH, args.filename, ext)
                print_verbose(args.verbose, "Extracted audio file.")

                args.sound_saved_path = str(audio_file)

            print_verbose(args.verbose, args.sound_saved_path)

        # If the new anim frames is shorter than the old one, then in /output there will be both new and old frames.
        # Empty the directory to fix this.
        shutil.rmtree(OUTPUT_DIR)
        os.mkdir(OUTPUT_DIR)

        print_verbose(args.verbose, "Emptied the output folder.")

        # get the frames
        animation_files = os.listdir(VIDEO_DIR)
        animation_files.sort()
        for i, f in enumerate(animation_files):
            # f = 00001.png
            chafa_args = args.chafa_arguments.strip()
            chafa_args += " --format symbols"  # Fixes https://github.com/Notenlish/anifetch/issues/1

            path = VIDEO_DIR / f
            frame = render_frame(path, WIDTH, HEIGHT, chafa_args)

            chafa_lines = frame.splitlines()

            if args.center:
                # centering the fetch output or the chafa animation if needed.
                len_chafa = len(chafa_lines)

                if (
                    len_chafa < len_fetch
                ):  # if the chafa animation is shorter than the fetch output
                    pad = (len_fetch - len_chafa) // 2
                    remind = (len_fetch - len_chafa) % 2
                    chafa_lines.pop()  # don't ask me why, the last line always seems to be empty
                    chafa_lines = (
                        [" " * WIDTH] * pad
                        + chafa_lines
                        + [" " * WIDTH] * (pad + remind)
                    )

                elif (
                    len_fetch < len_chafa
                ):  # if the chafa animation is longer than the fetch output
                    pad = (len_chafa - len_fetch) // 2
                    remind = (len_chafa - len_fetch) % 2
                    fetch_lines = (
                        [" " * WIDTH] * pad
                        + fetch_output
                        + [" " * WIDTH] * (pad + remind)
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

            frames.append("\n".join(chafa_lines))

            with open((OUTPUT_DIR / f).with_suffix(".txt"), "w") as file:
                file.write("\n".join(chafa_lines))

            # if wanted aspect ratio doesnt match source, chafa makes width as high as it can, and adjusts height accordingly.
            # AKA: even if I specify 40x20, chafa might give me 40x11 or something like that.
    else:
        # just use cached
        for filename in os.listdir(OUTPUT_DIR):
            path = OUTPUT_DIR / filename
            with open(path, "r") as file:
                frame = file.read()
                frames.append(frame)
            break  # first frame used for the template and the height

        if args.center:
            len_chafa = len(frame.splitlines())
            if len_fetch < len_chafa:
                pad = (len_chafa - len_fetch) // 2
                remind = (len_chafa - len_fetch) % 2
                fetch_lines = (
                    [" " * WIDTH] * pad + fetch_output + [" " * WIDTH] * (pad + remind)
                )

        with open(BASE_PATH / "frame.txt", "w") as f:
            f.writelines(frames)

        HEIGHT = len(frames[0].splitlines())

        # reloarding the cached output
        with open(CACHE_PATH, "r") as f:
            data = json.load(f)

        if args.sound_flag_given:
            args.sound_saved_path = data["sound_saved_path"]
        else:
            args.sound_saved_path = None

    print_verbose(args.verbose, "-----------")

    # save the caching arguments
    with open(CACHE_PATH, "w") as f:
        args_dict = {key: value for key, value in args._get_kwargs()}
        json.dump(args_dict, f, indent=2)

    if len(fetch_lines) == 0:
        raise Exception("fetch_lines has no items in it:", fetch_lines)

    template = []
    for fetch_line in fetch_lines:
        output = f"{' ' * (PAD_LEFT + GAP)}{' ' * WIDTH}{' ' * GAP}{fetch_line}"
        template.append(output + "\n")

    # Only do this once instead of for every line.
    output_width = get_text_length_of_formatted_text(output)
    template_actual_width = output_width  # TODO: maybe this should instead be the text_length_of_formatted_text(cleaned_line)

    # writing the tempate to a file.
    with open(BASE_PATH / "template.txt", "w") as f:
        f.writelines(template)
    print_verbose(args.verbose, "Template updated")

    # for defining the positions of the cursor, that way I can set cursor pos and only redraw a portion of the text, not the entire text.
    TOP = 2
    LEFT = PAD_LEFT
    RIGHT = WIDTH + PAD_LEFT
    BOTTOM = HEIGHT

    bash_script_name = "anifetch-static-resize2.sh"
    script_dir = pathlib.Path(__file__).parent
    bash_script_path = script_dir / bash_script_name

    if not args.benchmark:
        try:
            framerate_to_use = args.playback_rate
            if args.sound_flag_given:
                framerate_to_use = (
                    args.framerate
                )  # ignore wanted playback rate so that desync doesn't happen

            script_args = [
                "bash",
                str(bash_script_path),
                str(framerate_to_use),
                str(TOP),
                str(LEFT),
                str(RIGHT),
                str(BOTTOM),
                str(template_actual_width),
            ]
            if args.sound_flag_given:  # if user requested for sound to be played
                script_args.append(str(args.sound_saved_path))

            print_verbose(args.verbose, script_args)
            # raise SystemExit
            subprocess.call(
                script_args,
                text=True,
            )
        except KeyboardInterrupt:
            # Reset the terminal in case it doesnt render the user inputted text after Ctrl+C
            subprocess.call(["stty", "sane"])
    else:
        print(f"It took {time.time() - st} seconds.")

    if pathlib.Path(VIDEO_DIR).exists():
        shutil.rmtree(VIDEO_DIR)  # no need to keep the video frames.
