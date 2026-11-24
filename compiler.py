"Abstract compiler class."

import os
import pathlib

import constants
import text
import utils


class Compiler:
    "Abstract compiler class; to be inherited and elaborated."

    def __init__(self, text):
        self.text = text

        # Get output parameters from text frontmatter.
        fm = self.text.frontmatter
        # Write out the reference title.
        self.reference_title = fm.get("reference-title", False)
        # Write paragraph numbers.
        if fm.get("paragraph-numbers", False):
            self.paragraph_number = 0  # Paragraph numbers.
        else:
            self.paragraph_number = None  # No paragraph numbers.

        # Book; has subtexts.
        if self.text.subtexts:
            self.footnotes_location = fm.get(
                "footnotes-location", constants.FOOTNOTES_TEXT
            )
            self.reference_usage = fm.get("reference-usage", True)
        # Essay; one single Markdown source file.
        else:
            self.footnotes_location = constants.FOOTNOTES_TEXT
            self.reference_usage = False

        # Translator.
        self.tx = Tx(self.text.language)

        # References library. Collect references in the text(s). Error if any missing.
        self.referenced = {}
        if not (path := self.text.frontmatter.get("reflib")):
            path = os.environ.get("REFLIB_DIR")
        if path:
            self.reflib = RefLib(path)
            missing = set()
            for text in self.text:
                for element in text.elements("reference"):
                    name = element["name"]
                    try:
                        reference = self.reflib[name]
                    except KeyError:
                        missing.add(name)
                    else:
                        # Ignore multiple use of the same reference in a text.
                        texts = reference.setdefault("texts", [])
                        if text in texts:
                            element["multiple"] = True
                        else:
                            texts.append(text)
                        self.referenced[name] = reference
            if missing:
                raise ValueError(f"Missing references: {', '.join(sorted(missing))}")
        else:
            self.reflib = None

        # Collect index terms.
        if self.text.subtexts:
            self.index_terms = {}
            for text in self.text:
                for element in text.elements("indexed"):
                    texts = self.index_terms.setdefault(element["canonical"], [])
                    # Ignore multiple indexing of the same term in a text.
                    if text in texts:
                        element["multiple"] = True
                    else:
                        texts.append(text)
        else:  # No index for essay.
            self.index_terms = None
        # Transfer footnotes to the appropriate texts, and number them.
        match self.footnotes_location:
            case constants.FOOTNOTES_TEXT:
                for text in self.text:
                    number = 0
                    for element in text.elements("footnote_ref"):
                        element["number"] = str(number := number + 1)
                        element["text"] = text
                        identifier = f"{text.identifier}-footnote-{number}"
                        element["identifier"] = identifier
                        footnote = text.footnotes[element["label"]]
                        footnote["number"] = number
                        footnote["identifier"] = identifier
            case constants.FOOTNOTES_CHAPTER:
                for chapter in self.text.subtexts:
                    number = 0
                    for text in chapter:
                        for element in text.elements("footnote_ref"):
                            element["number"] = str(number := number + 1)
                            element["text"] = chapter
                            identifier = f"{chapter.identifier}-footnote-{number}"
                            element["identifier"] = identifier
                            footnote = text.footnotes[element["label"]]
                            footnote["number"] = number
                            footnote["identifier"] = identifier
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
                    for element in text.elements("footnote_ref"):
                        element["number"] = str(number := number + 1)
                        element["text"] = self.text
                        identifier = f"{self.text.identifier}-footnote-{number}"
                        element["identifier"] = identifier
                        footnote = text.footnotes[element["label"]]
                        footnote["number"] = number
                        footnote["identifier"] = identifier
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
        """Write the contents to a file.
        Return the filepath actually used.
        """
        self.write_initialize(pathlib.Path(output_filepath))

        if self.text.subtexts:  # There are subtexts: a book.
            self.within_footnote = None
            self.write_title_page()
            self.write_toc()
            for text in self.text.subtexts:  # Write out chapter-wise.
                self.write_text(text)
                self.write_footnotes_chapter(text)
            self.write_footnotes_book()
            if self.referenced:
                self.write_references()
            if self.index_terms:
                self.write_index()

        else:  # There are no subtexts; an essay.
            self.write_title_page()
            if self.referenced:
                self.write_references()
            # No index for essay.

        self.write_finalize()
        return self.output_filepath

    def write_initialize(self, output_filepath):
        "Set up the output document."
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
        self.within_footnote = None
        self.write_text_initialize(text)
        self.write_heading(text.ordinal_title, text.level)
        if text.subtitle:
            self.write_heading(text.subtitle, text.level + 1)
        self.render(text.ast, level=text.level + 2)
        self.write_footnotes_text(text)
        self.write_text_finalize(text)
        for subtext in text.subtexts:
            self.write_text(subtext)

    def write_text_initialize(self, text):
        "Set up for the next text. To be redefined."
        pass

    def write_text_finalize(self, text):
        "Wrap up for this text. To be redefined."
        pass

    def write_footnotes_text(self, text):
        "Write out footnotes for the text, if that mode."
        if not text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_TEXT:
            return
        self.write_heading(
            self.tx("Footnotes"), 3 if text is self.text else text.level + 3
        )
        self.write_footnotes(text)

    def write_footnotes_chapter(self, text):
        "Write out footnotes for the chapter, if that mode and any footnotes."
        raise NotImplemented

    def write_footnotes_book(self):
        "Write out footnotes for the book, if that mode and any footnotes."
        raise NotImplemented

    def write_footnotes(self, text):
        "Write the footnotes in the given text."
        for footnote in sorted(text.footnotes.values(), key=lambda f: f["number"]):
            footnote["text"] = text
            self.render(footnote)

    def write_references(self):
        "Write the references section, if any references."
        raise NotImplementedError

    def write_index(self):
        "Write the index section. Only for book."
        raise NotImplementedError

    def write_finalize(self):
        "Finalize the document and write to file. Return the filepath actually used."
        raise NotImplementedError

    def render(self, ast, level=None):
        """Render the Markdown text AST node hierarchy.
        If level is not None, then initialize render at the given level.
        """
        if level is not None:
            self.level = level
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
        "Render a fenced block of code. Simply calls 'render_code_block'."
        self.render_code_block(ast)

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
        "Render a footnote definition. Save the AST element for paragraph creation."
        if not "number" in ast:  # Skip on first pass, when within text.
            return
        self.within_footnote = ast
        for child in ast["children"]:
            self.render(child)
        self.within_footnote = None

    def render_reference(self, ast):
        "Render a reference."
        raise NotImplementedError


class Tx:
    "Translate fixed terms in the code."

    def __init__(self, language):
        self.language = language

    def __call__(self, term):
        try:
            return constants.LEXICON[self.language][term]
        except KeyError:
            return term


class RefLib:
    "Access reflib files."

    def __init__(self, dirpath):
        if not dirpath:
            raise ValueError("no dirpath provided")
        dirpath = pathlib.Path(dirpath)
        if not dirpath.exists():
            raise IOError(f"no such reflib directory: {dirpath}")
        if not dirpath.is_dir():
            raise IOError(f"reflib path is not a directory: {dirpath}")
        self.dirpath = dirpath

    def __str__(self):
        return str(self.dirpath)

    def __getitem__(self, name):
        "Return the reference as a dictionary, given the name 'Lastname year'."
        filepath = self.dirpath / f"{utils.safe(name)}.md"
        if not filepath.exists():
            raise KeyError(name)
        return text.split_file(filepath)[0]  # Return frontmatter only.
