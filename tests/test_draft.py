import unittest

from tools.draft import DraftError, parse_draft
from tests.helpers import DRAFT


class DraftTests(unittest.TestCase):
    def test_parse_draft_ok(self):
        a = parse_draft(DRAFT)
        self.assertEqual(a.headline, "Why Tonic Greens Is Worth a Look")
        self.assertEqual(a.subheadline, "A friendly look at a daily greens powder")
        self.assertEqual([b.title for b in a.benefits],
                         ["Benefit 1: Easy daily habit", "Benefit 2: Handy for busy days",
                          "Benefit 3: Simple ingredient list"])
        self.assertEqual(a.con.title, "The one con: Taste varies")
        self.assertIn("earthy", a.con.body_md)
        self.assertEqual(a.conclusion.title, "Conclusion")
        self.assertIn("Short intro", a.intro_md)

    def test_parse_draft_missing_benefit_names_part(self):
        text = DRAFT.replace("## Benefit 3: Simple ingredient list\nEasy to read.\n\n", "")
        with self.assertRaises(DraftError) as ctx:
            parse_draft(text)
        self.assertIn("Benefit 3", str(ctx.exception))

    def test_parse_draft_missing_con_and_conclusion(self):
        no_con = DRAFT.replace("## The one con: Taste varies\nSome people find the flavor earthy.\n\n", "")
        with self.assertRaises(DraftError) as c1:
            parse_draft(no_con)
        self.assertIn("one con", str(c1.exception))
        no_end = DRAFT.replace("## Conclusion\nA reasonable option to look at.\n", "")
        with self.assertRaises(DraftError) as c2:
            parse_draft(no_end)
        self.assertIn("Conclusion", str(c2.exception))

    def test_parse_draft_extra_benefit_is_rejected(self):
        text = DRAFT + "\n## Benefit 4: One too many\nText.\n"
        with self.assertRaises(DraftError) as ctx:
            parse_draft(text)
        self.assertIn("Benefit 4", str(ctx.exception))

    def test_parse_draft_missing_headline(self):
        with self.assertRaises(DraftError) as ctx:
            parse_draft(DRAFT.split("\n", 1)[1])
        self.assertIn("headline", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
