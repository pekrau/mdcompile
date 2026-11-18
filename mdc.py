"""Compile Markdown file(s) to DOCX or PDF. With extensions for hierachy,
footnotes, indexed terms and references.
"""

import pathlib
import time

import click
from click_option_group import optgroup, MutuallyExclusiveOptionGroup
import icecream

# For debugging.
icecream.install()

import constants
from docx_compiler import DocxCompiler
from pdf_compiler import PdfCompiler
from epub3_compiler import Epub3Compiler
from text import read_texts, Text


class Timer:
    "CPU timer."

    def __init__(self):
        self.start = time.perf_counter()

    def __str__(self):
        return f"CPU time: {time.perf_counter() - self.start:.3f} seconds."


@click.command()
@click.help_option("--help", "-h")
@click.option(
    "--input_path",
    "-i",
    type=click.Path(exists=True, resolve_path=True, path_type=pathlib.Path),
    default=f"{constants.TEXT_FILENAME}",
    help=f"Markdown file or directory to compile. Default '{constants.TEXT_FILENAME}'.",
)
@click.option(
    "--output_filepath",
    "-o",
    type=click.Path(exists=False, path_type=pathlib.Path),
    default=f"{constants.OUTPUT_FILENAME}",
    help=f"Output file name. The extension depends on the output format. Default '{constants.OUTPUT_FILENAME}'.",
)
@click.option(
    "--readme",
    "-r",
    is_flag=True,
    help=f"Write out a '{constants.README_FILENAME}' file for the compiled file(s).",
)
@optgroup.group(
    "Output formats",
    cls=MutuallyExclusiveOptionGroup,
    help="Formats to compile Markdown into.",
)
@optgroup.option("--docx", "-d", is_flag=True, help="DOCX format (default).")
@optgroup.option("--pdf", "-p", is_flag=True, help="PDF format.")
@optgroup.option("--epub3", "-e", is_flag=True, help="EPUB3 format.")
def cli(input_path, output_filepath, readme, docx, pdf, epub3):
    "Command-line script to compile Markdown file(s)."
    timer = Timer()
    click.echo(f"mdc {constants.__version__}")

    if input_path.is_dir():
        text = read_texts(input_path)
    else:
        text = Text(input_path)

    format = "epub3" if epub3 else "pdf" if pdf else "docx"
    compiler = get_compiler(text, format=format)

    click.echo(f"{len(text)} Markdown files read.")
    click.echo(f"Footnotes at end of {compiler.footnotes_location}.")
    if compiler.library:
        click.echo(f"{len(compiler.referenced)} references from '{compiler.library}'.")

    try:
        filepath = compiler.write(output_filepath)
    except (ValueError, IOError) as error:
        raise click.UsageError(str(error))
    click.echo(f"{len(compiler.indexed)} terms indexed.")

    if compiler.paragraph_number is not None:
        click.echo(f"{compiler.paragraph_number} paragraphs.")
    click.echo(f"Wrote '{filepath}'.")

    if readme:
        filepath = output_filepath.parent / constants.README_FILENAME
        write_readme(filepath, text)
        click.echo(f"Wrote '{filepath}'.")

    click.echo(timer)


def get_compiler(text, format="docx"):
    "Create and return the compiler for the format."
    match format:
        case "pdf":
            compiler = PdfCompiler(text)
        case "epub3":
            compiler = Epub3Compiler(text)
        case "docx":
            compiler = DocxCompiler(text)
        case _:
            raise ValueError(f"unknown format '{format}'")
    return compiler


def write_readme(output_filepath, text):
    "Write out a README.md file for the book."
    with open(output_filepath, "w") as outfile:
        outfile.write(compiler.text.title + "\n")
        outfile.write("=" * len(compiler.text.title) + "\n\n")
        for subtext in compiler.text:
            if subtext is compiler.text:
                continue
            outfile.write(" " * 5 * (len(subtext.ordinal) - 1))
            outfile.write(f"{subtext.ordinal[-1]}. {subtext.title}\n")


if __name__ == "__main__":
    cli()
