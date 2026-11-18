"Compile Markdown file(s) to EPUB3."

import datetime as dt
import pathlib
from xml.sax.saxutils import escape

import constants
import epub3_writer as epub3
import utils
from compiler import Compiler


class Epub3Compiler(Compiler):
    "Compile Markdown file(s) to EPUB3."

    def write_setup(self):
        "Set up the EPUB3 document."
        self.book = epub3.Book(
            self.text.title, self.text.identifier, self.text.language
        )
        self.book.add_style("standard",
"""body {
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
}""")
        for author in self.text.authors:
            self.book.creators.append(author)
        self.book.contributor = f"mdcompile {constants.__version__}"
        self.book.type = "book" if self.text.subtexts else "essay"
        if self.text.subtitle:
            self.book.description = self.text.subtitle
        if source := self.text.frontmatter.get("source"):
            self.book.source = source
        if subject := self.text.frontmatter.get("subject"):
            self.book.subject = subject
        if publisher := self.text.frontmatter.get("publisher"):
            self.book.publisher = publisher
        if rights := self.text.frontmatter.get("rights"):
            self.book.rights = rights
        self.book.date = self.text.modified.isoformat()
        self.stack = []

    def push(self):
        self.stack.append([])

    def append(self, content):
        self.stack[-1].append(content)

    def pop(self):
        content = "".join(self.stack.pop())
        if self.stack:
            self.stack[-1].append(content)
        else:
            self.current_section.append(content)

    def write_heading(self, heading, level, target=None):
        "Write heading at the specified level."
        level = min(level, constants.MAX_LEVEL)
        self.push()
        self.append(f"<h{level}>{escape(heading)}</h{level}>")
        self.pop()

    def write_title_page(self):
        "Write the title page. If no subtexts, this is all content except references."
        title = self.tx("Title page") if self.text.subtexts else self.text.title
        self.current_section = epub3.Section(title, add_title=False)
        self.book.add_section(self.current_section)
        self.push()
        self.append(f"<h1>{escape(self.text.title)}</h1>")
        if self.text.subtitle:
            self.append(f"<h2>{escape(self.text.subtitle)}</h2>")
        self.append(f'<h3>{"<br/>".join(self.text.authors)}</h3>')
        if rights := self.text.frontmatter.get("rights"):
            self.append(f"<p>{rights}</p>")
        self.append(
            f"<p><em>{self.tx('Last modification')}: {utils.isoformat(self.text.modified)}</em></p>"
        )
        self.pop()
        self.render(self.text.ast, level=3)
        self.write_footnotes_text(self.text)

    def write_toc(self):
        "Set up TOC. Done automatically by 'epub3.write'"
        pass

    def write_text_setup(self, text):
        "Set up for the next text. Output the text title. Record section for TOC."
        title = text.ordinal_title
        self.current_section = text.section = epub3.Section(title, add_title=text.level, name=text.identifier)
        if text.supertext is self.text:  # First-level subtext; chapter.
            self.book.add_section(self.current_section)
        else:
            text.supertext.section.add_section(self.current_section)

    def write_footnotes_chapter(self, text):
        "Write out footnotes for the chapter, if that mode and any footnotes."
        if not text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_CHAPTER:
            return
        self.current_section = epub3.Section(self.tx("Footnotes"), add_title=2, name=f"{text.identifier}-footnotes")
        sections = list(self.book.sections.values())
        sections[-1].add_section(self.current_section)
        self.write_footnotes(text)

    def write_footnotes_book(self):
        "Write out footnotes for the book, if that mode, and any footnotes."
        if not self.text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_BOOK:
            return
        self.current_section = epub3.Section(self.tx("Footnotes"))
        self.text.section.add_section(self.current_section)
        self.write_footnotes(self.text)

    def write_footnote(self, text, footnote):
        "Write the definition for the footnote."
        self.push()
        self.append(f'<a id="{footnote["identifier"]}"/>')
        for child in footnote["children"]:
            self.render(child)
        self.pop()

    def write_references(self):
        "Write the references section, if any references."
        if self.referenced:
            title = self.tx("References")
            if self.text.subtexts:  # Book; references in a separate section.
                self.current_section = epub3.Section(title)
                self.book.add_section(self.current_section)
            else:  # Essay; references after the text; no new section.
                self.references_section = None
                self.push()
                self.append(f"<h3>{title}</h3>")
                self.pop()
        else:
            self.references_section = None
            return
        for name, reference in sorted(self.referenced.items()):
            self.push()
            self.append("<p>")
            self.append(f'<a id="{utils.safe(name)}"/>')
            # Authors.
            count = len(reference["authors"])
            for pos, author in enumerate(reference["authors"]):
                if pos > 0:
                    if pos == count - 1:
                        self.append(escape(" & "))
                    else:
                        self.append(", ")
                self.append(author)
            self.append(". ")
            # Original publication year.
            self.append(reference["year"])
            self.append(". ")
            # Title and bibliographic data according to publication type.
            try:
                method = getattr(self, f"write_reference_{reference['type']}")
            except AttributeError:
                raise ValueError(f"unknown reference type {reference['type']}")
            else:
                method(reference)
            # External link.
            if url := reference.get("url"):
                self.append(f' <a href="{url}">{escape(url)}</a>')
            # Cross-references to other databases.
            for key, (label, template) in constants.EXTERNAL_LINKS.items():
                try:
                    value = reference[key]
                    text = f"{label}:{value}"
                    url = template.format(value=value)
                    self.append(f' <a href="{url}">{escape(text)}</a>')
                except KeyError:
                    pass
            self.append("</p>")
            self.pop()

    def write_reference_article(self, reference):
        "Write data for reference of type 'article'."
        self.append(reference["title"].rstrip("."))
        self.append(".")
        if journal := reference.get("journal"):
            self.append(f" <em>{escape(journal)}</em>")
        if volume := reference.get("volume"):
            self.append(f" <em>{escape(volume)}</em>")
        if issue := reference.get("number"):
            self.append(f" ({escape(issue)})")
        if pages := reference.get("pages"):
            self.append(", ")
            self.append(escape(pages.replace("--", "-")))
        self.append(".")

    def write_reference_book(self, reference):
        "Write data for reference of type 'book'."
        self.append(f"<em>{reference['title'].rstrip('.')}</em>,")
        if publisher := reference.get("publisher"):
            self.append(" ")
            self.append(escape(publisher))
        if published := reference.get("published"):
            published = published.split("-")[0]
            if published != reference.get("year"):
                self.append(" ")
                self.append(published)
        self.append(".")

    def write_reference_post(self, reference):
        "Write data for reference of type 'post'."
        self.append(f"{reference['title'].rstrip('.')}.")
        if published := reference.get("published"):
            self.append(f" {self.tx('published')} {published}")
        if href := reference.get("href"):
            self.append(f' <a href="{href}">{escape(href)}</a>')
            if accessed := reference.get("accessed"):
                self.append(f" ({self.tx('accessed')} {accessed})")
        self.append(".")

    def write_indexed(self):
        "Write the index section, if any indexed terms. Only for book."
        if not self.indexed:
            return
        self.current_section = epub3.Section(self.tx("Index"))
        self.book.add_section(self.current_section)
        self.push()
        items = sorted(self.indexed.items(), key=lambda i: i[0].casefold())
        for canonical, texts in items:
            self.push()
            self.append("<dl>")
            self.append(f'<dt><a id="{utils.safe(canonical)}"/>{escape(canonical)}</dt>')
            self.append("<dd>")
            for text in texts:
                self.append(f'<a href="{text.identifier}.xhtml#{utils.safe(canonical)}">{escape(text.ordinal_title)}</a>')
                if text is not texts[-1]:
                    self.append("<br/>")
            self.append("</dd></dl>")
            self.pop()
        self.pop()

    def write_to_file(self, output_filepath):
        "Write the EPUB3 contents to file."
        self.book.write(output_filepath)

    def render_document(self, ast):
        "Render the contents of the text."
        self.push()
        for child in ast["children"]:
            self.render(child)
        self.pop()
        assert not self.stack

    def render_heading(self, ast):
        level = min(self.level + ast["level"], constants.MAX_LEVEL)
        self.push()
        self.append(f"<h{level}>")
        for child in ast["children"]:
            self.render(child)
        self.append(f"</h{level}>")
        self.pop()

    def render_paragraph(self, ast):
        self.push()
        self.append("<p>")
        if self.footnote_def_flag is not None:
            # Starting footnote definitions.
            if self.footnote_def_flag > 0:
                # XXX Link to footnote definition.
                self.append(f"<strong>{self.footnote_def_flag}.</strong> ")
                # Signal for being within footnote definition.
                self.footnote_def_flag = -1
        if self.paragraph_number is not None:
            self.paragraph_number += 1
            self.append(f"<mark>({self.paragraph_number})</mark> ")
        for child in ast["children"]:
            self.render(child)
        self.append("</p>")
        self.pop()

    def render_raw_text(self, ast):
        self.append(escape(ast["children"]))

    def render_quote(self, ast):
        self.push()
        self.append("<blockquote>")
        for child in ast["children"]:
            self.render(child)
        self.append("</blockquote>")
        self.pop()

    def render_code_span(self, ast):
        self.append(f'<code>{escape(ast["children"])}</code>')

    def render_code_block(self, ast):
        # The <pre> element does not seem to work in common EPUB3 readers?
        # This is a workaround.
        self.push()
        self.append('<p class="codeblock">')
        for child in ast["children"]:
            self.render(child)
        self.append("</p>")
        self.stack[-1] = ["<br/>".join("".join(self.stack[-1]).split("\n"))]
        self.pop()

    def render_fenced_code(self, ast):
        self.render_code_block(ast)

    def render_emphasis(self, ast):
        self.push()
        self.append("<em>")
        for child in ast["children"]:
            self.render(child)
        self.append("</em>")
        self.pop()

    def render_strong_emphasis(self, ast):
        self.push()
        self.append("<strong>")
        for child in ast["children"]:
            self.render(child)
        self.append("</strong>")
        self.pop()

    def render_subscript(self, ast):
        self.push()
        self.append("<sub>")
        for child in ast["children"]:
            self.render(child)
        self.append("</sub>")
        self.pop()

    def render_superscript(self, ast):
        self.push()
        self.append("<sup>")
        for child in ast["children"]:
            self.render(child)
        self.append("</sup>")
        self.pop()

    def render_emdash(self, ast):
        self.append(constants.EM_DASH)

    def render_line_break(self, ast):
        if ast.get("soft"):
            self.append(" ")
        else:
            self.append("<br/>")

    def render_thematic_break(self, ast):
        self.append('<hr style="width: 60%;"/>')

    def render_link(self, ast):
        self.push()
        self.append(f'<a href="{ast["dest"]}">')
        for child in ast["children"]:
            self.render(child)
        self.append("↗</a>")
        self.pop()

    def render_list(self, ast):
        self.push()
        if ast["ordered"]:
            self.append("<ol>")
        else:
            self.append("<ul>")
        for child in ast["children"]:
            self.render(child)
        if ast["ordered"]:
            self.append("</ol>")
        else:
            self.append("</ul>")
        self.pop()

    def render_list_item(self, ast):
        self.push()
        self.append("<li>")
        for child in ast["children"]:
            self.render(child)
        self.append("</li>")
        self.pop()

    def render_indexed(self, ast):
        self.append("<a ")
        # Disallow multiple indexing of the same term in a text.
        if not ast.get("multiple"):
            self.append(f'id="{utils.safe(ast["canonical"])}" ')
        self.append(f'href="{self.tx("Index")}.xhtml#{utils.safe(ast["canonical"])}">{escape(ast["term"])}</a>')

    def render_footnote_ref(self, ast):
        self.append(f'<sup>{ast["number"]}</sup>')

    def render_reference(self, ast):
        self.push()
        self.append(f'<a href="{self.tx("References")}.xhtml#{utils.safe(ast["name"])}">{escape(ast["name"])}</a>')
        if self.reference_title:
            self.append(": ")
            reference = self.referenced[ast["name"]]
            if self.reference_title_italic:
                self.append("<em>")
            self.append(escape(reference["title"]))
            if self.reference_title_italic:
                self.append("</em>")
        self.pop()
