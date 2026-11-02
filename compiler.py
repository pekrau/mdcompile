"Abstract compiler class."

import os

import constants
import library
from text import Text
import utils


class Tx:
    "Translate fixed terms in the code."

    def __init__(self, language):
        self.language = language

    def __call__(self, term):
        try:
            return constants.LEXICON[self.language][term]
        except KeyError:
            return term


class Compiler:
    "Abstract compiler class; to be inherited and elaborated."

    def __init__(self, text):
        assert isinstance(text, Text)
        self.text = text

        # Get output parameters from text frontmatter.
        fm = self.text.frontmatter
        self.indexed_underlined = fm.get("indexed-underlined", True)
        self.reference_bold = fm.get("reference-bold", True)
        self.reference_title = fm.get("reference-title", False)
        self.reference_title_italic = fm.get("reference-title-italic", True)
        if fm.get("paragraph_numbers", False):
            self.paragraph_number = 0
        else:
            self.paragraph_number = None

        # Book with subtexts.
        if self.text.subtexts:
            self.toc_level = max(0, fm.get("toc-level", 1))
            self.page_break_level = max(0, fm.get("page-break-level", 1))
            self.text_number_level = max(0, fm.get("text-number-level", 1))
            self.footnotes_location = fm.get(
                "footnotes-location", constants.FOOTNOTES_TEXT
            )

        # Essay being one single Markdown source file.
        else:
            self.toc_level = 0
            self.footnotes_location = constants.FOOTNOTES_TEXT

        # Translator.
        self.tx = Tx(self.text.language)

        # References library
        self.library = library.Library(self.text.frontmatter.get("library"))

    def preprocess(self):
        "Collect references, indexes, footnotes and internal links."
        self.referenced = {}
        missing = set()
        for text in self.text:
            for element in text.elements():
                if element["element"] != "reference":
                    continue
                name = element["name"]
                if name not in self.referenced:
                    try:
                        self.referenced[name] = self.library[name]
                    except KeyError:
                        missing.add(name)
        if missing:
            raise ValueError(f"Missing references: {', '.join(sorted(missing))}")

        self.indexed = {}
        for text in self.text:
            for element in text.elements():
                if element["element"] == "indexed":
                    self.indexed.setdefault(element["canonical"], []).append(text)

        # Transfer footnotes to the appropriate texts, and number them.
        match self.footnotes_location:
            case constants.FOOTNOTES_TEXT:
                for text in self.text:
                    number = 0
                    for element in text.elements():
                        if element["element"] == "footnote_ref":
                            element["number"] = str(number := number + 1)
                            text.footnotes[element["label"]]["number"] = number
            case constants.FOOTNOTES_CHAPTER:
                for chapter in self.text.subtexts:
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
                for text in self.text:
                    for element in text.elements():
                        if element["element"] == "footnote_ref":
                            element["number"] = str(number := number + 1)
                            text.footnotes[element["label"]]["number"] = number
                    if text is not self.text:
                        labels = set(self.text.footnotes.keys()).intersection(
                            text.footnotes.keys()
                        )
                        if labels:
                            raise ValueError(
                                f"footnote labels collision: {', '.join(labels)}"
                            )
                        self.text.footnotes.update(text.footnotes)
                        text.footnotes.clear()

        self.section_titles = {}
        for text in self.text:
            if text is self.text:
                continue
            key = text.title.casefold().replace(" ", "_")
            if key in self.section_titles:
                raise ValueError(f"multiple uses of title '{text.title}'")
            self.section_titles[key] = text.ordinal_title

        for text in self.text:
            for element in text.elements():
                if element["element"] == "internal_link":
                    target = element["target"].casefold().replace(" ", "_")
                    try:
                        element["section"] = self.section_titles[target]
                    except KeyError:
                        for key, title in self.section_titles.items():
                            if key.startswith(target):
                                element["section"] = title
                                break

    def write(self, filename=None):
        "Convert the main text and its subtexts, if any, into the format."
        raise NotImplementedError

    def text_render(self, text):
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
            raise KeyError(f"renderer could not handle ast {ast}")
        method(ast)
