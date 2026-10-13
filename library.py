"Interface to library containing references to articles and books."

import pathlib

import yaml

import utils


class Library:
    "Interface to library containing references to articles and books."

    def __init__(self, dirpath):
        self.dirpath = pathlib.Path(dirpath)
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
        return utils.parse_md(filepath)[0] # frontmatter only.
