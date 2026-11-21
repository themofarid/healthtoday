"""Command line: build, preview, approve, watchdog, publish."""
from __future__ import annotations

import argparse
import subprocess
import webbrowser
from pathlib import Path

from tools.builder import build_site
from tools.compliance import ComplianceError, check_draft
from tools.config import load_config
from tools.draft import DraftError, parse_draft
from tools.offers import load_offers, save_offers
from tools.social import write_social_kits
from tools.watchdog import http_fetch, run_watchdog


def _base_url(root: Path) -> str:
    cfg = load_config(root / "config.toml")
    return f"https://{cfg.github_user}.github.io/{cfg.repo_name}"


def _build(root: Path) -> int:
    try:
        slugs = build_site(root)
        write_social_kits(root, _base_url(root))
    except (DraftError, ComplianceError, ValueError) as err:
        print(err)
        return 1
    print("Built pages: " + (", ".join(slugs) if slugs else "none (nothing in approved/)"))
    return 0


def _approve(root: Path, slug: str) -> int:
    draft = root / "drafts" / f"{slug}.md"
    if not draft.exists():
        print(f"No draft found at drafts/{slug}.md")
        return 1
    if slug not in {o.slug for o in load_offers(root / "offers.csv")}:
        print(f"No offer with slug '{slug}' in offers.csv - add it first.")
        return 1
    text = draft.read_text(encoding="utf-8")
    try:
        parse_draft(text)
    except DraftError as err:
        print(err)
        return 1
    issues = check_draft(text)
    if issues:
        print(ComplianceError(issues, draft.name))
        return 1
    target = root / "approved" / draft.name
    target.parent.mkdir(exist_ok=True)
    draft.replace(target)
    print(f"Approved {slug}. Run 'build' or 'publish' next.")
    return 0


def _watchdog(root: Path, fetch) -> int:
    offers = load_offers(root / "offers.csv")
    updated, newly_dead = run_watchdog(offers, fetch)
    save_offers(root / "offers.csv", updated)
    (root / "newly_dead.txt").write_text("".join(o.slug + "\n" for o in newly_dead), encoding="utf-8")
    for o in updated:
        print(f"{o.slug}: {o.status} (strikes {o.strikes})")
    return _build(root)


def _publish(root: Path, run) -> int:
    code = _build(root)
    if code:
        return code
    steps = [["git", "add", "-A"], ["git", "commit", "-m", "Publish approved pages"], ["git", "push"]]
    for cmd in steps:
        result = run(cmd, cwd=root)
        # 'git commit' exits 1 when there is nothing new to commit; that is fine.
        if result.returncode != 0 and cmd[1] != "commit":
            print(f"'{' '.join(cmd)}' failed")
            return 1
    print("Published.")
    return 0


def main(argv: list, root: Path = Path("."), run=subprocess.run, fetch=http_fetch) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    sub.add_parser("watchdog")
    sub.add_parser("publish")
    for name in ("approve", "preview"):
        sub.add_parser(name).add_argument("slug")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return int(exit_.code or 0)
    root = Path(root)
    if args.command == "build":
        return _build(root)
    if args.command == "approve":
        return _approve(root, args.slug)
    if args.command == "watchdog":
        return _watchdog(root, fetch)
    if args.command == "publish":
        return _publish(root, run)
    page = root / "site" / args.slug / "index.html"
    if not page.exists():
        print(f"No built page for '{args.slug}'. Run 'build' first.")
        return 1
    webbrowser.open(page.resolve().as_uri())
    return 0
