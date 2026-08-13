"Compile Markdown file(s) with footnotes, indexed terms and references to PDF."

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
from compiler import Compiler
from text import Text
import utils


class PdfCompiler(Compiler):
    "Compile to PDF format."

    def write(self, filename=None):
        self.stylesheet = getSampleStyleSheet()
        # self.stylesheet.list()

        # These modifications will affect subsquent styles inheriting from Normal.
        self.stylesheet["Normal"].fontName = constants.PDF_NORMAL_FONT
        self.stylesheet["Normal"].fontSize = constants.PDF_NORMAL_FONT_SIZE
        self.stylesheet["Normal"].leading = constants.PDF_NORMAL_LEADING

        self.stylesheet["Title"].fontSize = constants.PDF_TITLE_FONT_SIZE
        self.stylesheet["Title"].leading = constants.PDF_TITLE_LEADING
        self.stylesheet["Title"].alignment = 0  # Left
        self.stylesheet["Title"].spaceAfter = constants.PDF_TITLE_SPACE_AFTER

        self.stylesheet["Code"].fontName = constants.PDF_CODE_FONT
        self.stylesheet["Code"].fontSize = constants.PDF_CODE_FONT_SIZE
        self.stylesheet["Code"].leading = constants.PDF_CODE_LEADING
        self.stylesheet["Code"].leftIndent = constants.PDF_CODE_INDENT

        self.stylesheet["OrderedList"].fontName = constants.PDF_NORMAL_FONT
        self.stylesheet["OrderedList"].fontSize = constants.PDF_NORMAL_FONT_SIZE
        self.stylesheet["OrderedList"].bulletFormat = "%s. "
        self.stylesheet["UnorderedList"].fontName = constants.PDF_NORMAL_FONT
        self.stylesheet["UnorderedList"].fontSize = constants.PDF_NORMAL_FONT_SIZE
        self.stylesheet["UnorderedList"].bulletType = "bullet"
        self.stylesheet["UnorderedList"].bulletFont = constants.PDF_NORMAL_FONT_SIZE

        self.stylesheet.add(
            ParagraphStyle(
                name="Index",
                parent=self.stylesheet["Normal"],
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Quote",
                parent=self.stylesheet["Normal"],
                fontName=constants.PDF_QUOTE_FONT,
                fontSize=constants.PDF_QUOTE_FONT_SIZE,
                leading=constants.PDF_QUOTE_LEADING,
                spaceBefore=constants.PDF_QUOTE_SPACE_BEFORE,
                leftIndent=constants.PDF_QUOTE_INDENT,
                rightIndent=constants.PDF_QUOTE_INDENT,
            )
        )
        self.stylesheet.add(
            ParagraphStyle(
                name="Footnote",
                parent=self.stylesheet["Normal"],
                spaceBefore=constants.PDF_FOOTNOTE_SPACE_BEFORE,
                leftIndent=constants.PDF_FOOTNOTE_INDENT,
                firstLineIndent=-constants.PDF_FOOTNOTE_INDENT,
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
                spaceBefore=constants.PDF_REFERENCE_SPACE_BEFORE,
                leftIndent=constants.PDF_REFERENCE_INDENT,
                firstLineIndent=-constants.PDF_REFERENCE_INDENT,
            )
        )

        # Placed here to avoid affecting previously defined styles.
        self.stylesheet["Normal"].spaceBefore = constants.PDF_NORMAL_SPACE_BEFORE
        self.stylesheet["Normal"].spaceAfter = constants.PDF_NORMAL_SPACE_AFTER

        # Document contents.
        self.flowables = []

        # Write title page: title, subtitle, initial note, authors, dates.
        self.write_paragraph(self.main.title, "Title")
        self.flowables.append(
            HRFlowable(width="100%", color=reportlab.lib.colors.black, spaceAfter=20)
        )
        if self.main.subtitle:
            self.write_heading(self.main.subtitle, 1)

        for author in self.main.authors:
            self.write_heading(", ".join(self.main.authors), 2)

        self.flowables.append(Spacer(0, 28))
        self.text_render(self.main)

        self.flowables.append(Spacer(0, 28))
        self.write_preformatted(
            f'{self.tx("Created")}: {utils.isoformat()}\n'
            f'{self.tx("Latest modification")}: {utils.isoformat(self.main.modified)}',
            stylename="Italic",
        )

        # Write table of contents (TOC) page(s).
        if self.toc_level and self.main.subtexts:
            self.write_page_break()
            self.write_heading(self.tx("Contents"), 1)
            # Define the TOC level styles.
            toc_level_styles = []
            for level in range(0, constants.PDF_MAX_TOC_LEVEL + 1):
                style = ParagraphStyle(
                    name=f"TOC level {level}",
                    fontName=constants.PDF_NORMAL_FONT,
                    fontSize=constants.PDF_TOC_FONT_SIZE,
                    leading=constants.PDF_TOC_LEADING,
                    firstLineIndent=constants.PDF_TOC_INDENT * level,
                    leftIndent=constants.PDF_TOC_INDENT * (level + 1),
                )
                toc_level_styles.append(style)
            self.toc = TableOfContents(
                dotsMinLevel=-1,
                levelStyles=toc_level_styles,
                notifyKind="TOCEntry",
            )
            self.flowables.append(self.toc)
        else:
            self.toc = None

        # First-level subtexts are chapters.
        for text in self.main.subtexts:
            self.write_text(text)
            if self.footnotes_location == constants.FOOTNOTES_CHAPTER:
                if text.footnotes:
                    self.write_page_break()
                    self.write_heading(self.tx("Footnotes"), 3)
                    self.write_footnotes(text)

        if self.footnotes_location == constants.FOOTNOTES_BOOK:
            if self.main.footnotes:
                self.write_page_break()
                self.write_heading(self.tx("Footnotes"), 1, anchor="footnotes")
                self.write_footnotes(self.main)

        self.write_referenced()
        simple_index = self.write_indexed()

        filename or self.main.filename.with_suffix(".pdf")
        with open(filename, "wb") as outfile:
            if self.toc is not None:
                document = TocDocTemplate(
                    outfile,
                    toc_level=self.toc_level,
                    title=self.main.title,
                    author=", ".join(self.main.authors) or None,
                    creator=f"mdcompile {constants.__version__}",
                    lang=self.language,
                )

                if self.indexed:
                    document.multiBuild(
                        self.flowables,
                        onLaterPages=self.display_page_number,
                        canvasmaker=simple_index.getCanvasMaker(),
                    )
                else:
                    document.multiBuild(
                        self.flowables, onLaterPages=self.display_page_number
                    )
            else:
                document = SimpleDocTemplate(
                    outfile,
                    title=self.main.title,
                    author=", ".join(self.main.authors) or None,
                    creator=f"mdcompile {constants.__version__}",
                    lang=self.language,
                )
                if self.indexed:
                    document.build(
                        self.flowables,
                        onLaterPages=self.display_page_number,
                        canvasmaker=simple_index.getCanvasMaker(),
                    )
                else:
                    document.build(
                        self.flowables, onLaterPages=self.display_page_number
                    )

    def write_text(self, text):
        if text.level <= self.page_break_level:
            self.write_page_break()
        if text.level <= self.toc_level:
            anchor = text.ordinal
        else:
            anchor = None
        self.write_heading(self.numbered_title(text), text.level, anchor=anchor)
        if text.subtitle:
            self.write_heading(text.subtitle, text.level + 1)

        self.text_render(text)

        if self.footnotes_location == constants.FOOTNOTES_TEXT and text.footnotes:
            self.write_heading(self.tx("Footnotes"), text.level + 2)
            self.write_footnotes(text)

        for subtext in text.subtexts:
            self.write_text(subtext)

    def write_paragraph(self, text, stylename="Normal"):
        self.flowables.append(Paragraph(text, style=self.stylesheet[stylename]))

    def write_preformatted(self, text, stylename="Normal"):
        self.flowables.append(Preformatted(text, style=self.stylesheet[stylename]))

    def write_heading(self, heading, level, anchor=None):
        """Add heading given the level.
        If the anchor is given, create TOC entry and anchor.
        """
        level = min(level, constants.MAX_LEVEL)
        if anchor:
            if level <= self.toc_level:
                self.flowables.append(TocMarker(level - 1, heading, anchor))
            heading = f'<a name="__anchor__{anchor}"/>' + heading
        self.write_paragraph(heading, stylename=f"Heading{level}")

    def write_page_break(self):
        self.flowables.append(NotAtTopPageBreak())

    def write_footnotes(self, text):
        "Write out the footnotes for the text."
        for footnote in sorted(text.footnotes.values(), key=lambda f: f["number"]):
            self.footnote_def_flag = footnote["number"]
            for child in footnote["children"]:
                self.render(child)
            self.footnote_def_flag = 0

    def write_referenced(self):
        "Write the referenced pages, if any."
        if not self.referenced:
            return
        self.write_page_break()
        self.write_heading(self.tx("References"), 1, anchor="references")
        for name, reference in sorted(self.referenced.items()):
            self.para_push("Reference")
            self.para_text(f'<a name="{name}"/><b>{name}</b>')
            self.para_text('<span size="40"> </span>')
            self.write_reference_authors(reference)
            try:
                method = getattr(self, f"write_reference_{reference['type']}")
            except AttributeError:
                raise ValueError(f"unknown reference type {reference['type']}")
            else:
                method(reference)
            self.para_text(".")
            self.write_reference_external_links(reference)
            self.para_pop()

    def write_reference_authors(self, reference):
        count = len(reference["authors"])
        for pos, author in enumerate(reference["authors"]):
            if pos > 0:
                if pos == count - 1:
                    self.para_text(" & ")
                else:
                    self.para_text(", ")
            self.para_text(author)
        self.para_text(": ")

    def write_reference_article(self, reference):
        "Write data for reference of type 'article'."
        self.para_text(reference["title"])
        self.para_text(",")
        if journal := reference.get("journal"):
            self.para_text(f" <i>{journal}</i>")
        if volume := reference.get("volume"):
            self.para_text(f" <b>{volume}</b>")
        if issue := reference.get("issue"):
            self.para_text(f" ({issue})")
        if pages := reference.get("pages"):
            self.para_text(" ")
            self.para_text(pages.replace("--", "-"))

    def write_reference_book(self, reference):
        "Write data for reference of type 'book'."
        self.para_text(f"<i>{reference['title']}</i>")
        if edition := reference.get("edition"):
            self.para_text(",")
            if publisher := edition.get("publisher"):
                self.para_text(" ")
                self.para_text(publisher)
            if published := edition.get("published"):
                self.para_text(" ")
                self.para_text(published)

    def write_reference_link(self, reference):
        "Write data for reference of type 'link'."
        self.para_text(f" {reference['title']}")
        if url := reference.get("url"):
            self.para_text(
                f' <link href="{url}" underline="true" color="blue">{url}</link>'
            )
            if accessed := reference.get("accessed"):
                self.para_text(f" ({self.tx('accessed')} {accessed})")

    def write_reference_external_links(self, reference):
        "Write external links; doi, pmid, isbn, ..."
        if url := reference.get("url"):
            self.para_text(
                f' <link href="{url}" underline="true" color="royalblue">{url}</link>'
            )
        for key, (label, template) in constants.REFS_LINKS.items():
            try:
                value = reference[key]
                text = f"{label}:{value}"
                url = template.format(value=value)
                self.para_text(
                    f' <link href="{url}" underline="true" color="royalblue">{text}</link>'
                )
            except KeyError:
                pass

    def write_indexed(self):
        "Write the index; return the SimpleIndex object."
        if not self.indexed:
            return None
        self.write_page_break()
        self.write_heading(self.tx("Index"), 1, anchor="index")
        result = SimpleIndex(style=self.stylesheet["Index"], headers=False)
        self.flowables.append(result)
        return result

    def para_push(self, stylename="Normal", preformatted=False):
        "Push new container for text in a paragraph onto the stack."
        self.para_stack.append(([], stylename, preformatted))

    def para_pop(self, stylename=None, preformatted=None, add=True):
        "Write out paragraph containing the saved-up text."
        popped = self.para_stack.pop()
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
                self.write_preformatted(text, stylename)
            else:
                self.write_paragraph(text, stylename)
        else:
            return Paragraph(text, style=self.stylesheet[stylename])

    def para_text(self, text):
        "Add text to container on top of stack."
        self.para_stack[-1][0].append(text)

    def display_page_number(self, canvas, doc):
        "Output page number onto the current canvas."
        width, height = reportlab.rl_config.defaultPageSize
        canvas.saveState()
        canvas.setFont("Helvetica", 10)
        canvas.drawString(width - 84, height - 56, str(doc.page))
        canvas.restoreState()

    def render_document(self, ast):
        self.within_quote = False
        self.within_code = False
        self.para_stack = []
        for child in ast["children"]:
            self.render(child)

    def render_heading(self, ast):
        self.para_push(f"Heading{ast['level']}")
        for child in ast["children"]:
            self.render(child)
        level = min(ast["level"], constants.MAX_LEVEL)
        self.para_pop()

    def render_paragraph(self, ast):
        self.para_push()
        if self.paragraph_number is not None:
            self.paragraph_number += 1
            self.para_text('<font face="courier">')
            self.para_text(f"{self.paragraph_number}.")
            self.para_text("</font> ")
        for child in ast["children"]:
            self.render(child)
        if self.within_quote:
            self.para_pop(stylename="Quote")
        elif self.within_code:
            self.para_pop(stylename="Code", preformatted=True)
        elif self.footnote_def_flag:
            if self.footnote_def_flag >= 1:
                self.para_stack[-1][0].insert(0, f"<b>{self.footnote_def_flag}.</b> ")
                self.footnote_def_flag = -1
                self.para_pop(stylename="Footnote")
            else:
                self.para_pop(stylename="Footnote subsequent")
        else:
            self.para_pop()

    def render_raw_text(self, ast):
        self.para_text(ast["children"])

    def render_blank_line(self, ast):
        pass

    def render_quote(self, ast):
        self.para_push("Quote")
        self.within_quote = True
        for child in ast["children"]:
            self.render(child)
        self.within_quote = False
        self.para_pop()

    def render_code_span(self, ast):
        self.para_text(f'<font face="{constants.PDF_QUOTE_FONT}">')
        self.para_text(ast["children"])
        self.para_text("</font>")

    def render_code_block(self, ast):
        self.para_push("Code", preformatted=True)
        self.within_code = True
        for child in ast["children"]:
            self.render(child)
        self.within_code = False
        self.para_pop()

    def render_fenced_code(self, ast):
        self.para_push("Code", preformatted=True)
        self.within_code = True
        for child in ast["children"]:
            self.render(child)
        self.within_code = False
        self.para_pop()

    def render_image(self, ast):
        self.para_pop()
        self.para_push()
        flowables = [
            HRFlowable(
                width="100%",
                color=reportlab.lib.colors.grey,
                spaceBefore=4,
                spaceAfter=constants.PDF_IMAGE_SPACE,
            )
        ]
        # Fetch image from the web.
        if urllib.parse.urlparse(ast["dest"]).scheme:
            response = requests.get(ast["dest"])
            if response.status_code != HTTP.OK:
                flowables.append(Paragraph(f"Could not fetch image '{ast['dest']}'"))
            elif response.headers["Content-Type"] in (
                constants.PNG_MIMETYPE,
                constants.JPEG_MIMETYPE,
            ):
                image_data = io.BytesIO(response.content)
                flowables.append(Image(image_data, hAlign="LEFT"))
            else:
                flowables.append(
                    Paragraph(
                        f"Cannot handle image '{ast['dest']}' with content type '{response.headers['Content-Type']}'"
                    )
                )

        # Use image from the image library.
        elif ast["dest"] in get_imgs():
            img = get_imgs()[ast["dest"]]
            scale_factor = img["pdf"]["scale_factor"]

            if img["content_type"] in (
                constants.SVG_MIMETYPE,
                constants.JSON_MIMETYPE,
            ):
                # SVG image.
                if img["content_type"] == constants.SVG_MIMETYPE:
                    # SVG in image library has already been checked for validity.
                    root = minixml.parse_content(img["data"])

                # Vega-Lite plot.
                else:
                    # JSON in image library has already been checked for validity.
                    vl_spec = json.loads(img["data"])
                    root = minixml.parse_content(vl_convert.vegalite_to_svg(vl_spec))

                # Set viewbox so that scaling behaves.
                root["viewBox"] = f"0 0 {root['width']} {root['height']}"

                # SVG convert to ReportLab graphics.
                if img["pdf"]["reportlab_graphics"]:
                    # Scale width and height in SVG element.
                    root["width"] = scale_factor * float(root["width"])
                    root["height"] = scale_factor * float(root["height"])
                    flowables.append(svglib.svglib.svg2rlg(io.StringIO(repr(root))))

                # SVG convert to PNG.
                else:
                    png_factor = img["pdf"]["png_rendering_factor"]
                    # Scale width and height in SVG element.
                    root["width"] = png_factor * scale_factor * float(root["width"])
                    root["height"] = png_factor * scale_factor * float(root["height"])
                    flowables.append(
                        Image(
                            io.BytesIO(vl_convert.svg_to_png(repr(root))),
                            hAlign="LEFT",
                            width=float(root["width"]) / png_factor,
                            height=float(root["height"]) / png_factor,
                        )
                    )

            # JPEG or PNG.
            elif img["content_type"] in (
                constants.PNG_MIMETYPE,
                constants.JPEG_MIMETYPE,
            ):
                image_data = io.BytesIO(base64.standard_b64decode(img["data"]))
                width, height = PIL.Image.open(image_data).size
                flowables.append(
                    Image(
                        image_data,
                        hAlign="LEFT",
                        width=scale_factor * width,
                        height=scale_factor * height,
                    )
                )
            else:
                flowables.append(
                    Paragraph(
                        f"Cannot handle image content type '{img['content_type']}'"
                    )
                )
        else:
            flowables.append(Paragraph(f"No such image '{ast['dest']}'"))

        if ast["children"]:
            self.para_push("Normal")
            for child in ast["children"]:
                self.render(child)
            flowables.append(self.para_pop(add=False))
        flowables.append(
            HRFlowable(
                width="100%",
                color=reportlab.lib.colors.grey,
                spaceBefore=4,
                spaceAfter=constants.PDF_IMAGE_SPACE,
            )
        )
        self.flowables.append(KeepTogether(flowables))

    def render_emphasis(self, ast):
        self.para_text("<i>")
        for child in ast["children"]:
            self.render(child)
        self.para_text("</i>")

    def render_strong_emphasis(self, ast):
        self.para_text("<b>")
        for child in ast["children"]:
            self.render(child)
        self.para_text("</b>")

    def render_superscript(self, ast):
        self.para_text("<super>")
        for child in ast["children"]:
            self.render(child)
        self.para_text("</super>")

    def render_subscript(self, ast):
        self.para_text("<sub>")
        for child in ast["children"]:
            self.render(child)
        self.para_text("</sub>")

    def render_emdash(self, ast):
        self.para_text(constants.EM_DASH)

    def render_line_break(self, ast):
        # XXX Cannot handle hard/soft distinction.
        self.para_text(" ")

    def render_thematic_break(self, ast):
        self.flowables.append(
            HRFlowable(width="60%", color=reportlab.lib.colors.black, spaceAfter=10)
        )

    def render_link(self, ast):
        self.para_text(f'<link href="{ast["dest"]}" underline="true" color="blue">')
        for child in ast["children"]:
            self.render(child)
        self.para_text("</link>")

    def render_list(self, ast):
        self.list_stack.append([])
        for child in ast["children"]:
            self.render(child)
        # XXX ast["tight"] is currently not used.
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
        item = ast["canonical"].replace(",", ",,").replace(";", ",")
        self.para_text(f'<index item="{item}"/>')
        if self.underline_indexed:
            self.para_text(f'<u>{ast["term"]}</u>')
        else:
            self.para_text(ast["term"])

    def render_footnote_ref(self, ast):
        self.para_text(f" <super><b>{ast['number']}</b></super>")

    def render_footnote_def(self, ast):
        "The footnote definition in the element stream is not used; ignore."
        pass

    def render_reference(self, ast):
        self.para_text(f'<link href="#{ast["name"]}"><b>{ast["name"]}</b></link>')
        reference = self.referenced[ast["name"]]
        self.para_text(f": <i>{reference['title']}</i>")


class TocDocTemplate(SimpleDocTemplate):
    "Subclass for creating a table of contents."

    def __init__(self, filename, toc_level, **kw):
        super().__init__(filename, **kw)
        self.toc_level = toc_level

    def afterFlowable(self, flowable):
        if not isinstance(flowable, TocMarker):
            return
        if self.toc_level < flowable.toc_level:
            return
        key = f"__{flowable.toc_anchor}__"
        self.canv.bookmarkPage(key)
        self.notify("TOCEntry", (flowable.toc_level, flowable.toc_text, self.page, key))


class TocMarker(NullDraw):
    "Marker for TOC entry."

    def __init__(self, toc_level, toc_text, toc_anchor):
        super().__init__()
        self.toc_level = toc_level
        self.toc_text = toc_text
        self.toc_anchor = toc_anchor
