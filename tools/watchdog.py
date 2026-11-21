"""Daily affiliate link health check."""
from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

Fetcher = Callable[[str], tuple]  # url -> (status, final_url, body_text)

# Starting guess. Verified against real dead links in Task 8.
ERROR_PHRASES = (
    "invalid hoplink",
    "hoplink is not valid",
    "product not found",
    "no longer available",
    "offer not found",
)
STRIKES_TO_DEAD = 2
BLOCKED_STATUSES = (403, 429)
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


@dataclass(frozen=True)
class LinkResult:
    ok: bool
    reason: str
    final_url: str
    inconclusive: bool = False


def http_fetch(url: str) -> tuple:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(200_000).decode("utf-8", errors="replace")
            return resp.status, resp.geturl(), body
    except urllib.error.HTTPError as err:
        return err.code, err.geturl() or url, ""


def check_link(offer, fetch: Fetcher) -> LinkResult:
    try:
        status, final_url, body = fetch(offer.link)
    except Exception:
        return LinkResult(False, "unreachable", "")
    if status in BLOCKED_STATUSES:
        # The site refused our bot; that says nothing about whether the offer is alive.
        return LinkResult(False, f"blocked ({status}), not counted", final_url, inconclusive=True)
    if status != 200:
        return LinkResult(False, f"http {status}", final_url)
    if offer.link_mode == "hoplink":
        if urlparse(final_url).hostname == urlparse(offer.link).hostname:
            return LinkResult(False, "redirect did not leave the link host", final_url)
    text = body.lower()
    for phrase in ERROR_PHRASES:
        if phrase in text:
            return LinkResult(False, f"page says: {phrase}", final_url)
    return LinkResult(True, "ok", final_url)


def run_watchdog(offers: list, fetch: Fetcher) -> tuple:
    updated, newly_dead = [], []
    for o in offers:
        if o.status == "paused":
            updated.append(o)
            continue
        result = check_link(o, fetch)
        if result.inconclusive:
            updated.append(o)
            continue
        if result.ok:
            updated.append(o.with_(strikes=0, status="live"))
            continue
        strikes = o.strikes + 1
        status = "dead" if strikes >= STRIKES_TO_DEAD else o.status
        new = o.with_(strikes=strikes, status=status)
        updated.append(new)
        if o.status != "dead" and new.status == "dead":
            newly_dead.append(new)
    return updated, newly_dead
