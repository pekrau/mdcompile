"Various utility functions."

import argparse
import datetime as dt
import string
import unicodedata

import constants


def get_args(prog, default="main.md"):
    "Define the command-line argument parser and return the arguments."
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("infile", nargs="?", default=default)
    return parser.parse_args()


def normalize(title):
    "Normalize string to ASCII, fold case, replace non-file characters with '-'."
    result = unicodedata.normalize("NFKD", title).encode("ASCII", "ignore")
    result = "".join(
        [c if c in constants.SAFE_CHARACTERS else "-" for c in result.decode("utf-8")]
    )
    return result.casefold()


def isoformat(datetime=None):
    if datetime is None:
        datetime = dt.datetime.now()
    return datetime.strftime(constants.DATETIME_ISOFORMAT)


class Tx:
    "Translate fixed words in the code."

    def __init__(self, language):
        self.language = language

    def __call__(self, word):
        try:
            return constants.LEXICON[self.language][word]
        except KeyError:
            return word
