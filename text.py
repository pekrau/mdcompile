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

    def elements(self):
        "Return an iterator over the AST elements of this text."
        return AstIterator(self.ast)


class AstIterator:

    def __init__(self, ast):
        self.ast = ast

    def __iter__(self):
        yield self.ast
        try:
            children = self.ast["children"]
            if isinstance(children, list):
                for ast in children:
                    yield from iter(AstIterator(ast))
        except KeyError:
            pass


if __name__ == "__main__":
    t = Text("main.md")
    for t2 in list(t):
        print("   ", t2, t2.ordinal)
        for e in t2.elements():
            print(e["element"])
