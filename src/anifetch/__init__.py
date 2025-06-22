"""
Anifetch package initialization module.
"""

from .core import run_anifetch
from .cli import parse_args


def main():
    args = parse_args()

    if args.filename:
        run_anifetch(args)


if __name__ == "__main__":
    main()
