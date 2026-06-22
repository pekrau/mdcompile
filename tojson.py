"""Compile Markdown files with footnotes, indexed terms and references to JSON for
the Abstract Syntax Tree (AST) of the book.
"""

import json

# For debugging.
import icecream

icecream.install()

from text import Text

if __name__ == "__main__":
    args = utils.get_args("tojson")
    text = Text(args.infile)
    ast = text.ast()
    outfile = pathlib.Path(args.infile).with_suffix(".json")
    outfile.write_text(json.dumps(ast, indent=2))
