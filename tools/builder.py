"""Turn approved drafts into static pages under site/."""
from __future__ import annotations

import html
from pathlib import Path

import markdown

from tools import templates as t
from tools.config import Config, load_config
from tools.draft import Article, DraftError, parse_draft
from tools.offers import Offer, load_offers


def _e(text: str) -> str:
    return html.escape(text, quote=True)


def _md(text: str) -> str:
    return markdown.markdown(text) if text.strip() else ""


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
             _md(article.intro_md)]
    for sec in [*article.benefits, article.con, article.conclusion]:
        parts += [f"<h2>{_e(sec.title)}</h2>", _md(sec.body_md)]
    parts += [_cta(offer), f'<p class="note">{t.MEDICAL_NOTE}</p>']
    body = "\n".join(p for p in parts if p)
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
    root = Path(root)
    cfg = load_config(root / "config.toml")
    offers = {o.slug: o for o in load_offers(root / "offers.csv")}
    built: list = []
    for f in sorted((root / "approved").glob("*.md")):
        offer = offers.get(f.stem)
        if offer is None:
            raise DraftError(f"{f.name}: no offer with slug '{f.stem}' in offers.csv")
        if offer.status == "paused":
            continue
        try:
            article = parse_draft(f.read_text(encoding="utf-8"))
        except DraftError as err:
            raise DraftError(f"{f.name}: {err}") from err
        out = root / "site" / offer.slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_page(article, offer, cfg), encoding="utf-8")
        built.append(offer.slug)
    about = root / "about.md"
    about_md = about.read_text(encoding="utf-8") if about.exists() else None
    for rel, doc in render_support_pages([offers[s] for s in built], cfg, about_md).items():
        out = root / "site" / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc, encoding="utf-8")
    return built
