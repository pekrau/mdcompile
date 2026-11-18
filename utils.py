"Various utility functions."

import datetime as dt
import string
import unicodedata

import constants


SAFE_CHARACTERS = set(string.ascii_letters + string.digits) # Blank is not safe.


def safe(s, casefold=True):
    "Make string safe: convert to ASCII and replace non-safe characters with '-'."
    result = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    if casefold:
        result = result.casefold()
    return "".join(
        [c if c in SAFE_CHARACTERS else "-" for c in result]
    )


def isoformat(datetime=None):
    "ISO format date, no seconds."
    if datetime is None:
        datetime = dt.datetime.now()
    return datetime.strftime(constants.DATETIME_ISOFORMAT)
