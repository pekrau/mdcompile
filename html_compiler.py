"Compile Markdown file(s) to HTML."

import constants
from compiler import Compiler
import utils
import minixml
from html_mixin import HtmlMixin


class Element(minixml.Element):
    HTML = True


class HtmlCompiler(HtmlMixin, Compiler):
    "Compile Markdown file(s) to HTML."

    STYLESHEET_HREF = "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"

    def write_initialize(self, output_filepath):
        "Set up the HTML document."
        self.output_filepath = output_filepath.with_suffix(".html")

        self.document = Element("html")
        self.head = self.document.create("head")
        self.head.create("meta", charset="utf-8")
        self.head.create(
            "meta", name="viewport", content="width=device-width, initial-scale=1"
        )
        self.head.create("meta", name="DC.title", content=self.text.title)
        for author in self.text.authors:
            self.head.create("meta", name="DC.creator", content=author)
        for term in [
            "description",
            "subject",
            "type",
            "identifier",
            "language",
            "rights",
        ]:
            if content := self.text.frontmatter.get(term):
                self.head.create("meta", name=f"DC.{term}", content=content)
        self.head.create("title").append(self.text.title)
        self.head.create("link", rel="stylesheet", href=self.STYLESHEET_HREF)

        # Initial values.
        main = self.document.create("body").create("main")
        main["class"] = "container"
        self.stack = [main]
        self.within_footnote = None

    def write_toc(self):
        "Write the table of contents (TOC)."
        with self.push("h1"):
            self.append(self.tx("Contents"))
        with self.push("ol") as ol:
            ol["class"] = "toc"
            for subtext in self.text.subtexts:
                self.write_toc_subtext(subtext)
            if self.referenced:
                with self.push("li"):
                    with self.push("a") as a:
                        a["href"] = f"#__references__"
                        a["class"] = "contrast"
                        a.append(self.tx("References"))
            if self.index_terms:
                with self.push("li"):
                    with self.push("a") as a:
                        a["href"] = f"#__index__"
                        a["class"] = "contrast"
                        a.append(self.tx("Index"))

    def write_toc_subtext(self, text):
        "Write TOC list for this text and recursively its subtexts."
        with self.push("li"):
            with self.push("a") as a:
                a["href"] = f"#{text.identifier}"
                a["class"] = "contrast"
                a.append(text.title)
            if text.subtexts:
                with self.push("ol") as ol:
                    ol["class"] = "toc"
                    for subtext in text.subtexts:
                        self.write_toc_subtext(subtext)

    def write_text_initialize(self, text):
        "Set up for the next text."
        self.write_spacing(
            constants.MAX_LEVEL - min(text.level, constants.MAX_LEVEL) + 1
        )
        with self.push("a", id=text.identifier):
            self.append(" ")  # Avoid problem with non-finished element in HTML.

    def write_footnotes_chapter(self, text):
        "Write out footnotes for the chapter, if that mode and any footnotes."
        if not text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_CHAPTER:
            return
        with self.push("a", id=f"{text.identifier}-footnotes"):
            self.append(" ")  # Avoid problem with non-finished element in HTML.
        with self.push("h3"):
            self.append(self.tx("Footnotes"))
        self.write_footnotes(text)

    def write_footnotes_book(self):
        "Write out footnotes for the book, if that mode and any footnotes."
        if not self.text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_BOOK:
            return
        self.write_spacing(5)
        with self.push("h2"):
            self.append(self.tx("Footnotes"))
        self.write_footnotes(self.text)

    def write_references(self):
        "Write the references section."
        assert self.referenced
        if self.text.subtexts:
            self.write_spacing(6)
        else:
            self.write_spacing(3)
        with self.push("a", id="__references__"):
            self.append(" ")  # Avoid problem with non-finished element in HTML.
        title = self.tx("References")
        if self.text.subtexts:
            with self.push("h2"):
                self.append(title)
        else:
            with self.push("h3"):
                self.append(title)
        self.write_references_entries()

    def write_index(self):
        "Write the index section. Only for book."
        assert self.index_terms
        self.write_spacing(6)
        with self.push("a", id="__index__"):
            self.append(" ")  # Avoid problem with non-finished element in HTML.
        title = self.tx("Index")
        if self.text.subtexts:
            with self.push("h2"):
                self.append(title)
        else:
            with self.push("h3"):
                self.append(title)
        self.write_index_entries()

    def write_finalize(self):
        with open(str(self.output_filepath), "w") as outfile:
            self.document.write(outfile, indent=None, decl="<!DOCTYPE html>")

    def render_code_block(self, ast):
        "Render a block of code. It appears that EPUB3 and HTML disagree on this."
        with self.push("code"):
            with self.push("pre") as pre:
                pre["class"] = "codeblock"
                for child in ast["children"]:
                    self.render(child)

    def get_footnote_href(self, ast):
        "Href to the footnote definition in HTML format."
        return f"#{ast['identifier']}"

    def get_ref_id(self, name):
        "Id for the reference in the text."
        return f"__ref__{self.get_reference_id(name)}"

    def get_ref_href(self, name, text):
        "Href to the reference in the text."
        return f"#{self.get_ref_id(name)}"

    def get_reference_id(self, name):
        "Id for the reference."
        return f"__reference__{utils.safe(name)}"

    def get_reference_href(self, ast):
        "Href to the reference."
        return f"#{self.get_reference_id(ast['name'])}"

    def get_index_id(self, canonical):
        "Id for the index entry."
        return f"__index__{utils.safe(canonical)}"

    def get_index_href(self, canonical):
        "Href to the index entry."
        return f"#{self.get_index_id(canonical)}"

    def get_indexed_id(self, canonical):
        "Id for the index term in the text."
        return f"__term__{utils.safe(canonical)}"

    def get_indexed_href(self, text, canonical):
        "Href to the indexed term in the text."
        return f"#{self.get_indexed_id(canonical)}"


if __name__ == "__main__":
    from text import Text

    text = Text("no such file")
    text.frontmatter["title"] = "A title"
    text.frontmatter["identifier"] = "abc123"
    text.frontmatter["authors"] = ["Per Kraulis"]
    compiler = HtmlCompiler(text)
    compiler.write("test.html")
