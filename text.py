"Frontmatter and text read from a Markdown (.md) file, possibly with sections."

import datetime as dt
import pathlib
import re

import markdown
import yaml

import constants


class Text:
    "Frontmatter and text read from a Markdown (.md) file, possibly with sections."

    FRONTMATTER = re.compile(r"^---([\n\r].*?[\n\r])---[\n\r](.*)$", re.DOTALL)

    def __init__(self, filename, supertext=None):
        self.filename = pathlib.Path(filename)
        self.supertext = supertext
        self.read()

    def __iter__(self):
        return iter(self.sections)

    def read(self):
        "Read this Markdown file and any sections it specifies."
        content = self.filename.read_text()
        match = self.FRONTMATTER.match(content)
        if match:
            self.frontmatter = yaml.safe_load(match.group(1))
            self.text = content[match.start(2) :]
        else:
            self.frontmatter = {}
            self.text = content
        self.sections = [
            Text(filename, self) for filename in self.frontmatter.get("sections", [])
        ]

    @property
    def modified(self):
        return dt.datetime.fromtimestamp(self.filename.stat().st_mtime)

    @property
    def title(self):
        return self.frontmatter.get("title", "no title")

    @property
    def subtitle(self):
        return self.frontmatter.get("subtitle")

    @property
    def toc(self):
        return self.frontmatter.get("toc", True)

    @property
    def authors(self):
        return self.frontmatter.get("authors", [])

    @property
    def language(self):
        return self.frontmatter.get("language", constants.SV_SE)

    @property
    def title_page_metadata(self):
        return self.frontmatter.get("title_page_metadata", False)

    @property
    def output_comments(self):
        return self.frontmatter.get("output_comments", False)

    @property
    def page_break_level(self):
        return self.frontmatter.get("page_break_level", 1)

    @property
    def footnotes_location(self):
        return self.frontmatter.get("footnotes_location", constants.FOOTNOTES_EACH_TEXT)

    @property
    def exclude(self):
        return self.frontmatter.get("exclude", False)

    def ast(self):
        return markdown.to_ast(self.text)


if __name__ == "__main__":
    t = Text("main.md")
    print(t.modified)
