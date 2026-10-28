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


def parse_md(filepath):
    "Read the Markdown file, parse, and return the frontmatter and text."
    assert filepath.exists(), filepath
    assert filepath.suffix == ".md", filepath
    content = filepath.read_text()
    match = constants.FRONTMATTER.match(content)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        text = content[match.start(2) :]
    else:
        frontmatter = {}
        text = content
    return (frontmatter, text)


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
