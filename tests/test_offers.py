import tempfile
import unittest
from pathlib import Path

from tools.offers import Offer, load_offers, save_offers

HEADER = "slug,name,network,link,link_mode,tags,status,strikes\n"
GOOD = "tonicgreens,Tonic Greens,digistore24,https://www.digistore24.com/redir/1/2/k,hoplink,back pain;lower back pain,live,0\n"


def write(rows: str) -> Path:
    p = Path(tempfile.mkdtemp()) / "offers.csv"
    p.write_text(HEADER + rows, encoding="utf-8")
    return p


class OffersTests(unittest.TestCase):
    def test_load_offers_parses_row(self):
        (o,) = load_offers(write(GOOD))
        self.assertEqual(o.slug, "tonicgreens")
        self.assertEqual(o.network, "digistore24")
        self.assertEqual(o.tags, ["back pain", "lower back pain"])
        self.assertEqual(o.strikes, 0)
        self.assertIsInstance(o.strikes, int)

    def test_defaults(self):
        row = "a-1,A,clickbank,https://x.hop.clickbank.net,,,,\n"
        (o,) = load_offers(write(row))
        self.assertEqual((o.link_mode, o.status, o.strikes, o.tags), ("hoplink", "live", 0, []))

    def test_rejects_non_https_link(self):
        with self.assertRaises(ValueError):
            load_offers(write(GOOD.replace("https://", "http://")))

    def test_rejects_unsafe_slug(self):
        for bad in ("../x", "a b", "Upper"):
            with self.subTest(slug=bad), self.assertRaises(ValueError):
                load_offers(write(GOOD.replace("tonicgreens,", bad + ",", 1)))

    def test_rejects_unknown_network(self):
        with self.assertRaises(ValueError):
            load_offers(write(GOOD.replace("digistore24", "amazon", 1)))

    def test_rejects_unknown_link_mode(self):
        with self.assertRaises(ValueError):
            load_offers(write(GOOD.replace("hoplink", "magic")))

    def test_rejects_unknown_status(self):
        with self.assertRaises(ValueError):
            load_offers(write(GOOD.replace(",live,", ",zombie,")))

    def test_save_roundtrip(self):
        path = write(GOOD)
        offers = load_offers(path)
        out = path.parent / "out.csv"
        save_offers(out, offers)
        self.assertEqual(load_offers(out), offers)


if __name__ == "__main__":
    unittest.main()
