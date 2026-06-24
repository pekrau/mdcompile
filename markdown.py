"Markdown converters."

import re

import marko
import marko.html_renderer
import marko.ast_renderer
import marko.inline
import marko.helpers

import constants
import utils


class Subscript(marko.inline.InlineElement):
    "Markdown extension for subscript."

    pattern = re.compile(r"(?<!~)(~)([^~]+)\1(?!~)")
    priority = 5
    parse_children = True
    parse_group = 2


class SubscriptRenderer:
    "Output subscript text."

    def render_subscript(self, element):
        return f"<sub>{self.render_children(element)}</sub>"


class Superscript(marko.inline.InlineElement):
    "Markdown extension for superscript."

    pattern = re.compile(r"(?<!\^)(\^)([^\^]+)\1(?!\^)")
    priority = 5
    parse_children = True
    parse_group = 2


class SuperscriptRenderer:
    "Output superscript text."

    def render_superscript(self, element):
        return f"<sup>{self.render_children(element)}</sup>"


class Emdash(marko.inline.InlineElement):
    "Markdown extension for em-dash."

    pattern = re.compile(r"(\-\-)(?=\s)")
    parse_children = False


class EmdashRenderer:
    "Output em-dash character."

    def render_emdash(self, element):
        return constants.EM_DASH


class Indexed(marko.inline.InlineElement):
    "Markdown extension for an indexed term."

    pattern = re.compile(r"\[#(.+?)(\|(.+?))?\]", re.S)  # Yes, this isn't quite right.
    parse_children = False

    def __init__(self, match):
        self.term = match.group(1).strip()
        if match.group(3):  # Because of the not-quite-right regexp...
            self.canonical = " ".join(match.group(3).strip().split())
        else:
            self.canonical = " ".join(self.term.split())


class IndexedRenderer:
    "Output a link to the index page and item."

    def render_indexed(self, element):
        if element.term == element.canonical:
            title = "Indexed"
        else:
            title = "Indexed" + ": " + element.canonical
        return f'<a class="contrast" title="{title}" href="{get_index_href(element.canonical)}">{element.term}</a>'


class Reference(marko.inline.InlineElement):
    "Markdown extension for reference."

    pattern = re.compile(r"\[@(.+?)\]")
    parse_children = False

    def __init__(self, match):
        self.name = match.group(1).strip()


class ReferenceRenderer:
    "Output a link to the reference page and item."

    def render_reference(self, element):
        return f'<strong><a href="/refs/view/{element.id}">{element.name}</a></strong>'


class Comment(marko.inline.InlineElement):
    "Markdown extension for comment."

    pattern = re.compile(r"\[!(.+?)\]")
    parse_children = False

    def __init__(self, match):
        self.comment = match.group(1).strip()


class CommentRenderer:
    "Output a the comment text."

    def render_comment(self, element):
        return f'<span class="comment">{element.comment}</span>'


class ThematicBreakRenderer:
    "Thematic break before a paragraph."

    def render_thematic_break(self, element):
        return '<hr class="break" />\n'


def to_ast(content):
    "Convert Markdown content into an AST (Abstract Syntax Tree) structure."
    converter = marko.Markdown(renderer=marko.ast_renderer.ASTRenderer)
    converter.use("footnote")
    converter.use(
        marko.helpers.MarkoExtension(
            elements=[Subscript, Superscript, Emdash, Indexed, Reference, Comment],
        )
    )
    ast = converter.convert(content)
    # Corrent the weird left-over class instances in the 'footnotes' list items.
    for key, value in list(ast["footnotes"].items()):
        ast["footnotes"][key] = converter.renderer.render_children(value)
    return ast


def to_html(content):
    converter = marko.Markdown()
    converter.use("footnote")
    converter.use(
        marko.helpers.MarkoExtension(
            elements=[
                Subscript,
                Superscript,
                Emdash,
                Indexed,
                Reference,
                Comment,
            ],
            renderer_mixins=[
                SubscriptRenderer,
                SuperscriptRenderer,
                EmdashRenderer,
                IndexedRenderer,
                ReferenceRenderer,
                CommentRenderer,
                ThematicBreakRenderer,
            ],
        )
    )
    return converter.convert(content)
