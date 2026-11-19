"Constants."

import re

VERSION = (0, 9, 1)
__version__ = ".".join([str(n) for n in VERSION])

FRONTMATTER = re.compile(r"^---([\n\r].*?[\n\r])---[\n\r](.*)$", re.DOTALL)

EM_DASH = "\u2014"

DATETIME_ISOFORMAT = "%Y-%m-%d %H:%M"

TEXT_FILENAME = "text.md"
OUTPUT_FILENAME = "document"
README_FILENAME = "README.md"
CSS_FILENAME = "pico.min.css"
CSS_URL = "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"

MAX_LEVEL = 6

FOOTNOTES_BOOK = "book"
FOOTNOTES_CHAPTER = "chapter"
FOOTNOTES_TEXT = "text"
FOOTNOTES_LOCATIONS = [FOOTNOTES_BOOK, FOOTNOTES_CHAPTER, FOOTNOTES_TEXT]

EXTERNAL_LINKS = dict(
    doi=("DOI", "https://doi.org/{value}"),
    pmid=("PubMed", "https://pubmed.ncbi.nlm.nih.gov/{value}"),
    isbn=("ISBN", "https://isbnsearch.org/isbn/{value}"),
)

SV_SE = "sv-SE"

LEXICON = {
    SV_SE: {  # Key: 'en-GB' term; value: 'sv-SE' term.
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
for k, v in list(LEXICON[SV_SE].items()):  # 'list': Avoid update collision issues.
    # Add capitalized variants.
    LEXICON[SV_SE][k.capitalize()] = v.capitalize()
