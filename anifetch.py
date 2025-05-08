from posix import truncate
import subprocess
import os
import pathlib
import argparse
import shutil
import time
import json
import sys


def print_verbose(*msg):
    if args.verbose:
        print(*msg)

def get_ext_from_codec(codec:str):
    codec_extension_map = {
        "aac": "m4a",
        "mp3": "mp3",
        "opus": "opus",
        "vorbis": "ogg",
        "pcm_s16le": "wav",
        "flac": "flac",
        "alac": "m4a"
    }
    return codec_extension_map.get(codec,"bin")

def check_codec_of_file(file:str):
    ffprobe_cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=nokey=1:noprint_wrappers=1", file]
    codec = str(subprocess.check_output(ffprobe_cmd, text=True).strip())
    return codec

def extract_audio_from_file(file:str, extension):
    audio_file = BASE_PATH / f"output_audio.{extension}"
    extract_cmd = ["ffmpeg", "-i", file, "-y", "-vn", "-c:a", "copy", "-loglevel","quiet", audio_file]
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



st = time.time()

GAP = 2
PAD_LEFT = 4

parser = argparse.ArgumentParser(
    prog="Anifetch",
    description="Allows you to use neofetch with video in terminal(using chafa).",
)
parser.add_argument(
    "-b",
    "--benchmark",
    default=False,
    help="For testing. Runs Anifetch without actually starting the animation.",
    action="store_true",
)
parser.add_argument(
    "-f",
    "--filename",
    "--file",
    required=True,
    help="Specify a file via this argument.",
    type=str,
)
parser.add_argument(
    "-w", "-W", "--width", default=40, help="Width of the chafa animation.", type=int
)
parser.add_argument(
    "-H", "--height", default=20, help="Height of the chafa animation.", type=int
)
parser.add_argument("-v", "--verbose", default=False, action="store_true")
parser.add_argument(
    "-r",
    "--framerate",
    default=10,
    help="Sets the framerate when extracting frames from ffmpeg.",
    type=int,
)
parser.add_argument(
    "-pr",
    "--playback-rate",
    default=10,
    help="Ignored when a sound is playing so that desync doesn't happen. Sets the playback rate of the animation. Not to be confused with the 'framerate' option. This basically sets for how long the script will wait before rendering new frame, while the framerate option affects how many frames are generated via ffmpeg.",
)
parser.add_argument(
    "-s",
    "--sound",
    required=False,
    nargs="?",
    help="Optional. Will playback a sound file while displaying the animation. If you give only -s without any sound file it will attempt to extract the sound from the video.",
    type=str,
)
parser.add_argument(
    "-fr",
    "--force-render",
    default=False,
    action="store_true",
    help="Disabled by default. Anifetch saves the filename to check if the file has changed, if the name is same, it won't render it again. If enabled, the video will be forcefully rendered, whether it has the same name or not. Please note that it only checks for filename, if you changed the framerate then you'll need to force render.",
)
parser.add_argument(
    "-c",
    "--chafa-arguments",
    default="--symbols ascii --fg-only",
    help="Specify the arguments to give to chafa. For more informations, use 'chafa --help'",
)
parser.add_argument(
    "-ff",
    "--fast-fetch",
    default=False,
    help="Add this argument if you want to use fastfetch instead. Note than fastfetch will be run with '--logo none'.",
    action="store_true",
)
args = parser.parse_args()
args.sound_flag_given = check_sound_flag()  # adding this to the args so that it considers whether the flag was given or not and if the flag is given what the sound file was.


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
                    "fast_fetch",
                    "benchmark",
                    "force_render"
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
HEIGHT = args.height


