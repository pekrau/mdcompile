mdcompile
=========

Compile Markdown file(s) with extensions for hierachy, footnotes, indexed terms
and references to DOCX or PDF.

```
usage: mdc [-h] [-o OUTPUT_FILENAME] [-r REFS_DIRNAME] [-s | -v] [-c] [-p]
           [-R]
           [input_filename]

Compile Markdown file(s) with extensions for hierachy, footnotes, indexed terms
and references to DOCX or PDF.

positional arguments:
  input_filename        Name of Markdown file to compile. Default: 'main.md'.

options:
  -h, --help            show this help message and exit
  -o OUTPUT_FILENAME, --output_filename OUTPUT_FILENAME
                        Name of the output file. Its extension determines the
                        format (docx or pdf). Default: 'main.docx'.
  -r REFS_DIRNAME, --refs_dirname REFS_DIRNAME
                        Directory containing the YAML files for references
                        (articles, books). Default
                        '/home/pekrau/Dropbox/pekrau.github.io/references'
  -s, --silent          Output no execution information.
  -v, --verbose         Output more execution information.
  -c, --comments        Write comments.
  -p, --paragraph-numbers
                        Write consecutive number for each paragraph.
  -R, --README          Write out a 'README.md' file.
```

## Dependencies

- Marko https://marko-py.readthedocs.io/
- PyYAML https://pyyaml.org/
- python-docx https://python-docx.readthedocs.io/
- ReportLab https://www.reportlab.com/
