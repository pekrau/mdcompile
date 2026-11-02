mdcompile
=========

Compile Markdown file(s) with extensions for hierachy, footnotes, indexed terms
and references to DOCX or PDF.

## DOCX

```
Usage: todocx.py [OPTIONS] [DIRECTORY]

  Compile Markdown file(s) with footnotes, indexed terms and references to
  DOCX.

Options:
  -h, --help    Show this message and exit.
  -r, --readme  Write out a 'README.md' file.
```

## PDF

```
Usage: topdf.py [OPTIONS] [DIRECTORY]

  Compile Markdown file(s) with footnotes, indexed terms and references to
  PDF.

Options:
  -h, --help    Show this message and exit.
  -r, --readme  Write out a 'README.md' file.
```

## Dependencies

- Marko https://marko-py.readthedocs.io/
- PyYAML https://pyyaml.org/
- python-docx https://python-docx.readthedocs.io/
- ReportLab https://www.reportlab.com/
- Click https://click.palletsprojects.com/
