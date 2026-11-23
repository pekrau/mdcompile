mdcompile
=========

Compile Markdown file(s) to DOCX, PDF, EPUB3 and HTML. With extensions
for hierarchy, footnotes, indexed terms and references.

```
Usage: mdcompile.py [OPTIONS] [INPUTPATH] [OUTPUTPATH]

  Command-line script to compile Markdown file(s).

Positional arguments:
  [INPUTPATH]   Directory or Markdown file to compile. If directory, assumes
                the existence of the file 'text.md' in it.
  [OUTPUTPATH]  Output file path (optional). Computed from INPUTPATH if not
                given. The file extension, if given, determines the output
                format.

Options:
  -h, --help                      Show this message and exit.

  Output formats: [mutually_exclusive]
                                  Formats to compile Markdown into. Overridden
                                  by an explicit extension in OUTPUTPATH.
    -D, --docx                    DOCX format (default).
    -P, --pdf                     PDF format.
    -E, --epub3                   EPUB3 format.
    -H, --html                    HTML format.
    -R, --readme                  Write out a 'README.md' file with a table of
                                  contents.
```

## Description of inputs

The input path may be a file or a directory, which must exist.

If the input path is a file, it will be the only file to be compiled.
The extension of the path determines the format, overriding any format
option provided.  A document is prepared from a single Markdown file
will have no table of contents.

If the input path is a directory, all Markdown files and subdirectories within
it will be compiled. The directory structure must be as follows:

- The top directory and all its subdirectories must contain a 'text.md' file,
  which may be empty.

- Each Markdown file and subdirectory on the first level are compiled into
  chapters of the document.

- The subdirectory's Markdown files and its subdirectories are compiled into
  sections of the chapter, recursively.

- The Markdown files and/or subdirectories in the each directory will be added
  to the document in lexicographic order by their names.

The Markdown files may contain frontmatter in YAML dictionary format.
The following entries are effective in all Markdown files:

- *title*: The title of the document (if the top 'text.md' file) or
  title of the chapter or section. Default: the name of the file or
  directory.

- *subtitle*: The subtitle of the document, chapter or section. Default: none.

- *include*: List of all names of files and subdirectorites that are
  to be included as subsections. The order is significant.

- *exclude*: A list of the names of files in the same directory that are to
  be ignored.

The following frontmatter entries are effective only when provided in the top
Markdown file for a document:

- *authors*: A list of strings giving the authors of the document or
   document. No default.

- *language*: Default: 'sv'.

- *identifier*: A unique identifier for the document.

- *footnotes-location*: One of 'document', 'chapter' or 'text', specifying
  where footnote definitions will be written. Default: 'text'

- *reference-title*: Boolean 'true' or 'false': Whether to output the title of a
  reference when given in the text. Default: 'false'

- *paragraph-numbers*: Boolean 'true' or 'false': Whether to output
  the number of each paragraph in the document. Default: 'false'

- *library*: The path to the library directory containing references.
  Default: environment variable LIBRARY_DIR

- *description*: Description. Default: none.

- *subject*: Subject description, keywords. Default: none.

- *publisher*: Publisher. Default: none.

- *rights*: Copyright notice or similar. Default: none.


## Software

This code has been lovingly hand-crafted. No AI tools were used in its development.

Written in Python https://www.python.org/ using:

- Marko https://marko-py.readthedocs.io/
- PyYAML https://pyyaml.org/
- python-docx https://python-docx.readthedocs.io/
- ReportLab https://www.reportlab.com/
- Click https://click.palletsprojects.com/

