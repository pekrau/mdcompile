"""Compile Markdown file(s) with extensions for hierachy, footnotes, indexed terms
and references to DOCX, PDF or EPUB.
"""

# For debugging.
import icecream

icecream.install()

import argparse
import os
import pathlib
import time

import constants
from docx_compiler import DocxCompiler
from text import Text
import utils


def get_cli_parser(default_filename="main"):
    "Get the command-line parser."
    parser = argparse.ArgumentParser(prog="mdc", description=__doc__)
    parser.add_argument(
        "input_filename",
        nargs="?",
        default=f"{default_filename}.md",
        help=f"Name of Markdown file to compile. Default: '{default_filename}.md'.",
    )
    parser.add_argument(
        "-o",
        "--output_filename",
        default=f"{default_filename}.docx",
        help=f"Name of the output file. Its extension determines the format (docx, pdf or epub). Default: '{default_filename}.docx'.",
    )
    try:
        default_refs_dirname = os.environ["REFERENCES"]
    except KeyError:
        default_refs_dirname = "./references"
    parser.add_argument(
        "-r",
        "--refs_dirname",
        default=default_refs_dirname,
        help=f"Directory containing the YAML files for references (articles, books). Default '{default_refs_dirname}'",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Output no execution information.",
    )
    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Output more execution information.",
    )
    parser.add_argument(
        "-c",
        "--comments",
        action="store_true",
        help="Write comments.",
    )
    parser.add_argument(
        "-p",
        "--paragraph-numbers",
        action="store_true",
        help="Write consecutive number for each paragraph.",
    )
    parser.add_argument(
        "-R",
        "--README",
        action="store_true",
        help="Write out a 'README.md' file.",
    )
    return parser


def main(
    input_filename,
    output_filename,
    refs_dirname,
    silent,
    verbose,
    comments,
    paragraph_numbers,
    README,
):
    start_time = time.perf_counter()
    if not silent:
        print(f"mdc {constants.__version__}")

    main = Text(input_filename)
    if verbose:
        print("Texts:")
        print(main.contents(indent=2))
    elif not silent:
        print(f"{len(main)} texts")
    refs_dir = utils.ReferencesDir(refs_dirname)

    format = pathlib.Path(output_filename).suffix.lstrip(".")
    match format:
        case "docx":
            compiler = DocxCompiler(
                main, refs_dir, comments=comments, paragraph_numbers=paragraph_numbers
            )
            pass
        case "pdf":
            raise NotImplementedError(f"format {format}")
        case "epub":
            raise NotImplementedError(f"format {format}")
        case _:
            raise NotImplementedError(f"format {format}")

    compiler.write(output_filename)
    if not silent:
        print(f"'{output_filename}' written.")

    if README:
        with open("README.md", "w") as outfile:
            outfile.write(main.title + "\n")
            outfile.write("=" * len(main.title) + "\n\n")
            for subtext in main:
                if subtext is main:
                    continue
                outfile.write("  " * len(subtext.ordinal))
                outfile.write(f"{subtext.ordinal[-1]}. {subtext.title}\n\n")
        if not silent:
            print("'README.md' written.")

    if verbose:
        print(f"CPU time: {time.perf_counter() - start_time:.3f}s")


if __name__ == "__main__":
    main(**vars(get_cli_parser().parse_args()))
