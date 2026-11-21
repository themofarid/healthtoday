import tempfile
from pathlib import Path

CONFIG = (
    'site_title = "Greens Guide"\nauthor_name = "Themo"\n'
    'contact_email = "me@example.com"\ngithub_user = "themofarid"\nrepo_name = "tonicgreens"\n'
)
HEADER = "slug,name,network,link,link_mode,tags,status,strikes\n"
LINK = "https://www.digistore24.com/redir/1/2/k"
ROW = f"tonicgreens,Tonic Greens,digistore24,{LINK},hoplink,greens powder;daily greens,live,0\n"

DRAFT = """# Why Tonic Greens Is Worth a Look
### A friendly look at a daily greens powder

Short intro about the product.

## Benefit 1: Easy daily habit
One scoop in water.

## Benefit 2: Handy for busy days
Mix it anywhere.

## Benefit 3: Simple ingredient list
Easy to read.

## The one con: Taste varies
Some people find the flavor earthy.

## Conclusion
A reasonable option to look at.
"""


def make_root(rows: str = ROW, drafts: dict | None = None, approved: dict | None = None) -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "config.toml").write_text(CONFIG, encoding="utf-8")
    (root / "offers.csv").write_text(HEADER + rows, encoding="utf-8")
    for folder, files in (("drafts", drafts or {}), ("approved", approved or {}), ("site", {}), ("social", {})):
        (root / folder).mkdir()
        for name, text in files.items():
            (root / folder / name).write_text(text, encoding="utf-8")
    return root
