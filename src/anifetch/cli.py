"""
Anifetch CLI module for parsing command line arguments.
"""

import argparse
from .utils import get_version_of_anifetch


def parse_args():
    parser = argparse.ArgumentParser(
        prog="Anifetch",
        description="Allows you to use neofetch with video in terminal (using chafa).",
    )
    parser.add_argument(
        "-b",
        "--benchmark",
        default=False,
        help="For testing. Runs Anifetch without actually starting the animation and times how long it took. Also does the same for neofetch and fastfetch. Checks anifetch for both cached and not cached version.",
        action="store_true",
    )
    parser.add_argument(
        "filename",
        help="Video file to use (default: example.mp4)",
        type=str,
    )
    parser.add_argument(
        "-w",
        "-W",
        "--width",
        default=40,
        help="Width of the chafa animation.",
        type=int,
    )
    parser.add_argument(
        "-H",
        "--height",
        default=20,
        help="Height of the chafa animation.",
        type=int,
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
        "-C",
        "--center",
        default=False,
        action="store_true",
        help="Disabled by default. Use this argument to center the animation relative to the fetch output. Note that centering may slow down the execution.",
    )
    parser.add_argument(
        "-c",
        "--chafa-arguments",
        default="--symbols ascii --fg-only",
        help="Specify the arguments to give to chafa. For more informations, use 'chafa --help'",
    )
    parser.add_argument(
        "--force",
        default=False,
        help="Add this argument if you want to use neofetch even if it is deprecated.",
        action="store_true",
    )
    parser.add_argument(
        "-ff",
        "--fast-fetch",
        default=False,
        help="Add this argument if you want to use fastfetch instead. Note than fastfetch will be run with '--logo none'.",
        action="store_true",
    )
    parser.add_argument(
        "--chroma",
        required=False,
        nargs="?",
        help="Add this argument to chromakey a hexadecimal color from the video using ffmpeg using syntax of '--chroma <hex color>:<similarity>:<blend>' with <hex-color> being 0xRRGGBB with a 0x as opposed to a # e.g. '--chroma 0xc82044:0.1:0.1'",
        type=str,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=get_version_of_anifetch()),
    )

    args = parser.parse_args()

    return args
