"Interface to library containing references to articles and books."

import pathlib

import utils
from text import split_file


class Library:
    "Interface to library containing references to articles and books."

    def __init__(self, dirpath):
        if not dirpath:
            raise ValueError("no dirpath provided")
        dirpath = pathlib.Path(dirpath)
        if not dirpath.exists():
            raise IOError(f"no such library directory: {dirpath}")
        if not dirpath.is_dir():
            raise IOError(f"library path is not a directory: {dirpath}")
        self.dirpath = dirpath

    def __str__(self):
        return str(self.dirpath)

    def __len__(self):
        return len(list(self.dirpath.glob("*.md")))

    def __getitem__(self, name):
        "Return the reference as a dictionary, given the name 'Lastname year'."
        filepath = self.dirpath / f"{utils.safe(name)}.md"
        if not filepath.exists():
            raise KeyError(name)
        return split_file(filepath)[0]  # Return frontmatter only.
