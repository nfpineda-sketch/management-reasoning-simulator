"""The colours of the faculty documents, defined once.

``faculty_report`` wraps these in ReportLab colours for the page; the rubric
radar draws the same palette as SVG for the screen, where importing ReportLab
would be a page-rendering dependency in a browser view. Two copies of a hex
string drift, and a chart that is nearly the document's blue looks like a
mistake rather than a family.
"""

NAVY = "#16324F"
BLUE = "#1671A6"
ORANGE = "#D57C2A"
INK = "#243746"
MUTED = "#63788A"
PALE = "#F0F5F9"
LINE = "#D8E2EB"
