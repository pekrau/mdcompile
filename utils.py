"Various utility functions."

import datetime as dt
import pathlib
import unicodedata

import yaml

import constants


def normalize(s):
    "Normalize string to ASCII, fold case, replace non-file characters with '-'."
    result = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore")
    result = "".join(
        [c if c in constants.SAFE_CHARACTERS else "-" for c in result.decode("utf-8")]
    )
    return result.casefold()


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
