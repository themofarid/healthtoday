import tempfile
import unittest
from pathlib import Path

from tools.config import Config, load_config

FULL = (
    'site_title = "Greens Guide"\n'
    'author_name = "Themo"\n'
    'contact_email = "me@example.com"\n'
    'github_user = "themofarid"\n'
    'repo_name = "tonicgreens"\n'
)


def write(text: str) -> Path:
    p = Path(tempfile.mkdtemp()) / "config.toml"
    p.write_text(text, encoding="utf-8")
    return p


class ConfigTests(unittest.TestCase):
    def test_load_config_reads_all_keys(self):
        cfg = load_config(write(FULL))
        self.assertEqual(
            cfg,
            Config("Greens Guide", "Themo", "me@example.com", "themofarid", "tonicgreens"),
        )

    def test_load_config_missing_key_raises(self):
        text = FULL.replace('repo_name = "tonicgreens"\n', "")
        with self.assertRaises(ValueError) as ctx:
            load_config(write(text))
        self.assertIn("repo_name", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
