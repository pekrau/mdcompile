"""Compile Markdown file(s) with extensions for hierachy, footnotes, indexed terms
and references to DOCX or PDF.
"""

# For debugging.
import icecream

icecream.install()

import os
import pathlib
import time

import constants
from docx_compiler import DocxCompiler
from pdf_compiler import PdfCompiler
from text import Text
import utils

import click


COMPILER_CLASSES = dict(docx=DocxCompiler,
                        pdf=PdfCompiler)


@click.command()
@click.help_option("--help", "-h")
@click.argument(
    "input_filename",
    type=click.Path(exists=True, readable=True, file_okay=True),
    default="main.md",
    nargs=1,
)
@click.option(
    "--output_filename",
    "-o",
    default="ms.docx",
    help="Name of the output file. Its extension ('.docx' or '.pdf') determines the format. Default: 'ms.docx'.",
)
@click.option(
    "--refs_dirname",
    type=click.Path(exists=True, readable=True, file_okay=False, dir_okay=True),
    envvar="REFERENCES",
    help="Path to the directory containing the YAML files for references (articles, books).",
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
    paragraph_numbers,
    readme,
):
    start_time = time.perf_counter()
    click.echo(f"mdc {constants.__version__}")

    output_filename = pathlib.Path(output_filename)
    format = output_filename.suffix.lstrip(".")
    try:
        compiler_class = COMPILER_CLASSES[format]
    except KeyError:
        click.get_current_context().fail(f"Error: unknown output format '{format}'.")

    try:
        refs_dir = utils.ReferencesDir(refs_dirname)
        click.echo(f"{len(refs_dir)} references in '{refs_dirname}'.")
    except IOError:
        click.get_current_context().fail(f"Error: no such reference directory '{refs_dirname}'.")

    try:
        main = Text(input_filename)
    except OSError as error:
        click.get_current_context().fail(str(error))
    click.echo(f"{len(main)} texts included via '{input_filename}'.")

    all_md_filenames = set([str(n) for n in main.filename.parent.glob("*.md")])
    all_md_filenames.discard("README.md")
    all_text_filenames = set([str(t.filename) for t in main])
    if unincluded := list(all_md_filenames.difference(all_text_filenames)):
        click.echo("Files not included:")
        for filename in unincluded:
            click.echo(f"  {filename}")

    compiler = compiler_class(main, refs_dir, paragraph_numbers=paragraph_numbers)
    compiler.preprocess()

    click.echo(f"Footnotes at end of {compiler.footnotes_location}.")
    click.echo(f"{len(compiler.referenced)} references used from '{refs_dirname}'")
    click.echo(f"{len(compiler.indexed)} terms indexed")

    compiler.write(output_filename)

    if paragraph_numbers:
        click.echo(f"{compiler.paragraph_number} paragraphs")
    click.echo(f"Wrote '{output_filename}'.")

    if readme:
        with open("README.md", "w") as outfile:
            outfile.write(main.title + "\n")
            outfile.write("=" * len(main.title) + "\n\n")
            for subtext in main:
                if subtext is main:
                    continue
                outfile.write(" " * 5 * (len(subtext.ordinal) - 1))
                outfile.write(f"{subtext.ordinal[-1]}. {subtext.title}\n")
        click.echo("Wrote 'README.md'.")

    click.echo(f"CPU time: {time.perf_counter() - start_time:.3f}s")


if __name__ == "__main__":
    main()
