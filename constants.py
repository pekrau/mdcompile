"Constants."

import string

VERSION = (0, 2, 0)
__version__ = ".".join([str(n) for n in VERSION])

EM_DASH = "\u2014"

SAFE_CHARACTERS = set(string.ascii_letters + string.digits)

DATETIME_ISOFORMAT = "%Y-%m-%d %H:%M"

MAX_LEVEL = 6

NORMAL = "normal"
ITALIC = "italic"
BOLD = "bold"
UNDERLINE = "underline"

FOOTNOTES_BOOK = "book"
FOOTNOTES_CHAPTER = "chapter"
FOOTNOTES_TEXT = "text"
FOOTNOTES_LOCATIONS = [FOOTNOTES_BOOK, FOOTNOTES_CHAPTER, FOOTNOTES_TEXT]

REFS_LINKS = dict(
    doi=("DOI", "https://doi.org/{value}"),
    pmid=("PubMed", "https://pubmed.ncbi.nlm.nih.gov/{value}"),
    isbn=("ISBN", "https://isbnsearch.org/isbn/{value}"),
)

DOCX_MAX_PAGE_BREAK_LEVEL = 4
DOCX_MAX_TOC_LEVEL = 4
DOCX_TOC_INDENT = 15
DOCX_TOC_SPACE_BEFORE = 0
DOCX_TOC_SPACE_AFTER = 0
DOCX_NORMAL_FONT = "Arial"
DOCX_FONT_SIZES = [28, 22, 19, 16, 14, 13, 12]
DOCX_NORMAL_FONT_SIZE = 12
DOCX_NORMAL_LINE_SPACING = 17
DOCX_QUOTE_INDENT = 16
DOCX_CODE_FONT = "Courier"
DOCX_CODE_FONT_SIZE = 11
DOCX_CODE_LINE_SPACING = 12
DOCX_CODE_INDENT = 10
DOCX_FOOTER_FONT_SIZE = 10
DOCX_FOOTNOTE_INDENT = 15
DOCX_CAPTION_INDENT = 15
DOCX_REFERENCE_INDENT = 10
DOCX_METADATA_SPACER = 80
DOCX_INDEXED_INDENT = 15
DOCX_INDEXED_SPACE_AFTER = 8
DOCX_DEFAULT_IMAGE_SCALE_FACTOR = 0.6
DOCX_DEFAULT_PNG_RENDERING_FACTOR = 2.0

SV_SE = "sv-SE"
EN_GB = "en-GB"
EN_US = "en-US"
LANGUAGES = [SV_SE, EN_GB, EN_US]

LEXICON = {
    SV_SE: {  # Key: 'en-GB' term; value: 'sv-SE' term.
        "created": "skapad",
        "latest modification": "senast ändrad",
        "contents": "innehåll",
        "references": "referenser",
        "index": "register",
        "footnotes": "fotnoter",
    }
}
for k, v in list(LEXICON[SV_SE].items()):  # 'list': Avoid update collision issues.
    if k.lower() == k:  # If not lower-case, then explicit case.
        LEXICON[SV_SE][k.capitalize()] = v.capitalize()
