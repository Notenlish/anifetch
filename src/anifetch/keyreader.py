import os
import sys
import atexit

class KeyReader:
    """
    Cross-platform, non-blocking key reader for terminal animations.
    - Windows: msvcrt
    - macOS/Linux: termios + select
    Restores terminal settings on exit.
    """
    def __init__(self):
        self.is_windows = (os.name == "nt")
        self._started = False

        if not self.is_windows:
            import termios
            self.termios = termios
            self.fd = sys.stdin.fileno()
            self.old_attrs = None

    def start(self):
        if self._started:
            return
        self._started = True

        if not self.is_windows:
            import tty
            self.old_attrs = self.termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)  # no-Enter input, but less aggressive than raw
            atexit.register(self.stop)

    def stop(self):
        if not self._started:
            return
        self._started = False

        if not self.is_windows and self.old_attrs is not None:
            self.termios.tcsetattr(self.fd, self.termios.TCSADRAIN, self.old_attrs)
            self.old_attrs = None

    def poll(self):
        """
        Returns:
          - None if no key was pressed
          - a string representing the key pressed
            (single char for normal keys; escape sequences possible for arrows on Unix;
             two-char sequences possible for arrows/function keys on Windows)
        """
        if not self._started:
            self.start()

        if self.is_windows:
            import msvcrt
            if not msvcrt.kbhit():
                return None
            ch = msvcrt.getwch()
            # arrows / function keys: prefix then code
            if ch in ("\x00", "\xe0"):
                return ch + msvcrt.getwch()
            return ch
        else:
            import select
            r, _, _ = select.select([sys.stdin], [], [], 0)
            if not r:
                return None
            return sys.stdin.read(1)
