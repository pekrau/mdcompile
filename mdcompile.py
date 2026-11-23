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
from html_compiler import HtmlCompiler
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
    "--readme",
    "-r",
    is_flag=True,
    help=f"Also write out a '{constants.README_FILENAME}' file for the compiled file(s).",
)
@optgroup.group(
    "Output formats",
    cls=MutuallyExclusiveOptionGroup,
    help="Formats to compile Markdown into. Overridden by an explicit extension in OUTPUTPATH.",
)
@optgroup.option("--docx", "-D", is_flag=True, help="DOCX format (default).")
@optgroup.option("--pdf", "-P", is_flag=True, help="PDF format.")
@optgroup.option("--epub3", "-E", is_flag=True, help="EPUB3 format.")
@optgroup.option("--html", "-H", is_flag=True, help="HTML format.")
@click.argument(
    "inputpath",
    default=None,
    type=click.Path(exists=True, resolve_path=True, path_type=pathlib.Path),
    help=f"Directory or Markdown file to compile. If directory, assumes the existence of the file '{constants.TEXT_FILENAME}' in it.",
)
@click.argument(
    "outputpath",
    default=None,
    type=click.Path(exists=False, path_type=pathlib.Path),
    help="Output file path (optional). Computed from INPUTPATH if not given. The file extension, if given, determines the output format.",
)
def cli(inputpath, outputpath, readme, docx, pdf, epub3, html):
    "Command-line script to compile Markdown file(s)."
    timer = Timer()
    click.echo(f"mdc {constants.__version__}")

    if not inputpath:
        raise click.UsageError("no inputpath given")
    elif inputpath.is_dir():
        text = read_texts(inputpath)
    else:
        text = Text(inputpath)

    format = "html" if html else "epub3" if epub3 else "pdf" if pdf else "docx"
    if outputpath:
        if extension := outputpath.suffix.lower():
            format = extension.lstrip(".")
            if format == "epub":
                format = "epub3"
    extension = f".{format}"
    try:
        compiler = get_compiler(text, format=format)
    except ValueError as error:
        raise click.UsageError(str(error))

    click.echo(f"{len(text)} Markdown files read.")
    if compiler.reflib:
        click.echo(f"{len(compiler.referenced)} references from '{compiler.reflib}'.")
    else:
        click.echo("No reflib defined; no references output.")

    if inputpath.is_dir():
        if outputpath is None:
            outputpath = inputpath / constants.OUTPUT_FILENAME
        elif outputpath.is_dir():
            outputpath = outputpath / constants.OUTPUT_FILENAME
    elif outputpath is None:
        outputpath = inputpath.with_suffix(extension)

    try:
        filepath = compiler.write(outputpath.with_suffix(extension))
    except (ValueError, IOError) as error:
        raise click.UsageError(str(error))
    if compiler.index_terms is None:
        click.echo("No indexing was done.")
    else:
        click.echo(f"{len(compiler.index_terms)} terms indexed.")

    if compiler.paragraph_number is not None:
        click.echo(f"{compiler.paragraph_number} paragraphs.")
    click.echo(f"Wrote '{filepath}'.")

    if readme:
        filepath = outputpath.parent / constants.README_FILENAME
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
        case "html":
            compiler = HtmlCompiler(text)
        case "docx":
            compiler = DocxCompiler(text)
        case _:
            raise ValueError(f"unknown format '{format}'")
    return compiler


def write_readme(outputpath, text):
    "Write out a README.md file for the book."
    with open(outputpath, "w") as outfile:
        outfile.write(compiler.text.title + "\n")
        outfile.write("=" * len(compiler.text.title) + "\n\n")
        for subtext in compiler.text:
            if subtext is compiler.text:
                continue
            outfile.write(" " * 5 * (len(subtext.ordinal) - 1))
            outfile.write(f"{subtext.ordinal[-1]}. {subtext.title}\n")


if __name__ == "__main__":
    cli()
