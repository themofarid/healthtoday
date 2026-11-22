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

## Editing a page later
Open the article in a text editor, change the words, save. Drafts you have not approved yet are in
`drafts/`; approved pages are in `approved/`. After any change run `python -m tools build`, check it with
`python -m tools preview <slug>`, then `python -m tools publish`. No new files from anyone are needed for text changes.
To add your own first-hand section, see `docs/my-experience-template.md`.

## Images
1. Put the picture files (png, jpg, webp, gif or svg) in the `images/` folder, for example `images/tonicgreens-pack.jpg`.
2. In the article, add an image on its own line with markdown: `![TonicGreens pack](images/tonicgreens-pack.jpg)`.
   Always write the path as `images/<file name>` and always give a short description inside the square brackets.
3. To make the picture a clickable link to the offer, use the token instead of pasting the link:
   `[![TonicGreens pack](images/tonicgreens-pack.jpg)]({{AFFILIATE_LINK}})`. The site adds the right
   link, marks it as sponsored, and removes the link automatically if the offer dies.
4. Build stops with a clear message if a picture named in the article is missing from `images/`.
Use pictures you own or have permission to use: your own photos, free-licence stock photos, or the
vendor's official affiliate materials. Do not copy pictures from a vendor site without permission.

## What runs by itself
`.github/workflows/watchdog.yml` checks every link daily. An offer failing two days in a row is marked
dead, its page shows an "offer unavailable" notice, and GitHub opens an issue (you get an email).

## Tests
`python -m unittest discover -s tests -t .`
