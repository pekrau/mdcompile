"Compile Markdown file(s) to PDF."

import datetime as dt
import io

import reportlab
import reportlab.rl_config
import reportlab.lib.colors
from reportlab.lib.styles import *
from reportlab.platypus import *
from reportlab.platypus.doctemplate import LayoutError
from reportlab.platypus.tables import *
from reportlab.platypus.tableofcontents import TableOfContents, SimpleIndex

import constants
import utils
from compiler import Compiler


class PdfCompiler(Compiler):
    "Compile to PDF format."

    def write_setup(self):
        "Set up the the PDF document."
        self.stylesheet = getSampleStyleSheet()
        # self.stylesheet.list()  # To see which are predefined.

        # These modifications will affect subsquent styles inheriting from Normal.
        self.stylesheet["Normal"].fontName = "Helvetica"
        self.stylesheet["Normal"].fontSize = 12
        self.stylesheet["Normal"].leading = 17

        self.stylesheet["Title"].fontSize = 24
        self.stylesheet["Title"].leading = 30
        self.stylesheet["Title"].alignment = 0  # Left
        self.stylesheet["Title"].spaceAfter = 15

        self.stylesheet["Code"].fontName = "Courier"
        self.stylesheet["Code"].fontSize = 11
        self.stylesheet["Code"].leading = 12
        self.stylesheet["Code"].leftIndent = 10
        self.stylesheet["Code"].spaceAfter = 15

        self.stylesheet["OrderedList"].fontName = "Helvetica"
        self.stylesheet["OrderedList"].fontSize = 12
        self.stylesheet["OrderedList"].bulletFormat = "%s. "
        self.stylesheet["UnorderedList"].fontName = "Helvetica"
        self.stylesheet["UnorderedList"].fontSize = 12
        self.stylesheet["UnorderedList"].bulletType = "bullet"
        self.stylesheet["UnorderedList"].bulletFont = 12

        self.stylesheet.add(
            ParagraphStyle(
                name="Index",
                parent=self.stylesheet["Normal"],
                leading=12,  # Cannot set to 0: the clickable area in index page lost.
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Quote",
                parent=self.stylesheet["Normal"],
                fontName="Times-Roman",
                fontSize=14,
                leading=16,
                spaceBefore=6,
                leftIndent=28,
                rightIndent=28,
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Footnote",
                parent=self.stylesheet["Normal"],
                spaceBefore=6,
                leftIndent=10,
                firstLineIndent=-10,
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Footnote subsequent",
                parent=self.stylesheet["Footnote"],
                firstLineIndent=0,
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Reference",
                parent=self.stylesheet["Normal"],
                spaceBefore=7,
                leftIndent=10,
                firstLineIndent=-10,
            )
        )

        # Placed here to avoid affecting previously defined styles.
        self.stylesheet["Normal"].spaceBefore = 6
        self.stylesheet["Normal"].spaceAfter = 6

        # Set attribute for essay having no TOC.
        self.toc = None

        # Document contents.
        self.flowables = []

    def write_heading(self, heading, level, target=None):
        "Write heading at the specified level."
        level = min(level, constants.MAX_LEVEL)
        if target:
            self.flowables.append(TocMarker(level - 1, heading, target))
        self.flowables.append(
            Paragraph(heading, style=self.stylesheet[f"Heading{level}"])
        )

    def write_title_page(self):
        "Write the title page. If no subtexts, this is all content except references."
        self.flowables.append(
            Paragraph(self.text.title, style=self.stylesheet["Title"])
        )
        self.flowables.append(
            HRFlowable(width="100%", color=reportlab.lib.colors.black, spaceAfter=20)
        )
        if self.text.subtitle:
            self.write_heading(self.text.subtitle, 1)
        for author in self.text.authors:
            self.write_heading(", ".join(self.text.authors), 2)
        if rights := self.text.frontmatter.get("rights"):
            self.flowables.append(Paragraph(rights, style=self.stylesheet["Normal"]))
        self.flowables.append(
            Paragraph(
                f'{self.tx("Last modification")}: {utils.isoformat(self.text.modified)}',
                style=self.stylesheet["Italic"],
            )
        )
        # Spacer beneath header items.
        self.flowables.append(Spacer(0, 20))
        self.render(self.text.ast, level=3)
        self.write_footnotes_text(self.text)

    def write_toc(self):
        "Write the table of contents. For PDF, setting up the predefined TOC handling."
        self.flowables.append(NotAtTopPageBreak())
        self.flowables.append(
            Paragraph(self.tx("Contents"), style=self.stylesheet["Heading1"])
        )
        # Define the TOC level styles.
        toc_level_styles = []
        for level in range(0, self.text.depth):
            toc_level_styles.append(
                ParagraphStyle(
                    name=f"TOC level {level}",
                    fontName="Helvetica",
                    fontSize=10,
                    leading=11,
                    firstLineIndent=15 * level,
                )
            )
        self.toc = TableOfContents(
            dotsMinLevel=-1,
            levelStyles=toc_level_styles,
            notifyKind="TOCEntry",
        )
        self.flowables.append(self.toc)

    def write_text_setup(self, text):
        "Set up for the next text."
        self.flowables.append(NotAtTopPageBreak())
        self.write_heading(text.ordinal_title, text.level, target=text.identifier)

    def write_footnotes_chapter(self, text):
        "Write out footnotes for the chapter, if that mode, and any footnotes."
        if not text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_CHAPTER:
            return
        self.flowables.append(NotAtTopPageBreak())
        title = self.tx("Footnotes")
        self.flowables.append(TocMarker(1, title, f"__footnotes_{text.identifier}__"))
        self.flowables.append(Paragraph(title, style=self.stylesheet["Heading1"]))
        self.write_footnotes_items(text)

    def write_footnotes_book(self):
        "Write out footnotes for the book, if that mode, and any footnotes."
        if not self.text.footnotes:
            return
        if not self.footnotes_location == constants.FOOTNOTES_BOOK:
            return
        self.flowables.append(NotAtTopPageBreak())
        title = self.tx("Footnotes")
        self.flowables.append(TocMarker(0, title, "__footnotes__"))
        self.flowables.append(Paragraph(title, style=self.stylesheet["Heading1"]))
        self.write_footnotes_items(self.text)

    def write_references(self):
        "Write the references section, if any references."
        if not self.referenced:
            return
        title = self.tx("References")
        if self.text.subtexts:  # Book; references in separate section.
            self.flowables.append(NotAtTopPageBreak())
            self.flowables.append(TocMarker(0, title, "__references__"))
            self.flowables.append(Paragraph(title, style=self.stylesheet["Heading1"]))
        else:  # Essay; references after the text; no page break, no TOC.
            self.flowables.append(Paragraph(title, style=self.stylesheet["Heading3"]))
        for name, reference in sorted(self.referenced.items()):
            self.push("Reference")
            self.append(f'<a name="{name}"/>')
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
                method = getattr(self, f"write_reference_{reference['type']}")
            except AttributeError:
                raise ValueError(f"unknown reference type {reference['type']}")
            else:
                method(reference)
            self.append(".")
            # External link.
            if url := reference.get("url"):
                self.append(
                    f' <link href="{url}" underline="true" color="royalblue">{url}</link>'
                )
            # Cross-references to other databases.
            for key, (label, template) in constants.EXTERNAL_LINKS.items():
                try:
                    value = reference[key]
                    text = f"{label}:{value}"
                    url = template.format(value=value)
                    self.append(
                        f' <link href="{url}" underline="true" color="royalblue">{text}</link>'
                    )
                except KeyError:
                    pass
            self.pop()

    def write_reference_article(self, reference):
        "Write data for reference of type 'article'."
        self.append(reference["title"].rstrip("."))
        self.append(".")
        if journal := reference.get("journal"):
            self.append(f" <em>{journal}</em>")
        if volume := reference.get("volume"):
            self.append(f" <em>{volume}</em>")
        if issue := reference.get("number"):
            self.append(f" ({issue})")
        if pages := reference.get("pages"):
            self.append(", ")
            self.append(pages.replace("--", "-"))

    def write_reference_book(self, reference):
        "Write data for reference of type 'book'."
        self.append(f"<em>{reference['title'].rstrip('.')}</em>,")
        if publisher := reference.get("publisher"):
            self.append(" ")
            self.append(publisher)
        if published := reference.get("published"):
            published = published.split("-")[0]
            if published != reference.get("year"):
                self.append(" ")
                self.append(published)

    def write_reference_post(self, reference):
        "Write data for reference of type 'post'."
        self.append(f"{reference['title'].rstrip('.')}.")
        if published := reference.get("published"):
            self.append(f" {self.tx('published')} {published}")
        if href := reference.get("href"):
            self.append(
                f' <link href="{href}" underline="true" color="royalblue">{href}</link>'
            )
            if accessed := reference.get("accessed"):
                self.append(f" ({self.tx('accessed')} {accessed})")

    def write_indexed(self):
        "Write the contents of the index section."
        if not self.indexed:
            return
        title = self.tx("Index")
        self.flowables.append(NotAtTopPageBreak())
        self.flowables.append(TocMarker(0, title, "__index__"))
        self.flowables.append(Paragraph(title, style=self.stylesheet["Heading1"]))
        self.simple_index = SimpleIndex(style=self.stylesheet["Index"], headers=False)
        self.flowables.append(self.simple_index)

    def write_to_file(self, output_filepath):
        "Write the PDF contents to file."
        with open(str(output_filepath), "wb") as outfile:
            props = dict(
                title=self.text.title,
                language=self.text.language,
                author=", ".join(self.text.authors) or None,
                creator=f"mdcompile {constants.__version__}",
                date=self.text.modified,
            )
            if self.text.subtitle:
                props["subject"] = self.text.subtitle
            if self.toc:
                document = TocDocTemplate(outfile, toc_level=self.text.depth, **props)
                if self.indexed:
                    document.multiBuild(
                        self.flowables,
                        onLaterPages=self.write_page_number,
                        canvasmaker=self.simple_index.getCanvasMaker(),
                    )
                else:
                    document.multiBuild(
                        self.flowables, onLaterPages=self.write_page_number
                    )
            else:
                document = SimpleDocTemplate(outfile, **props)
                if self.indexed:
                    document.build(
                        self.flowables,
                        onLaterPages=self.write_page_number,
                        canvasmaker=self.simple_index.getCanvasMaker(),
                    )
                else:
                    document.build(self.flowables, onLaterPages=self.write_page_number)

    def write_page_number(self, canvas, doc):
        "Write page number onto the current canvas."
        width, height = reportlab.rl_config.defaultPageSize
        canvas.saveState()
        canvas.setFont("Helvetica", 10)
        canvas.drawString(width - 84, height - 56, str(doc.page))
        canvas.restoreState()

    def render_document(self, ast):
        self.within_quote = False
        self.within_code = False
        self.stack = []
        self.list_stack = []
        for child in ast["children"]:
            self.render(child)

    def push(self, stylename="Normal", preformatted=False):
        "Push new container for text in a paragraph onto the stack."
        self.stack.append(([], stylename, preformatted))

    def pop(self, stylename=None, preformatted=None, add=True):
        "Write out the paragraph containing the saved-up text."
        popped = self.stack.pop()
        parts = popped[0]
        if stylename is None:
            stylename = popped[1]
        if preformatted is None:
            preformatted = popped[2]
        text = "".join(parts)
        if self.list_stack:
            if preformatted:
                self.list_stack[-1].append(
                    Preformatted(text, style=self.stylesheet[stylename])
                )
            else:
                self.list_stack[-1].append(
                    Paragraph(text, style=self.stylesheet[stylename])
                )
        elif add:
            if preformatted:
                self.flowables.append(
                    Preformatted(text, style=self.stylesheet[stylename])
                )
            else:
                self.flowables.append(Paragraph(text, style=self.stylesheet[stylename]))
        else:
            return Paragraph(text, style=self.stylesheet[stylename])

    def append(self, text):
        "Append text to the container on top of the stack."
        self.stack[-1][0].append(text)

    def render_heading(self, ast):
        level = min(self.level + ast["level"], constants.MAX_LEVEL)
        self.push(f"Heading{level}")
        for child in ast["children"]:
            self.render(child)
        self.pop()

    def render_paragraph(self, ast):
        self.push()
        if self.paragraph_number is not None:
            self.paragraph_number += 1
            self.append('<font face="courier">')
            self.append(f"{self.paragraph_number}.")
            self.append("</font> ")
        for child in ast["children"]:
            self.render(child)
        if self.within_quote:
            self.pop(stylename="Quote")
        elif self.within_code:
            self.pop(stylename="Code", preformatted=True)
        elif self.footnote_def_flag is not None:
            # Starting footnote definition.
            if self.footnote_def_flag > 0:
                self.stack[-1][0].insert(
                    0, f"<strong>{self.footnote_def_flag}.</strong> "
                )
                # Signal for being within footnote definition.
                self.footnote_def_flag = -1
                self.pop(stylename="Footnote")
            # Continuing footnote definition.
            else:
                self.pop(stylename="Footnote subsequent")
        else:
            self.pop()

    def render_raw_text(self, ast):
        self.append(ast["children"])

    def render_quote(self, ast):
        self.push("Quote")
        self.within_quote = True
        for child in ast["children"]:
            self.render(child)
        self.within_quote = False
        self.pop()

    def render_code_span(self, ast):
        self.append('<font face="Courier">')
        self.append(ast["children"])
        self.append("</font>")

    def render_code_block(self, ast):
        self.push("Code", preformatted=True)
        self.within_code = True
        for child in ast["children"]:
            self.render(child)
        self.within_code = False
        self.pop()

    def render_fenced_code(self, ast):
        self.render_code_block(ast)

    def render_emphasis(self, ast):
        self.append("<em>")
        for child in ast["children"]:
            self.render(child)
        self.append("</em>")

    def render_strong_emphasis(self, ast):
        self.append("<strong>")
        for child in ast["children"]:
            self.render(child)
        self.append("</strong>")

    def render_superscript(self, ast):
        self.append("<sup>")
        for child in ast["children"]:
            self.render(child)
        self.append("</sup>")

    def render_subscript(self, ast):
        self.append("<sub>")
        for child in ast["children"]:
            self.render(child)
        self.append("</sub>")

    def render_emdash(self, ast):
        self.append(constants.EM_DASH)

    def render_line_break(self, ast):
        if ast["soft"]:
            self.append(" ")
        else:
            self.append("<br/>")

    def render_thematic_break(self, ast):
        self.flowables.append(
            HRFlowable(
                width="60%",
                color=reportlab.lib.colors.black,
                spaceBefore=15,
                spaceAfter=20,
            )
        )

    def render_link(self, ast):
        self.append(f'<link href="{ast["dest"]}" underline="true" color="blue">')
        for child in ast["children"]:
            self.render(child)
        self.append("</link>")

    def render_list(self, ast):
        self.list_stack.append([])
        for child in ast["children"]:
            self.render(child)
        # Currently not used: ast["bullet"], ast["start"], ast["tight"]
        if ast["ordered"]:
            style = self.stylesheet["OrderedList"]
        else:
            style = self.stylesheet["UnorderedList"]
        flowable = ListFlowable(self.list_stack.pop(), style=style)
        if self.list_stack:
            self.list_stack[-1].append(flowable)
        else:
            self.flowables.append(flowable)

    def render_list_item(self, ast):
        self.list_stack.append([])
        for child in ast["children"]:
            self.render(child)
        item = ListItem(self.list_stack.pop())
        self.list_stack[-1].append(item)

    def render_indexed(self, ast):
        # XXX Link to item in Index section.
        item = ast["canonical"].replace(",", ",,").replace(";", ",")
        self.append(f'<index item="{item}"/><u>{ast["term"]}</u>')

    def render_footnote_ref(self, ast):
        self.append(f" <sup><strong>{ast['number']}</strong></sup>")

    def render_reference(self, ast):
        self.append(f'<em><link href="#{ast["name"]}">{ast["name"]}</link></em>')
        if self.reference_title:
            self.append(f': <em>{self.referenced[ast["name"]]["title"]}</em>')


class TocDocTemplate(SimpleDocTemplate):
    "Subclass for creating a table of contents."

    def afterFlowable(self, flowable):
        if not isinstance(flowable, TocMarker):
            return
        self.canv.bookmarkPage(flowable.toc_anchor)
        self.notify(
            "TOCEntry",
            (flowable.toc_level, flowable.toc_text, self.page, flowable.toc_anchor),
        )


class TocMarker(NullDraw):
    "Marker for TOC entry."

    def __init__(self, toc_level, toc_text, toc_anchor):
        super().__init__()
        self.toc_level = toc_level
        self.toc_text = toc_text
        self.toc_anchor = toc_anchor
