import unittest

from tests.helpers import DRAFT, LINK, ROW, make_root
from tools.builder import build_site
from tools.draft import DraftError

WITH_IMAGE = DRAFT.replace("Short intro about the product.",
                           "Short intro about the product.\n\n![Pack shot](images/pack.png)")
WITH_LINKED_IMAGE = DRAFT.replace("Short intro about the product.",
                                  "Short intro about the product.\n\n[![Pack](images/pack.png)]({{AFFILIATE_LINK}})")


def root_with(draft, images=("pack.png",), rows=ROW):
    root = make_root(rows, approved={"tonicgreens.md": draft})
    (root / "images").mkdir()
    for name in images:
        (root / "images" / name).write_bytes(b"fake-image-bytes")
    return root


def page(root):
    return (root / "site" / "tonicgreens" / "index.html").read_text(encoding="utf-8")


class ImageTests(unittest.TestCase):
    def test_images_copied_to_site_but_not_other_files(self):
        root = root_with(WITH_IMAGE, images=("pack.png", "notes.txt"))
        build_site(root)
        self.assertEqual((root / "site" / "images" / "pack.png").read_bytes(), b"fake-image-bytes")
        self.assertFalse((root / "site" / "images" / "notes.txt").exists())

    def test_image_path_rewritten_for_article_page(self):
        root = root_with(WITH_IMAGE)
        build_site(root)
        self.assertIn('src="../images/pack.png"', page(root))

    def test_missing_image_is_an_error_and_writes_nothing(self):
        root = root_with(WITH_IMAGE, images=())
        with self.assertRaises(DraftError) as ctx:
            build_site(root)
        self.assertIn("images/pack.png", str(ctx.exception))
        self.assertFalse((root / "site" / "tonicgreens").exists())

    def test_image_path_with_dotdot_is_rejected(self):
        bad = DRAFT.replace("Short intro about the product.", "![x](images/../config.toml)")
        with self.assertRaises(DraftError):
            build_site(root_with(bad))

    def test_affiliate_link_token_becomes_sponsored_link(self):
        root = root_with(WITH_LINKED_IMAGE)
        build_site(root)
        doc = page(root)
        self.assertIn(f'<a href="{LINK}" rel="sponsored nofollow noopener"><img', doc)
        self.assertNotIn("{{AFFILIATE_LINK}}", doc)

    def test_dead_offer_unwraps_affiliate_links_but_keeps_image(self):
        root = root_with(WITH_LINKED_IMAGE, rows=ROW.replace(",live,0", ",dead,0"))
        build_site(root)
        doc = page(root)
        self.assertNotIn(LINK, doc)
        self.assertIn('src="../images/pack.png"', doc)

    def test_pages_have_responsive_images_and_logo(self):
        root = root_with(WITH_IMAGE)
        build_site(root)
        doc = page(root)
        self.assertIn("max-width:100%", doc)
        self.assertIn("<svg", doc)

    def test_about_md_images_use_parent_prefix(self):
        root = root_with(WITH_IMAGE)
        (root / "about.md").write_text("![me](images/pack.png)", encoding="utf-8")
        build_site(root)
        about = (root / "site" / "about" / "index.html").read_text(encoding="utf-8")
        self.assertIn('src="../images/pack.png"', about)


if __name__ == "__main__":
    unittest.main()
