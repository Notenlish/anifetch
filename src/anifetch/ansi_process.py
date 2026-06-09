from typing import Literal
import re
from .utils import debug_write_str, overwrite_string
from .ansi2txt import ansi2txt



class Token:
    def __init__(self, type_:Literal["text", "go_left", "go_right", "move_to_column"], value) -> None:
        self.type = type_
        self.value: str|int = value 
    
    def __repr__(self) -> str:
        if self.type == "text":
            # pyrefly: ignore [bad-return]
            return self.value
        else:
            code = "C" if self.type == "go_left" else "D"
            return f"<{self.type} {self.value}>"
            # return f"\x1b[{self.value}{code}"

# How to fix this
# 1 Proper handling of text length via wcwidth(color escape sequences mess with the strings)
# 2 proper handling of emojis. When this 💻 emoji is present in the config, the code prints 1 more border than required


def strip_ansi_colors(lines: list[str]) -> list[str]:
    ANSI_COLOR_RE = re.compile(r'\x1B\[[0-9;]*m')
    return [ANSI_COLOR_RE.sub('', line) for line in lines]

def tokenize_lines(lines:list[str]):
    # lines = ["lllllll  lllllll[1G[7A[18C╔════════════════════════════════════════════════════════════════════════════════════════════════════╗[101D root@debian 💻 ","[18C║[100C║[100D kernel   >  6.12.1"]
    ## attempt to tokenize every line.
    # pattern = r"(?:\x1B\[|\x9B)\d*(?:;\d*)*[A-FfHhsu]"
    pattern = r"(?:\x1B\[|\x9B)\d*(?:;\d*)*[A-GHfhsu]"


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
            
            debug_write_str(f"MATCH.STRING\n\n {match_text}")
            # example:   \x1b[100D
            _left = match_text.find("[") + 1
            _right = len(match_text) -1
            # print(f"lets see what this is?? \n\n {match_text[_left: _right]}")
            try:
                amount = int(match_text[_left: _right])
            except ValueError:
                amount = None

            code = match_text[-1]

            if code == "C":
                line_tokens.append(Token("go_right", amount))
            elif code == "D":
                line_tokens.append(Token("go_left", amount))
            elif code == "G":
                if not amount: amount = 1
                line_tokens.append(Token("move_to_column", amount))
            #else:
            #    continue
            
            text_index = end
        
        # check if there is remaining text after the last escape sequence match.
        if text_index < len(line):
            line_tokens.append(Token("text", line[text_index:]))

        line_tokens_all.append(line_tokens)
    return line_tokens_all

def expand_ansi_movement_seq(lines:list[str]):
    # debug_write_str("\n\n\n".join(lines))
    line_tokens_all = tokenize_lines(lines)

    lines = []
    
    for line_tokens in line_tokens_all:
        line = ""
        cur_i = 0  # cursor pos(x)
        for token in line_tokens:
            if token.type == "text":
                # this doesn't overwrite text
                # line = line[:cur_i] + token.value + line[cur_i:]
                line = overwrite_string(line, cur_i, token.value)
                
                cur_i += len(token.value)
            if token.type == "go_right":
                # pyrefly: ignore [unsupported-operation]
                wanted_i = cur_i + token.value
                max_i = len(line)
                needed_space = max(wanted_i - max_i, 0)
                line += " " * needed_space
                cur_i = wanted_i
            if token.type == "go_left":
                # cur_i = 10
                # token.value = 20(wants to go 20 left)
                # max_i = 20
                # min_i = 0
                # wanted_i = -10

                # pyrefly: ignore [unsupported-operation]
                wanted_i = cur_i - token.value
                min_i = 0
                needed_space = max(wanted_i * -1, 0)  # 10
                line = " " * needed_space + line
                cur_i = wanted_i + needed_space  # 0
            if token.type == "go_to_column":
                # ANSI ESC[nG -> move to column n (1-based)
                wanted_i = max(token.value, 1) - 1  # convert to 0-based

                # extend line if needed
                if wanted_i > len(line):
                    line += " " * (wanted_i - len(line))
                
                cur_i = wanted_i
        lines.append(line)
    
    debug_write_str("\n".join(lines))
    print("\n".join(lines))
    return lines
