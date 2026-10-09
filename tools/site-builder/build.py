#!/usr/bin/env python3
"""Build the seven Lotus waitlist sites.

Each app's content lives in tools/site-builder/apps/<slug>.py. This script
renders every app into its own folder under public/ (public/lotus-g-1/, ...),
copying the shared CSS/JS into each one, and writes public/apps.js for the
catalogue at bishal.app/. public/ is served by the Cloudflare Pages project
bishal-app-pages, so each app lives at bishal.app/<slug>/ and posts sign-ups to
bishal.app/<slug>/api/join (functions/[app]/api/join.js).

Usage:
    python3 tools/site-builder/build.py                     # build all apps
    python3 tools/site-builder/build.py lotus-g-1           # build one app

Only the Python standard library is used.
"""

import html
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APPS_DIR = os.path.join(HERE, "apps")
ASSETS_DIR = os.path.join(HERE, "assets")
PUBLIC_DIR = os.path.join(ROOT, "public")

# Shared settings -------------------------------------------------------------
ORDER = ["lotus-g-1", "lotus-c-1", "lotus-f-1", "lotus-f-2", "lotus-e-1", "lotus-e-2", "lotus-e-3"]
OWNER = "Joel Vargas"
LAST_UPDATED = "October 9, 2026"
# Relative, so each app's forms post to bishal.app/<slug>/api/join.
WAITLIST_ENDPOINT = "api/join"

FONTS = (
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,600,0..1,0&display=block">\n'
    '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..700&display=swap">\n'
)

esc = html.escape


