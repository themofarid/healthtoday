import unittest

from tests.helpers import DRAFT, ROW, make_root
from tools.builder import build_site
from tools.compliance import ComplianceError, check_draft, check_page

DISCLOSURE = "This page contains affiliate links. If you buy through them, I may earn a commission at no extra cost to you."
MEDICAL = "This is not medical advice. Talk to your doctor before starting any supplement."


def claims(text):
    return [i for i in check_draft(text) if i.kind == "claim"]


class DraftCheckTests(unittest.TestCase):
    def test_flags_cure_variants(self):
        for text in ("Cure", "it cures pain", "curing back pain", "a miracle cure"):
            with self.subTest(text=text):
                self.assertTrue(claims(text))

    def test_does_not_flag_look_alike_words(self):
        for text in ("a secure lid", "I am curious", "procurement team"):
            with self.subTest(text=text):
                self.assertEqual(claims(text), [])

    def test_flags_before_and_after_variants(self):
        for text in ("before and after", "before-and-after photos", "Before & After"):
            with self.subTest(text=text):
                self.assertTrue(claims(text))

    def test_flags_guaranteed_but_not_money_back_guarantee(self):
        self.assertTrue(claims("Results are guaranteed to work"))
        self.assertEqual(claims("It has a 60-day money-back guarantee."), [])

    def test_flags_remaining_phrases(self):
        for text in ("doctors hate this", "a miracle", "no side effects", "reverse diabetes fast",
                     "you can get off medication", "Doctors Hate it"):
            with self.subTest(text=text):
                self.assertTrue(claims(text))

    def test_clean_text_has_no_issues(self):
        self.assertEqual(check_draft(DRAFT), [])

    def test_issue_has_line_number_and_phrase(self):
        (issue,) = claims("fine line\nthis cures it\n")
        self.assertEqual(issue.line, 2)
        self.assertIn("cure", issue.phrase)


class PageCheckTests(unittest.TestCase):
    def doc(self, body):
        return f"<html><body>{body}</body></html>"

    def test_clean_page_passes(self):
        self.assertEqual(check_page(self.doc(f"<h1>x</h1><p>{DISCLOSURE}</p><p>{MEDICAL}</p>")), [])

    def test_check_page_missing_disclosure(self):
        kinds = [i.kind for i in check_page(self.doc(f"<p>{MEDICAL}</p>"))]
        self.assertEqual(kinds, ["disclosure"])

    def test_disclosure_buried_too_deep_fails(self):
        doc = self.doc("<p>" + "word " * 200 + f"</p><p>{DISCLOSURE}</p><p>{MEDICAL}</p>")
        self.assertEqual([i.kind for i in check_page(doc)], ["disclosure"])

    def test_check_page_missing_medical_note(self):
        kinds = [i.kind for i in check_page(self.doc(f"<p>{DISCLOSURE}</p>"))]
        self.assertEqual(kinds, ["medical-note"])


class BuildWiringTests(unittest.TestCase):
    BAD = DRAFT.replace("One scoop in water.", "This cures everything.")

    def test_build_site_refuses_flagged_draft(self):
        root = make_root(approved={"tonicgreens.md": self.BAD})
        with self.assertRaises(ComplianceError) as ctx:
            build_site(root)
        self.assertIn("cure", str(ctx.exception))
        self.assertIn("tonicgreens.md", str(ctx.exception))
        self.assertFalse((root / "site" / "tonicgreens").exists())

    def test_build_is_all_or_nothing(self):
        rows = ROW + ROW.replace("tonicgreens", "other-one").replace("Tonic Greens", "Other One")
        root = make_root(rows, approved={"tonicgreens.md": DRAFT, "other-one.md": self.BAD})
        with self.assertRaises(ComplianceError):
            build_site(root)
        self.assertFalse((root / "site" / "tonicgreens").exists())
        self.assertFalse((root / "site" / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
