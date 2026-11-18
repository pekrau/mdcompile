mdcompile
=========

Compile Markdown file(s) to DOCX, PDF and EPUB3. With extensions for
hierarchy, footnotes, indexed terms and references.

```
Usage: mdc.py [OPTIONS]

  Command-line script to compile Markdown file(s).

Options:
  -h, --help                      Show this message and exit.
  -i, --input_path PATH           Markdown file or directory to compile.
                                  Default 'text.md'.
  -o, --output_filepath PATH      Output file name. The extension depends on
                                  the output format. Default 'manuscript'.
  -r, --readme                    Write out a 'README.md' file for the
                                  compiled file(s).
  Output formats: [mutually_exclusive]
                                  Formats to compile Markdown into.
    -d, --docx                    DOCX format (default).
    -p, --pdf                     PDF format.
    -e, --epub3                   EPUB3 format.
```

## Description of inputs

In the simplest case, a Markdown file is specified using the **-i** option.
Only that file will be compiled. It is rendered as an essay, not a book.
It will not contain a table of contents.

If a directory is specified using the **-i** option, its contents will be
compiled into a book. The directory must be organized in a defined fashion:

- The title page file must be called 'text.md'. 
- The Markdown files or subdirectories will be added to the book in lexicographic
  order by their names.
- Each Markdown file and subdirectory on the first level are compiled into
  chapters of the book.
- A subdirectory must contain its own 'text.md' file, which may be empty.
- The subdirectory's Markdown files and subdirectories are compiled into
  sections of the chapters, recursively.

The Markdown files may contain frontmatter in YAML format. The entries may be:
- *title*: The title of the book (if the top 'text.md' file) or title of the chapter
  or section. Default: the name of the file or directory.
- *subtitle*: The subtitle of the book, chapter or section. Default: none.
- *authors*: A list of strings giving the authors of the book or document. No default.
- *language*: Default: 'sv-SE'.
- *identifier*: A unique identifier for the book.
- *footnotes-location*: One of 'book', 'chapter' or 'text' (default), specifying
  where footnote definitions will be written. Default: 'text'
- *reference-title*: Boolean 'true' or 'false': Whether to output the title of a
  reference when given in the text. Default: 'false'
- *paragraph-numbers*: Boolean 'true' or 'false': Whether to output the number of
  each paragraph in the book. Default: 'false'
- *library*: The path to the library directory containing references.
  Default: environment variable LIBRARY_DIR

## Dependencies

- Marko https://marko-py.readthedocs.io/
- PyYAML https://pyyaml.org/
- python-docx https://python-docx.readthedocs.io/
- ReportLab https://www.reportlab.com/
- Click https://click.palletsprojects.com/
