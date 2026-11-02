"Various utility functions."

import datetime as dt
import pathlib
import time
import unicodedata

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


class Timer:
    "CPU timer."

    def __init__(self):
        self.start = time.perf_counter()

    def __str__(self):
        return f"CPU time: {time.perf_counter() - self.start:.3f} seconds."
