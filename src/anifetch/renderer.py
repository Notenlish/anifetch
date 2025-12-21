from anifetch.utils import get_character_width
import os

from .utils import hide_cursor, show_cursor, clear_screen, tput_cup, tput_el


def cleanup():
    show_cursor()

    # stty echo  # display typed characters on the terminal
    # stty icanon  # input is line based(input buffered until you press enter).


class Renderer:
    def __init__(
        self,
        cache_path: str,
        framerate_to_use: int,
        top: int,
        left: int,
        right: int,
        bottom: int,
        template_width: int,
        sound_saved_path: str,
    ):
        self.cache_path: str = cache_path
        self.framerate_to_use: int = framerate_to_use
        self.top: int = top
        self.left: int = left
        self.right: int = right
        self.bottom: int = bottom
        self.template_width: int = template_width
        self.sound_saved_path: str = sound_saved_path
        self.frame_dir = f"{cache_path}/output"
        self.static_template_path = f"{cache_path}/template.txt"
        num_lines = bottom - top
        sleep_time = 1 / framerate_to_use
        self.adjusted_sleep_time = sleep_time / num_lines
        self.template_buffer = []
        self.last_terminal_width = 0

        self.resize_requested = False
        self.resize_in_progress = False
        self.resize_delay = 0.2  # seconds
        self.last_resize_time = 0

    def on_resize(self):
        self.resize_requested = True

    def process_resize_if_requested(self):
        current_time = time.time()

        if self.resize_in_progress or not self.resize_requested:
            return
        
        if self.last_resize_time != 0:
            time_diff=current_time-self.last_resize_time
            # Not enough time has passed, wait more
            if time_diff < self.resize_delay:
                return
            
        # we can process
        resize_in_progress=True
        resize_requested=False
        last_resize_time=current_time

        new_width=$(tput cols)
        new_height=$(tput lines)

        # calculate the new template
        process_template

        tput clear
        tput cup $top 0

        # Print buffer all at once with terminal control codes to prevent wrapping
        for line in "${template_buffer[@]}"; do
            # First clear to end of line to ensure no artifacts
            tput el
            printf "%b\n" "$line"
        done

        # Reset flag
        resize_in_progress=false

    def start_rendering(self):
        hide_cursor()
        cleanup()
        # TODO: call cleanup when CTRL+C(KeyboardInterrupt) happens
        # TODO: disallow characters to be written and disallow line by line mode.

    def draw_static_template(self):
        # Process template first
        self.process_template()

        # Clear screen and position cursor
        clear_screen()
        tput_cup(self.top, 0)

        # Print the buffer in one go(faster than one by line)
        # for line in self.template_buffer:
        # Clear to end of line before printing to eliminate any potential artifacts
        # tput_el()
        print("".join(self.template_buffer))  # TODO: maybe use a "\n".join() instead?

    def process_template(self):
        terminal_width = os.get_terminal_size().columns

        # only reprocess template if the terminal width has changed.
        if terminal_width != self.last_terminal_width:
            self.template_buffer = []

            if terminal_width < 1:
                terminal_width = 1

            # process each line and store it in a buffer
            line_num = 0
            with open(self.static_template_path, "r") as f:
                for template_line in f.readlines():
                    self.template_buffer.append(
                        truncate_line(template_line, terminal_width)
                    )
