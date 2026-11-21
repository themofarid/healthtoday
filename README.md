# Affiliate review site (ClickBank + Digistore24)

Free review pages on GitHub Pages, a daily affiliate-link check, a claim checker and a social kit.

## One-time setup
1. Install Python 3.11 or newer, then run `pip install -r requirements.txt`.
2. Edit `config.toml` (your name and contact email; the GitHub user and repo are already filled in).
3. Create a **public** GitHub repository named as in `config.toml`, then run:
   `git branch -M main`, `git remote add origin <your repo URL>`, `git push -u origin main`.
4. In the repo: Settings > Pages > Source: **GitHub Actions**.
5. Optional: put your own About text in `about.md` (markdown) in the project root.

## Adding a page
1. Add a row to `offers.csv` (slug, name, network, your affiliate link, tags).
2. Get a draft from Claude using `docs/article-prompt.md`; save it as `drafts/<slug>.md`.
3. `python -m tools approve <slug>` (blocked if the draft has risky claims or missing sections).
4. `python -m tools build`, then `python -m tools preview <slug>` to look at it.
5. `python -m tools publish` to push it live. Pages appear at `https://<user>.github.io/<repo>/<slug>/`.
6. Copy the pin text and Shorts script from `social/<slug>.md` into Pinterest and YouTube and schedule them.

## What runs by itself
`.github/workflows/watchdog.yml` checks every link daily. An offer failing two days in a row is marked
dead, its page shows an "offer unavailable" notice, and GitHub opens an issue (you get an email).

## Tests
`python -m unittest discover -s tests -t .`
