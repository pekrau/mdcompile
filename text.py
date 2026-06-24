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
        return f'Text("{self.filename}")'

    def __len__(self):
        "Number of texts."
        # XXX Why does 'list(self)' give infinite recursion?
        return len([t for t in self])

    def __iter__(self):
        "Yield this text and all its subtexts in order."
        yield self
        for subtext in self.subtexts:
            yield from iter(subtext)

    @property
    def main(self):
        "Return the main (root) text in the hierarchy."
        text = self
        while text.supertext is not None:
            text = text.supertext
        return text

    @property
    def ordinal(self):
        "The position if this text in its parent's subtexts list."
        text = self
        supertext = self.supertext
        result = []
        while supertext is not None:
            result.append(supertext.subtexts.index(text))
            text = supertext
            supertext = text.supertext
        return tuple(reversed(result))

    @property
    def level(self):
        "Level of the text in the hierarchy."
        result = 0
        supertext = self.supertext
        while supertext is not None:
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
        return self.frontmatter.get("title") or self.filename.stem.replace("_", " ")

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
        "Return the language used. From the nearest text."
        return self._get_nearest("language", constants.SV_SE)

    @property
    def title_page_metadata(self):
        "Whether to display metadata in the title page. From the main text."
        return self.main.frontmatter.get("title_page_metadata", False)

    @property
    def output_comments(self):
        "Whether comments are to be output. From the nearest text."
        return self._get_nearest("output_comments", False)

    @property
    def page_break_level(self):
        "Hierarchy level at which to do page break. From the main text."
        return self.main.frontmatter.get("page_break_level", 1)

    @property
    def toc_level(self):
        "The table-of-contents level. From the main text."
        return self.main.frontmatter.get("toc_level", 1)

    @property
    def footnotes_location(self):
        "The footnotes location. From the main text."
        return self.main.frontmatter.get("footnotes_location", constants.FOOTNOTES_TEXT)

    @property
    def indexed_font(self):
        "The font modifier use for display of indexed terms. From the main text."
        return self.main.frontmatter.get("indexed_font", constants.UNDERLINE)

    @property
    def reference_font(self):
        "The font modifier use for display of reference. From the main text."
        return self.main.frontmatter.get("reference_font", constants.NORMAL)

    def elements(self):
        "Return an iterator over the AST elements of this text."
        return ASTIterator(self.ast)

    def _get_nearest(self, key, default=None):
        text = self
        while text is not None:
            try:
                return self.frontmatter[key]
            except KeyError:
                pass
            text = text.supertext
        else:
            return default


class ASTIterator:

    def __init__(self, ast):
        self.ast = ast

    def __iter__(self):
        yield self.ast
        try:
            children = self.ast["children"]
            if isinstance(children, list):
                for ast in children:
                    yield from iter(ASTIterator(ast))
        except KeyError:
            pass


if __name__ == "__main__":
    t = Text("main.md")
    for t2 in list(t):
        print("   ", t2, t2.ordinal)
        for e in t2.elements():
            print(e["element"])
