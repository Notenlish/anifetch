import re
import regex
from wcwidth import wcswidth
from dataclasses import dataclass
from .utils import debug_write_str

# this is slower but more readable, don't use this.
# this is because im using \X to get graphemes
# creating Cell objects
# wcswidth(maybe?)
# and using regex? I'd assume 're' is faster


@dataclass
class Token:
    pass


@dataclass
class TextToken(Token):
    text: str


@dataclass
class SGRToken(Token):  # coloring stuff
    params: list[int]


@dataclass
class GoLeftToken(Token):
    amount: int


@dataclass
class GoToColumn(Token):
    index: int  # 0 based


@dataclass
class GoRightToken(Token):
    amount: int


GENERAL_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
GENERAL_ANSI_REGEX = regex.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
COLOR_ANSI_RE = re.compile(r"\x1B\[[0-9;]*m")


class Cell:
    # modifier = ANSI coloring sequences
    # text = a piece of text
    # this could be an emoji, or just a normal piece of string.
    # width = how many cells this would visually occupy
    def __init__(self, text: str, modifier: str, width: int = 1):
        self.text = text
        self.modifier = modifier
        self.width = width


@dataclass
class CellMap:
    """2D array of cells."""

    lines: list[list[Cell]]


def tokenize(raw_lines: list[str]):
    """Tokenize raw string, to be later used to create a CellMap"""
    tokens_per_line: list[list[Token]] = []

    for line in raw_lines:
        tokens: list[Token] = []
        text_index = 0

        for match in regex.finditer(GENERAL_ANSI_REGEX, line):
            start, end = match.span()

            if start > text_index:
                tokens.append(TextToken(line[text_index:start]))

            match_text = line[start:end]

            bracket = match_text.find("[")
            # example:   \x1b[100D
            _left = (bracket + 1) if bracket != -1 else 1
            _right = len(match_text) - 1

            amount_str = match_text[_left:_right]

            code = match_text[-1].upper()

            if code in ("C", "D", "G"):
                try:
                    amount = int(amount_str) if amount_str else 1
                except ValueError:
                    amount = 1
                if code == "C":
                    tokens.append(GoRightToken(amount))
                elif code == "D":
                    tokens.append(GoLeftToken(amount))
                elif code == "G":
                    tokens.append(
                        GoToColumn(amount - 1)
                    )  # escape seq is 1 based, convert to 0 based

            # TODO: also check for ANSI formatting string bs
            if code == "M":
                if amount_str:
                    amount_values = [int(v) for v in amount_str.split(";")]
                else:
                    amount_values = [0]
                tokens.append(SGRToken(amount_values))
                debug_write_str(f"shitty sgr ansi coloring shit {amount_str} \n")

            text_index = end

        # check if
        if text_index < len(line):
            tokens.append(TextToken(line[text_index:]))

        tokens_per_line.append(tokens)

    return tokens_per_line


def split_to_cells(tokenised_lines: list[list[Token]]):
    grapheme_pattern = regex.compile(r"\X")

    cellmap = CellMap([])
    for line_tokens in tokenised_lines:
        cells: list[Cell] = []
        current_modifier = ""
        cell_index = 0
        for token in line_tokens:
            if isinstance(token, TextToken):
                graphemes = grapheme_pattern.findall(token.text)
                for g in graphemes:
                    # g: str
                    width = wcswidth(g)
                    if width == 1:
                        # Extend if needed, then overwrite
                        while len(cells) <= cell_index:
                            cells.append(Cell(" ", modifier=""))
                        cells[cell_index] = Cell(g, modifier=current_modifier)
                        cell_index += 1
                    elif width == 2:
                        while len(cells) <= cell_index + 1:
                            cells.append(Cell(" ", modifier=""))
                        cells[cell_index] = Cell(g, modifier=current_modifier, width=2)
                        cells[cell_index + 1] = Cell(
                            "", modifier=""
                        )  # continuation cell
                        cell_index += 2
                    else:
                        raise Exception(f"Invalid width {width} {g}")
                    # current_modifier = ""  # HUHHHH if I just disable it it gets better
            if isinstance(token, SGRToken):
                debug_write_str(f"skibidi skibidi the sgrtoken is here guys {token}\n")
                # example: \x1b[1;31m
                # depending on whether there is '=' or '+=' there the formatting can be fucked
                if token.params == [0]:  # reset
                    current_modifier = "\x1b[0m"
                else:  # add
                    current_modifier += (
                        "\x1b[" + ";".join([str(v) for v in token.params]) + "m"
                    )
            if isinstance(token, GoRightToken):
                wanted_cell_index = cell_index + token.amount
                needed = max(wanted_cell_index - len(cells), 0)
                for _ in range(needed):
                    cells.append(Cell(" ", modifier=""))
                cell_index = wanted_cell_index
            if isinstance(token, GoLeftToken):
                wanted_cell_index = cell_index - token.amount
                if wanted_cell_index < 0:
                    needed = -wanted_cell_index
                    for _ in range(needed):
                        cells.insert(0, Cell(" ", modifier=""))
                    cell_index = 0
                else:
                    cell_index = wanted_cell_index
        cellmap.lines.append(cells)
    return cellmap


def expand_ansi_movement_seq2(lines: list[str]):
    debug_write_str("---------------\n")
    cellmap = split_to_cells(tokenize(lines))
    out = []
    for line in cellmap.lines:
        out_line = ""
        for cell in line:
            out_line += cell.modifier + cell.text
        out.append(out_line)
    out[-1] += "\x1b[0m"  # reset

    # debug_write_str("\n".join(out))
    print("\n".join(out))
    return out