# put cached frames here
frames: list[str] = []

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
            print_verbose("Sound file to use:",args.sound)
            source = pathlib.Path(args.sound)
            dest = BASE_PATH / source.with_name(f"output_audio{source.suffix}")
            shutil.copy(source, dest)
            args.sound_saved_path = str(dest)
        else:
            print_verbose("No sound file specified, will attempt to extract it from video.")
            codec = check_codec_of_file(args.filename)
            ext = get_ext_from_codec(codec)
            audio_file = extract_audio_from_file(args.filename, ext)
            print_verbose("Extracted audio file.")

            args.sound_saved_path = str(audio_file)

        print_verbose(args.sound_saved_path)


    # If the new anim frames is shorter than the old one, then in /output there will be both new and old frames. Empty the directory to fix this.
    shutil.rmtree(BASE_PATH / "output")
    os.mkdir(BASE_PATH / "output")

    print_verbose("Emptied the output folder.")

    # get the frames
    animation_files = os.listdir(BASE_PATH / "video")
    animation_files.sort()
    for i, f in enumerate(animation_files):
        # TODO: REMOVE THIS
        #print_verbose(f"- Frame: {f}")

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

        with open((BASE_PATH / "output" / f).with_suffix(".txt"), "w") as file:
            file.write(frame)

        # if wanted aspect ratio doesnt match source, chafa makes width as high as it can, and adjusts height accordingly.
        # AKA: even if I specify 40x20, chafa might give me 40x11 or something like that.
        if i == 0:
            HEIGHT = len(frame.splitlines())
            frames.append(frame) # dont question this, I need frames to have at least a single item
else:
    # just use cached
    for filename in os.listdir(BASE_PATH / "output"):
        path = BASE_PATH / "output" / filename
        with open(path, "r") as file:
            frame = file.read()
            frames.append(frame)
        break  # dont question this, I just need frames to have a single item
    HEIGHT = len(frames[0].splitlines())

    with open(BASE_PATH / "cache.json", "r") as f:
        data = json.load(f)
    
    if args.sound_flag_given:
        args.sound_saved_path = data["sound_saved_path"]
    else:
        args.sound_saved_path = None

print_verbose("-----------")


# print_verbose("ARGS FOR SAVING CACHE.JSON", args)

# save the caching arguments
with open(BASE_PATH / "cache.json", "w") as f:
    args_dict = {key: value for key, value in args._get_kwargs()}
    json.dump(args_dict, f, indent=2)



# Get the fetch output(neofetch/fastfetch)
if not args.fast_fetch:
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
else:
    fetch_output = subprocess.check_output(
        ["fastfetch", "--logo", "none", "--pipe", "false"], text=True
    ).splitlines()


# modifying template to account for the width of the chafa animation.
chafa_rows = frames[0].splitlines()
template = []
for y, fetch_line in enumerate(fetch_output):
    output = ""
    try:
        chafa_line = chafa_rows[y]
    except IndexError:
        chafa_line = ""

    width_to_offset = GAP + WIDTH

    # Removing the dust that may appear with a padding
    output = f"{(PAD_LEFT + (GAP * 2)) * ' '}{' ' * width_to_offset}{fetch_line}\n"
    max_width = shutil.get_terminal_size().columns
    cleaned_line = (output.rstrip() + ' ' * (max_width - len(output.rstrip())))[:max_width] + '\n'
    template.append(cleaned_line)

# writing the tempate to a file.
with open(BASE_PATH / "template.txt", "w") as f:
    f.writelines(template)
    # I just need to move this down, and also apply that padding thingy(for lines that dont have chafa anim)
    # so basically repeat what I have done but this time its for layout.
    # If I do this then I can get rid of the layout padding code on the last part. because the layout will already be fixed.
print_verbose("Template updated")

# for defining the positions of the cursor, that way I can set cursor pos and only redraw a portion of the text, not the entire text.
TOP = 2
LEFT = PAD_LEFT
RIGHT = WIDTH + PAD_LEFT
BOTTOM = HEIGHT  # + TOP

script_dir = os.path.dirname(__file__)
script_path = os.path.join(script_dir, "loop.sh")


RIGHT = WIDTH + PAD_LEFT
BOTTOM = HEIGHT  # + TOP


if not args.benchmark:
    try:

        framerate_to_use = args.playback_rate
        if args.sound_flag_given:
            framerate_to_use = args.framerate  # ignore wanted playback rate so that desync doesn't happen

        script_args = [
            "bash",
            script_path,
            str(framerate_to_use),
            str(TOP),
            str(LEFT),
            str(RIGHT),
            str(BOTTOM),
        ]
        if args.sound_flag_given:  # if user requested for sound to be played
            script_args.append(str(args.sound_saved_path))

        print(script_args)
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
