"""Turn approved drafts into static pages under site/."""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import markdown

from tools import templates as t
from tools.compliance import ComplianceError, check_draft, check_page
from tools.config import Config, load_config
from tools.draft import Article, DraftError, parse_draft
from tools.offers import Offer, load_offers


def _e(text: str) -> str:
    return html.escape(text, quote=True)


IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")
_IMAGE_REF = re.compile(r"\(images/([^)\s]*)\)")


def _md(text: str, offer: Offer | None = None) -> str:
    """Markdown to HTML. Pages sit one folder below the site root, so images/ becomes ../images/."""
    if not text.strip():
        return ""
    text = text.replace("](images/", "](../images/")
    if offer is not None:
        text = text.replace("{{AFFILIATE_LINK}}", offer.link)
    return markdown.markdown(text)


def _mark_links(body: str, offer: Offer) -> str:
    """Affiliate links written in the article get rel=sponsored; on a dead offer they are removed."""
    href = offer.link.replace("&", "&amp;")
    if offer.status == "dead":
        return re.sub(r'<a href="' + re.escape(href) + r'">(.*?)</a>', r"\1", body, flags=re.S)
    return body.replace(f'<a href="{href}">', f'<a href="{href}" rel="{t.BUTTON_REL}">')


def _check_images(text: str, root: Path, filename: str) -> None:
    for name in _IMAGE_REF.findall(text):
        if ".." in name or "/" in name or not (root / "images" / name).is_file():
            raise DraftError(f"{filename}: image 'images/{name}' not found in the images folder")


def _copy_images(root: Path) -> None:
    src = root / "images"
    if not src.is_dir():
        return
    for f in sorted(src.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
            dest = root / "site" / "images"
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest / f.name)


def _shell(title: str, description: str, keywords: str, body: str, prefix: str, cfg: Config) -> str:
    return t.PAGE.substitute(title=_e(title), description=_e(description), keywords=_e(keywords),
                             body=body, prefix=prefix, site_title=_e(cfg.site_title))


def _cta(offer: Offer) -> str:
    if offer.status == "dead":
        return f'<p class="gone">{t.DEAD_NOTICE}</p>'
    return (f'<p class="cta"><a class="button" href="{_e(offer.link)}" rel="{t.BUTTON_REL}">'
            f'{t.BUTTON_TEXT}</a></p>\n<p class="note">{t.BUTTON_NOTE}</p>')


def render_page(article: Article, offer: Offer, config: Config) -> str:
    parts = [f"<h1>{_e(article.headline)}</h1>",
             f'<p class="sub">{_e(article.subheadline)}</p>',
             f'<p class="disclosure">{t.DISCLOSURE}</p>',
             _md(article.intro_md, offer)]
    for sec in [*article.benefits, article.con, article.conclusion]:
        parts += [f"<h2>{_e(sec.title)}</h2>", _md(sec.body_md, offer)]
    parts += [_cta(offer), f'<p class="note">{t.MEDICAL_NOTE}</p>']
    body = _mark_links("\n".join(p for p in parts if p), offer)
    return _shell(article.headline, article.subheadline, ", ".join(offer.tags), body, "../", config)


def render_support_pages(offers: list, config: Config, about_md: str | None = None) -> dict:
    live = [o for o in offers if o.status == "live"]
    items = "\n".join(f'<li><a href="{_e(o.slug)}/">{_e(o.name)}</a></li>' for o in live)
    index_body = (f"<h1>{_e(config.site_title)}</h1>\n"
                  f'<p class="disclosure">{t.DISCLOSURE}</p>\n'
                  f"<ul>\n{items}\n</ul>" if items else
                  f"<h1>{_e(config.site_title)}</h1>\n" f'<p class="disclosure">{t.DISCLOSURE}</p>')
    if about_md and about_md.strip():
        about_body = _md(about_md)
    else:
        about_body = (f"<h1>About</h1>\n<p>Hi, I'm {_e(config.author_name)}. I write plain-language "
                      "reviews of health and wellness products and say what I like and what I don't.</p>\n"
                      f'<p class="note">{t.DISCLOSURE}</p>')
    email = _e(config.contact_email)
    contact_body = f'<h1>Contact</h1>\n<p>You can reach me at <a href="mailto:{email}">{email}</a>.</p>'
    d = config.site_title
    return {
        "index.html": _shell(d, d, "", index_body, "", config),
        "about/index.html": _shell(f"About - {d}", f"About {d}", "", about_body, "../", config),
        "contact/index.html": _shell(f"Contact - {d}", f"Contact {d}", "", contact_body, "../", config),
    }


def build_site(root: Path) -> list:
    """Render every approved draft; write nothing unless all of them pass the checks."""
    root = Path(root)
    cfg = load_config(root / "config.toml")
    offers = {o.slug: o for o in load_offers(root / "offers.csv")}
    outputs: dict = {}
    built: list = []
    for f in sorted((root / "approved").glob("*.md")):
        offer = offers.get(f.stem)
        if offer is None:
            raise DraftError(f"{f.name}: no offer with slug '{f.stem}' in offers.csv")
        if offer.status == "paused":
            continue
        text = f.read_text(encoding="utf-8")
        _check_images(text, root, f.name)
        issues = check_draft(text)
        if issues:
            raise ComplianceError(issues, f.name)
        try:
            article = parse_draft(text)
        except DraftError as err:
            raise DraftError(f"{f.name}: {err}") from err
        doc = render_page(article, offer, cfg)
        issues = check_page(doc)
        if issues:
            raise ComplianceError(issues, f.name)
        outputs[root / "site" / offer.slug / "index.html"] = doc
        built.append(offer.slug)
    about = root / "about.md"
    about_md = about.read_text(encoding="utf-8") if about.exists() else None
    for rel, doc in render_support_pages([offers[s] for s in built], cfg, about_md).items():
        outputs[root / "site" / rel] = doc
    for path, doc in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(doc, encoding="utf-8")
    _copy_images(root)
    return built
