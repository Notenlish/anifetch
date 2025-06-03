# anifetch/__init__.py

'''
    Anifetch package initialization module.
'''

from .core import run_anifetch
from .cli import parse_args

def main():
    args = parse_args()
    run_anifetch(args)