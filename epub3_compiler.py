"Compile Markdown file(s) to EPUB3."

import constants
from compiler import Compiler
import genepub3 as epub3
import utils
from html_mixin import HtmlMixin


class Epub3Compiler(HtmlMixin, Compiler):
    "Compile Markdown file(s) to EPUB3."

    STANDARD_CSS = """body {
  font-family: Helvetica, Arial, sans-serif;
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
pre.codeblock {
  margin-left: 3em;
}
ol.toc {
  list-style: none;
}
a.contrast {
  color: black;
}"""

    def write_initialize(self, output_filepath):
        "Set up the EPUB3 document."
        self.output_filepath = output_filepath.with_suffix(".epub")

        self.document = epub3.Document(
            self.text.title, self.text.identifier, self.text.language
        )
        self.document.add_style("standard", self.STANDARD_CSS)
        self.document.creators.extend(self.text.authors)
        self.document.subject = self.text.frontmatter.get("subject")
        self.document.contributors.append(f"mdcompile {constants.__version__}")
        self.document.type = "book" if self.text.subtexts else "essay"
        self.document.description = self.text.frontmatter.get("description")
        self.document.subject = self.text.frontmatter.get("subject")
        self.document.publisher = self.text.frontmatter.get("publisher")
        self.document.rights = self.text.frontmatter.get("rights")
        self.document.date = self.text.modified.isoformat()

        # Initial values.
        self.stack = []
        self.within_footnote = None

    def write_toc(self):
        "Set up TOC. Not needed; 'self.document.write' generates the TOC."
        pass

    def write_title_page(self):
        "Write the title page. If no subtexts, this is all content except references."
        title = self.tx("Title page") if self.text.subtexts else self.text.title
        self.current_section = epub3.Section(title, add_title=False)
        self.document.add_section(self.current_section)
        self.stack = [self.current_section.body]
        super().write_title_page()

    def write_text_initialize(self, text):
        "Set up for the next text. Outputs the text title. Adds section to TOC."
        title = text.ordinal_title
        self.current_section = text.section = epub3.Section(
            title, add_title=False, name=text.identifier
        )
        if text.supertext is self.text:  # First-level subtext; chapter.
            self.document.add_section(self.current_section)
        else:
            text.supertext.section.add_section(self.current_section)
        self.stack = [self.current_section.body]

    def write_footnotes_chapter(self, text):
        "Write out footnotes for the chapter, if that mode and any footnotes."
        if not text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_CHAPTER:
            return
        self.current_section = epub3.Section(
            self.tx("Footnotes"), add_title=2, name=f"{text.identifier}-footnotes"
        )
        sections = list(self.document.sections.values())
        sections[-1].add_section(self.current_section)
        self.stack = [self.current_section.body]
        self.write_footnotes(text)

    def write_footnotes_book(self):
        "Write out footnotes for the book, if that mode and any footnotes."
        if not self.text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_BOOK:
            return
        self.current_section = epub3.Section(self.tx("Footnotes"))
        self.text.section.add_section(self.current_section)
        self.stack = [self.current_section.body]
        self.write_footnotes(self.text)

    def write_references(self):
        "Write the references section."
        assert self.referenced
        title = self.tx("References")
        if self.text.subtexts:  # Book; references in a separate section.
            self.current_section = epub3.Section(title)
            self.document.add_section(self.current_section)
            self.stack = [self.current_section.body]
        else:  # Essay; references after the text; no new section.
            with self.push("h3"):
                self.append(title)
        self.write_references_entries()

    def write_index(self):
        "Write the index section. Only for book."
        assert self.index_terms
        self.current_section = epub3.Section(self.tx("Index"))
        self.document.add_section(self.current_section)
        self.stack = [self.current_section.body]
        self.write_index_entries()

    def write_finalize(self):
        "Write the EPUB3 contents to file."
        self.document.write(self.output_filepath)

    def render_code_block(self, ast):
        "Render a block of code. It appears that EPUB3 and HTML disagree on this."
        with self.push("pre") as pre:
            pre["class"] = "codeblock"
            with self.push("code"):
                for child in ast["children"]:
                    self.render(child)

    def get_footnote_href(self, ast):
        "Href to the footnote definition in EPUB3 format."
        if self.text.subtexts:
            return f"{ast['text'].identifier}-footnotes.xhtml#{ast['identifier']}"
        else:
            return f"{ast['text'].identifier}.xhtml#{ast['identifier']}"

    def get_reference_id(self, name):
        "Id for the reference in EPUB3 format."
        return utils.safe(name)

    def get_reference_href(self, ast):
        "Href to the reference in EPUB3 format."
        if self.text.subtexts:
            return f"{self.tx('References')}.xhtml#{self.get_reference_id(ast['name'])}"
        else:
            return f"#{self.get_reference_id(ast['name'])}"

    def get_index_id(self, canonical):
        "Id for the index entry."
        return utils.safe(canonical)

    def get_index_href(self, canonical):
        "Href to the index entry."
        return f"{self.tx('Index')}.xhtml#{self.get_index_id(canonical)}"

    def get_indexed_id(self, canonical):
        "Id for the index term in the text."
        return utils.safe(canonical)

    def get_indexed_href(self, text, canonical):
        "Href to the indexed term in the text."
        return f"{text.identifier}.xhtml#{self.get_indexed_id(canonical)}"
            
