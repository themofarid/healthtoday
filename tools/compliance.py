"""Checks for risky health claims and the required disclosure wording."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass

from tools.templates import DISCLOSURE, MEDICAL_NOTE

DISCLOSURE_WINDOW = 600


@dataclass(frozen=True)
class Issue:
    kind: str  # 'claim', 'disclosure' or 'medical-note'
    phrase: str
    line: int


class ComplianceError(Exception):
    def __init__(self, issues: list, source: str = ""):
        self.issues = issues
        prefix = f"{source}: " if source else ""
        lines = [f"{prefix}line {i.line}: {i.kind} - {i.phrase}" for i in issues]
        super().__init__("Compliance check failed:\n" + "\n".join(lines))


# Matched against lowercased text where '&' became ' and ' and hyphens became spaces.
_CLAIMS = [
    r"\bcur(?:e|es|ed|ing)\b",
    r"\bguaranteed\b",
    r"\bguarantees (?:results|relief|success)\b",
    r"\bdoctors? hate\b",
    r"\bmiracles?\b|\bmiraculous\b",
    r"\b(?:no|zero) side effects?\b",
    r"\bbefore and after\b",
    r"\brevers(?:e|es|ed|ing) (?:your |the )?(?:type (?:2|two) )?diabetes\b",
    r"\b(?:get|gets|getting|got|come|coming) off (?:your |the )?(?:medication|medications|meds)\b",
]
_CLAIM_RES = [re.compile(p) for p in _CLAIMS]


def _normalize(line: str) -> str:
    line = line.lower().replace("&", " and ").replace("-", " ").replace("_", " ")
    return re.sub(r"\s+", " ", line)


def check_draft(text: str) -> list:
    issues = []
    for number, line in enumerate(text.splitlines(), start=1):
        norm = _normalize(line)
        for rx in _CLAIM_RES:
            for m in rx.finditer(norm):
                issues.append(Issue("claim", m.group(0), number))
    return issues


def _body_text(doc: str) -> str:
    m = re.search(r"<body[^>]*>(.*)</body>", doc, re.S | re.I)
    inner = m.group(1) if m else doc
    return html.unescape(re.sub(r"<[^>]+>", "", inner))


def check_page(doc: str) -> list:
    text = _body_text(doc)
    issues = []
    pos = text.find(DISCLOSURE)
    if pos < 0 or pos >= DISCLOSURE_WINDOW:
        issues.append(Issue("disclosure", "affiliate disclosure missing or not near the top", 0))
    if MEDICAL_NOTE not in text:
        issues.append(Issue("medical-note", "medical note missing", 0))
    return issues
