"Read frontmatter and text from a Markdown (.md) file, possibly with subtexts."

import datetime as dt

import markdown
import yaml

import constants


def read_texts(directory, text_filename, supertext=None, ordinal=None):
    """Read the Markdown file(s) in the given directory,
    and recursively in any subdirectories.
    """
    root = Text(directory / text_filename, supertext=supertext, ordinal=ordinal)
    ordinal = 0
    for path in sorted(directory.iterdir()):
        if path.name == text_filename:
            continue
        if path.name == constants.README_FILENAME:
            continue
        if path.name.startswith("."):
            continue
        if path.is_dir():
            ordinal += 1
            read_texts(path, text_filename, supertext=root, ordinal=ordinal)
        elif path.suffix == ".md":
            ordinal += 1
            Text(path, supertext=root, ordinal=ordinal)
    return root


def split_file(filepath):
    "Read the Markdown file, parse the YAML frontmatter, and return it and the text."
    assert filepath.exists(), filepath
    assert filepath.suffix == ".md", filepath
    content = filepath.read_text()
    match = constants.FRONTMATTER.match(content)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        text = content[match.start(2) :]
    else:
        frontmatter = {}
        text = content
    return (frontmatter, text)


class Text:
    "Read frontmatter and text from a Markdown (.md) file."

    def __init__(self, filepath, supertext=None, ordinal=None):
        """Read the Markdown file, if it exists.
        Parse the YAML into frontmatter.
        Convert the Markdown text into AST.
        Include into the supertext, if any.
        """
        self.filepath = filepath
        if supertext is None:
            self.ordinal = ()
        else:
            self.ordinal = supertext.ordinal + (ordinal,)
            supertext.subtexts.append(self)
        self.supertext = supertext
        if self.filepath.exists():
            self.frontmatter, self.text = split_file(self.filepath)
        elif self.supertext is None:
            raise FileNotFoundError(f"no such file '{filepath}'")
        else:
            self.frontmatter = {}
            self.text = ""
        self.ast = markdown.to_ast(self.text)
        # Discard redundant item; link defs are included in-place in the AST.
        self.ast.pop("link_ref_defs", None)
        # Store the footnote definitions for later handling.
        self.footnotes = self.ast.pop("footnotes", {})
        self.subtexts = []

    def __repr__(self):
        return f'Text("{self.filepath}")'

    def __len__(self):
        "Number of texts, including this one and its subtexts."
        # XXX Why does 'list(self)' give infinite recursion?
        return len([t for t in self])

    def __iter__(self):
        "Yield this text and all its subtexts in order."
        yield self
        for subtext in self.subtexts:
            yield from iter(subtext)

    @property
    def root(self):
        "Return the root text."
        text = self
        while text.supertext is not None:
            text = text.supertext
        return text

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
        if self.filepath.exists():
            result = dt.datetime.fromtimestamp(self.filepath.stat().st_mtime)
        else:
            result = dt.datetime.fromtimestamp(self.filepath.parent.stat().st_mtime)
        for subtext in self.subtexts:
            result = max(result, subtext.modified)
        return result

    @property
    def title(self):
        "The title for this text."
        try:
            return self.frontmatter["title"]
        except KeyError:
            if self.filepath.name == constants.TEXT_FILENAME:
                title = self.filepath.parent.stem
            else:
                title = self.filepath.stem
            title = title.replace("_", " ")
            parts = title.split()
            if parts[0].isdigit():
                return " ".join(parts[1:])
            else:
                return title

    @property
    def ordinal_title(self):
        "The title for this text with the text ordinal prepended."
        return f"{'.'.join([str(i) for i in self.ordinal])}. {self.title}"

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
        return self.frontmatter.get("language", constants.SV_SE)

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
