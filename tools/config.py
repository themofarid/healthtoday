"""Site configuration loaded from config.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

_KEYS = ("site_title", "author_name", "contact_email", "github_user", "repo_name")


@dataclass(frozen=True)
class Config:
    site_title: str
    author_name: str
    contact_email: str
    github_user: str
    repo_name: str


def load_config(path: Path) -> Config:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in _KEYS if not str(data.get(k, "")).strip()]
    if missing:
        raise ValueError("config.toml is missing: " + ", ".join(missing))
    return Config(**{k: str(data[k]).strip() for k in _KEYS})
