#!/usr/bin/env python

# SPDX-License-Identifier: MIT AND AGPL-3.0-only

# Original code from https://github.com/mmlb/ansi2txt


def ansi2txt(text: str) -> str:
    EOF = ""
    pos = 0
    output = []

    def getchar():
        nonlocal pos
        if pos >= len(text):
            return EOF
        ch = text[pos]
        pos += 1
        return ch

    ch = None

    while ch != EOF:
        ch = getchar()

        while ch == "\r":
            ch = getchar()
            if ch != "\n":
                output.append("\r")

        if ch == "\x1b":
            ch = getchar()

            if ch == "[":
                ch = getchar()
                while ch == ";" or ("0" <= ch <= "9") or ch == "?":
                    ch = getchar()

            elif ch == "]":
                ch = getchar()
                if ch != EOF and "0" <= ch <= "9":
                    while True:
                        ch = getchar()
                        if ch == EOF or ord(ch) == 7:
                            break
                        elif ch == "\x1b":
                            ch = getchar()
                            break

            elif ch == "%":
                ch = getchar()

        elif ch != EOF:
            output.append(ch)

    return "".join(output)
