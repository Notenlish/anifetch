from anifetch.utils import get_terminal_width
import os
import sys
import time
from .utils import (
    hide_cursor,
    show_cursor,
    clear_screen,
    tput_cup,
    tput_el,
    truncate_line,
    enable_autowrap,
    disable_autowrap,
)
import subprocess
from .keyreader import KeyReader
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="anifetch.log", encoding="utf-8", level=logging.DEBUG, filemode="w"
)

# TODO: add an argument to also update the system info over time. The timing period could be changed over time.
# TODO: nix flake update needed
# TODO: Install script for macos/windows
# TODO: multithreading (also add ability to specify num of threads to use)
# TODO: add streaming mode(instead of processing all files at once, process them over time. It will just check whether the next frame is available, and use that. If not available, wait for it to be available.)
# TODO: add a "nocache" mode.
# TODO: add an option to not clear the screen when animation loop ends
# TODO: Make installation process easier for nixos(tell users to use flakes or smth), MacOS and Windows
# TODO: For windows check PATH and autodownload chafa and ffmpeg binaries to anifetch installation folder or just use choco / winget idk.
# TODO: remove bc from readme and setup.sh and the nixos config stuff
# TODO: remove the old bash script
# TODO: if possible find the origin of the example.mp4 file, for licensing and whatnot
# TODO: Make a documentation site with Astro(use a premade theme and configure to your liking)
# TODO: Ship 1.0 version


def cleanup():
    show_cursor()
    # clear_screen()  # TODO: uncomment this line when done testing

    # stty echo  # display typed characters on the terminal
    # stty icanon  # input is line based(input buffered until you press enter).


class Renderer:
    def __init__(
        self,
        base_path: str,
        cache_path: str,
        framerate_to_use: int,
        top: int,
        left: int,
        right: int,
        bottom: int,
        template_width: int,
        sound_saved_path: str = "",
    ):
        self.base_path: str = base_path
        self.cache_path: str = cache_path
        self.framerate_to_use: int = framerate_to_use
        self.top: int = top
        self.left: int = left
        self.right: int = right
        self.bottom: int = bottom
        self.template_width: int = template_width
        self.sound_saved_path: str = sound_saved_path
        self.frame_dir: str = f"{cache_path}/output"
        self.static_template_path: str = f"{base_path}/template.txt"
        logging.info("static template path", self.static_template_path)
        num_lines = bottom - top
        sleep_time = 1 / framerate_to_use
        self.adjusted_sleep_time: float = sleep_time / num_lines
        self.template_buffer: list[str] = []

        self.last_terminal_width: int = get_terminal_width()
        print(self.last_terminal_width)
        self.resize_requested: bool = False
        self.resize_in_progress: bool = False
        self.resize_delay: float = 0.033  # seconds
        self.last_resize_time: float = 0

        self.sound_process: subprocess.Popen[bytes] | None = None

        self.key_reader = KeyReader()

    def process_resize_if_requested(self):
        """This is being run every frame of the animation."""
        if self.resize_in_progress:  # TODO: dont know whether I should keep this or not
            return

        current_time = time.time()

        changed = self.process_template()
        if not changed:
            return

        if self.last_resize_time != 0:
            time_diff = current_time - self.last_resize_time
            # Not enough time has passed, wait more
            if time_diff < self.resize_delay:
                return

        # we can process
        self.resize_in_progress = True
        self.last_resize_time = current_time

        clear_screen()
        tput_cup(self.top, 0)

        # print(self.template_buffer)

        # Print buffer all at once with terminal control codes to prevent wrapping
        print("\n".join(self.template_buffer), flush=False)

        # Reset flag
        self.resize_in_progress = False

    def start_rendering(self):
        hide_cursor()
        cleanup()

        self.draw_static_template()
        if self.sound_saved_path:
            self.sound_process = subprocess.Popen(
                [
                    "ffplay",
                    "-nodisp",
                    "-autoexit",
                    "-loop",
                    "0",
                    "-loglevel",
                    "quiet",
                    self.sound_saved_path,
                ]
            )
        try:
            # disable_autowrap()
            self.draw_loop()
            # enable_autowrap()
        except KeyboardInterrupt:
            cleanup()
            # enable_autowrap()
            # subprocess.call(["stty", "sane"])  # TODO: find cross platform version of this
        # TODO: disallow characters to be written and disallow line by line mode.

    def draw_static_template(self):
        """Only ran once."""

        changed_template = self.process_template()

        # Clear screen and position cursor
        clear_screen()
        tput_cup(self.top, 0)  # problem originates in here?

        # Print the buffer in one go(faster than one by line)
        print("\n".join(self.template_buffer))
        # raise SystemExit

        # TODO: this works fine atm. I just need to clean the screen without causing the black refresh thing and that should be it
        # TODO: also maybe truncate stuff for height(lines) as well?
        # Oh and check the issues on github, try to do all of them, then do 1.0 release and also include a tutorial as well.

    def process_template(self) -> bool:
        """Returns whether it changed anything or not. Responsible for updating template_buffer with a truncated version of the saved template."""
        terminal_width = get_terminal_width()
        changed = False

        # initial fill(if empty)
        if not self.template_buffer:
            logging.info(
                f"Empty so doing initial fill, heres template path: {self.static_template_path}"
            )
            with open(self.static_template_path, "r") as f:
                self.template_buffer = [
                    truncate_line(line, terminal_width) for line in f.readlines()
                ]
            changed = True
        # reprocess template if the terminal width has changed.
        if terminal_width != self.last_terminal_width:
            logging.info(
                f"Window size changed, remaking template buffer. Max size is {terminal_width}"
            )
            self.template_buffer = []

            if terminal_width < 1:
                terminal_width = 1

            line_num = 0
            with open(self.static_template_path, "r") as f:
                self.template_buffer = [
                    truncate_line(line, terminal_width) for line in f.readlines()
                ]

            self.last_terminal_width = terminal_width
            changed = True

        return changed

    def draw_loop(self):
        i = 1
        wanted_epoch = 0
        start_time = time.time()
        while True:
            for frame_name in sorted(os.listdir(self.frame_dir)):
                frame_path = f"{self.frame_dir}/{frame_name}"

                current_top = self.top
                with open(frame_path) as f:
                    for line in f.readlines():
                        tput_cup(current_top, self.left)

                        # dont echo new line and enable special characters
                        # echo -ne "$line"
                        print(
                            line, end="", flush=False
                        )  # there may be a faster way to do this.
                        current_top += 1
                        if current_top > self.bottom:
                            break

                wanted_epoch = i / self.framerate_to_use

                # current time in seconds (with fractional part)
                now = time.time()

                # Calculate how long to sleep to stay in sync
                sleep_duration = wanted_epoch - (now - start_time)

                # Only sleep if ahead of schedule
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

                i += 1

                # runs every frame.
                logger.info(f"kafayı yicem {self.last_terminal_width}")

                k = self.key_reader.poll()
                if k is not None:
                    # if k in ("q", "Q"):
                    raise KeyboardInterrupt

                self.process_resize_if_requested()
                sys.stdout.flush()
            time.sleep(0.0000005)  # TODO: is this even required?
