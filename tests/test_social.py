import unittest

from tests.helpers import DRAFT, ROW, make_root
from tools.compliance import check_draft
from tools.draft import parse_draft
from tools.offers import Offer
from tools.social import make_social_kit, write_social_kits

URL = "https://themofarid.github.io/tonicgreens/tonicgreens/"
OFFER = Offer("tonicgreens", "Tonic Greens", "digistore24", "https://x.example/a", "hoplink",
              ["greens powder", "daily greens"], "live", 0)


def field(kit: str, name: str) -> str:
    line = next(l for l in kit.splitlines() if l.startswith(name + ":"))
    return line.split(":", 1)[1].strip()


class SocialKitTests(unittest.TestCase):
    def setUp(self):
        self.article = parse_draft(DRAFT)

    def test_pin_title_max_100_chars(self):
        long = parse_draft(DRAFT.replace("Why Tonic Greens Is Worth a Look", "Word " * 60))
        title = field(make_social_kit(long, OFFER, URL), "Pin title")
        self.assertLessEqual(len(title), 100)
        self.assertTrue(title.startswith("Word Word"))

    def test_pin_description_max_500_chars_and_contains_page_url(self):
        long = parse_draft(DRAFT.replace("A friendly look at a daily greens powder", "word " * 300))
        desc = field(make_social_kit(long, OFFER, URL), "Pin description")
        self.assertLessEqual(len(desc), 500)
        self.assertIn(URL, desc)

    def test_pin_tags_come_from_offer_tags(self):
        tags = field(make_social_kit(self.article, OFFER, URL), "Pin tags")
        self.assertEqual(tags, "#greenspowder #dailygreens")

    def test_shorts_script_has_hook_three_points_and_cta(self):
        kit = make_social_kit(self.article, OFFER, URL)
        self.assertIn("Why Tonic Greens Is Worth a Look", field(kit, "Hook"))
        self.assertEqual(field(kit, "Point 1"), "Easy daily habit")
        self.assertEqual(field(kit, "Point 2"), "Handy for busy days")
        self.assertEqual(field(kit, "Point 3"), "Simple ingredient list")
        cta = field(kit, "Call to action")
        self.assertIn("full details", cta)
        self.assertIn("affiliate link", cta)

    def test_kit_has_no_blocked_phrases(self):
        self.assertEqual(check_draft(make_social_kit(self.article, OFFER, URL)), [])


class WriteKitsTests(unittest.TestCase):
    def test_write_social_kits_skips_dead_offers(self):
        rows = ROW + ROW.replace("tonicgreens", "old-one").replace(",live,", ",dead,")
        root = make_root(rows, approved={"tonicgreens.md": DRAFT, "old-one.md": DRAFT})
        paths = write_social_kits(root, "https://themofarid.github.io/tonicgreens")
        self.assertEqual([p.name for p in paths], ["tonicgreens.md"])
        text = (root / "social" / "tonicgreens.md").read_text(encoding="utf-8")
        self.assertIn(URL, text)
        self.assertFalse((root / "social" / "old-one.md").exists())


if __name__ == "__main__":
    unittest.main()
