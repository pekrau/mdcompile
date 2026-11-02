"""Interface to library containing references to articles and books.
First try explicit location, then use envvar LIBRARY_DIR as fallback.
"""

import os
import pathlib

from text import parse_md
import utils


class Library:
    "Interface to library containing references to articles and books."

    def __init__(self, dirpath=None):
        if dirpath:
            self.dirpath = pathlib.Path(dirpath)
        else:
            try:
                self.dirpath = pathlib.Path(os.environ["LIBRARY_DIR"])
            except KeyError:
                raise IOError("environment variable LIBRARY_DIR not defined")
        if not self.dirpath.exists():
            raise IOError(f"no such library directory: {self.dirpath}")
        if not self.dirpath.is_dir():
            raise IOError(f"library path is not a directory: {self.dirpath}")

    def __str__(self):
        return str(self.dirpath)

    def __len__(self):
        return len(list(self.dirpath.glob("*.md")))

    def __getitem__(self, name):
        "Return the reference as a dictionary, given the name 'Lastname year'."
        filepath = self.dirpath / f"{utils.normalize(name)}.md"
        if not filepath.exists():
            raise KeyError(f"no such reference: '{name}'")
        return parse_md(filepath)[0]  # frontmatter only.
