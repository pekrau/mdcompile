"Constants."

import re

VERSION = (0, 9, 2)
__version__ = ".".join([str(n) for n in VERSION])

FRONTMATTER = re.compile(r"^---([\n\r].*?[\n\r])---[\n\r](.*)$", re.DOTALL)

EM_DASH = "\u2014"

DATETIME_ISOFORMAT = "%Y-%m-%d %H:%M"

TEXT_FILENAME = "text.md"
OUTPUT_FILENAME = "document"
README_FILENAME = "README.md"

MAX_LEVEL = 6

FOOTNOTES_BOOK = "book"
FOOTNOTES_CHAPTER = "chapter"
FOOTNOTES_TEXT = "text"
FOOTNOTES_LOCATIONS = [FOOTNOTES_BOOK, FOOTNOTES_CHAPTER, FOOTNOTES_TEXT]

STANDARD_CSS = """body {
  font-family: Helvetica, Arial, Verdana, sans-serif;
  background-color: white;
}
blockquote {
  font-family: Garamond, 'Times New Roman', serif;
  margin: 2em;
  padding-left: 1em;
  border-left: 0.5em solid lightgray;
}
mark {
  font-family: 'Courier New', monospace;
  background-color: white;
}
p.codeblock {
  font-family: 'Courier New', monospace;
  margin-left: 3em;
}
a.internal {
  color: darkgreen;
}"""

EXTERNAL_LINKS = dict(
    doi=("DOI", "https://doi.org/{value}"),
    pmid=("PubMed", "https://pubmed.ncbi.nlm.nih.gov/{value}"),
    isbn=("ISBN", "https://isbnsearch.org/isbn/{value}"),
)

DEFAULT_LANGUAGE = "sv"

# Lexicon key: code for language of translation.
# Each dictionary has keys in English and values in the language of translation.
LEXICON = {
    "se": {
        "created": "skapad",
        "last modification": "senast ändrad",
        "contents": "innehåll",
        "references": "referenser",
        "index": "register",
        "footnotes": "fotnoter",
        "accessed": "läst",
        "notes": "anteckningar",
        "title page": "titelsida",
    }
}
# Add capitalized terms.
for language in LEXICON:
    for key, value in list(LEXICON[language].items()):
        LEXICON[language][key.capitalize()] = value.capitalize()
