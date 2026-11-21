"""Pinterest and YouTube Shorts text for each live page."""
from __future__ import annotations

import re
from pathlib import Path

from tools.compliance import ComplianceError, check_draft
from tools.config import load_config
from tools.draft import Article, parse_draft
from tools.offers import Offer, load_offers


def _cut(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:-") + "\u2026"


def _hashtag(tag: str) -> str:
    return "#" + re.sub(r"[^a-z0-9]", "", tag.lower())


def _point(title: str) -> str:
    return re.sub(r"^benefit\s+\d+\s*:\s*", "", title, flags=re.I).strip()


def make_social_kit(article: Article, offer: Offer, page_url: str) -> str:
    tail = f" Full review: {page_url}"
    description = _cut(article.subheadline, 500 - len(tail)) + tail
    lines = [
        f"# Social kit: {offer.name}",
        "",
        "## Pinterest pin",
        f"Pin title: {_cut(article.headline, 100)}",
        f"Pin description: {description}",
        f"Pin tags: {' '.join(_hashtag(t) for t in offer.tags)}",
        f"Pin link: {page_url}",
        "",
        "## YouTube Shorts script",
        f"Hook: {article.headline}",
        f"Point 1: {_point(article.benefits[0].title)}",
        f"Point 2: {_point(article.benefits[1].title)}",
        f"Point 3: {_point(article.benefits[2].title)}",
        "Call to action: The full details and the guarantee are on the page - "
        "the link is in the description, and it is an affiliate link.",
        "",
    ]
    return "\n".join(lines)


def write_social_kits(root: Path, base_url: str) -> list:
    root = Path(root)
    load_config(root / "config.toml")
    offers = {o.slug: o for o in load_offers(root / "offers.csv")}
    written = []
    (root / "social").mkdir(exist_ok=True)
    for f in sorted((root / "approved").glob("*.md")):
        offer = offers.get(f.stem)
        if offer is None or offer.status != "live":
            continue
        page_url = f"{base_url.rstrip('/')}/{offer.slug}/"
        kit = make_social_kit(parse_draft(f.read_text(encoding="utf-8")), offer, page_url)
        issues = check_draft(kit)
        if issues:
            raise ComplianceError(issues, f"social/{offer.slug}.md")
        out = root / "social" / f"{offer.slug}.md"
        out.write_text(kit, encoding="utf-8")
        written.append(out)
    return written
