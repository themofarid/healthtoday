"""Affiliate offers stored in offers.csv."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, replace
from pathlib import Path

FIELDS = ["slug", "name", "network", "link", "link_mode", "tags", "status", "strikes"]
NETWORKS = ("clickbank", "digistore24")
LINK_MODES = ("hoplink", "direct_tracking")
STATUSES = ("live", "dead", "paused")
_SLUG = re.compile(r"^[a-z0-9-]+$")


@dataclass(frozen=True)
class Offer:
    slug: str
    name: str
    network: str
    link: str
    link_mode: str
    tags: list
    status: str
    strikes: int

    def with_(self, **changes) -> "Offer":
        return replace(self, **changes)


def _parse(row: dict, line: int) -> Offer:
    def bad(msg: str) -> ValueError:
        return ValueError(f"offers.csv line {line}: {msg}")

    slug = (row.get("slug") or "").strip()
    if not _SLUG.match(slug):
        raise bad(f"unsafe slug {slug!r} (use lowercase letters, digits and hyphens)")
    network = (row.get("network") or "").strip()
    if network not in NETWORKS:
        raise bad(f"unknown network {network!r}")
    link = (row.get("link") or "").strip()
    if not link.startswith("https://"):
        raise bad("link must start with https://")
    link_mode = (row.get("link_mode") or "").strip() or "hoplink"
    if link_mode not in LINK_MODES:
        raise bad(f"unknown link_mode {link_mode!r}")
    status = (row.get("status") or "").strip() or "live"
    if status not in STATUSES:
        raise bad(f"unknown status {status!r}")
    strikes_text = (row.get("strikes") or "").strip() or "0"
    if not strikes_text.isdigit():
        raise bad("strikes must be a whole number")
    tags = [t.strip() for t in (row.get("tags") or "").split(";") if t.strip()]
    return Offer(slug, (row.get("name") or slug).strip(), network, link,
                 link_mode, tags, status, int(strikes_text))


def load_offers(path: Path) -> list:
    with Path(path).open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return [_parse(row, i) for i, row in enumerate(reader, start=2)]


def save_offers(path: Path, offers: list) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for o in offers:
            writer.writerow({
                "slug": o.slug, "name": o.name, "network": o.network, "link": o.link,
                "link_mode": o.link_mode, "tags": ";".join(o.tags),
                "status": o.status, "strikes": o.strikes,
            })
