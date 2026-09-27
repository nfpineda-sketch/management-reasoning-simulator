"""A screen's own words in the reader's language (faculty, 2026-09-26).

"Whatever the app stores can be seen in English or Spanish." The portals and
screens say their own words -- titles, captions, buttons, notices -- from the
same reviewed catalog the documents use (``report_language``), in the language
the reader chose in the sidebar. English is returned untouched. What is stored
is shown as stored: the resident's words, the model's prose, the clinical
identifiers; the case's own narrative follows its faculty approval (case_text).
"""


def t(text, **values):
    """The screen's own words, with their values named so Spanish can order them."""
    import language
    import report_language
    said = report_language.t(text, language.current())
    return said.format(**values) if values else said


def rows(table):
    """A table's column names in the reader's language; its cells are shown as given."""
    return [{t(name): value for name, value in row.items()} for row in table]
