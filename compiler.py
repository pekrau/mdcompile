"Abstract compiler and renderer classes."

import constants
from text import Text
import utils


class Compiler:
    "Abstract compiler class; to be inherited and elaborated."

    def __init__(self, text, refs_dir, paragraph_numbers=False, silent=False):
        assert isinstance(text, Text)

        self.main = text
        self.refs_dir = refs_dir

        # Output parameters from arguments.
        if paragraph_numbers:
            self.paragraph_number = 0
        else:
            self.paragraph_number = None
        self.silent = silent

        # Translator.
        self.tx = utils.Tx(self.main.language)

        # Output parameters from main text frontmatter.
        fm = self.main.frontmatter
        self.toc_level = max(0, fm.get("toc-level", 1))
        self.page_break_level = max(0, fm.get("page-break-level", 1))
        self.text_number_level = max(0, fm.get("text-number-level", 1))
        self.underline_indexed = fm.get("underline-indexed", True)
        self.footnotes_location = fm.get("footnotes-location", constants.FOOTNOTES_TEXT)

    def preprocess(self):
        "Collect references, indexes, footnotes and internal links."
        self.referenced = {}
        for text in self.main:
            for element in text.elements():
                if element["element"] == "reference":
                    if element["name"] not in self.referenced:
                        self.referenced[element["name"]] = self.refs_dir[
                            element["name"]
                        ]

        self.indexed = {}
        for text in self.main:
            for element in text.elements():
                if element["element"] == "indexed":
                    self.indexed.setdefault(element["canonical"], []).append(text)

        # Transfer footnotes to the appropriate texts, and number them.
        match self.footnotes_location:
            case constants.FOOTNOTES_TEXT:
                for text in self.main:
                    number = 0
                    for element in text.elements():
                        if element["element"] == "footnote_ref":
                            element["number"] = str(number := number + 1)
                            text.footnotes[element["label"]]["number"] = number
            case constants.FOOTNOTES_CHAPTER:
                for chapter in self.main.subtexts:
                    number = 0
                    for text in chapter:
                        for element in text.elements():
                            if element["element"] == "footnote_ref":
                                element["number"] = str(number := number + 1)
                                text.footnotes[element["label"]]["number"] = number
                        if text is not chapter:
                            labels = set(chapter.footnotes.keys()).intersection(
                                text.footnotes.keys()
                            )
                            if labels:
                                raise ValueError(
                                    f"footnote labels collision: {', '.join(labels)}"
                                )
                            chapter.footnotes.update(text.footnotes)
                            text.footnotes.clear()
            case constants.FOOTNOTES_BOOK:
                number = 0
                for text in self.main:
                    for element in text.elements():
                        if element["element"] == "footnote_ref":
                            element["number"] = str(number := number + 1)
                            text.footnotes[element["label"]]["number"] = number
                    if text is not self.main:
                        labels = set(self.main.footnotes.keys()).intersection(
                            text.footnotes.keys()
                        )
                        if labels:
                            raise ValueError(
                                f"footnote labels collision: {', '.join(labels)}"
                            )
                        self.main.footnotes.update(text.footnotes)
                        text.footnotes.clear()

        self.internal_anchors = {}
        for text in self.main:
            for element in text.elements():
                if element["element"] == "internal_anchor":
                    if element["anchor"] in self.internal_anchors:
                        raise ValueError(
                            f"multiple uses of internal anchor {element.anchor}"
                        )
                    self.internal_anchors[element["anchor"]] = text.ordinal_title
        for text in self.main:
            for element in text.elements():
                if element["element"] == "internal_link":
                    try:
                        element["location"] = self.internal_anchors[element["anchor"]]
                    except KeyError:
                        element["location"] = "unknown anchor"

    def numbered_title(self, text, force=False):
        "Return the title with a number prefix."
        if text.level <= self.text_number_level or force:
            return f"{'.'.join([str(i) for i in text.ordinal])}. {text.title}"
        else:
            return text.title

    def write(self, filename=None):
        "Convert the main text and its subtexts, if any, into the format."
        raise NotImplementedError

    def text_render(self, text=None):
        self.current_text = text
        # 0: not in footnote; -1: footnote started; >= 1: footnote number to start
        self.footnote_def_flag = 0
        self.list_stack = []
        self.style_stack = ["Normal"]
        self.bold = False
        self.italic = False
        self.subscript = False
        self.superscript = False
        self.render(text.ast)

    def render(self, ast):
        "Render the Markdown text AST node hierarchy."
        try:
            method = getattr(self, f"render_{ast['element']}")
        except AttributeError:
            print(f"renderer could not handle ast {ast}")
        else:
            method(ast)
