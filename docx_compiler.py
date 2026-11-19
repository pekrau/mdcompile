"Compile Markdown file(s) to DOCX."

import datetime as dt
import os
import pathlib

import docx
import docx.oxml
import docx.shared
import docx.styles.style
from docx.enum.style import WD_STYLE_TYPE

import constants
import utils
from compiler import Compiler


class DocxCompiler(Compiler):
    "Compile to DOCX format."

    def write_setup(self):
        "Set up the the DOCX document."
        self.doc = docx.Document()

        # Set the default document-wide language.
        # From https://stackoverflow.com/questions/36967416/how-can-i-set-the-language-in-text-with-python-docx
        styles_element = self.doc.styles.element
        rpr_default = styles_element.xpath("./w:docDefaults/w:rPrDefault/w:rPr")[0]
        lang_default = rpr_default.xpath("w:lang")[0]
        lang_default.set(docx.oxml.shared.qn("w:val"), self.text.language)

        # Set to A4 page size. XXX Allow alternatives.
        section = self.doc.sections[0]
        section.page_height = docx.shared.Mm(297)
        section.page_width = docx.shared.Mm(210)
        section.left_margin = docx.shared.Mm(25.4)
        section.right_margin = docx.shared.Mm(25.4)
        section.top_margin = docx.shared.Mm(25.4)
        section.bottom_margin = docx.shared.Mm(25.4)
        section.header_distance = docx.shared.Mm(12.7)
        section.footer_distance = docx.shared.Mm(12.7)

        # Create or modify styles to be used in the DOCX document.
        style = self.doc.styles.add_style("Title 0", WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = self.doc.styles["Title"]
        style.font.name = "Arial"
        style.font.size = docx.shared.Pt(28)
        style.font.color.rgb = docx.shared.RGBColor(0, 0, 0)

        # Number of items in list: MAX_LEVEL
        for level, font_size in enumerate([22, 19, 16, 14, 13, 12], start=1):
            style = self.doc.styles.add_style(f"Title {level}", WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = self.doc.styles[f"Heading {level}"]
            style.font.name = "Arial"
            style.font.size = docx.shared.Pt(font_size)
            style.font.bold = True
            style.font.italic = False
            style.paragraph_format.space_before = docx.shared.Pt(
                5 * (constants.MAX_LEVEL + 1 - level)
            )
            style.paragraph_format.space_after = docx.shared.Pt(
                3 * (constants.MAX_LEVEL + 1 - level)
            )
            style.paragraph_format.line_spacing = 1
            style.font.color.rgb = docx.shared.RGBColor(0, 0, 0)

        style = self.doc.styles["Normal"]
        style.font.name = "Arial"
        style.font.size = docx.shared.Pt(12)
        style.paragraph_format.line_spacing = docx.shared.Pt(17)

        # "Body Text": Table-of-contents (TOC) entries and index pages.
        style = self.doc.styles["Body Text"]
        style.paragraph_format.space_before = docx.shared.Pt(0)
        style.paragraph_format.space_after = docx.shared.Pt(0)

        style = self.doc.styles["Quote"]
        style.font.name = "Times-Roman"
        style.paragraph_format.left_indent = docx.shared.Pt(16)
        style.paragraph_format.right_indent = docx.shared.Pt(16)
        style.font.size = docx.shared.Pt(13)

        style = self.doc.styles.add_style("Code", WD_STYLE_TYPE.PARAGRAPH)
        style.font.name = "Courier"
        style.font.size = docx.shared.Pt(11)
        style.paragraph_format.line_spacing = docx.shared.Pt(12)
        style.paragraph_format.left_indent = docx.shared.Pt(11)

        # Dublin core metadata.
        self.doc.core_properties.title = self.text.title
        self.doc.core_properties.author = ", ".join(self.text.authors)
        self.doc.core_properties.language = self.text.language
        self.doc.core_properties.subject = self.text.frontmatter.get("subject")
        self.doc.core_properties.contributor = f"mdcompile {constants.__version__}"
        self.doc.core_properties.category = "book" if self.text.subtexts else "essay"
        self.doc.core_properties.date = self.text.modified

        # Display page number in the DOCX header on each page.
        # https://stackoverflow.com/questions/56658872/add-page-number-using-python-docx
        paragraph = self.doc.sections[-1].header.paragraphs[0]
        paragraph.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.RIGHT
        run = paragraph.add_run()
        fldChar1 = docx.oxml.OxmlElement("w:fldChar")
        fldChar1.set(docx.oxml.ns.qn("w:fldCharType"), "begin")
        instrText = docx.oxml.OxmlElement("w:instrText")
        instrText.set(docx.oxml.ns.qn("xml:space"), "preserve")
        instrText.text = "PAGE"
        fldChar2 = docx.oxml.OxmlElement("w:fldChar")
        fldChar2.set(docx.oxml.ns.qn("w:fldCharType"), "end")
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)

    def write_title_page(self):
        "Write the title page. If no subtexts, this is all content except references."
        paragraph = self.doc.add_paragraph(style="Title 0")
        paragraph.add_run(self.text.title)
        if self.text.subtitle:
            paragraph = self.doc.add_paragraph(style="Title 1")
            paragraph.add_run(self.text.subtitle)
        # Split authors into runs to allow line break between them.
        paragraph = self.doc.add_paragraph(style="Title 2")
        for author in self.text.authors:
            paragraph.add_run(author)
            if author != self.text.authors[-1]:
                paragraph.add_run(", ")
        paragraph = self.doc.add_paragraph(style="Normal")
        if rights := self.text.frontmatter.get("rights"):
            paragraph.add_run(rights)
        paragraph = self.doc.add_paragraph(style="Normal")
        paragraph.add_run(
            f'{self.tx("Last modification")}: {utils.isoformat(self.text.modified)}'
        ).font.italic = True
        paragraph.paragraph_format.space_after = docx.shared.Pt(30)
        self.within_footnote = False
        self.render(self.text.ast, level=3)
        self.write_footnotes_text(self.text)

    def write_heading(self, heading, level):
        "Write heading at the specified level."
        level = min(level, constants.MAX_LEVEL)
        paragraph = self.doc.add_paragraph(style=f"Title {level}")
        paragraph.add_run(heading)

    def write_toc(self):
        """Write the table of contents for the book.
        The DOCX format does not allow determining the page numbers before printing.
        """
        self.doc.add_page_break()
        paragraph = self.doc.add_paragraph(style="Title 1")
        paragraph.add_run(self.tx("Contents"))
        previous_chapter_footnotes = False
        for text in list(self.text)[1:]:  # Skip the root file (title page).
            if text.level == 1 and previous_chapter_footnotes:
                paragraph = self.doc.add_paragraph(style="Body Text")
                paragraph.paragraph_format.left_indent = docx.shared.Pt(15)
                paragraph.add_run(self.tx("Footnotes"))
                previous_chapter_footnotes = False
            paragraph = self.doc.add_paragraph(style="Body Text")
            paragraph.paragraph_format.first_line_indent = -docx.shared.Pt(15)
            paragraph.paragraph_format.left_indent = docx.shared.Pt(15 * text.level)
            paragraph.add_run(text.ordinal_title)
            if (
                self.footnotes_location == constants.FOOTNOTES_CHAPTER
                and text.level == 1
                and text.footnotes
            ):
                previous_chapter_footnotes = True
        else:
            if previous_chapter_footnotes:
                paragraph = self.doc.add_paragraph(style="Body Text")
                paragraph.paragraph_format.left_indent = docx.shared.Pt(15)
                paragraph.add_run(self.tx("Footnotes"))

        # Write TOC entries for book footnotes, references and indexed, if any such.
        if self.text.footnotes and self.footnotes_location == constants.FOOTNOTES_BOOK:
            self.doc.add_paragraph(self.tx("Footnotes"), style="Body Text")
        if self.referenced:
            self.doc.add_paragraph(self.tx("References"), style="Body Text")
        if self.indexed:
            self.doc.add_paragraph(self.tx("Index"), style="Body Text")

    def write_text_setup(self, text):
        "Set up for the next text."
        self.doc.add_page_break()
        self.write_heading(text.ordinal_title, text.level)

    def write_footnotes_chapter(self, text):
        "Write out footnotes for the chapter, if that mode, and any footnotes."
        if not text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_CHAPTER:
            return
        self.doc.add_page_break()
        paragraph = self.doc.add_paragraph(style="Title 3")
        paragraph.add_run(self.tx("Footnotes"))
        self.write_footnotes(text)

    def write_footnotes_book(self):
        "Write out footnotes for the book, if that mode, and any footnotes."
        if not self.text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_BOOK:
            return
        self.doc.add_page_break()
        paragraph = self.doc.add_paragraph(style="Title 1")
        paragraph.add_run(self.tx("Footnotes"))
        self.write_footnotes(self.text)

    def write_references(self):
        "Write the references section, if any references."
        if not self.referenced:
            return
        if self.text.subtexts:  # Book; references in separate section.
            self.doc.add_page_break()
            paragraph = self.doc.add_paragraph(style="Title 1")
        else:  # Essay; references after the text; no page break.
            paragraph = self.doc.add_paragraph(style="Title 3")
        paragraph.add_run(self.tx("References"))
        for name, reference in sorted(self.referenced.items()):
            paragraph = self.doc.add_paragraph()
            paragraph.paragraph_format.left_indent = docx.shared.Pt(10)
            paragraph.paragraph_format.first_line_indent = docx.shared.Pt(-10)
            # Authors.
            count = len(reference["authors"])
            for pos, author in enumerate(reference["authors"]):
                if pos > 0:
                    if pos == count - 1:
                        paragraph.add_run(" & ")
                    else:
                        paragraph.add_run(", ")
                paragraph.add_run(author)
            paragraph.add_run(". ")
            # Original publication year.
            paragraph.add_run(f"{reference['year']}.")
            # Title and bibliographic data according to publication type.
            try:
                method = getattr(self, f"write_reference_{reference['type']}")
            except AttributeError:
                raise ValueError(f"unknown reference type {reference['type']}")
            else:
                method(paragraph, reference)
            paragraph.add_run(".")
            # External link.
            if url := reference.get("url"):
                paragraph.add_run(" ")
                self.add_hyperlink(paragraph, url, url)
            # Cross-references to other databases.
            for key, (label, template) in constants.EXTERNAL_LINKS.items():
                try:
                    value = reference[key]
                    url = template.format(value=value)
                    paragraph.add_run(" ")
                    self.add_hyperlink(paragraph, url, f"{label}:{value}")
                except KeyError:
                    pass

    def write_reference_article(self, paragraph, reference):
        paragraph.add_run(reference["title"].rstrip("."))
        paragraph.add_run(".")
        if journal := reference.get("journal"):
            paragraph.add_run(" ")
            paragraph.add_run(journal).font.italic = True
        if volume := reference.get("volume"):
            paragraph.add_run(" ")
            paragraph.add_run(volume).font.italic = True
        if issue := reference.get("number"):
            paragraph.add_run(f" ({issue})")
        if pages := reference.get("pages"):
            paragraph.add_run(", ")
            paragraph.add_run(pages.replace("--", "-"))

    def write_reference_book(self, paragraph, reference):
        paragraph.add_run(reference["title"].rstrip(".")).font.italic = True
        paragraph.add_run(".")
        if publisher := reference.get("publisher"):
            paragraph.add_run(" ")
            paragraph.add_run(publisher)
        if published := reference.get("published"):
            published = published.split("-")[0]
            if published != reference.get("year"):
                paragraph.add_run(" ")
                paragraph.add_run(published)

    def write_reference_post(self, paragraph, reference):
        "Write reference which is a URL to a website."
        paragraph.add_run(reference["title"].rstrip(".")).font.italic = True
        if href := reference.get("href"):
            paragraph.add_run(". ")
            self.add_hyperlink(paragraph, href, href)
            if accessed := reference.get("accessed"):
                paragraph.add_run(f" ({self.tx('accessed')} {accessed})")

    def write_indexed(self):
        "Write the index section, if any indexed terms. Only for book."
        if not self.indexed:
            return
        self.doc.add_page_break()
        paragraph = self.doc.add_paragraph(style="Title 1")
        paragraph.add_run(self.tx("Index"))
        items = sorted(self.indexed.items(), key=lambda i: i[0].casefold())
        for canonical, texts in items:
            paragraph = self.doc.add_paragraph(canonical, style="Body Text")
            paragraph.paragraph_format.keep_with_next = True
            for text in texts:
                paragraph = self.doc.add_paragraph(
                    text.ordinal_title, style="Body Text"
                )
                paragraph.paragraph_format.left_indent = docx.shared.Pt(15)
                if text is not texts[:-1]:
                    paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.space_after = docx.shared.Pt(8)

    def write_to_file(self, output_filepath):
        "Write the DOCX contents to file."
        output_filepath = pathlib.Path(output_filepath.with_suffix(".docx"))
        self.doc.save(str(output_filepath))
        return output_filepath

    def render_document(self, ast):
        self.list_stack = []
        self.style_stack = ["Normal"]
        self.bold = False
        self.italic = False
        self.subscript = False
        self.superscript = False
        for child in ast["children"]:
            self.render(child)

    def render_heading(self, ast):
        # XXX Limited implementation; this just handles one child of raw text.
        level = min(self.level + ast["level"], constants.MAX_LEVEL)
        paragraph = self.doc.add_paragraph(style=f"Title {level}")
        paragraph.add_run(ast["children"][0]["children"])

    def render_paragraph(self, ast):
        # NOTE: this flag may have value -True, denoting continued definition.
        if (
            self.within_footnote == False
        ):  # If footnote started, then paragraph created.
            self.current_paragraph = self.doc.add_paragraph()

        # Handle list special case.
        if self.list_stack:
            data = self.list_stack[-1]
            levels = min(3, data["levels"])  # Max list levels in predef list styles.
            if data["first_paragraph"]:
                if data["ordered"]:
                    if levels == 1:
                        style = self.doc.styles["List Number"]
                    else:
                        style = self.doc.styles[f"List Number {levels}"]
                else:
                    if levels == 1:
                        style = self.doc.styles["List Bullet"]
                    else:
                        style = self.doc.styles[f"List Bullet {levels}"]
            else:
                if levels == 1:
                    style = self.doc.styles["List Continue"]
                else:
                    style = self.doc.styles[f"List Continue {levels}"]
            data["first_paragraph"] = False
            self.current_paragraph.style = style
        else:
            self.current_paragraph.style = self.style_stack[-1]

        # Prepend paragraph number.
        if self.paragraph_number is not None:
            self.paragraph_number += 1
            self.current_paragraph.add_run(f"({self.paragraph_number}) ").style = (
                self.doc.styles["Intense Quote Char"]
            )

        for child in ast["children"]:
            self.render(child)

    def render_raw_text(self, ast):
        line = ast["children"]
        line = line.rstrip("\n")
        run = self.current_paragraph.add_run(line)
        if self.bold:
            run.font.bold = True
        if self.italic:
            run.font.italic = True
        if self.subscript:
            run.font.subscript = True
        if self.superscript:
            run.font.superscript = True

    def render_quote(self, ast):
        self.style_stack.append("Quote")
        for child in ast["children"]:
            self.render(child)
        self.style_stack.pop()

    def render_code_span(self, ast):
        self.current_paragraph.add_run(ast["children"]).style = self.doc.styles[
            "Macro Text Char"
        ]

    def render_code_block(self, ast):
        self.current_paragraph = self.doc.add_paragraph(style="Code")
        self.style_stack.append("Code")
        for child in ast["children"]:
            self.render(child)
        self.style_stack.pop()

    def render_fenced_code(self, ast):
        self.render_code_block(ast)

    def render_emphasis(self, ast):
        self.italic = True
        for child in ast["children"]:
            self.render(child)
        self.italic = False

    def render_strong_emphasis(self, ast):
        self.bold = True
        for child in ast["children"]:
            self.render(child)
        self.bold = False

    def render_subscript(self, ast):
        self.subscript = True
        for child in ast["children"]:
            self.render(child)
        self.subscript = False

    def render_superscript(self, ast):
        self.superscript = True
        for child in ast["children"]:
            self.render(child)
        self.superscript = False

    def render_emdash(self, ast):
        self.current_paragraph.add_run(constants.EM_DASH)

    def render_line_break(self, ast):
        if ast["soft"]:
            self.current_paragraph.add_run(" ")
        else:
            self.current_paragraph.add_run("\n")

    def render_thematic_break(self, ast):
        paragraph = self.doc.add_paragraph(constants.EM_DASH * 20)
        paragraph.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER

    def render_link(self, ast):
        # This handles only raw text within a link; can't handle other children.
        raw_text = []
        for child in ast["children"]:
            if child["element"] == "raw_text":
                raw_text.append(child["children"])
        self.add_hyperlink(self.current_paragraph, ast["dest"], "".join(raw_text))

    def render_list(self, ast):
        self.list_stack.append(
            dict(
                ordered=ast["ordered"],
                # Currently not used: ast["bullet"], ast["start"], ast["tight"]
                levels=len(self.list_stack) + 1,
            )
        )
        for child in ast["children"]:
            self.render(child)
        self.list_stack.pop()

    def render_list_item(self, ast):
        data = self.list_stack[-1]
        data["first_paragraph"] = True
        for child in ast["children"]:
            self.render(child)

    def render_indexed(self, ast):
        run = self.current_paragraph.add_run(ast["term"])
        run.font.underline = True
        if self.bold:
            run.font.bold = True
        if self.italic:
            run.font.italic = True

    def render_footnote_ref(self, ast):
        run = self.current_paragraph.add_run(str(ast['number']))
        run.font.superscript = True
        run.font.bold = True

    def render_footnote_def_setup(self, ast):
        "Setup the footnote rendering; output number."
        self.current_paragraph = self.doc.add_paragraph()
        self.current_paragraph.paragraph_format.left_indent = docx.shared.Pt(15)
        self.current_paragraph.paragraph_format.first_line_indent = docx.shared.Pt(-15)
        run = self.current_paragraph.add_run(f"{ast['number']}.")
        run.font.bold = True
        self.current_paragraph.add_run(" ")

    def render_reference(self, ast):
        run = self.current_paragraph.add_run(ast["name"])
        run.font.italic = True
        if self.reference_title:
            reference = self.referenced[ast["name"]]
            self.current_paragraph.add_run(": ")
            run = self.current_paragraph.add_run(reference["title"])
            run.font.italic = True

    # https://github.com/python-openxml/python-docx/issues/610
    def add_hyperlink(self, paragraph, url, text):
        "Link to a web page."
        run = paragraph.add_run(text)
        # Gets access to the document.xml.rels file and gets a new relation id value
        part = paragraph.part
        r_id = part.relate_to(
            url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True
        )
        # Create the w:hyperlink tag and add needed values
        hyperlink = docx.oxml.shared.OxmlElement("w:hyperlink")
        hyperlink.set(docx.oxml.shared.qn("r:id"), r_id)
        hyperlink.append(run._r)
        paragraph._p.insert(len(paragraph.runs) + 2, hyperlink)
        run.font.color.rgb = docx.shared.RGBColor(65, 105, 225)
        run.font.underline = True
