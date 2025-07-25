"""
Anifetch package initialization module.
"""

from .core import run_anifetch
from .cli import parse_args, parser
import sys

def main():
    args = parse_args()

    allowed_alternatives = ["cache_list", "clear", "delete"]

    if (
        args.filename is None
        and not any(getattr(args, key) for key in allowed_alternatives)
    ):
        print("[ERROR] Missing input. Use a filename or an option like --cache-list.")
        sys.exit(1)

    run_anifetch(args)


if __name__ == "__main__":
    main()
