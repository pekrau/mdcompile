# mdcompile

Compile Markdown files with footnotes, indexed terms and references to
DOCX or PDF book.

```
usage: todocx [-h] [-r REFERENCES] [-l {sv-SE,en-GB,en-US}] [-t TOC_LEVEL]
              [-b PAGE_BREAK_LEVEL] [--no-comments] [-f {book,chapter,text}]
              [-p]
              [infile]

positional arguments:
  infile                Main Markdown file to convert. Default 'main.md'.

options:
  -h, --help            show this help message and exit
  -r REFERENCES, --references REFERENCES
                        Directory containing the references YAML files.
                        Default: Environment variable REFERENCES if defined,
                        else './references'.
  -l {sv-SE,en-GB,en-US}, --language {sv-SE,en-GB,en-US}
                        Language specification. Default 'sv-SE'.
  -t TOC_LEVEL, --toc-level TOC_LEVEL
                        Level for display in Table of contents. Default 1.
  -b PAGE_BREAK_LEVEL, --page-break-level PAGE_BREAK_LEVEL
                        Level at which to break for a new page. Default 1.
  --no-comments         Do not output comments.
  -f {book,chapter,text}, --footnotes-location {book,chapter,text}
                        Location of footnotes. Default 'text'.
  -p, --paragraph-numbers
                        Output consecutive number to each paragraph.
```
