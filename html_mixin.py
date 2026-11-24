"Mixin for HTML code generation common to EPUB3 and HTML."

from contextlib import contextmanager

import constants
import utils


class HtmlMixin:
    "Common methods for EPUB3 and HTML."

    @contextmanager
    def push(self, tag, **attrs):
        """Context manager for a new element on the stack.
        Create the element with the given tag and attributes in the element
        on the top of the stack and push it onto the stack.
        The element is popped when leaving the context.
        """
        elem = self.top.create(tag, **attrs)
        self.stack.append(elem)
        try:
            yield elem
        finally:
            self.pop()

    def pop(self):
        return self.stack.pop()

    @property
    def top(self):
        "Return the element on the top of the stack."
        return self.stack[-1]

    def append(self, content):
        "Append the content onto the element on the top of the stack."
        self.top.append(content)

    def write_title_page(self):
        "Write the title page content. If no subtexts, all content except references."
        with self.push("h1"):
            self.append(self.text.title)
        if self.text.subtitle:
            with self.push("h2"):
                self.append(self.text.subtitle)
        if self.text.authors:
            with self.push("h3"):
                for author in self.text.authors:
                    self.append(author)
                    if author != self.text.authors[-1]:
                        with self.push("br"):
                            pass
        if rights := self.text.frontmatter.get("rights"):
            with self.push("p"):
                self.append(rights)
        with self.push("p"):
            with self.push("em"):
                self.append(f"{self.tx('Last modification')}: ")
                self.append(utils.timeformat(self.text.modified))
        self.render(self.text.ast, level=3)
        if self.text.footnotes:
            self.write_spacing(3)
        self.write_footnotes_text(self.text)

    def write_heading(self, heading, level, target=None):
        "Write heading at the specified level."
        with self.push(f"h{min(level, constants.MAX_LEVEL)}"):
            self.append(heading)

    def write_references_entries(self):
        "Write out the references entries."
        assert self.referenced
        references = sorted(self.referenced.items())
        if self.reference_usage:
            for name, reference in references:
                with self.push("dl"):
                    with self.push("dt"):
                        self.write_reference_entry(name, reference)
                    with self.push("dd"):
                        for text in reference["texts"]:
                            with self.push("a") as a:
                                a["href"] = self.get_ref_href(name, text)
                                a["class"] = "contrast"
                                a.append(text.ordinal_title)
                            if text is not reference["texts"][-1]:
                                with self.push("br"):
                                    pass
        else:
            for name, reference in references:
                with self.push("p"):
                    self.write_reference_entry(name, reference)

    def write_reference_entry(self, name, reference):
        "Write out a single reference entry."
        with self.push("a", id=self.get_reference_id(name)):
            self.append(" ")  # Avoid problem with non-finished element in HTML.
        # Authors.
        count = len(reference["authors"])
        for pos, author in enumerate(reference["authors"]):
            if pos > 0:
                if pos == count - 1:
                    self.append(" & ")
                else:
                    self.append(", ")
            self.append(author)
        self.append(". ")
        # Original publication year.
        self.append(reference["year"])
        self.append(". ")
        # Title and bibliographic data according to publication type.
        try:
            method = getattr(self, f"write_reference_entry_{reference['type']}")
        except AttributeError:
            raise ValueError(f"unknown reference type {reference['type']}")
        else:
            method(reference)
        # External link.
        if url := reference.get("url"):
            self.append(" ")
            with self.push("a", href=url):
                self.append(url)
        # Cross-references to other databases.
        for key, (label, template) in constants.EXTERNAL_LINKS.items():
            try:
                value = reference[key]
            except KeyError:
                pass
            else:
                self.append(" ")
                with self.push("a", href=template.format(value=value)):
                    self.append(f"{label}:{value}")

    def write_reference_entry_article(self, reference):
        "Write title and bibliographic data for reference of type 'article'."
        self.append(reference["title"].rstrip("."))
        self.append(".")
        if journal := reference.get("journal"):
            self.append(" ")
            with self.push("em"):
                self.append(journal)
        if volume := reference.get("volume"):
            self.append(" ")
            with self.push("em"):
                self.append(volume)
        if issue := reference.get("number"):
            self.append(f" ({issue})")
        if pages := reference.get("pages"):
            self.append(f', {pages.replace("--", "-")}')
        self.append(".")

    def write_reference_entry_book(self, reference):
        "Write title and bibliographic data for reference of type 'book'."
        with self.push("em"):
            self.append(reference["title"].rstrip("."))
            self.append(".")
        if publisher := reference.get("publisher"):
            self.append(" ")
            self.append(publisher)
        if published := reference.get("published"):
            published = published.split("-")[0]
            if published != reference.get("year"):
                self.append(" ")
                self.append(published)
        self.append(".")

    def write_reference_entry_post(self, reference):
        "Write title and bibliographic data for reference of type 'post'."
        self.append(reference["title"].rstrip("."))
        self.append(".")
        if published := reference.get("published"):
            self.append(f" {self.tx('published')} {published}")
        if href := reference.get("href"):
            with self.push("a", href=href):
                self.append(href)
            if accessed := reference.get("accessed"):
                self.append(f" ({self.tx('accessed')} {accessed})")
        self.append(".")

    def write_index_entries(self):
        "Write the index section entries. Only for book."
        assert self.text.subtexts
        assert self.index_terms
        items = sorted(self.index_terms.items(), key=lambda i: i[0].casefold())
        with self.push("dl"):
            for canonical, texts in items:
                with self.push("dt"):
                    with self.push("a", id=self.get_index_id(canonical)):
                        # Avoid problem with non-finished element in HTML.
                        self.append(" ")
                    self.append(canonical)
                with self.push("dd"):
                    for text in texts:
                        with self.push("a") as a:
                            a["href"] = href = self.get_indexed_href(text, canonical)
                            a["class"] = "contrast"
                            a.append(text.ordinal_title)
                        if text is not texts[-1]:
                            with self.push("br"):
                                pass

    def write_spacing(self, spacing):
        with self.push("hr", style=f"border-width: 0.2em; margin-top: {spacing}em;"):
            pass

    def render_document(self, ast):
        "Render the contents of the text."
        for child in ast["children"]:
            self.render(child)

    def render_heading(self, ast):
        "Heading in the text."
        level = min(self.level + ast["level"], constants.MAX_LEVEL)
        with self.push(f"h{level}"):
            for child in ast["children"]:
                self.render(child)

    def render_paragraph(self, ast):
        "A paragraph in the text."
        with self.push("p"):
            if fn := self.within_footnote:
                if not fn.get("started"):
                    with self.push("a", id=fn["identifier"]):
                        self.append(
                            " "
                        )  # Avoid problem with non-finished element in HTML.
                    with self.push("strong"):
                        self.append(str(fn["number"]))
                        self.append(". ")
                    fn["started"] = True
            if self.paragraph_number is not None:
                self.paragraph_number += 1
                with self.push("mark"):
                    self.append(str(self.paragraph_number))
                    self.append(" ")
            for child in ast["children"]:
                self.render(child)

    def render_raw_text(self, ast):
        "Render simple text content."
        self.append(ast["children"])

    def render_quote(self, ast):
        "Render a quote block."
        with self.push("blockquote"):
            for child in ast["children"]:
                self.render(child)

    def render_code_span(self, ast):
        "Render a stretch of code."
        with self.push("code"):
            self.append(ast["children"])

    def render_code_block(self, ast):
        "Render a block of code. It appears that EPUB3 and HTML disagree on this."
        raise NotImplementedError

    def render_image(self, ast):
        "Render an image."
        raise NotImplementedError

    def render_emphasis(self, ast):
        "Render emphasis, i.e. italic text."
        with self.push("em"):
            for child in ast["children"]:
                self.render(child)

    def render_strong_emphasis(self, ast):
        "Render strong emphasis, i.e. bold text."
        with self.push("strong"):
            for child in ast["children"]:
                self.render(child)

    def render_subscript(self, ast):
        "Render subscript."
        with self.push("sub"):
            for child in ast["children"]:
                self.render(child)

    def render_superscript(self, ast):
        "Render superscript."
        with self.push("sup"):
            for child in ast["children"]:
                self.render(child)

    def render_emdash(self, ast):
        "Render and em-dash character."
        self.append(constants.EM_DASH)

    def render_line_break(self, ast):
        "Render a line break."
        if ast.get("soft"):
            self.append(" ")
        else:
            with self.push("br"):
                pass

    def render_thematic_break(self, ast):
        "Render a thematic break, i.e. a horizontal line."
        with self.push("hr"):
            pass

    def render_link(self, ast):
        "Render a link to a URL."
        with self.push("a", href=ast["dest"], target="_blank"):
            for child in ast["children"]:
                self.render(child)

    def render_list(self, ast):
        "Render a list, ordered or unordered."
        if ast["ordered"]:
            with self.push("ol"):
                for child in ast["children"]:
                    self.render(child)
        else:
            with self.push("ul"):
                for child in ast["children"]:
                    self.render(child)

    def render_list_item(self, ast):
        "Render an item in  list."
        with self.push("li"):
            for child in ast["children"]:
                self.render(child)

    def render_indexed(self, ast):
        "Render an indexed word or phrase."
        with self.push("a") as a:
            a["href"] = self.get_index_href(ast["canonical"])
            a["class"] = "contrast"
            self.append(ast["term"])
            if not ast.get("multiple"):
                a["id"] = self.get_indexed_id(ast["canonical"])

    def render_footnote_ref(self, ast):
        "Render a reference to a footnote."
        with self.push("sup"):
            with self.push("a") as a:
                a["href"] = self.get_footnote_href(ast)
                a["class"] = "contrast"
                with self.push("strong"):
                    self.append(str(ast["number"]))

    def render_reference(self, ast):
        "Render a reference in the text."
        if reference := self.referenced.get(ast["name"]):
            with self.push("a") as a:
                a["href"] = self.get_reference_href(ast)
                a["class"] = "contrast"
                self.append(ast["name"])
                if not ast.get("multiple"):
                    a["id"] = self.get_ref_id(ast["name"])
            if self.reference_title:
                self.append(": ")
                with self.push("em"):
                    self.append(reference["title"])
        else:
            self.append(ast["name"])

    def get_footnote_href(self, ast):
        "Href to the footnote definition."
        raise NotImplemented

    def get_ref_id(self, name):
        "Id for the reference in the text."
        raise NotImplemented

    def get_ref_href(self, name, text):
        "Href to the reference in the text."
        raise NotImplemented

    def get_reference_id(self, name):
        "Id for the reference."
        raise NotImplemented

    def get_reference_href(self, ast):
        "Href to the reference."
        raise NotImplemented

    def get_index_id(self, canonical):
        "Id for the index entry."
        raise NotImplemented

    def get_index_href(self, canonical):
        "Href to the index entry."
        raise NotImplemented

    def get_indexed_id(self, canonical):
        "Id for the index term in the text."
        raise NotImplemented

    def get_indexed_href(self, text, canonical):
        "Href to the indexed term in the text."
        raise NotImplemented
