import html
import re
import unittest
from pathlib import Path

from tests.helpers import DRAFT, LINK, make_root
from tools.builder import build_site, render_page, render_support_pages
from tools.config import load_config
from tools.draft import DraftError, parse_draft
from tools.offers import load_offers

DISCLOSURE = "This page contains affiliate links. If you buy through them, I may earn a commission at no extra cost to you."
MEDICAL = "This is not medical advice. Talk to your doctor before starting any supplement."


def page_for(status: str = "live") -> str:
    root = make_root()
    offer = load_offers(root / "offers.csv")[0].with_(status=status)
    return render_page(parse_draft(DRAFT), offer, load_config(root / "config.toml"))


def body_text(doc: str) -> str:
    body = re.search(r"<body[^>]*>(.*)</body>", doc, re.S).group(1)
    return html.unescape(re.sub(r"<[^>]+>", "", body))


class RenderPageTests(unittest.TestCase):
    def test_disclosure_within_first_600_chars_of_body(self):
        idx = body_text(page_for()).find(DISCLOSURE)
        self.assertTrue(0 <= idx < 600, idx)

    def test_button_uses_offer_link_and_rel(self):
        doc = page_for()
        self.assertIn(f'href="{LINK}"', doc)
        self.assertIn('rel="sponsored nofollow noopener"', doc)
        self.assertIn("See the full details and guarantee", doc)
        self.assertIn("Read the vendor's full details and guarantee before ordering.", body_text(doc))

    def test_medical_note_present(self):
        self.assertIn(MEDICAL, body_text(page_for()))

    def test_dead_offer_has_no_button_and_keeps_disclosure(self):
        doc = page_for("dead")
        self.assertIn("This offer is no longer available.", body_text(doc))
        self.assertNotIn(LINK, doc)
        self.assertIn(DISCLOSURE, body_text(doc))

    def test_head_has_title_description_keywords_viewport(self):
        doc = page_for()
        self.assertIn("<title>Why Tonic Greens Is Worth a Look</title>", doc)
        self.assertIn('<meta name="description" content="A friendly look at a daily greens powder">', doc)
        self.assertIn('<meta name="keywords" content="greens powder, daily greens">', doc)
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', doc)

    def test_draft_text_is_escaped_in_head(self):
        root = make_root()
        offer = load_offers(root / "offers.csv")[0]
        art = parse_draft(DRAFT.replace("A friendly look", 'A "friendly" <look>'))
        doc = render_page(art, offer, load_config(root / "config.toml"))
        self.assertIn("&quot;friendly&quot; &lt;look&gt;", doc)


class SupportPageTests(unittest.TestCase):
    def setUp(self):
        self.root = make_root()
        self.cfg = load_config(self.root / "config.toml")
        self.offers = load_offers(self.root / "offers.csv")

    def test_support_pages_use_author_and_email(self):
        pages = render_support_pages(self.offers, self.cfg)
        self.assertEqual(set(pages), {"index.html", "about/index.html", "contact/index.html"})
        self.assertIn("Themo", pages["about/index.html"])
        self.assertIn("me@example.com", pages["contact/index.html"])

    def test_index_lists_only_live_pages(self):
        dead = self.offers[0].with_(slug="old-one", name="Old One", status="dead")
        index = render_support_pages(self.offers + [dead], self.cfg)["index.html"]
        self.assertIn("Tonic Greens", index)
        self.assertNotIn("Old One", index)

    def test_about_md_overrides_default(self):
        pages = render_support_pages(self.offers, self.cfg, about_md="## My story\nHello there.")
        self.assertIn("Hello there.", pages["about/index.html"])


class BuildSiteTests(unittest.TestCase):
    def test_build_site_only_builds_approved(self):
        root = make_root(drafts={"tonicgreens.md": DRAFT})
        self.assertEqual(build_site(root), [])
        self.assertFalse((root / "site" / "tonicgreens").exists())
        (root / "approved" / "tonicgreens.md").write_text(DRAFT, encoding="utf-8")
        self.assertEqual(build_site(root), ["tonicgreens"])
        self.assertTrue((root / "site" / "tonicgreens" / "index.html").exists())
        self.assertTrue((root / "site" / "index.html").exists())

    def test_build_site_unknown_slug_errors(self):
        root = make_root(approved={"ghost.md": DRAFT})
        with self.assertRaises(DraftError) as ctx:
            build_site(root)
        self.assertIn("ghost.md", str(ctx.exception))

    def test_build_site_uses_root_about_md(self):
        root = make_root(approved={"tonicgreens.md": DRAFT})
        (root / "about.md").write_text("Written by me.", encoding="utf-8")
        build_site(root)
        about = (root / "site" / "about" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Written by me.", about)


if __name__ == "__main__":
    unittest.main()
