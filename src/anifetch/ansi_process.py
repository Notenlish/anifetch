from typing import Literal
import re
from .utils import printable_len
import wcwidth


_ANSI_RE = re.compile(r"(?:\x1B\[|\x9B)[\d;]*[A-Za-z]")


def _active_ansi_state(line: str, up_to: int) -> str:
    """
    Return all ANSI SGR (color/style) sequences active just before Python
    position `up_to`. Prepending this to a tail restores the correct color
    state even when the preceding text contains an ANSI reset.
    """
    return "".join(
        m.group()
        for m in _ANSI_RE.finditer(line, 0, up_to)
        if m.group()[-1] == "m"  # only SGR codes affect color/style
    )


def _col_to_char(line: str, col: int) -> int:
    """
    Return the Python string index where visual column *col* begins in *line*.
    ANSI sequences are zero-width; double-width characters (emoji, CJK) count as 2.
    Returns len(line) if *col* exceeds the visual width of the string.
    """
    i, c = 0, 0
    while i < len(line):
        if c >= col:
            break
        m = _ANSI_RE.match(line, i)
        if m:
            i = m.end()  # ANSI sequences are invisible aka: skip, don't count
        else:
            w = wcwidth.wcwidth(line[i])
            c += max(w, 0)  # wcwidth returns -1 for non-printable; treat as 0-wide
            i += 1
    return i


class Token:
    def __init__(
        self,
        type_: Literal["text", "go_left", "go_right", "go_to_column", "sgr"],
        value,
    ) -> None:
        self.type = type_
        self.value: str | int = value

    def __repr__(self) -> str:
        if self.type == "text":
            # pyrefly: ignore [bad-return]
            return self.value
        else:
            return f"<{self.type} {self.value}>"
            # return f"\x1b[{self.value}{code}"


def strip_ansi_colors(lines: list[str]) -> list[str]:
    ANSI_COLOR_RE = re.compile(r"\x1B\[[0-9;]*m")
    return [ANSI_COLOR_RE.sub("", line) for line in lines]


def tokenize_lines(lines: list[str]):
    # lines = ["lllllll  lllllll[1G[7A[18C╔════════════════════════════════════════════════════════════════════════════════════════════════════╗[101D root@debian 💻 ","[18C║[100C║[100D kernel   >  6.12.1"]
    # pattern = r"(?:\x1B\[|\x9B)\d*(?:;\d*)*[A-FfHhsu]"
    pattern = r"(?:\x1B\[|\x9B)\d*(?:;\d*)*[A-GHfhsu]"
    # pattern = r"(?:\x1B\[|\x9B)\d*(?:;\d*)*[A-GHfhsum]"

    line_tokens_all: list[list[Token]] = []

    for line in lines:
        line_tokens: list[Token] = []
        text_index = 0

        for match in re.finditer(pattern, line):
            start, end = match.span()

            # if there is text before the escape sequence
            if start > text_index:
                line_tokens.append(Token("text", line[text_index:start]))

            match_text = line[start:end]

            bracket = match_text.find("[")
            # example:   \x1b[100D
            _left = (bracket + 1) if bracket != -1 else 1
            _right = len(match_text) - 1

            amount_str = match_text[_left:_right]

            try:
                amount = int(amount_str) if amount_str else 1
            except ValueError:
                amount = 1

            code = match_text[-1]

            if code == "C":
                line_tokens.append(Token("go_right", amount))
            elif code == "D":
                line_tokens.append(Token("go_left", amount))
            elif code == "G":
                line_tokens.append(Token("go_to_column", amount))

            # else:
            #    continue

            text_index = end

        # check if there is remaining text after the last escape sequence match.
        if text_index < len(line):
            line_tokens.append(Token("text", line[text_index:]))

        line_tokens_all.append(line_tokens)
    return line_tokens_all


def expand_ansi_movement_seq(lines: list[str]):
    # debug_write_str("\n\n\n".join(lines))
    line_tokens_all = tokenize_lines(lines)

    result: list[str] = []

    for line_tokens in line_tokens_all:
        line = ""
        cur_col = 0  # visual terminal column
        cur_char = 0  # string index(raw data)
        for token in line_tokens:
            if token.type == "text":
                text: str = token.value  # type: ignore[assignment]
                vis_len = printable_len(text)

                if cur_char > len(line):
                    line += " " * (cur_char - len(line))

                tail_char = _col_to_char(line, cur_col + vis_len)

                # Collect the SGR state active at tail_char so that border characters
                # in the tail (spaces, ║) keep their original color even when the
                # inserted text ends with \x1b[0m.
                state = _active_ansi_state(line, tail_char)

                line = line[:cur_char] + text + state + line[tail_char:]
                cur_col += vis_len
                cur_char += len(text) + len(state)  # state bytes are in the string now

            if token.type == "go_right":
                wanted_col = cur_col + token.value  # type: ignore[operator]
                needed = max(wanted_col - printable_len(line), 0)
                line += " " * needed
                cur_col = wanted_col
                cur_char = _col_to_char(line, cur_col)

            if token.type == "go_left":
                wanted_col = cur_col - token.value  # type: ignore[operator]
                if wanted_col < 0:
                    needed = -wanted_col
                    line = " " * needed + line
                    cur_col = 0
                    cur_char = 0
                else:
                    cur_col = wanted_col
                    cur_char = _col_to_char(line, cur_col)
            if token.type == "go_to_column":
                # escape seq is 1-based, convert to 0-based
                wanted_col = token.value - 1  # type: ignore[operator]
                needed = max(wanted_col - printable_len(line), 0)
                if needed:
                    line += " " * needed
                cur_col = wanted_col
                cur_char = _col_to_char(line, cur_col)

                # cur_i = wanted_i
        result.append(line)

    # debug_write_str("\n".join(result))
    print("\n".join(result))
    return result
