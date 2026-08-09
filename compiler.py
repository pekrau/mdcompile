"Abstract compiler class."

import constants
from text import Text
import utils


class Compiler:
    "Abstract compiler class; to be inherited."

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

        # Output parameters from main text frontmatter.
        fm = self.main.frontmatter
        self.language = fm.get("language", constants.SV_SE)
        self.tx = utils.Tx(self.language)
        self.toc_level = fm.get("toc-level", 1)
        self.page_break_level = fm.get("page-break-level", 1)
        self.section_number_level = fm.get("text-number-level", 1)
        self.footnotes_location = fm.get("footnotes-location", constants.FOOTNOTES_TEXT)

    def preprocess(self):
        "Set up references, indexes and footnotes."
        # Collect references.
        self.referenced = {}
        for text in self.main:
            for element in text.elements():
                if element["element"] != "reference":
                    continue
                if element["name"] not in self.referenced:
                    self.referenced[element["name"]] = self.refs_dir[element["name"]]

        # Collect indexed terms.
        self.indexed = {}
        for text in self.main:
            for element in text.elements():
                if element["element"] != "indexed":
                    continue
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

    def write(self, filename=None):
        "Convert the main text and its subtexts, if any, into the format."
        raise NotImplementedError

    
