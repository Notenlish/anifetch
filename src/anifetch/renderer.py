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
    get_fetch_output,
    center_template_to_animation,
    make_template_from_fetch_lines,
    clear_screen_soft,
    get_terminal_width,
    get_terminal_height,
)
import subprocess
from .keyreader import KeyReader
import logging
from typing import Literal
from threading import Thread
import blessed



logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="anifetch.log", encoding="utf-8", level=logging.DEBUG, filemode="w"
)


# TODO: Stop adding random whitespace to chafa and template, just use terminal control codes etc. to do it
# TODO: move rendering to textual because fuck you. OR use rich module, live class?
# OR just use prompt_toolkit

# TODO: instead of writing frames one by one just write them once to a single frame.txt
# TODO: instead of writing template.txt to somewhere just stop writing it to a file,


# TODO: nix flake update needed
# TODO: pypi release
# TODO: add streaming mode(instead of processing all files at once, process them over time. It will just check whether the next frame is available, and use that. If not available, wait for it to be available.)
# TODO: add a "nocache" mode(for streaming mode).
# TODO: Make installation process easier for nixos on setup script(tell users to use flakes or smth), installation script for MacOS and Windows(maybe?)
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
        template: list[str],
        chafa_frames: list[str],
        use_fastfetch: bool,
        neofetch_status: Literal["neofetch", "uninstalled", "wrapper"],
        force_neofetch: bool,
        is_centered: bool,
        len_chafa: int | None,
        width: int,
        gap: int,
        refresh_interval: float,
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

        self.refresh_interval: float = refresh_interval
        self.last_refresh_time: float = time.time()
        self.use_fastfetch: bool = use_fastfetch
        self.neofetch_status: Literal["neofetch", "uninstalled", "wrapper"] = (
            neofetch_status
        )
        self.force_neofetch: bool = force_neofetch
        self.is_centered: bool = is_centered
        self.len_chafa: int | None = len_chafa
        self.width: int = width
        self.gap: int = gap
        self.refetched = False
        self.stop_fetch_thread = False

        self.last_terminal_width: int = get_terminal_width()
        self.original_template_buffer: list[str] = template
        self.template_buffer: list[str] = []
        self._make_truncated_template(self.last_terminal_width)

        num_lines = bottom - top
        sleep_time = 1 / framerate_to_use
        self.adjusted_sleep_time: float = sleep_time / num_lines

        self.resize_requested: bool = False
        self.resize_in_progress: bool = False
        self.resize_delay: float = 0.033  # seconds
        self.last_resize_time: float = 0

        self.sound_process: subprocess.Popen[bytes] | None = None

        self.key_reader = KeyReader()
        self.terminal: blessed.Terminal = blessed.Terminal()

        self.chafa_frames = chafa_frames

    def check_template_buffer_refresh(self):
        def _():
            if self.refresh_interval == -1:
                return
            dif = time.time() - self.last_refresh_time
            if dif < self.refresh_interval:  # not enough time passed
                return
            self.len_chafa: int  # trick pyright

            self.last_refresh_time = time.time()

            if self.stop_fetch_thread:
                return
            fetch_output: list[str] = get_fetch_output(
                self.use_fastfetch, self.neofetch_status, self.force_neofetch
            )

            if self.stop_fetch_thread:
                return
            len_fetch = len(fetch_output)
            if self.is_centered and len_fetch < self.len_chafa:
                fetch_lines: list[str] = center_template_to_animation(
                    self.width, self.len_chafa, len_fetch, fetch_output
                )
            else:
                fetch_lines: list[str] = fetch_output[:]  # copy

            if self.stop_fetch_thread:
                return
            template, template_width = make_template_from_fetch_lines(
                fetch_lines, self.left, self.gap, self.width
            )
            if self.stop_fetch_thread:
                return
            self.original_template_buffer = template
            self.template_width = template_width
            self.refetched = True

        while not self.stop_fetch_thread:
            _()
            time.sleep(0.05)

    def draw_stuff(self, chafa_frame: str):
        """My brain is melting"""
        t_w, t_h = get_terminal_width(), get_terminal_height()

        out = []
        out.append(self.terminal.move(self.top, 0))
        out.append("\n".join(self.template_buffer))
        out.append(self.terminal.move(self.top, 0))
        out.append(chafa_frame)
        sys.stdout.write("".join(out))

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

        # clear_screen()
        # clear_screen_soft()
        # tput_cup(self.top, 0)

        # Print buffer all at once with terminal control codes to prevent wrapping
        # print("\n".join(self.template_buffer), flush=False)

        # Reset flag
        self.resize_in_progress = False

    def start_rendering(self):
        sys.stdout.write(self.terminal.exit_fullscreen())  # dont question it
        sys.stdout.write(self.terminal.enter_fullscreen())
        sys.stdout.write(self.terminal.hide_cursor())
        # hide_cursor()
        # cleanup()

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
            self.fetch_update_thread = Thread(target=self.check_template_buffer_refresh)
            self.fetch_update_thread.start()

            # disable_autowrap()
            self.draw_loop()
            # enable_autowrap()
        except KeyboardInterrupt:
            pass

        # cleanup()
        self.stop_fetch_thread = True
        self.fetch_update_thread.join()

        # sys.stdout.write(self.terminal.exit_fullscreen())
        sys.stdout.write(self.terminal.normal_cursor())

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

    def _make_truncated_template(self, terminal_width: int):
        self.template_buffer = [
            truncate_line(line, terminal_width)
            for line in self.original_template_buffer
        ]

    def process_template(self) -> bool:
        """Returns whether it changed anything or not. Responsible for updating template_buffer with a truncated version of the saved template."""
        terminal_width = get_terminal_width()
        changed = False

        # reprocess template if the terminal width has changed.
        if terminal_width != self.last_terminal_width or self.refetched:
            logging.info(
                f"Window size changed / refreshed the fetch, remaking template buffer. Max size is {terminal_width}"
            )
            self.refetched = False
            if terminal_width < 1:
                terminal_width = 1

            self._make_truncated_template(terminal_width)

            self.last_terminal_width = terminal_width
            changed = True

        return changed

    def draw_loop(self):
        i = 1
        wanted_epoch = 0
        start_time = time.time()
        self.last_refresh_time = time.time()
        while True:
            for chafa_frame in self.chafa_frames:
                wanted_epoch = i / self.framerate_to_use

                # current time in seconds (with fractional part)
                now = time.time()

                # Calculate how long to sleep to stay in sync
                sleep_duration = wanted_epoch - (now - start_time)

                # Only sleep if ahead of schedule
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

                i += 1

                k = self.key_reader.poll()
                if k is not None:
                    # if k in ("q", "Q"):
                    raise KeyboardInterrupt

                self.process_resize_if_requested()
                self.draw_stuff(chafa_frame)
                sys.stdout.flush()
            # time.sleep(0.0000005)  # TODO: is this even required?