# Building blocks -------------------------------------------------------------
def icon_svg(app):
    i = app["icon"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{i["from"]}"/>
      <stop offset="1" stop-color="{i["to"]}"/>
    </linearGradient>
  </defs>
  <rect width="120" height="120" rx="27" fill="url(#bg)"/>
  <g fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">
    {i["glyph"]}
  </g>
</svg>
'''


def head(app, title, description):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#f4f4f7" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#1c1c1e" media="(prefers-color-scheme: dark)">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <link rel="icon" href="assets/app-icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="assets/app-icon.svg">
{FONTS}  <link rel="stylesheet" href="assets/styles.css">
  <style>:root {{ --brand: {app["brand"]}; --brand-2: {app["brand2"]}; }}</style>
  <script>if (scrollY < 8) document.documentElement.classList.add("nav-top");</script>
</head>
'''


def nav(app, current, on_home):
    links = [("index.html#features", "Features", "features"),
             ("release-notes.html", "Release Notes", "release-notes"),
             ("contact.html", "Contact", "contact")]
    items = "\n".join(
        f'        <li><a href="{href}"{" aria-current=\"page\"" if key == current else ""}>{label}</a></li>'
        for href, label, key in links)
    cta_href = "#waitlist" if on_home else "index.html#waitlist"
    return f'''  <div class="nav-spacer"></div>
  <header class="nav-wrap">
    <nav class="nav" aria-label="Main">
      <a class="app-identity" href="index.html">
        <span>{esc(app["name"])}</span>
        <img class="app-icon" src="assets/app-icon.svg" alt="">
      </a>
      <ul class="nav-links">
{items}
      </ul>
      <a class="button" href="{cta_href}">Join waitlist</a>
    </nav>
  </header>
'''


def footer(app):
    return f'''  <footer class="footer">
    <div class="footer-top">
      <a class="app-identity" href="index.html"><span>{esc(app["name"])}</span><img class="app-icon" src="assets/app-icon.svg" alt=""></a>
      <ul class="footer-links">
        <li><a href="privacy.html">Privacy</a></li>
        <li><a href="terms.html">Terms of Use</a></li>
        <li><a href="updates.html">Follow Updates</a></li>
      </ul>
    </div>
    <div class="footer-bottom">© <span data-year>2026</span> {esc(OWNER)}. All rights reserved.</div>
  </footer>

  <script src="assets/site.js" defer></script>
</body>
</html>
'''


def waitlist_form(app, source, label="Join the waitlist", center=False):
    action = esc(WAITLIST_ENDPOINT)
    return f'''<div class="waitlist-wrap{' center' if center else ''}">
          <form class="waitlist" action="{action}" method="post" data-waitlist data-source="{source}">
            <input type="hidden" name="source" value="{source}">
            <label class="hp" aria-hidden="true">Company<input name="company" tabindex="-1" autocomplete="off"></label>
            <input class="input" type="email" name="email" placeholder="you@example.com" autocomplete="email" aria-label="Email address" required>
            <button class="button" type="submit">{esc(label)}</button>
          </form>
          <p class="waitlist-status" role="status" aria-live="polite"></p>
        </div>'''


def page(app, filename, title, description, body, current=None, on_home=False):
    out = head(app, title, description) + "<body>\n" + nav(app, current, on_home) + \
        "\n  <main>\n" + body + "\n  </main>\n\n" + footer(app)
    with open(os.path.join(public_dir(app["slug"]), filename), "w") as f:
        f.write(out)


# Pages -----------------------------------------------------------------------
# The Dayline bento layout every home page follows.
LAYOUT = ["third", "two-thirds", "half", "half", "two-thirds", "third", "full"]

SCREENS_DIR = os.path.join(HERE, "screens")
SHOT_EXTS = (".png", ".jpg", ".jpeg", ".webp")
# How many phone screenshots each card size shows.
SHOTS_PER_SIZE = {"third": 1, "half": 1, "two-thirds": 2, "full": 3}


def shot(app, key, label):
    """A phone screenshot slot. Uses screens/<slug>/<key>.<ext> if it exists,
    otherwise a placeholder that names the file to add."""
    for ext in SHOT_EXTS:
        src = os.path.join(SCREENS_DIR, app["slug"], key + ext)
        if os.path.exists(src):
            dest = os.path.join(public_dir(app["slug"]), "assets", "screens")
            os.makedirs(dest, exist_ok=True)
            shutil.copyfile(src, os.path.join(dest, key + ext))
            return f'<div class="shot"><img src="assets/screens/{key}{ext}" alt="{esc(app["name"])}: {esc(label)}" loading="lazy"></div>'
    return f'''<div class="shot" role="img" aria-label="{esc(app["name"])} screenshot placeholder: {esc(label)}">
              <div class="shot-ph"><img class="app-icon" src="assets/app-icon.svg" alt=""><b>{esc(label)}</b><code>screens/{app["slug"]}/{key}.png</code></div>
            </div>'''


def card(app, i, f):
    n = SHOTS_PER_SIZE[f["size"]]
    keys = [f"card-{i}"] if n == 1 else [f"card-{i}-{j}" for j in range(1, n + 1)]
    labels = f.get("shots") or [f["title"]] * n
    phones = "\n".join(
        f'''            <div class="mini-phone">
            {shot(app, k, lbl)}
            </div>''' for k, lbl in zip(keys, labels))
    return f'''        <figure class="card {f["size"]}" style="--k: var(--accent-{f["color"]})">
          <figcaption class="card-text">
            <span class="kicker">{esc(f["kicker"])}</span>
            <h2>{esc(f["title"])}</h2>
            <p>{esc(f["text"])}</p>
          </figcaption>
          <div class="card-media peek peek-{n}">
{phones}
          </div>
        </figure>
'''


def chip(cls, icon, color, title, sub):
    return f'''        <div class="float-chip {cls}" aria-hidden="true">
          <span class="chip-icon icon" style="--c: var(--accent-{color})">{icon}</span>
          <div><b class="rounded">{esc(title)}</b><small>{esc(sub)}</small></div>
        </div>'''


def build_index(app):
    assert [f["size"] for f in app["features"]] == LAYOUT, f'{app["slug"]}: features must follow {LAYOUT}'
    features = "".join(card(app, i, f) for i, f in enumerate(app["features"], 1))
    chips = "\n".join(chip(cls, *ch) for cls, ch in zip(("chip-streak", "chip-done"), app["chips"]))
    faq = "\n".join(f'''        <div class="faq-item">
          <h3>{esc(q)}</h3>
          <p>{esc(a)}</p>
        </div>''' for q, a in app["faq"])
    values = "\n".join(f'''        <figure class="value" style="--c: var(--accent-{color})">
          <span class="badge icon">{icon}</span>
          <div><h3>{esc(t)}</h3><p>{esc(d)}</p></div>
        </figure>''' for icon, color, t, d in app["values"])
    body = f'''    <!-- ===================== Hero ===================== -->
    <section class="hero" id="waitlist">
      <div class="hero-content">
        <span class="status-pill"><span class="dot"></span>{esc(app["status"])}</span>
        <h1>{app["h1"]}</h1>
        <p>{esc(app["sub"])}</p>
        {waitlist_form(app, "hero")}
        <span class="hero-note">{esc(app["hero_note"])}</span>
      </div>

      <div class="hero-media">
        <div class="hero-glow" aria-hidden="true"></div>
        <div class="phone">
          <div class="phone-screen has-shot">
            {shot(app, "hero", app["hero_shot"])}
          </div>
        </div>
{chips}
      </div>
    </section>

    <!-- ===================== Features ===================== -->
    <section class="section" id="features">
      <div class="section-head">
        <span class="eyebrow">Features</span>
        <h2 class="section-title">{app["features_title"]}</h2>
      </div>
      <div class="card-grid">
{features}
      </div>
    </section>

    <!-- ===================== FAQ ===================== -->
    <section class="section reviews-section">
      <h2 class="reviews-title">Questions, answered</h2>
      <div class="faq">
{faq}
      </div>
    </section>

    <!-- ===================== Values ===================== -->
    <section class="section">
      <div class="section-head">
        <span class="eyebrow">Values</span>
        <h2 class="section-title">{esc(app["values_title"])}</h2>
      </div>
      <div class="values">
{values}
      </div>
    </section>

    <!-- ===================== CTA ===================== -->
    <section class="cta">
      <div class="cta-inner">
        <img class="app-icon" src="assets/app-icon.svg" alt="{esc(app["name"])} app icon">
        <h2>{esc(app["cta_title"])}</h2>
        <p>{esc(app["cta_sub"])}</p>
        {waitlist_form(app, "cta")}
      </div>
    </section>'''
    page(app, "index.html", f'{app["name"]}: {app["title"]}', app["description"], body, on_home=True)


def build_release_notes(app):
    entries = []
    for e in app["release_notes"]:
        entries.append(f'''      <article class="article">
        <span class="date"><span class="version-tag">{esc(e["tag"])}</span>{esc(e["date"])}</span>
        <h1>{esc(e["title"])}</h1>
{e["body"]}
      </article>''')
    steps = "\n".join(f'''          <div class="step {state}">
            <span class="n">{'<span class="icon">check</span>' if state == "done" else i + 1}</span>
            <div><b>{esc(t)}</b><span>{esc(d)}</span></div>
          </div>''' for i, (state, t, d) in enumerate(app["roadmap"]))
    body = f'''    <div class="page-head">
      <h1>Release Notes</h1>
      <p>{esc(app["name"])} is in development. Here's where things stand.</p>
    </div>
    <div class="article-list">
{chr(10).join(entries)}

      <article class="article">
        <h1>Roadmap</h1>
        <p>What we're working on, in order. Plans may change as we learn from early testers.</p>
        <div class="steps roadmap">
{steps}
        </div>
      </article>

      <section class="article" style="text-align: center">
        <h2 style="margin-top: 0">Be first to try it</h2>
        <p>Join the waitlist and we'll email you when {esc(app["name"])} is ready.</p>
        {waitlist_form(app, "release-notes", center=True)}
      </section>
    </div>'''
    page(app, "release-notes.html", f'Release Notes · {app["name"]}', f'What\'s new with {app["name"]}.', body, current="release-notes")


def build_contact(app):
    email = app["contact_email"]
    topics = "\n".join(f"              <option>{esc(t)}</option>" for t in app["contact_topics"])
    body = f'''    <div class="page-head">
      <h1>Contact</h1>
      <p>Questions, ideas or partnership requests. We read everything.</p>
    </div>
    <div class="article-list">
      <section class="article">
        <h2 style="margin-top: 0">Get in touch</h2>
        <div class="contact-options">
          <a class="option" href="mailto:{email}" style="--c: var(--accent-blue)">
            <span class="badge icon">mail</span>
            <div><b>Email</b><span>{email}</span></div>
          </a>
          <a class="option" href="mailto:{email}?subject=Feature%20idea%20for%20{esc(app["name"]).replace(" ", "%20")}" style="--c: var(--accent-orange)">
            <span class="badge icon">lightbulb</span>
            <div><b>Suggest a feature</b><span>Tell us what would help you most</span></div>
          </a>
          <a class="option" href="mailto:{email}?subject=Early%20testing" style="--c: var(--accent-green)">
            <span class="badge icon">science</span>
            <div><b>Become an early tester</b><span>Help shape {esc(app["name"])} before launch</span></div>
          </a>
          <a class="option" href="mailto:{email}?subject=Press" style="--c: var(--accent-purple)">
            <span class="badge icon">campaign</span>
            <div><b>Press and partnerships</b><span>We'd love to hear from you</span></div>
          </a>
        </div>
      </section>

      <section class="article">
        <h2 style="margin-top: 0">Send a message</h2>
        <p>Fill this in and it'll open in your mail app, ready to send.</p>
        <form class="form" action="#" data-form="contact" data-mailto="{email}" data-app-name="{esc(app["name"])}">
          <div class="form-row">
            <label>Name<input class="input" name="name" autocomplete="name" placeholder="Your name" required></label>
            <label>Email<input class="input" type="email" name="email" autocomplete="email" placeholder="you@example.com" required></label>
          </div>
          <label>Topic
            <select class="input" name="topic">
{topics}
            </select>
          </label>
          <label>Message<textarea class="input" name="message" placeholder="How can we help?" required></textarea></label>
          <button class="button" type="submit"><span class="icon">send</span>Send</button>
        </form>
        <div class="success" role="status"><span class="icon">check_circle</span>Your mail app should open now.</div>
      </section>
    </div>'''
    page(app, "contact.html", f'Contact · {app["name"]}', f'Get in touch with the {app["name"]} team.', body, current="contact")


def sections_html(sections):
    return "\n".join(f"        <h2>{esc(h)}</h2>\n{b}" for h, b in sections)


def build_privacy(app):
    email = app["contact_email"]
    waitlist = [
        ("This website and the waitlist", f'''        <p>When you join the waitlist, we store your email address, which app you signed up for, and the time you signed up. We also store your approximate location (country, region, city and time zone, estimated from your IP address by Cloudflare; we don't store the IP address itself) and how you found this site (the page you signed up on, the site that linked you here, and any campaign tags in the link). We use this only to tell you about {esc(app["name"])}'s launch and major updates, and to understand where interest in it comes from. We don't sell or share it, and every email includes a way to unsubscribe.</p>
        <p>Waitlist sign-ups are stored with our hosting provider, Cloudflare. To remove your email from the waitlist, contact us at <a href="mailto:{email}">{email}</a>.</p>
        <p>This site doesn't use advertising or tracking cookies. We count visits with Cloudflare Web Analytics, which doesn't use cookies or track you across other websites.</p>'''),
    ]
    body = f'''    <div class="article-list">
      <article class="article">
        <h1>Privacy Policy</h1>
        <p>{esc(app["privacy_intro"])}</p>
{sections_html(waitlist + app["privacy"])}
        <h2>Changes to this policy</h2>
        <p>{esc(app["name"])} hasn't launched yet. We'll update this policy before launch to reflect exactly how the app works, and note material changes in the <a href="release-notes.html">release notes</a>.</p>
        <p>Questions? Reach us at <a href="mailto:{email}">{email}</a>.</p>
        <p class="date">Last updated: {LAST_UPDATED}</p>
      </article>
    </div>'''
    page(app, "privacy.html", f'Privacy Policy · {app["name"]}', f'How {app["name"]} handles your data.', body)


def build_terms(app):
    email = app["contact_email"]
    common_top = [
        ("Pre-launch", f'''        <p>{esc(app["name"])} is still in development. Joining the waitlist doesn't create an account, involve any payment, or guarantee access on a particular date. Features described on this site reflect our current plans and may change before launch.</p>'''),
    ]
    common_bottom = [
        ("App Store terms", '''        <p>Once released, the app will be distributed through the App Store and licensed to you under Apple's <a href="https://www.apple.com/legal/internet-services/itunes/dev/stdeula/">Standard Licensed Application End User License Agreement</a>, together with these terms.</p>'''),
        ("Disclaimer", f'''        <p>{esc(app["name"])} is provided "as is" without warranties of any kind. To the fullest extent permitted by law, we're not liable for any indirect or consequential damages arising from use of the website or the app.</p>'''),
        ("Changes", '''        <p>We may update these terms from time to time. Continuing to use the website or app after changes take effect means you accept the updated terms.</p>'''),
    ]
    body = f'''    <div class="article-list">
      <article class="article">
        <h1>Terms of Use</h1>
        <p>These terms cover this website, the {esc(app["name"])} waitlist, and the {esc(app["name"])} app once it's released.</p>
{sections_html(common_top + app["terms"] + common_bottom)}
        <p>Questions? Contact us at <a href="mailto:{email}">{email}</a>.</p>
        <p class="date">Last updated: {LAST_UPDATED}</p>
      </article>
    </div>'''
    page(app, "terms.html", f'Terms of Use · {app["name"]}', f'Terms of use for {app["name"]}.', body)


def build_updates(app):
    body = f'''    <div class="page-head">
      <h1>Follow Updates</h1>
      <p>Hear first when {esc(app["name"])} launches, plus the occasional behind-the-scenes update.</p>
    </div>
    <div class="article-list">
      <section class="article">
        <h2 style="margin-top: 0">Join the waitlist</h2>
        <p>One email when early access opens, and a few short updates along the way. No spam, unsubscribe anytime.</p>
        {waitlist_form(app, "updates")}
      </section>

      <section class="article">
        <h2 style="margin-top: 0">What to expect</h2>
        <div class="steps roadmap">
          <div class="step done"><span class="n"><span class="icon">check</span></span><div><b>You join</b><span>Just your email. No account, no payment.</span></div></div>
          <div class="step now"><span class="n">2</span><div><b>Progress updates</b><span>Short notes when we hit a milestone.</span></div></div>
          <div class="step"><span class="n">3</span><div><b>Early access</b><span>Waitlist members get the first TestFlight invites.</span></div></div>
        </div>
      </section>

      <section class="article" style="text-align: center">
        <h2 style="margin-top: 0">See where things stand</h2>
        <p>Read our progress and roadmap so far.</p>
        <p><a class="button" href="release-notes.html" style="align-self: center"><span class="icon">article</span>Read the release notes</a></p>
      </section>
    </div>'''
    page(app, "updates.html", f'Follow Updates · {app["name"]}', f'Stay up to date with {app["name"]}.', body)


# Driver ----------------------------------------------------------------------
def public_dir(slug):
    return os.path.join(PUBLIC_DIR, slug)


def load_app(slug):
    path = os.path.join(APPS_DIR, slug.replace("-", "_") + ".py")
    spec = importlib.util.spec_from_file_location(slug, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    app = mod.APP
    app["slug"] = slug
    return app


def build(slug):
    app = load_app(slug)
    out = public_dir(slug)
    os.makedirs(os.path.join(out, "assets"), exist_ok=True)
    shutil.rmtree(os.path.join(out, "assets", "screens"), ignore_errors=True)
    for name in ("styles.css", "site.js"):
        shutil.copyfile(os.path.join(ASSETS_DIR, name), os.path.join(out, "assets", name))
    with open(os.path.join(out, "assets", "app-icon.svg"), "w") as f:
        f.write(icon_svg(app))
    build_index(app)
    build_release_notes(app)
    build_contact(app)
    build_privacy(app)
    build_terms(app)
    build_updates(app)
    print(f"built public/{slug}/")
    return app


def build_catalogue():
    """Write public/apps.js, the app list the catalogue at bishal.app/ renders.

    Always covers every app in ORDER, so the catalogue matches the sites."""
    entries = []
    for slug in ORDER:
        app = load_app(slug)
        entries.append({
            "slug": slug,
            "name": app["name"],
            "tagline": app["title"],
            "url": f"/{slug}/",
            "icon": f"/{slug}/assets/app-icon.svg",
            "colors": [app["icon"]["from"], app["icon"]["to"]],
        })
    with open(os.path.join(PUBLIC_DIR, "apps.js"), "w") as f:
        f.write("// Generated by tools/site-builder/build.py from tools/site-builder/apps/*.py. Don't edit by hand.\n")
        f.write("window.APPS = " + json.dumps(entries, indent=2, ensure_ascii=False) + ";\n")
    print("built public/apps.js")


if __name__ == "__main__":
    targets = sys.argv[1:] or ORDER
    for slug in targets:
        if slug not in ORDER:
            sys.exit(f"unknown app: {slug} (expected one of {', '.join(ORDER)})")
        build(slug)
    build_catalogue()

