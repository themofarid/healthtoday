"""Fixed wording and the HTML shell shared by every page."""
from string import Template

DISCLOSURE = ("This page contains affiliate links. If you buy through them, "
              "I may earn a commission at no extra cost to you.")
MEDICAL_NOTE = "This is not medical advice. Talk to your doctor before starting any supplement."
BUTTON_TEXT = "See the full details and guarantee"
BUTTON_NOTE = "Read the vendor's full details and guarantee before ordering."
DEAD_NOTICE = "This offer is no longer available."
BUTTON_REL = "sponsored nofollow noopener"

PAGE = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<meta name="description" content="$description">
<meta name="keywords" content="$keywords">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.65;color:#1f2933;margin:0;background:#fafaf7}
header.site,footer{max-width:42rem;margin:0 auto;padding:1rem 1.25rem}
header.site a{font-weight:700;color:#2f6f4e;text-decoration:none}
main{max-width:42rem;margin:0 auto;padding:0 1.25rem 2rem}
h1{font-size:1.9rem;line-height:1.25;margin:.5rem 0}
h2{font-size:1.3rem;margin-top:2rem}
.sub{font-size:1.15rem;color:#52606d;margin-top:0}
.disclosure,.note{font-size:.9rem;color:#52606d}
.disclosure{border-left:3px solid #2f6f4e;padding-left:.75rem}
.button{display:inline-block;background:#2f6f4e;color:#fff;padding:.8rem 1.4rem;border-radius:.4rem;text-decoration:none;font-weight:600}
.gone{background:#f1ede4;padding:.8rem 1rem;border-radius:.4rem}
footer{font-size:.9rem;color:#52606d}
</style>
</head>
<body>
<header class="site"><a href="${prefix}">$site_title</a></header>
<main>
$body
</main>
<footer><a href="${prefix}about/">About</a> &middot; <a href="${prefix}contact/">Contact</a></footer>
</body>
</html>
""")
