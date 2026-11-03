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
from text import read_texts


class Timer:
    "CPU timer."

    def __init__(self):
        self.start = time.perf_counter()

    def __str__(self):
        return f"CPU time: {time.perf_counter() - self.start:.3f} seconds."


@click.command()
@click.help_option("--help", "-h")
@click.option(
    "--input_filepath",
    "-i",
    type=click.Path(exists=True, resolve_path=True, path_type=pathlib.Path),
    default=f"./{constants.TEXT_FILENAME}",
    help=f"Input Markdown file to compile. All sibling directories and files are traversed and compiled together. Default './{constants.TEXT_FILENAME}'.",
)
@click.option(
    "--output_filename",
    "-o",
    type=click.Path(exists=False, path_type=pathlib.Path),
    default=constants.OUTPUT_FILENAME,
    help=F"Output file. The extension depends on the output format. Default '{constants.OUTPUT_FILENAME}'.",
)
@click.option("--readme", "-r", is_flag=True, help="Write out a 'README.md' file.")
@optgroup.group(
    "Output formats",
    cls=MutuallyExclusiveOptionGroup,
    help="Formats to compile Markdown into.",
)
@optgroup.option(
    "--docx", "-d", is_flag=True, default=True, help="DOCX format (default)."
)
@optgroup.option("--pdf", "-p", is_flag=True, help="PDF format.")
def main(input_filepath, output_filename, readme, docx, pdf):
    "Command-line script to compile Markdown file(s)."
    timer = Timer()
    click.echo(f"mdc {constants.__version__}")

    if input_filepath.is_dir():
        directory = input_filepath
        text_filename = constants.TEXT_FILENAME
    else:
        directory = input_filepath.parent
        text_filename = input_filepath.name

    try:
        text = read_texts(directory, text_filename)
    except FileNotFoundError as error:
        raise click.UsageError(str(error))

    try:
        if pdf:
            compiler = PdfCompiler(text)
            output_filename = output_filename.with_suffix(".pdf")
        elif docx:
            compiler = DocxCompiler(text)
            output_filename = output_filename.with_suffix(".docx")
    except (ValueError, IOError) as error:
        raise click.UsageError(str(error))

    click.echo(f"{len(text)} Markdown files read.")
    click.echo(f"Footnotes at end of {compiler.footnotes_location}.")
    click.echo(
        f"{len(compiler.referenced)} references from library '{compiler.library}'."
    )
    click.echo(f"{len(compiler.indexed)} terms indexed.")

    output_filepath = directory / output_filename
    compiler.write(output_filepath)
    if compiler.paragraph_number is not None:
        click.echo(f"{compiler.paragraph_number} paragraphs.")
    click.echo(f"Wrote '{output_filepath}'.")

    if readme:
        output_filepath = directory / constants.README_FILENAME
        with open(output_filepath, "w") as outfile:
            outfile.write(compiler.text.title + "\n")
            outfile.write("=" * len(compiler.text.title) + "\n\n")
            for subtext in compiler.text:
                if subtext is compiler.text:
                    continue
                outfile.write(" " * 5 * (len(subtext.ordinal) - 1))
                outfile.write(f"{subtext.ordinal[-1]}. {subtext.title}\n")
        click.echo(f"Wrote '{output_filepath}'.")

    click.echo(timer)


if __name__ == "__main__":
    main()
