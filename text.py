"Frontmatter and text read from a Markdown (.md) file, possibly with subtexts."

import datetime as dt
import json
import pathlib
import re

import markdown
import yaml

import constants


class Text:
    "Frontmatter and text read from a Markdown (.md) file, possibly with subtexts."

    FRONTMATTER = re.compile(r"^---([\n\r].*?[\n\r])---[\n\r](.*)$", re.DOTALL)

    def __init__(self, filename, supertext=None):
        "Read this Markdown file and any subtexts it specifies and convert into AST."
        self.filename = pathlib.Path(filename)
        self.supertext = supertext
        content = self.filename.read_text()
        match = self.FRONTMATTER.match(content)
        if match:
            self.frontmatter = yaml.safe_load(match.group(1))
            self.text = content[match.start(2) :]
        else:
            self.frontmatter = {}
            self.text = content
        self.subtexts = [
            Text(filename, self) for filename in self.frontmatter.get("subtexts", [])
        ]
        self.ast = markdown.to_ast(self.text)
        # ========== XXX debug
        self.filename.with_suffix(".json").write_text(json.dumps(self.ast, indent=2))
        # ==========
        # The link definitions are included in-place in the AST. Redundant here; remove.
        self.ast.pop("link_ref_defs", None)
        # Store the footnote definitions for later handling.
        self.footnotes = self.ast.pop("footnotes", {})

    def __repr__(self):
        return f"Text({self.filename})"

    def all_texts(self):
        "Return the list of this text and its subtexts in order."
        result = [self]
        for subtext in self.subtexts:
            result.extend(subtext.all_texts())
        return result

    @property
    def main(self):
        "Return the main (root) text in the hierarchy."
        text = self
        while text.supertext:
            text = supertext
        return text

    @property
    def level(self):
        "Level of the text in the hierarchy."
        result = 0
        supertext = self.supertext
        while supertext:
            result += 1
            supertext = supertext.supertext
        return result

    @property
    def modified(self):
        "The most recently modified of this text and its subtexts (if any)."
        result = dt.datetime.fromtimestamp(self.filename.stat().st_mtime)
        for subtext in self.subtexts:
            result = max(result, subtext.modified)
        return result

    @property
    def title(self):
        "The title for this text."
        return self.frontmatter.get("title") or self.filename.stem

    @property
    def subtitle(self):
        "The subtitle for this text (if any)."
        return self.frontmatter.get("subtitle")

    @property
    def authors(self):
        "Return the author(s) for this text."
        return self.frontmatter.get("authors", [])

    @property
    def language(self):
        "Return the language used. Defined in the nearest text."
        return self.get_nearest("language", constants.SV_SE)

    @property
    def title_page_metadata(self):
        "Whether to display metadata in the title page. Defined in the main text."
        return self.main.frontmatter.get("title_page_metadata", False)

    @property
    def output_comments(self):
        "Whether comments are to be output. Defined in the nearest text."
        return self.get_nearest("output_comments", False)

    @property
    def page_break_level(self):
        "Hierarchy level at which to do page break. Defined in the main text."
        return self.main.frontmatter.get("page_break_level", 1)

    @property
    def toc_level(self):
        "The table-of-contents level. Defined in the main text."
        return self.main.frontmatter.get("toc_level", 1)

    @property
    def footnotes_location(self):
        "The footnotes location. Defined in the main text."
        return self.main.frontmatter.get("footnotes_location", constants.FOOTNOTES_TEXT)

    def get_nearest(self, key, default=None):
        text = self
        while text:
            try:
                return self.frontmatter[key]
            except KeyError:
                pass
            text = text.supertext
        else:
            return default


if __name__ == "__main__":
    t = Text("main.md")
    print(t.modified)
    for t2 in t.all_texts():
        print(t2, t2.level)
