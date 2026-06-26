"Various utility functions."

import argparse
import datetime as dt
import pathlib
import string
import unicodedata

import yaml

import constants


def get_args(prog, default="main.md"):
    "Define the command-line argument parser and return the arguments."
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument(
        "-r",
        "--references",
        default=None,
        help="Directory containing the references YAML files. Default: Environment variable REFERENCES if defined, else './references'.",
    )
    parser.add_argument(
        "-l",
        "--language",
        choices=constants.LANGUAGES,
        default=None,
        help=f"Language specification. Default '{constants.SV_SE}'.",
    )
    parser.add_argument(
        "-t",
        "--toc-level",
        type=int,
        default=None,
        help="Level for display in Table of contents. Default 1.",
    )
    parser.add_argument(
        "-b",
        "--page-break-level",
        type=int,
        default=None,
        help="Level at which to break for a new page. Default 1.",
    )
    parser.add_argument(
        "-n",
        "--text-number-level",
        type=int,
        default=None,
        help="Level at which to output number of the text. Default 1.",
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Do not output comments.",
    )
    parser.add_argument(
        "-f",
        "--footnotes-location",
        choices=constants.FOOTNOTES_LOCATIONS,
        default=None,
        help=f"Location of footnotes. Default '{constants.FOOTNOTES_TEXT}'.",
    )
    parser.add_argument(
        "-p",
        "--paragraph-numbers",
        action="store_true",
        help="Output consecutive number to each paragraph.",
    )
    parser.add_argument(
        "filename",
        nargs="?",
        default=default,
        help="Main Markdown file to convert. Default 'main.md'.",
    )
    return parser.parse_args()


def normalize(s):
    "Normalize string to ASCII, fold case, replace non-file characters with '-'."
    result = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore")
    result = "".join(
        [c if c in constants.SAFE_CHARACTERS else "-" for c in result.decode("utf-8")]
    )
    return result.casefold()


def short_person_name(name):
    "Return the person name in short form; given names as initials."
    parts = [p.strip() for p in name.split(",")]
    if len(parts) == 1:
        return name
    initials = [p.strip()[0] for p in parts.pop().split(" ")]
    parts.append("".join([f"{i}." for i in initials]))
    return ", ".join(parts)


def isoformat(datetime=None):
    "ISO format date, no seconds."
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


class ReferencesDir:
    "Reference files stored in a named directory."

    def __init__(self, filepath):
        self.filepath = pathlib.Path(filepath)
        if not self.filepath.exists():
            raise IOError
        if not self.filepath.is_dir():
            raise IOError

    def __getitem__(self, name):
        "Return the reference given the name 'Lastname year'."
        filepath = self.filepath / f"{normalize(name)}.yaml"
        if not filepath.exists():
            raise KeyError(f"no such reference: '{name}'")
        return yaml.safe_load(filepath.read_text())
