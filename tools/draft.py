"""Parse an article draft written in the agreed markdown format."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


class DraftError(ValueError):
    """The draft (or approved file) cannot be turned into a page."""


@dataclass(frozen=True)
class Section:
    title: str
    body_md: str


@dataclass(frozen=True)
class Article:
    headline: str
    subheadline: str
    benefits: list
    con: Section
    conclusion: Section
    intro_md: str = ""


_BENEFIT = re.compile(r"^benefit\s+(\d+)\s*:", re.I)


def parse_draft(text: str) -> Article:
    headline = subheadline = None
    intro: list = []
    sections: list = []  # [title, [lines]]
    for line in text.splitlines():
        if line.startswith("## "):
            sections.append([line[3:].strip(), []])
        elif sections:
            sections[-1][1].append(line)
        elif line.startswith("### ") and subheadline is None:
            subheadline = line[4:].strip()
        elif line.startswith("# ") and headline is None:
            headline = line[2:].strip()
        else:
            intro.append(line)
    if not headline:
        raise DraftError("Draft has no headline (first line must start with '# ').")
    if not subheadline:
        raise DraftError("Draft has no sub headline (a line starting with '### ').")

    benefits: dict = {}
    con = conclusion = None
    for title, lines in sections:
        sec = Section(title, "\n".join(lines).strip())
        m = _BENEFIT.match(title)
        if m:
            n = int(m.group(1))
            if n not in (1, 2, 3):
                raise DraftError(f"Unexpected section '{title}': use exactly Benefit 1, Benefit 2 and Benefit 3.")
            benefits[n] = sec
        elif title.lower().startswith("the one con"):
            con = sec
        elif title.lower() == "conclusion":
            conclusion = sec
        else:
            raise DraftError(f"Unknown section '## {title}'.")
    for n in (1, 2, 3):
        if n not in benefits:
            raise DraftError(f"Missing section: Benefit {n} (write '## Benefit {n}: ...').")
    if con is None:
        raise DraftError("Missing section: The one con (write '## The one con: ...').")
    if conclusion is None:
        raise DraftError("Missing section: Conclusion (write '## Conclusion').")
    return Article(headline, subheadline, [benefits[1], benefits[2], benefits[3]],
                   con, conclusion, "\n".join(intro).strip())
