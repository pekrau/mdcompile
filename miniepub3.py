"""Minimalist module for generating a EPUB3 format file.
Based on the minimal EPUB3 example in https://github.com/thansen0/sample-epub-minimal

TODO:
- add image
"""

__version__ = "0.8"

__all__ = ["Book", "Section", "minixml", "__version__"]

import datetime as dt
import zipfile

import minixml


class Book:
    "Book to write out as  EPUB3 format file."

    def __init__(self, identifier, title, language="sv-SE", toc_stylename="default"):
        self.identifier = identifier  # Dublin Core
        self.title = title  # Dublin Core
        self.language = language  # Dublin Core
        self.toc_stylename = toc_stylename  # CSS stylesheet for TOC, if any.
        self.creators = []  # Dublin Core for authors
        self.contributors = []  # Dublin core
        self.type = None  # Dublin Core
        self.description = None  # Dublin Core
        self.source = None  # Dublin Core
        self.subject = None  # Dublin Core
        self.publisher = None  # Dublin Core
        self.rights = None  # Dublin Core
        self.date = None  # Dublin Core
        self.sections = {}  # Key: name, value: Section instance.
        self.css = {}
        self.add_css("default", DEFAULT_CSS)

    def add_css(self, name, content):
        "Add the CSS contents under the given name."
        self.css[name] = content

    def add_section(self, section):
        """Add a Section instance having name, title, stylesheet name and XHTML content.
        The order of addition is significant.
        """
        assert isinstance(section, Section)
        assert section.stylename is None or section.stylename in self.css
        assert section.content
        assert isinstance(section.content, minixml.Element)
        if section.name in self.sections:
            raise ValueError(f"section name '{section.name}' is already in book")
        self.sections[section.name] = section
        section.book = self

    def get_all_sections(self):
        "Get a list of all sections, including subsections."
        result = []
        for section in self.sections.values():
            result.append(section)
            result.extend(section.get_all_sections())
        return result

    def get_container_xml(self):
        "Return XML content for 'container.xml' file."
        result = minixml.Element(
            "container",
            version="1.0",
            xmlns="urn:oasis:names:tc:opendocument:xmlns:container",
        )
        rootfile = result.create("rootfiles").create("rootfile")
        rootfile["media-type"] = "application/oebps-package+xml"
        rootfile["full-path"] = "OEBPS/content.opf"
        return repr(result)

    def get_content_opf(self):
        "Return XML content for the 'content.opf' file."
        root = minixml.Element(
            "package", xmlns="http://www.idpf.org/2007/opf", version="3.0"
        )
        root["xmlns:dc"] = "http://purl.org/dc/elements/1.1/"
        root["unique-identifier"] = "identifier"
        metadata = root.create("metadata")
        metadata.create("dc:title", id="title").append(self.title)
        metadata.create("dc:identifier", id="identifier").append(self.identifier)
        metadata.create("dc:language").append(self.language)
        for pos, creator in enumerate(self.creators, start=1):
            metadata.create("dc:creator", id=f"creator{pos}").append(creator)
        for pos, contributor in enumerate(self.contributors, start=1):
            metadata.create("dc:contributor", id=f"contributor{pos}").append(
                contributor
            )
        if self.type:
            metadata.create("dc:type").append(self.type)
        if self.source:
            metadata.create("dc:source").append(self.source)
        if self.subject:
            metadata.create("dc:subject").append(self.subject)
        if self.description:
            metadata.create("dc:description").append(self.description)
        if self.publisher:
            metadata.create("dc:publisher").append(self.publisher)
        if self.rights:
            metadata.create("dc:rights").append(self.rights)
        if self.date:
            metadata.create("dc:date").append(self.date)
        metadata.create("meta", property="dcterms:modified").append(
            dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        manifest = root.create("manifest")
        if self.toc_stylename:
            item = manifest.create("item", id="toc", href="toc.xhtml", properties="nav")
            item["media-type"] = "application/xhtml+xml"
        for name in self.css:
            item = manifest.create("item", id=f"{name}_css", href=f"CSS/{name}.css")
            item["media-type"] = "text/css"
        for section in self.get_all_sections():
            item = manifest.create(
                "item", id=section.name, href=f"{section.name}.xhtml"
            )
            item["media-type"] = "application/xhtml+xml"

        spine = root.create("spine")
        if self.toc_stylename:
            spine.create("itemref", idref="toc")
        for section in self.get_all_sections():
            spine.create("itemref", idref=section.name)
        return repr(root)

    def get_toc_xhtml(self):
        "Return the XHTML content for the TOC file."
        assert self.toc_stylename
        html = minixml.Element("html", xmlns="http://www.w3.org/1999/xhtml")
        html["xmlns:epub"] = "http://www.idpf.org/2007/ops"
        head = html.create("head")
        head.create("title").append("TOC")
        head.create(
            "link",
            href=f"CSS/{self.toc_stylename}.css",
            rel="stylesheet",
            type="text/css",
        )
        nav = html.create("body").create("nav", id="toc")
        nav["epub:type"] = "toc"
        h1 = nav.create("h1")
        h1["class"] = "frontmatter"
        h1.append("Table of contents")
        ol = nav.create("ol")
        ol["class"] = "contents"
        for name, section in self.sections.items():
            li = ol.create("li")
            li.create("a", href=f"{name}.xhtml").append(section.toc_title)
            section.append_sections_list(li)
        return repr(html)

    def write(self, outfile):
        "Write the EPUB3 file."
        with zipfile.ZipFile(
            outfile, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as zip:
            zip.writestr(
                "mimetype",
                "application/epub+zip",
                compress_type=zipfile.ZIP_STORED,
                compresslevel=0,
            )
            zip.writestr("META-INF/", "")
            zip.writestr("META-INF/container.xml", self.get_container_xml())
            zip.writestr("OEBPS/", "")
            zip.writestr("OEBPS/CSS/", "")
            for name, content in self.css.items():
                zip.writestr(f"OEBPS/CSS/{name}.css", content)
            zip.writestr("OEBPS/content.opf", self.get_content_opf())
            if self.toc_stylename:
                zip.writestr("OEBPS/toc.xhtml", self.get_toc_xhtml())
            for section in self.get_all_sections():
                zip.writestr(f"OEBPS/{section.name}.xhtml", str(section))


class Section:
    "Section in Book; XHTML code container."

    def __init__(self, name, toc_title=None, content=None, stylename="default"):
        """The 'name' is used for the XHTML file in the EPUB3 book.
        It must be unique in the book.
        The 'toc_title' is used for the HTML HEAD element and for the TOC.
        If None, then this section will not present in the TOC.
        The 'toc_title' is *not* output to the beginning of the content BODY.
        """
        assert name
        assert content is None or isinstance(content, (str, minixml.Element))
        self.name = name
        self.toc_title = toc_title
        self.stylename = stylename
        self.content = minixml.Element("html", xmlns="http://www.w3.org/1999/xhtml")
        self.content["xmlns:epub"] = "http://www.idpf.org/2007/ops"
        head = self.content.create("head")
        head.create("title").append(toc_title)
        if stylename:
            head.create(
                "link", href=f"CSS/{stylename}.css", rel="stylesheet", type="text/css"
            )
        self.body = self.content.create("body")
        if content:
            self.append(content)
        self.subsections = {}

    def __str__(self):
        "Return the XHTML code for the file."
        return repr(self.content)

    def append(self, content):
        """The content is either an 'minixml.Element' instance or a string.
        If a string, then it will be parsed using 'minixml.parse'.
        The content must *not* contain the 'html', 'head' and 'body' elements; these
        elements are automatically wrapped around the content, which must be valid XHTML.
        """
        if isinstance(content, str):
            for elem in list(minixml.parse(f"<tmp>{content}</tmp>").children):
                self.body.append(elem.free())
        elif isinstance(content, minixml.Element):
            self.body.append(content)
        else:
            raise ValueError(f"invalid content type: {type(content)}")

    def add_section(self, section):
        "Add a named subsection. The order of addition is significant."
        assert isinstance(section, Section)
        assert section.stylename is None or section.stylename in self.book.css
        self.subsections[section.name] = section
        section.book = self.book

    def get_all_sections(self):
        "Get all subsections recursively as list of sections."
        result = []
        for subsection in self.subsections.values():
            result.append(subsection)
            result.extend(subsection.get_all_sections())
        return result

    def append_sections_list(self, li):
        """Append the subsections of this section to the TOC list item, recursively.
        If the 'toc_title' of a subsection is None, it will not be added to the list.
        """
        subsections = [s for s in self.subsections.values() if s.toc_title]
        if not subsections:
            return
        ol = li.create("ol")
        for subsection in subsections:
            li = ol.create("li")
            li.create("a", href=f"{subsection.name}.xhtml").append(subsection.toc_title)
            subsection.append_sections_list(li)


DEFAULT_CSS = """body {
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
}
"""


if __name__ == "__main__":
    import pathlib

    book = Book("abc123", "Test")
    book.creators.append("Per Kraulis")
    book.contributors.append(f"miniepub3 {__version__}")
    book.type = "test"
    book.source = "Python"
    book.subject = "testing"
    book.description = "Testing a few chapters, a subsection, and a TOC."
    book.add_section(
        "chapter_1",
        Section(
            "Chapter 1",
            content="""<h1>Chapter 1</h1>

    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi id lectus dictum, lobortis urna a, luctus libero. Integer ultricies nisi nec nisi gravida, sit amet tempor diam posuere. Morbi consequat libero fringilla pellentesque venenatis. Donec ut porta metus. Etiam condimentum cursus elit pulvinar gravida. Nulla consequat interdum leo sed tincidunt. Suspendisse potenti. Integer pretium cursus libero, eu ornare erat dictum eu. Cras ultrices mi vel odio tempus fringilla. Nulla tristique nisi nisl, id scelerisque risus gravida a. Proin neque tellus, efficitur eu dictum hendrerit, lacinia vel neque. Proin augue risus, maximus ac eros consectetur, finibus mattis metus. Donec ut dictum diam. Vestibulum tempor orci id ultrices lacinia. Praesent bibendum, mi vitae euismod condimentum, eros enim tincidunt odio, id semper erat nisl vitae nisi. Nunc convallis mi sit amet velit venenatis vestibulum ac at mauris.</p>

	<p>Duis vestibulum elit non tortor luctus ultrices. Nulla facilisi. Aliquam rhoncus, est at elementum semper, tortor risus pretium diam, eget condimentum ipsum felis eget sapien. Nullam elit urna, lacinia a metus luctus, varius ultrices lectus. In pellentesque erat sit amet magna fringilla, in luctus lectus accumsan. Nulla tincidunt dignissim eleifend. Duis lacinia risus facilisis lacus tempor, et facilisis est ornare. Quisque vel sem congue, varius eros in, consequat purus. Nulla sodales id dui ut fermentum. Vestibulum sed justo sed sapien placerat congue. Nam in bibendum purus.</p>

	<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. In tincidunt, ex sed lobortis interdum, purus dui fermentum ex, non dictum ex quam eu nunc. Suspendisse potenti. Aenean ultricies commodo hendrerit. Etiam tristique sagittis tellus. Aliquam erat volutpat. Maecenas vitae tristique nulla. Sed vitae volutpat ex, et hendrerit ipsum. Nullam vehicula velit vitae vehicula maximus.</p>

	<p>Praesent ut nisi pellentesque, cursus nulla ac, vulputate leo. Fusce ultricies, magna cursus vestibulum viverra, erat eros maximus ex, id faucibus risus augue in sapien. Quisque tortor augue, pulvinar ac felis at, bibendum sollicitudin massa. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed mauris ipsum, sollicitudin facilisis velit non, tempus accumsan purus. Donec eget pharetra ipsum. Nullam vulputate malesuada ipsum sed mollis. Nulla porta elit nec egestas consequat. Fusce a purus viverra, ultrices sapien in, varius leo. Nam at tellus vel tortor pulvinar pulvinar sed sit amet ex. Quisque vestibulum placerat massa, ut porta eros blandit euismod. Nullam vitae nulla sed neque eleifend lobortis sed non lacus. Etiam vulputate mollis sapien sed ornare.</p>

	<p>Nullam eros diam, hendrerit vel nibh in, malesuada aliquet massa. Nam blandit egestas massa, sit amet efficitur erat luctus vel. In eu leo at nibh egestas venenatis vel nec eros. Nulla bibendum sapien vel velit iaculis, in feugiat risus vestibulum. Suspendisse placerat laoreet eros, et ullamcorper est ornare eu. Praesent imperdiet lacus vel vehicula accumsan. Donec fringilla odio velit. Cras tempus est in lacus eleifend, cursus pellentesque lorem vehicula. Ut metus turpis, posuere eget imperdiet eget, bibendum in tortor. Mauris id dolor tellus. Suspendisse at nisi tellus. Duis lectus arcu, pulvinar et pretium in, tincidunt facilisis nulla. Nulla ullamcorper aliquam ullamcorper. Nunc ultricies nibh vitae urna hendrerit varius.</p>""",
        ),
    )
    book.add_section(
        "chapter_2",
        Section(
            "Chapter 2",
            content="""<h1>Chapter 2</h1>

    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas id ex urna. Quisque at fringilla ex. Aliquam erat volutpat. Nullam ac dignissim eros, sed iaculis dolor. Nullam sit amet libero convallis, porttitor nisl sed, pulvinar dolor. Vivamus ornare libero ipsum, eget interdum lorem viverra sed. Praesent sollicitudin viverra mauris ut gravida. Cras nec lorem id velit malesuada auctor. Pellentesque dignissim tortor vel tempus mattis. Integer sapien tortor, dignissim non purus eget, laoreet convallis dolor. Morbi vitae ante non tortor pharetra rutrum. Fusce pretium sapien nulla, sed pretium tortor ultrices sit amet.</p>

	<p>Morbi sed euismod est, ut sodales erat. In hac habitasse platea dictumst. Mauris ipsum diam, venenatis vitae turpis sit amet, blandit consectetur arcu. Aliquam non aliquet augue, in pharetra velit. Quisque dapibus bibendum lorem sed rutrum. Maecenas blandit sit amet lorem tempus viverra. Nulla commodo, orci sed eleifend efficitur, felis est dapibus felis, non mollis nibh tellus quis nunc. Curabitur vulputate velit orci. Duis laoreet erat augue. Maecenas nisi enim, congue vitae accumsan quis, tincidunt quis velit. Morbi vel leo ultricies, bibendum nibh at, posuere massa. Integer iaculis scelerisque elit.</p>

	<p>Cras id porttitor nulla, eget consequat dui. Praesent volutpat placerat lorem a semper. Nulla facilisi. Vestibulum at tincidunt velit, ac consectetur diam. Nunc non arcu eget orci bibendum fermentum sed eget sapien. Vivamus rutrum scelerisque consectetur. Mauris nec augue sed est dignissim sagittis. Praesent ac urna quis justo ornare convallis quis et justo. Proin nunc metus, malesuada a nibh sit amet, eleifend facilisis tortor.</p>

	<p>Curabitur at consequat lorem, sollicitudin consequat elit. Morbi tempor non justo non hendrerit. Donec sit amet consectetur odio. Mauris cursus elit a vestibulum rutrum. Aliquam varius sit amet nulla vel lobortis. Curabitur dictum arcu velit, id feugiat turpis blandit a. Mauris euismod urna ac metus fringilla, sit amet vestibulum neque sagittis. Aenean et luctus nibh. Suspendisse sit amet scelerisque lacus, eget rutrum augue. Sed finibus id dolor vitae tempor. Duis convallis sit amet lacus eu porttitor. Mauris tempus, mi ut porta faucibus, ex enim mattis ante, et efficitur ipsum lectus at diam. Nunc ut ullamcorper odio. Nunc varius pulvinar elit nec faucibus. Donec nec diam tempus, congue lorem vel, elementum justo. Mauris auctor enim non nisi finibus placerat.</p>

	<p>Fusce vel lobortis sem, id mollis dui. Fusce iaculis erat magna, quis dignissim sapien porttitor ultrices. Duis ornare ipsum neque, ut sodales nulla elementum vel. Ut quam nibh, laoreet in orci sit amet, tristique imperdiet arcu. Fusce vitae hendrerit metus, sit amet porta erat. Duis finibus egestas mauris, eu volutpat nisi tempus in. Sed porttitor leo massa, ut condimentum dui lacinia sed. Morbi varius, augue et dignissim venenatis, erat ligula luctus nibh, et vulputate quam arcu at quam. Praesent faucibus ex lorem, a volutpat quam varius eu. Fusce efficitur iaculis diam, non sagittis neque imperdiet volutpat. Ut in velit dignissim, malesuada nunc non, iaculis massa. In hac habitasse platea dictumst.</p>

	<p>In tincidunt urna in est dapibus, non gravida orci lobortis. Pellentesque quis sem nec felis dictum sollicitudin a in magna. Integer tristique placerat est ut congue. Maecenas tincidunt purus vel purus convallis, id molestie enim tincidunt. Curabitur lobortis ac sapien sed accumsan. Quisque dapibus lacus lacus, nec rhoncus mauris viverra at. Integer leo magna, porta at euismod vel, placerat at lorem. Cras consequat sapien et scelerisque faucibus. Integer ultrices fermentum lacus, sed posuere nisl lobortis efficitur. Morbi aliquet lorem ut ante consequat consectetur. Quisque vel velit sed nisi tristique placerat quis in massa.</p>

	<p>Cras in est sem. Aliquam feugiat odio lorem, vel tempor massa laoreet at. Fusce ac porttitor felis. Donec ultrices urna mi, vitae vulputate mi faucibus sed. Curabitur in dui diam. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Nam eu finibus elit. Aenean laoreet pharetra erat, sit amet fermentum erat interdum sodales. Vestibulum ut lectus condimentum, vestibulum mi non, venenatis nunc. Fusce elementum arcu leo, ac rhoncus neque eleifend a.</p>

	<p>Proin massa arcu, interdum quis nibh volutpat, mattis pharetra leo. Sed tempus elit ac nunc feugiat, vel pharetra lorem dapibus. Aenean gravida neque sed orci viverra sagittis. Nunc semper sed ipsum quis laoreet. Cras sodales lacinia ornare. Proin sed mauris tortor. Ut sagittis diam augue, nec porta ante vehicula id. Cras gravida magna sollicitudin felis consequat, gravida posuere diam pulvinar. Vestibulum aliquam justo luctus ultrices iaculis. Nam vel hendrerit libero.</p>

	<p>Integer tincidunt facilisis dapibus. Integer viverra porta risus, a sagittis nulla congue sit amet. Cras placerat pulvinar pharetra. Nam malesuada tempor odio at suscipit. Morbi est mauris, facilisis vel dolor in, tincidunt rutrum erat. Phasellus quis ex feugiat, pharetra nisi eu, dapibus lacus. Sed tempus a felis id rhoncus. Pellentesque vel pellentesque lacus. Ut ut consectetur diam. Maecenas vitae rutrum erat, quis porta massa. Proin in tellus at metus tempus condimentum. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Aliquam ac egestas est. Vivamus hendrerit tempor dui, eu vehicula elit. Quisque felis felis, faucibus sit amet ligula at, porta elementum metus. Suspendisse iaculis metus vitae enim tincidunt, quis fermentum leo cursus.</p>

	<p>Proin a lobortis justo. Morbi metus ante, tempor id augue sit amet, finibus luctus nibh. Sed efficitur vehicula posuere. Fusce rutrum placerat auctor. Vestibulum ut sollicitudin purus. Praesent ullamcorper ex nisi, vitae finibus risus congue eu. Fusce volutpat efficitur commodo. Fusce pulvinar lobortis sodales. Proin eget eros ac augue pulvinar efficitur. Mauris at condimentum mi. Sed sit amet mi vel tortor interdum cursus.</p>""",
        ),
    )
    section = Section(
        "Copyright",
        content="""<h1>Copyright</h1>

    <p>You can create all sorts of pages that are not chapters as well, and simply give them different names.  As an idea you could use a page like this, and either list your name as the copyright or list it under another copyright, such as the <a href="https://en.wikipedia.org/wiki/GNU_General_Public_License">GNU License</a></p>""",
    )

    book.add_section("copyright", section)
    section.add_section(
        "additional", Section("Additional stuff", content="<p>Some more stuff.</p>")
    )
    book.write("minimal.epub")
