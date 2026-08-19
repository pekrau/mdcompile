"""Compile Markdown file(s) with extensions for hierachy, footnotes, indexed terms
and references to DOCX or PDF.
"""

# For debugging.
import icecream

icecream.install()

import os
import pathlib
import sys
import time

import constants
from docx_compiler import DocxCompiler
from pdf_compiler import PdfCompiler
from text import Text
import utils

import click


@click.command()
@click.help_option("--help", "-h")
@click.argument("input_filename",
                type=click.Path(exists=True, readable=True, file_okay=True),
                default="main.md", nargs=1)
@click.option(
    "--output_filename",
    "-o",
    default="main.docx",
    help="Name of the output file. Its extension ('.docx' or '.pdf') determines the format. Default: 'main.docx'.",
)
@click.option(
    "--refs_dirname",
    type=click.Path(exists=True, readable=True, file_okay=False, dir_okay=True),
    envvar="REFERENCES",
    help="Path to the directory containing the YAML files for references (articles, books).",
)
@click.option("--silent", "-s", is_flag=True, help="Output no execution information.")
@click.option(
    "--verbose", "-v", is_flag=True, help="Output more execution information."
)
@click.option(
    "--paragraph_numbers",
    "-p",
    is_flag=True,
    help="Write consecutive number for each paragraph.",
)
@click.option("--readme", "-r", is_flag=True, help="Write out a 'README.md' file.")
def main(
    input_filename,
    output_filename,
    refs_dirname,
    silent,
    verbose,
    paragraph_numbers,
    readme,
):
    if silent:
        verbose = False

    start_time = time.perf_counter()
    if not silent:
        click.echo(f"mdc {constants.__version__}")

    try:
        refs_dir = utils.ReferencesDir(refs_dirname)
        if verbose:
            click.echo(f"{len(refs_dir)} references in '{refs_dirname}'.")
    except IOError:
        sys.exit(f"Error: no such reference directory '{refs_dirname}'.")

    main = Text(input_filename, print=click.echo if verbose else None)
    if not silent:
        click.echo(f"{len(main)} texts")

    format = pathlib.Path(output_filename).suffix.lstrip(".")
    match format:
        case "docx":
            compiler = DocxCompiler(main, refs_dir, paragraph_numbers=paragraph_numbers)
        case "pdf":
            compiler = PdfCompiler(main, refs_dir, paragraph_numbers=paragraph_numbers)
        case _:
            sys.exit("Error: unknown output file format '{format}'")

    compiler.preprocess()
    if not silent:
        click.echo(f"footnotes at end of {compiler.footnotes_location}")
        click.echo(f"{len(compiler.referenced)} references used from '{refs_dirname}'")
        click.echo(f"{len(compiler.indexed)} terms indexed")

    compiler.write(output_filename)
    if not silent:
        if paragraph_numbers:
            click.echo(f"{compiler.paragraph_number} paragraphs")
        click.echo(f"'{output_filename}' written")

    if readme:
        with open("README.md", "w") as outfile:
            outfile.write(main.title + "\n")
            outfile.write("=" * len(main.title) + "\n\n")
            for subtext in main:
                if subtext is main:
                    continue
                outfile.write(" " * 5 * (len(subtext.ordinal) - 1))
                outfile.write(f"{subtext.ordinal[-1]}. {subtext.title}\n")
        if not silent:
            click.echo("'README.md' written")

    if not silent:
        input_filename = pathlib.Path(input_filename)
        all_md_filenames = set([str(n) for n in input_filename.parent.glob("*.md")])
        all_md_filenames.discard("README.md")
        all_text_filenames = set([str(t.filename) for t in main])
        if unread := all_md_filenames.difference(all_text_filenames):
            click.echo("Files not included:")
            for filename in sorted(unread):
                click.echo(f"  {filename}")

    if verbose:
        click.echo(f"CPU time: {time.perf_counter() - start_time:.3f}s")


if __name__ == "__main__":
    main()
