import contextlib
import io
import unittest
from types import SimpleNamespace

from tests.helpers import DRAFT, HEADER, LINK, ROW, make_root
from tools.cli import main
from tools.offers import load_offers


def quiet(*args, **kwargs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = main(*args, **kwargs)
    return code, buf.getvalue()


def boom(url):
    raise OSError("down")


class ApproveTests(unittest.TestCase):
    def test_approve_moves_clean_draft(self):
        root = make_root(drafts={"tonicgreens.md": DRAFT})
        code, _ = quiet(["approve", "tonicgreens"], root)
        self.assertEqual(code, 0)
        self.assertTrue((root / "approved" / "tonicgreens.md").exists())
        self.assertFalse((root / "drafts" / "tonicgreens.md").exists())

    def test_approve_refuses_flagged_draft(self):
        bad = DRAFT.replace("One scoop in water.", "This cures everything.")
        root = make_root(drafts={"tonicgreens.md": bad})
        code, out = quiet(["approve", "tonicgreens"], root)
        self.assertEqual(code, 1)
        self.assertIn("cure", out)
        self.assertTrue((root / "drafts" / "tonicgreens.md").exists())
        self.assertFalse((root / "approved" / "tonicgreens.md").exists())

    def test_approve_refuses_incomplete_draft(self):
        short = DRAFT.replace("## Benefit 3: Simple ingredient list\nEasy to read.\n\n", "")
        root = make_root(drafts={"tonicgreens.md": short})
        code, out = quiet(["approve", "tonicgreens"], root)
        self.assertEqual(code, 1)
        self.assertIn("Benefit 3", out)

    def test_approve_missing_draft_or_unknown_offer(self):
        root = make_root()
        self.assertEqual(quiet(["approve", "tonicgreens"], root)[0], 1)
        (root / "drafts" / "ghost.md").write_text(DRAFT, encoding="utf-8")
        self.assertEqual(quiet(["approve", "ghost"], root)[0], 1)


class BuildTests(unittest.TestCase):
    def test_build_ignores_unapproved_drafts(self):
        root = make_root(drafts={"tonicgreens.md": DRAFT})
        self.assertEqual(quiet(["build"], root)[0], 0)
        self.assertFalse((root / "site" / "tonicgreens").exists())
        self.assertEqual(list((root / "social").iterdir()), [])

    def test_build_writes_site_and_social_kit(self):
        root = make_root(approved={"tonicgreens.md": DRAFT})
        self.assertEqual(quiet(["build"], root)[0], 0)
        self.assertTrue((root / "site" / "tonicgreens" / "index.html").exists())
        kit = (root / "social" / "tonicgreens.md").read_text(encoding="utf-8")
        self.assertIn("https://themofarid.github.io/tonicgreens/tonicgreens/", kit)

    def test_build_reports_problem_and_returns_1(self):
        bad = DRAFT.replace("One scoop in water.", "This cures everything.")
        root = make_root(approved={"tonicgreens.md": bad})
        code, out = quiet(["build"], root)
        self.assertEqual(code, 1)
        self.assertIn("cure", out)


class PublishTests(unittest.TestCase):
    def test_publish_runs_git_add_commit_push_in_order(self):
        calls = []
        def fake_run(cmd, **kw):
            calls.append(cmd)
            return SimpleNamespace(returncode=0)
        root = make_root(approved={"tonicgreens.md": DRAFT})
        code, _ = quiet(["publish"], root, run=fake_run)
        self.assertEqual(code, 0)
        self.assertEqual([c[1] for c in calls], ["add", "commit", "push"])
        self.assertTrue((root / "site" / "tonicgreens" / "index.html").exists())

    def test_publish_does_not_push_when_build_fails(self):
        calls = []
        bad = DRAFT.replace("One scoop in water.", "This cures everything.")
        root = make_root(approved={"tonicgreens.md": bad})
        code, _ = quiet(["publish"], root, run=lambda cmd, **kw: calls.append(cmd))
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])

    def test_publish_fails_when_push_fails(self):
        def fake_run(cmd, **kw):
            return SimpleNamespace(returncode=1 if cmd[1] == "push" else 0)
        root = make_root(approved={"tonicgreens.md": DRAFT})
        self.assertEqual(quiet(["publish"], root, run=fake_run)[0], 1)


class WatchdogCommandTests(unittest.TestCase):
    def test_watchdog_command_updates_offers_rebuilds_and_lists_newly_dead(self):
        rows = ROW.replace(",live,0", ",live,1")
        root = make_root(rows, approved={"tonicgreens.md": DRAFT})
        code, _ = quiet(["watchdog"], root, fetch=boom)
        self.assertEqual(code, 0)
        (offer,) = load_offers(root / "offers.csv")
        self.assertEqual((offer.status, offer.strikes), ("dead", 2))
        self.assertEqual((root / "newly_dead.txt").read_text(encoding="utf-8").split(), ["tonicgreens"])
        page = (root / "site" / "tonicgreens" / "index.html").read_text(encoding="utf-8")
        self.assertIn("This offer is no longer available.", page)
        self.assertNotIn(LINK, page)

    def test_watchdog_command_leaves_empty_file_when_nothing_died(self):
        root = make_root(approved={"tonicgreens.md": DRAFT})
        ok = lambda url: (200, "https://vendor.example/sales", "hello")
        self.assertEqual(quiet(["watchdog"], root, fetch=ok)[0], 0)
        self.assertEqual((root / "newly_dead.txt").read_text(encoding="utf-8"), "")


class UsageTests(unittest.TestCase):
    def test_unknown_command_returns_2(self):
        self.assertEqual(quiet(["wat"], make_root())[0], 2)

    def test_no_command_returns_2(self):
        self.assertEqual(quiet([], make_root())[0], 2)

    def test_preview_missing_page_returns_1(self):
        self.assertEqual(quiet(["preview", "tonicgreens"], make_root())[0], 1)


if __name__ == "__main__":
    unittest.main()


class ModuleEntryTests(unittest.TestCase):
    def test_module_runs_from_any_directory(self):
        import os
        import shutil
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        proj = make_root(approved={"tonicgreens.md": DRAFT})
        shutil.copytree(Path(__file__).resolve().parent.parent / "tools", proj / "tools",
                        ignore=shutil.ignore_patterns("__pycache__"))
        elsewhere = tempfile.mkdtemp()
        env = {**os.environ, "PYTHONPATH": str(proj)}
        r = subprocess.run([sys.executable, "-m", "tools", "build"], cwd=elsewhere, env=env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((proj / "site" / "tonicgreens" / "index.html").exists())
