mdcompile
=========

Compile Markdown file(s) with extensions for hierachy, footnotes, indexed terms
and references to DOCX or PDF.

```
Usage: mdc.py [OPTIONS] [INPUT_FILENAME]

Options:
  -h, --help                  Show this message and exit.
  -o, --output_filename TEXT  Name of the output file. Its extension ('.docx'
                              or '.pdf') determines the format. Default:
                              'ms.docx'.
  --refs_dirname DIRECTORY    Path to the directory containing the YAML files
                              for references (articles, books).
  -s, --silent                Output no execution information.
  -v, --verbose               Output more execution information.
  -p, --paragraph_numbers     Write consecutive number for each paragraph.
  -r, --readme                Write out a 'README.md' file.
```

## Dependencies

- Marko https://marko-py.readthedocs.io/
- PyYAML https://pyyaml.org/
- python-docx https://python-docx.readthedocs.io/
- ReportLab https://www.reportlab.com/
- Click https://click.palletsprojects.com/
