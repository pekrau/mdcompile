"Abstract compiler class."

import os

import constants
import library
import utils
from text import Text


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
        # Write out the reference title.
        self.reference_title = fm.get("reference-title", False)
        if fm.get("paragraph-numbers", False):
            self.paragraph_number = 0  # Output paragraph numbers.
        else:
            self.paragraph_number = None  # No paragraph numbers.

        # Book; has subtexts.
        if self.text.subtexts:
            self.footnotes_location = fm.get(
                "footnotes-location", constants.FOOTNOTES_TEXT
            )
        # Essay; one single Markdown source file.
        else:
            self.footnotes_location = constants.FOOTNOTES_TEXT

        # Translator.
        self.tx = Tx(self.text.language)

        # References library
        self.library = library.Library(self.text.frontmatter.get("library"))

        # Collect references in the text(s). Error if any missing.
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

        # Collect indexed terms.
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
                                    f"footnote label collision: {', '.join(labels)}"
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
                                f"footnote label collision: {', '.join(labels)}"
                            )
                        self.text.footnotes.update(text.footnotes)
                        text.footnotes.clear()

    def write(self, output_filepath):
        "Write the contents to a file of the specified format."
        self.write_setup()
        # There are subtexts: a book.
        if self.text.subtexts:
            self.write_title_page()
            self.write_toc()
            for text in self.text.subtexts:
                self.write_text(text)
                self.write_footnotes_chapter(text)
            self.write_footnotes_book()
            self.write_references()
            self.write_indexed()
        # There are no subtexts; an essay.
        else:
            self.write_title_page()
            self.write_references()
            # No index for essay.
        self.write_to_file(output_filepath)

    def write_setup(self):
        "Set up the document for the specified format."
        raise NotImplemented

    def write_title_page(self):
        "Write the title page. If no subtexts, this is all content except references."
        raise NotImplemented

    def write_heading(self, heading, level):
        "Write heading at the specified level."
        raise NotImplemented

    def write_toc(self):
        "Write the table of contents."
        raise NotImplemented

    def write_text(self, text):
        "Write the contents of the text instance."
        self.write_text_setup(text)
        if text.subtitle:
            self.write_heading(text.subtitle, text.level + 1)
        self.render(text.ast, level=text.level + 2)
        self.write_footnotes_text(text)
        for subtext in text.subtexts:
            self.write_text(subtext)

    def write_text_setup(self, text):
        "Set up for the next text. Output the text title. Redefine when required."
        self.write_heading(text.title, text.level)

    def write_footnotes_text(self, text):
        "Write out footnotes for the text, if that mode."
        if not text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_TEXT:
            return
        self.write_heading(
            self.tx("Footnotes"), 4 if text is self.text else text.level + 3
        )
        self.write_footnotes_items(text)

    def write_footnotes_chapter(self, text):
        "Write out footnotes for the chapter, if that mode and any footnotes."
        raise NotImplemented

    def write_footnotes_book(self):
        "Write out footnotes for the book, if that mode, and any footnotes."
        raise NotImplemented

    def write_footnotes_items(self, text):
        "Write the footnotes in the given text."
        for footnote in sorted(text.footnotes.values(), key=lambda f: f["number"]):
            self.footnote_def_flag = footnote["number"]
            for child in footnote["children"]:
                self.render(child)
            self.footnote_def_flag = None

    def write_references(self):
        "Write the references section, if any references."
        raise NotImplementedError

    def write_indexed(self):
        "Write the index section, if any indexed terms. Only for book."
        raise NotImplementedError

    def write_to_file(output_filepath):
        raise NotImplementedError

    def render(self, ast, level=None):
        """Render the Markdown text AST node hierarchy.
        If level is not None, then initialize render at the given level.
        """
        if level is not None:
            self.level = level
            # None: not in footnote; -1: footnote started; >= 1: footnote number to start
            self.footnote_def_flag = None
        try:
            method = getattr(self, f"render_{ast['element']}")
        except AttributeError:
            raise KeyError(f"renderer could not handle ast {ast}")
        method(ast)

    def render_document(self, ast):
        "Render the contents of the text."
        raise NotImplementedError

    def render_heading(self, ast):
        "Heading in the text."
        raise NotImplementedError

    def render_paragraph(self, ast):
        "A paragraph in the text."
        raise NotImplementedError

    def render_raw_text(self, ast):
        "Render simple text content."
        raise NotImplementedError

    def render_blank_line(self, ast):
        "Render a simple blank line."
        pass

    def render_quote(self, ast):
        "Render a quote block."
        raise NotImplementedError

    def render_code_span(self, ast):
        "Render a stretch of code."
        raise NotImplementedError

    def render_code_block(self, ast):
        "Render a block of code."
        raise NotImplementedError

    def render_fenced_code(self, ast):
        "Render a fenced block of code."
        raise NotImplementedError

    def render_image(self, ast):
        "Render an image."
        raise NotImplementedError

    def render_emphasis(self, ast):
        "Render emphasis, i.e. italic text."
        raise NotImplementedError

    def render_strong_emphasis(self, ast):
        "Render strong emphasis, i.e. bold text."
        raise NotImplementedError

    def render_subscript(self, ast):
        "Render subscript."
        raise NotImplementedError

    def render_superscript(self, ast):
        "Render superscript."
        raise NotImplementedError

    def render_emdash(self, ast):
        "Render and em-dash character."
        raise NotImplementedError

    def render_line_break(self, ast):
        "Render a line break."
        raise NotImplementedError

    def render_thematic_break(self, ast):
        "Render a thematic break, i.e. a horizontal line."
        raise NotImplementedError

    def render_link(self, ast):
        "Render a link to a URL."
        raise NotImplementedError

    def render_list(self, ast):
        "Render a list, ordered or unordered."
        raise NotImplementedError

    def render_list_item(self, ast):
        "Render an item in  list."
        raise NotImplementedError

    def render_indexed(self, ast):
        "Render an indexed word or phrase."
        raise NotImplementedError

    def render_footnote_ref(self, ast):
        "Render a reference to a footnote."
        raise NotImplementedError

    def render_footnote_def(self, ast):
        "Footnote definition handled separately; this element is to be ignored."
        pass

    def render_reference(self, ast):
        "Render a reference."
        raise NotImplementedError
