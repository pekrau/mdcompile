mdcompile
=========

Compile Markdown file(s) to DOCX or PDF. With extensions for hierachy,
footnotes, indexed terms and references.

```
Usage: mdc.py [OPTIONS]

  Command-line script to compile Markdown file(s).

Options:
  -h, --help                      Show this message and exit.
  -i, --input_filepath PATH       Input Markdown file to compile. All sibling
                                  directories and files are traversed and
                                  compiled together. Default './text.md'.
  -o, --output_filename PATH      Output file. The extension depends on the
                                  output format. Default 'manuscript'.
  -r, --readme                    Write out a 'README.md' file.
  Output formats: [mutually_exclusive]
                                  Formats to compile Markdown into.
    -d, --docx                    DOCX format (default).
    -p, --pdf                     PDF format.
```

## Dependencies

- Marko https://marko-py.readthedocs.io/
- PyYAML https://pyyaml.org/
- python-docx https://python-docx.readthedocs.io/
- ReportLab https://www.reportlab.com/
- Click https://click.palletsprojects.com/
