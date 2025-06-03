# anifetch/core.py

"""
    Anifetch core module for running the animation.
"""


import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from .utils import (
    check_sound_flag,
    check_chroma_flag,
    check_codec_of_file,
    extract_audio_from_file,
    get_text_length_of_formatted_text,
    get_ext_from_codec,
    get_data_path,
    get_video_dimensions,
    get_neofetch_status,
    print_verbose,
)


GAP = 2
PAD_LEFT = 4


def run_anifetch(args):
    st = time.time()


    args.sound_flag_given = check_sound_flag()  # adding this to the args so that it considers whether the flag was given or not and if the flag is given what the sound file was.
    args.chroma_flag_given = check_chroma_flag()


    BASE_PATH = get_data_path()

    if not (BASE_PATH / "video").exists():
        os.mkdir(BASE_PATH / "video")
    if not (BASE_PATH / "output").exists():
        os.mkdir(BASE_PATH / "output")

    if not pathlib.Path(args.filename).exists():
        print("Couldn't find file", pathlib.Path(args.filename))
        raise FileNotFoundError(args.filename)


    if args.sound_flag_given:
        if args.sound:
            pass
        else:
            codec = check_codec_of_file(args.filename)
            ext = get_ext_from_codec(codec)
            args.sound_saved_path = str(BASE_PATH / f"output_audio.{ext}")

    if args.chroma_flag_given:
        if args.chroma.startswith("#"):
            sys.exit("Color for hex code starts with an '0x'! Not a '#'")




    # check cache
    old_filename = ""
    should_update = False
    try:
        args_dict = {key: value for key, value in args._get_kwargs()}
        if args.force_render:
            should_update = True
        else:
            with open(BASE_PATH / "cache.json", "r") as f:
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
                        "center-mode",
                        "fast_fetch",
                        "benchmark",
                        "force_render",
                    ):  # These arguments don't invalidate the cache.
                        print_verbose(
                            f"{key} INVALID! Will cache again. Value:{value} Cache:{cached_value}",
                        )
                        should_update = True
                        print_verbose("Cache invalid, will cache again.")
    except FileNotFoundError:
        should_update = True

    if should_update:
        print("Caching...")


    WIDTH = args.width
    # automatically calculate height if not given
    if not "--height" in sys.argv and not "-H" in sys.argv:
        vid_w, vid_h = get_video_dimensions(args.filename)
        ratio = vid_h / vid_w
        HEIGHT = round(args.width * ratio)
    else:
        HEIGHT = args.height


    # Get the fetch output(neofetch/fastfetch)
    if not args.fast_fetch:

        if (get_neofetch_status() == "wrapper" and args.force) or get_neofetch_status() == "neofetch":
            # Get Neofetch Output
            fetch_output = subprocess.check_output(
                ["neofetch"], shell=True, text=True
            ).splitlines()
            for i, line in enumerate(fetch_output):
                line = line[4:]  # i forgot what this does, but its important iirc.
                fetch_output[i] = line
            fetch_output.pop(0)
            fetch_output.pop(0)
            fetch_output.pop(0)
            fetch_output.pop(-1)

        elif get_neofetch_status() == "uninstalled":
                print("Neofetch is not installed. Please install Neofetch or Fastfetch.", file=sys.stderr)
                sys.exit(1)

        else:
            print("Neofetch is deprecated. Try fastfetch using '-ff' argument or force neofetch to run using '--force' argument.", file=sys.stderr)
            sys.exit

    else:
        fetch_output = subprocess.check_output(
            ["fastfetch", "--logo", "none", "--pipe", "false"], text=True
        ).splitlines()

    # put cached frames here
    frames: list[str] = []

    # copy the fetch output to the fetch_lines variable
    fetch_lines = fetch_output[:]
    len_fetch = len(fetch_lines)

    # cache is invalid, re-render
    if should_update:
        print_verbose("SHOULD RENDER WITH CHAFA")

        # delete all old frames
        shutil.rmtree(BASE_PATH / "video")
        os.mkdir(BASE_PATH / "video")

        stdout = None if args.verbose else subprocess.DEVNULL
        stderr = None if args.verbose else subprocess.STDOUT

        subprocess.call(
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
        )

        print_verbose(args.sound_flag_given)

        if args.sound_flag_given:
            if args.sound:  # sound file given
                print_verbose("Sound file to use:", args.sound)
                source = pathlib.Path(args.sound)
                dest = BASE_PATH / source.with_name(f"output_audio{source.suffix}")
                shutil.copy(source, dest)
                args.sound_saved_path = str(dest)
            else:
                print_verbose(
                    "No sound file specified, will attempt to extract it from video."
                )
                codec = check_codec_of_file(args.filename)
                ext = get_ext_from_codec(codec)
                audio_file = extract_audio_from_file(BASE_PATH, args.filename, ext)
                print_verbose("Extracted audio file.")

                args.sound_saved_path = str(audio_file)

            print_verbose(args.sound_saved_path)

        # If the new anim frames is shorter than the old one, then in /output there will be both new and old frames.
        # Empty the directory to fix this.
        shutil.rmtree(BASE_PATH / "output")
        os.mkdir(BASE_PATH / "output")

        print_verbose("Emptied the output folder.")

        # get the frames
        animation_files = os.listdir(BASE_PATH / "video")
        animation_files.sort()
        for i, f in enumerate(animation_files):
            # f = 00001.png
            chafa_args = args.chafa_arguments.strip()
            chafa_args += " --format symbols"  # Fixes https://github.com/Notenlish/anifetch/issues/1

            path = BASE_PATH / "video" / f
            chafa_cmd = [
                "chafa",
                *chafa_args.split(" "),
                # "--color-space=rgb",
                f"--size={WIDTH}x{HEIGHT}",
                path.as_posix(),
            ]
            frame = subprocess.check_output(
                chafa_cmd,
                text=True,
            )

            chafa_lines = frame.splitlines()

            if args.center_mode:
                # centering the fetch output or the chafa animation if needed.
                len_chafa = len(chafa_lines)

                if len_chafa < len_fetch:   # if the chafa animation is shorter than the fetch output
                    pad = (len_fetch - len_chafa) // 2
                    remind = (len_fetch - len_chafa) % 2
                    chafa_lines.pop() # don't ask me why, the last line always seems to be empty
                    chafa_lines = [' ' * WIDTH] * pad + chafa_lines + [' ' * WIDTH] * (pad + remind)

                elif len_fetch < len_chafa:    # if the chafa animation is longer than the fetch output
                    pad = (len_chafa - len_fetch) // 2
                    remind = (len_chafa - len_fetch) % 2
                    fetch_lines = [' ' * WIDTH] * pad + fetch_output +[' ' * WIDTH] * (pad + remind)

                if i == 0:
                # updating the HEIGHT variable from the first frame
                    HEIGHT = len(chafa_lines)
            else:
                if i == 0:
                    len_chafa = len(chafa_lines)
                    pad = abs(len_fetch - len_chafa) // 2
                    remind = abs(len_fetch - len_chafa) % 2
                    HEIGHT = len(chafa_lines) + (2 * pad + remind) * WIDTH 



            frames.append('\n'.join(chafa_lines))

            with open((BASE_PATH / "output" / f).with_suffix(".txt"), "w") as file:
                file.write('\n'.join(chafa_lines))

            # if wanted aspect ratio doesnt match source, chafa makes width as high as it can, and adjusts height accordingly.
            # AKA: even if I specify 40x20, chafa might give me 40x11 or something like that.
    else:
        # just use cached
        for filename in os.listdir(BASE_PATH / "output"):
            path = BASE_PATH / "output" / filename
            with open(path, "r") as file:
                frame = file.read()
                frames.append(frame)
            break  # first frame used for the template and the height
        
        if args.center_mode:
            len_chafa = len(frame.splitlines())
            if len_fetch < len_chafa:
                pad = (len_chafa - len_fetch) // 2
                remind = (len_chafa - len_fetch) % 2
                fetch_lines = [' ' * WIDTH] * pad + fetch_output + [' ' * WIDTH] * (pad + remind)

        with open(BASE_PATH / "frame.txt", "w") as f:
            f.writelines(frames)

        if args.center_mode:
            len_chafa = len(frame.splitlines())
            if len_fetch < len_chafa:
                pad = (len_chafa - len_fetch) // 2
                remind = (len_chafa - len_fetch) % 2
                fetch_lines = [' ' * WIDTH] * pad + fetch_output + [' ' * WIDTH] * (pad + remind)

        HEIGHT = len(frames[0].splitlines())

        # reloarding the cached output
        with open(BASE_PATH / "cache.json", "r") as f:
            data = json.load(f)

        if args.sound_flag_given:
            args.sound_saved_path = data["sound_saved_path"]
        else:
            args.sound_saved_path = None

    print_verbose("-----------")

    # save the caching arguments
    with open(BASE_PATH / "cache.json", "w") as f:
        args_dict = {key: value for key, value in args._get_kwargs()}
        json.dump(args_dict, f, indent=2)

    template = []
    for fetch_line in fetch_lines:
        output = f"{' ' * (PAD_LEFT + GAP)}{' ' * WIDTH}{' ' * GAP}{fetch_line}"
        template.append(output + '\n')
        output_width = get_text_length_of_formatted_text(output)
        template_actual_width = output_width  # TODO: maybe this should instead be the text_length_of_formatted_text(cleaned_line)


        """with open("debug.txt", "w") as f:
            f.writelines(
                [
                    "fetch_line:\n",
                    fetch_line,
                    "\n--------\n",
                    "output:\n",
                    output,
                    "\n--------\n",
                    "output_width:\n",
                    str(output_width),
                    "\n--------\n",
                    "output_width_with_color:\n",
                    str(output_width_with_color),
                    "\n--------\n",
                    "I have no idea what this is(something):\n",
                    str(width_for_safe_space),
                    "\n--------\n",
                    "max_width:\n",
                    str(max_width),
                    "\n--------\n",
                    "cleaned_line:\n",
                    cleaned_line,
                ]
            )"""


    # writing the tempate to a file.
    with open(BASE_PATH / "template.txt", "w") as f:
        f.writelines(template)
    print_verbose("Template updated")

    # for defining the positions of the cursor, that way I can set cursor pos and only redraw a portion of the text, not the entire text.
    TOP = 2
    LEFT = PAD_LEFT
    RIGHT = WIDTH + PAD_LEFT
    BOTTOM = HEIGHT

    bash_script_name = "anifetch-static-resize2.sh"
    script_dir = pathlib.Path(__file__).parent.parent / "scripts"
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
                str(template_actual_width)
            ]
            if args.sound_flag_given:  # if user requested for sound to be played
                script_args.append(str(args.sound_saved_path))

            print_verbose(script_args)
            #raise SystemExit
            subprocess.call(
                script_args,
                text=True,
            )
        except KeyboardInterrupt:
            # Reset the terminal in case it doesnt render the user inputted text after Ctrl+C
            subprocess.call(["stty", "sane"])
    else:
        print(f"It took {time.time() - st} seconds.")

    if pathlib.Path(BASE_PATH / "video").exists():
        shutil.rmtree(BASE_PATH / "video")  # no need to keep the video frames.
