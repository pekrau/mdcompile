mdcompile
=========

Compile Markdown file(s) with extensions for hierachy, footnotes, indexed terms
and references to DOCX or PDF.

```
Usage: mdcompile.py [OPTIONS] [INPUT_FILENAME]

Options:
  -h, --help                  Show this message and exit.
  -o, --output_filename TEXT  Name of the output file. Its extension ('.docx'
                              or '.pdf') determines the format. Default:
                              'ms.docx'.
  -r, --readme                Write out a 'README.md' file.
```

## Dependencies

- Marko https://marko-py.readthedocs.io/
- PyYAML https://pyyaml.org/
- python-docx https://python-docx.readthedocs.io/
- ReportLab https://www.reportlab.com/
- Click https://click.palletsprojects.com/
