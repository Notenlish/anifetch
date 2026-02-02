"""
Anifetch CLI module for parsing command line arguments.
"""

import argparse
from .utils import get_version_of_anifetch


parser = argparse.ArgumentParser(
    prog="Anifetch",
    description="Allows you to use fastfetch/neofetch with video in terminal.",
)
parser.add_argument(
    "filename",
    nargs="?",
    default=None,
    help="Video file to use (e.g. video.mp4).",
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
parser.add_argument(
    "-t",
    "-T",
    "--top",
    default=2,
    help="Sets the starting row(top) position.",
    type=int,
)
parser.add_argument(
    "-v",
    "--verbose",
    default=False,
    help="Enables some verbose print logs",
    action="store_true",
)
parser.add_argument(
    "-r",
    "--framerate",
    default=10,
    help="Sets the framerate when extracting frames from ffmpeg. Default is 10.",
    type=int,
)
parser.add_argument(
    "-pr",
    "--playback-rate",
    default=10,
    help="Default is 10. Ignored when a sound is playing so that desync doesn't happen. Sets the playback rate of the animation. Not to be confused with the 'framerate' option. This basically sets for how long the script will wait before rendering new frame, while the framerate option affects how many frames are generated via ffmpeg.",
)
parser.add_argument(
    "-s",
    "--sound",
    required=False,
    nargs="?",
    help="Optional. Will playback a sound file while displaying the animation. If you give only --sound without any sound file it will attempt to extract the sound from the video.",
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
    "-ca",
    "--chafa-arguments",
    default="--symbols ascii --fg-only",
    help="Specify the arguments to give to chafa. Default is \"--symbols ascii --fg-only\". For more information, use 'chafa --help'",
)
parser.add_argument(
    "--cleanup",
    default=False,
    help="Clears the screen when the program quits. Default is False.",
    action="store_true",
)
parser.add_argument(
    "--force",
    default=False,
    help="Add this argument if you want to use neofetch even if it is deprecated.",
    action="store_true",
)
parser.add_argument(
    "-l",
    "--loop",
    default=-1,
    help="Determines how many times the animation should loop. Default is -1(always loop).",
    type=int,
)
parser.add_argument(
    "--quality",
    "-q",
    default=6,
    help="Quality when extracting frames. 2-5 high quality, 6-10 lower quality. Default is 6.",
    type=int,
)
parser.add_argument(
    "-nf",
    "--neofetch",
    default=False,
    help="Add this argument if you want to use neofetch instead.",
    action="store_true",
)
parser.add_argument(
    "--chroma",
    required=False,
    nargs="?",
    help="Add this argument to chromakey a hexadecimal color from the video using ffmpeg using syntax of '--chroma <hex color>:<similarity>:<blend>' with <hex-color> being 0xRRGGBB with a 0x as opposed to a #. Example: '--chroma 0xc82044:0.1:0.1'",
    type=str,
)
parser.add_argument(
    "-i",
    "--interval",
    required=False,
    type=float,
    help="Set fetch refresh interval in seconds. Default is -1(never).",
    default=-1,
)
parser.add_argument(
    "--version",
    action="version",
    version="%(prog)s {version}".format(version=get_version_of_anifetch()),
)
parser.add_argument(
    "--cache-list",
    required=False,
    action="store_true",
    help="List all saved cache configurations.",
)
parser.add_argument(
    "--delete",
    required=False,
    type=int,
    nargs="+",
    help="Delete one or more caches by number(s) (as listed with --cache-list)",
)
parser.add_argument(
    "--clear",
    required=False,
    action="store_true",
    help="Clear all saved cache configurations.",
)

parser.add_argument(
    "-b",
    "--benchmark",
    default=False,
    help="For testing. Runs Anifetch without actually starting the animation and returns how long it took in seconds.",
    action="store_true",
)


def parse_args():
    return parser.parse_args()
