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
    get_ext_from_codec,
    get_data_path,
    default_asset_presence_check,
    get_video_dimensions,
    get_neofetch_status,
    print_verbose,
    normal_print,
    check_sound_flag_given,
    clean_cache_args,
    check_args_hash_same,
    find_corresponding_cache,
    hash_of_cache_args,
    get_caches_json,
    save_caches_json,
    args_checker,
    threaded_chafa_frame_gen,
    get_fetch_output,
    make_template_from_fetch_lines,
    clear_screen_soft,
)
from typing import Literal
from concurrent.futures import ThreadPoolExecutor, Future

GAP = 2
PAD_LEFT = 4
LEFT = PAD_LEFT


def run_anifetch(args):
    st = time.time()

    should_print: bool = not args.benchmark
    should_print_verbose: bool = args.verbose

    allowed_alternatives = ["cache_list", "clear", "delete"]
    try:
        args_checker(allowed_alternatives, args)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    args.sound_flag_given = check_sound_flag_given(sys.argv)
    args.chroma_flag_given = args.chroma is not None

    neofetch_status: Literal["neofetch", "uninstalled", "wrapper"] = "uninstalled"
    if args.neofetch:
        neofetch_status = get_neofetch_status()

    BASE_PATH = get_data_path()

    ASSET_PATH = BASE_PATH / "assets"
    (ASSET_PATH).mkdir(parents=True, exist_ok=True)

    default_asset_presence_check(ASSET_PATH)

    CACHE_LIST_PATH = BASE_PATH / "caches.json"

    if args.cache_list:
        all_caches = get_caches_json(CACHE_LIST_PATH)
        if not all_caches:
            normal_print(should_print, "No cached configurations found.")
        else:
            normal_print(should_print, "Available caches:")
            for i, cache in enumerate(all_caches, 1):
                line = f"[{i}] video: {cache.get('filename', '?')} | width: {cache.get('width')} | chroma: {cache.get('chroma')}"
                normal_print(should_print, line)
        sys.exit(0)

    if args.delete:
        all_caches = get_caches_json(CACHE_LIST_PATH)
        to_delete = sorted(set(args.delete), reverse=True)
        max_index = len(all_caches)

        for index in to_delete:
            real_index = index - 1
            if not (0 <= real_index < max_index):
                print(f"[ERROR] No cache found with number {index}")
                continue

            cache = all_caches[real_index]
            hash_to_delete = cache["hash"]
            cache_dir = BASE_PATH / hash_to_delete

            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                normal_print(should_print, f"Deleted cache directory: {cache_dir}")
            else:
                normal_print(
                    should_print,
                    f"[WARNING] Cache directory {cache_dir} already missing.",
                )

            # Supprimer du cache JSON
            del all_caches[real_index]
            max_index -= 1  # car on modifie la liste au fur et à mesure

        save_caches_json(CACHE_LIST_PATH, all_caches)
        sys.exit(0)

    if args.clear:
        all_caches = get_caches_json(CACHE_LIST_PATH)
        for cache in all_caches:
            hash_id = cache.get("hash")
            if hash_id:
                cache_dir = BASE_PATH / hash_id
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    normal_print(should_print, f"Deleted cache directory: {cache_dir}")
        save_caches_json(CACHE_LIST_PATH, [])
        normal_print(should_print, "All cache entries have been cleared.")
        sys.exit(0)

    filename = pathlib.Path(args.filename)
    IS_GIF = False
    if args.filename:
        IS_GIF = True

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

    args_dict = {key: value for key, value in args._get_kwargs()}
    cleaned_dict = clean_cache_args(args_dict)
    cleaned_dict["hash"] = hash_of_cache_args(cleaned_dict)

    CACHE_PATH = BASE_PATH / cleaned_dict["hash"]

    VIDEO_DIR: pathlib.Path = CACHE_PATH / "video"
    OUTPUT_DIR: pathlib.Path = CACHE_PATH / "output"

    CACHE_PATH.mkdir(parents=True, exist_ok=True)
    (VIDEO_DIR).mkdir(exist_ok=True)
    (OUTPUT_DIR).mkdir(exist_ok=True)

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

            # sound and sound_flag_given will be used for hash calculation.
            # sound_saved_path is a value that must be kept in the 'cleaned' variable but it shouldnt be used in calculating hash, that's what sound and sound_flag_given are for.
            args.sound_saved_path = str(CACHE_PATH / f"output_audio.{ext}")
            cleaned_dict["sound_saved_path"] = args.sound_saved_path

    if args.chroma and args.chroma.startswith("#"):
        print("[ERROR] Use '0x' prefix for chroma color, not '#'.", file=sys.stderr)
        sys.exit(1)

    # check cache
    should_update = args.force_render  # True if --force-render
    print_verbose(should_print_verbose, should_update)

    if not should_update:
        try:
            all_caches = get_caches_json(CACHE_LIST_PATH)

            for cache_args in all_caches:
                if check_args_hash_same(cache_args, cleaned_dict):
                    break
            else:
                normal_print(
                    should_print,
                    "Couldn't find a corresponding cache. Will cache the animation.",
                )
                should_update = True

        except FileNotFoundError:
            should_update = True

    if not (CACHE_PATH / "output").exists() and not should_update:
        normal_print(
            should_print,
            "[WARNING] Cache folder found but output is missing. Will regenerate.",
        )
        should_update = True

    if should_update:
        normal_print(should_print, "Caching...")

    WIDTH = args.width

    # automatically calculate height if not given
    if should_update and ("--height" not in sys.argv and "-H" not in sys.argv):
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
    fetch_output: list[str] = get_fetch_output(
        not args.neofetch, neofetch_status, args.force
    )

    # copy fetch_output to fetch_lines
    fetch_lines: list[str] = fetch_output[:]
    len_fetch = len(fetch_lines)

    # put cached frames here
    frames: dict[int, str] = {}  # {frame_id : frame}

    len_chafa = None

    # cache is invalid, re-render
    if should_update:
        print_verbose(should_print_verbose, "SHOULD RENDER WITH CHAFA")

        # deletes the old cache
        if CACHE_PATH.exists():
            shutil.rmtree(CACHE_PATH)

        os.mkdir(CACHE_PATH)
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
                    "-q:v",
                    str(
                        min(max(args.quality or 6, 2), 10)
                    ),  # 2-5 high quality, 6-10 lower
                    str(CACHE_PATH / "video/%05d.png")
                    if IS_GIF
                    else str(CACHE_PATH / "video/%05d.jpg"),
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

        print_verbose(should_print_verbose, args.sound_flag_given)

        if args.sound_flag_given:
            if args.sound:  # sound file given
                print_verbose(should_print_verbose, "Sound file to use:", args.sound)
                source = pathlib.Path(args.sound)
                dest = CACHE_PATH / source.with_name(f"output_audio{source.suffix}")
                shutil.copy(source, dest)
                args.sound_saved_path = str(dest)
            else:
                print_verbose(
                    args.verbose,
                    "No sound file specified, will attempt to extract it from video.",
                )
                codec = check_codec_of_file(args.filename)
                ext = get_ext_from_codec(codec)
                audio_file = extract_audio_from_file(CACHE_PATH, args.filename, ext)
                print_verbose(should_print_verbose, "Extracted audio file.")

                args.sound_saved_path = str(audio_file)

            cleaned_dict["sound_saved_path"] = args.sound_saved_path

            cleaned_dict["sound_saved_path"] = args.sound_saved_path

            print_verbose(should_print_verbose, args.sound_saved_path)

        # If the new anim frames is shorter than the old one, then in /output there will be both new and old frames.
        # Empty the directory to fix this.
        os.mkdir(OUTPUT_DIR)

        print_verbose(should_print_verbose, "Emptied the output folder.")

        # make sure height and width are at least 1
        WIDTH = max(WIDTH, 1)
        HEIGHT = max(HEIGHT, 1)

        # WHY IS THE FRAMES NOT PROPERLY FINISHED AND HANDLED???

        # get the frames
        animation_files = os.listdir(VIDEO_DIR)
        animation_files.sort()
        futures: list[Future] = []
        max_workers: int = max(1, (os.cpu_count() or 2) - 1)
        max_workers = 1

        chafa_args: str = args.chafa_arguments.strip()
        chafa_args += (
            " --format symbols"  # Fixes https://github.com/Notenlish/anifetch/issues/1
        )
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i, f in enumerate(animation_files):
                future = executor.submit(
                    threaded_chafa_frame_gen,
                    i,
                    f,
                    VIDEO_DIR,
                    OUTPUT_DIR,
                    WIDTH,
                    HEIGHT,
                    chafa_args,
                    args.center,
                    len_fetch,
                    fetch_output,
                )
                futures.append(future)
                # if wanted aspect ratio doesnt match source, chafa makes width as high as it can, and adjusts height accordingly.
                # AKA: even if I specify 40x20, chafa might give me 40x11 or something like that.
            for future in futures:
                _i, _frame = future.result()
                frames[_i] = _frame

    else:
        # just use cached
        animation_files: list[str] = os.listdir(OUTPUT_DIR)
        animation_files.sort()
        for i, filename in enumerate(animation_files):
            path = OUTPUT_DIR / filename
            with open(path, "r", encoding="utf-8") as file:
                frame = file.read()
                frames[i] = frame
            break  # first frame used for the template and the height

        if args.center:
            len_chafa = len(frame.splitlines())
            if len_fetch < len_chafa:
                pad = (len_chafa - len_fetch) // 2
                remind = (len_chafa - len_fetch) % 2
                fetch_lines = (
                    [" " * WIDTH] * pad + fetch_output + [" " * WIDTH] * (pad + remind)
                )

        HEIGHT = len(frames[0].splitlines())

        # reloading the cached output
        with open(CACHE_LIST_PATH, "r") as f:
            all_saved_caches = json.load(f)
            corresponding_cache = find_corresponding_cache(
                cleaned_dict, all_saved_caches
            )

        if args.sound_flag_given:
            args.sound_saved_path = corresponding_cache["sound_saved_path"]
        else:
            args.sound_saved_path = None

    print_verbose(should_print_verbose, "-----------")
    print_verbose(should_print_verbose, "ARGS FOR SAVING CACHES.JSON")

    # save the caching arguments
    caches_data = get_caches_json(CACHE_LIST_PATH)

    added = False
    for i, cache_dict in enumerate(caches_data):
        if cache_dict["hash"] == cleaned_dict["hash"]:
            caches_data[i] = cleaned_dict  # replace the cache with the new one
            added = True
    if not added:
        caches_data.append(cleaned_dict)

    with open(BASE_PATH / "caches.json", "w") as f:
        json.dump(caches_data, f, indent=2)

    if len(fetch_lines) == 0:
        raise Exception("fetch_lines has no items in it:", fetch_lines)

    template, template_actual_width = make_template_from_fetch_lines(
        fetch_lines, PAD_LEFT, GAP, WIDTH
    )

    # for defining the positions of the cursor, that way I can set cursor pos and only redraw a portion of the text, not the entire text.
    TOP = args.top
    RIGHT = WIDTH + PAD_LEFT
    BOTTOM = HEIGHT

    using_cached: bool = not should_update

    if args.benchmark:
        print(time.time() - st)
    else:
        from .renderer import Renderer

        try:
            if not args.sound_saved_path:
                args.sound_saved_path = ""
        except AttributeError:
            args.sound_saved_path = ""

        framerate_to_use = args.playback_rate

        renderer = Renderer(
            str(BASE_PATH),
            str(CACHE_PATH),
            framerate_to_use,
            TOP,
            LEFT,
            RIGHT,
            HEIGHT,
            len_fetch,
            BOTTOM,
            using_cached,
            template_actual_width,
            template,
            frames,
            not args.neofetch,
            neofetch_status,
            args.force,
            args.center,
            args.loop,
            args.cleanup,
            args.no_key_exit,
            len_chafa or None,
            WIDTH,
            GAP,
            refresh_interval=args.interval,
            sound_saved_path=args.sound_saved_path,
        )

        renderer.start_rendering()

        # stopped rendering
        # sys.stdout.flush()

        if args.cleanup:
            clear_screen_soft()
            # clear_screen()
        else:
            pass

        if renderer.last_key:
            from pynput.keyboard import Controller, Key

            keyboard = Controller()

            # needed because if I only enter one key even though the user pressed a bunch of keys the keys will be entered disorderly(only the a single key is not automatically entered and the other keys are entered)
            # so we store the key, go to line start, enter the first key(that the user pressed) and then go to the end of line.
            # that way even if the user presses a bunch of keys, it will all be in order.

            # start of line
            keyboard.press(Key.home)
            keyboard.release(Key.home)

            keyboard.press(renderer.last_key)

            # end of line
            keyboard.press(Key.end)
            keyboard.release(Key.end)

            keyboard.release(renderer.last_key)

    if pathlib.Path(VIDEO_DIR).exists():
        shutil.rmtree(VIDEO_DIR)  # no need to keep the video frames.
