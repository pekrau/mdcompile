"Compile Markdown files with footnotes, indexed terms and references to PDF book."

import constants
from text import Text
import utils


class Compiler:
    "Compile to PDF format document."

    def __init__(self, main):
        assert isinstance(main, Text)
        self.main = main
        self.tx = utils.Tx(self.main.language)


if __name__ == "__main__":
    args = utils.get_args("topdf")
    text = Text(args.infile)
    compiler = Compiler(text)
    compiler.write()
