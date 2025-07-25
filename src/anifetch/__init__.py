"""
Anifetch package initialization module.
"""

from .core import run_anifetch
from .cli import parse_args
import sys

def main():
    args = parse_args()

    run_anifetch(args)


if __name__ == "__main__":
    main()
