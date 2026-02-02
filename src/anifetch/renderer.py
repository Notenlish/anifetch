import os
import sys
import time
from .utils import (
    show_cursor,
    truncate_line,
    get_fetch_output,
    center_template_to_animation,
    make_template_from_fetch_lines,
    clear_screen_soft,
    get_terminal_width,
)
import subprocess
from .keyreader import KeyReader
import logging
from typing import Literal
from threading import Thread
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.console import Console
from rich.align import Align


logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="anifetch.log", encoding="utf-8", level=logging.DEBUG, filemode="w"
)

# TODO: pypi release


# TODO: instead of writing frames one by one just write them once to a single frame.txt
# TODO: add streaming mode(instead of processing all files at once, process them over time. It will just check whether the next frame is available, and use that. If not available, wait for it to be available.)
# TODO: add a "nocache" mode where it simply streams the frames.
# TODO: nixos config stuff
# TODO: Ship 1.0 version

# TODO: Make a documentation site with Astro(use a premade theme and configure to your liking)


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
        height: int,
        len_fetch: int,
        bottom: int,
        using_cached: bool,
        template_width: int,
        template: list[str],
        chafa_frames: dict[int, str],
        use_fastfetch: bool,
        neofetch_status: Literal["neofetch", "uninstalled", "wrapper"],
        force_neofetch: bool,
        is_centered: bool,
        loop: int,
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
        self.height: int = height
        self.bottom: int = bottom

        self.using_cached = using_cached

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
        self.loop: int = loop
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

        self.chafa_frames = chafa_frames

        self._some_max_height = max(len(self.chafa_frames[0].splitlines()), len_fetch)

        self.layout = Layout()
        self.layout.split_column(Layout(name="top", size=self.top), Layout(name="main"))

        self.layout["main"].split_row(
            Layout(name="left", size=self.left),
            Layout(name="chafa", size=self.width),
            Layout(name="gap", size=self.gap),
            Layout(
                name="template",
            ),  # right
        )

        self.layout["top"].update(Text(""))
        self.layout["main"]["left"].update(Text(""))
        self.layout["main"]["gap"].update(Text(""))

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
        chafa_t = Text.from_ansi(chafa_frame)
        if self.is_centered:
            self.layout["main"]["chafa"].update(
                Align.center(chafa_t, vertical="middle", height=self._some_max_height)
            )
        else:
            self.layout["main"]["chafa"].update(chafa_t)

        _template_str = "".join(self.original_template_buffer)

        self.layout["main"]["template"].update(
            Text.from_ansi(
                _template_str, justify="left", no_wrap=True
            )  # TODO: put align center here
        )

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

            clear_screen_soft()

            # avoid Live container drawing the placeholder boxes with borders
            self.draw_stuff(self.chafa_frames[0])

            with Live(
                self.layout,
                refresh_per_second=20,
                screen=True,
                transient=True,  # if false, keep the last frame
            ) as live:
                self.draw_loop()
            # enable_autowrap()
        except KeyboardInterrupt:
            pass

        # after frame finishes redraw the stuff
        def layout_to_ansi(layout, width: int) -> str:
            console = Console(
                force_terminal=True,  # emit ANSI
                color_system="truecolor",  # keep 24-bit colors when available
                width=width,
                legacy_windows=False,  # helps on modern Windows terminals
            )
            with console.capture() as cap:
                console.print(layout, end="")  # render exactly once
            return cap.get()

        text = layout_to_ansi(self.layout, width=get_terminal_width())
        lines = text.splitlines()
        while lines and not lines[-1].strip():
            lines.pop()
        print("\n".join(lines), end="")
        # cleanup()
        self.stop_fetch_thread = True
        self.fetch_update_thread.join()

        if self.sound_process:
            self.sound_process.kill()

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
        loop_count = 0
        i = 0
        start_time = time.time()
        self.last_refresh_time = time.time()

        first_reading = True if self.using_cached else False
        while loop_count < self.loop or self.loop == -1:
            # didnt read every file so we need to iterate over the files
            if first_reading:  # using_cached
                for frame_name in sorted(os.listdir(self.frame_dir)):
                    frame_path = f"{self.frame_dir}/{frame_name}"
                    with open(frame_path, "r", encoding="utf-8") as f:
                        chafa_frame = f.read()
                        self.chafa_frames[i] = chafa_frame

                    self._process_one_frame(i, start_time, chafa_frame)
                    i += 1
                first_reading = False
                loop_count += 1
            else:
                start_time = time.time()
                # in here it is guaranteed that every frame already exists in the self.chafa_frames
                for j, _chafa_frame in self.chafa_frames.items():
                    self._process_one_frame(j, start_time, _chafa_frame)
                loop_count += 1
            # time.sleep(0.0000005)

    def _process_one_frame(self, index, start_time, chafa_frame):
        wanted_epoch = index / self.framerate_to_use
        now = time.time()
        sleep_duration = wanted_epoch - (now - start_time)

        # Only sleep if ahead of schedule
        if sleep_duration > 0:
            time.sleep(sleep_duration)

        # index += 1

        k = self.key_reader.poll()
        if k is not None:
            # if k in ("q", "Q"):
            raise KeyboardInterrupt

        self.process_resize_if_requested()
        self.draw_stuff(chafa_frame)
        sys.stdout.flush()
