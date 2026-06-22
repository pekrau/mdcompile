---
title: The second chapter.
---
This is chapter 2.

Here is a second footnote[^footnote2].

Some Python code:
```
def write_text(self, text, level=1):
    if level <= self.main.page_break_level:
        self.doc.add_page_break()
    self.write_heading(text.title, level)
    if text.subtitle:
        self.write_heading(text.subtitle, level + 1)
    self.current_text = text

    Renderer(self)(text.ast())

    # if self.footnotes_location == constants.FOOTNOTES_TEXT:
    #     self.write_text_footnotes(text)

    for subtext in text.subtexts:
        self.write_text(subtext, level=level + 1)
```

[^footnote2]: And this is the definition of the second footnote.
