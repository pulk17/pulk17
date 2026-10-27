#!/usr/bin/env python3
"""Builds the profile README's images (assets/*.svg) and README.md.

Look: plain ink on a transparent background, so the images sit on GitHub's own
page in light and dark mode. One accent, a violet close to GitHub's "merged"
purple, used only on things that were actually shipped or measured. The only
motion is the order book in the hero.

Type is Geist, converted to outlines so every viewer sees the same thing.

    npm i @fontsource/geist-sans@5.3.0 @fontsource/geist-mono@5.3.0
    pip install fonttools brotli
    FONTDIR=node_modules/@fontsource python3 build.py

The "Open source" table is not written here: scripts/contrib.py owns the block
between <!-- contrib:start --> and <!-- contrib:end -->, and this script keeps
whatever is there.
"""
import html
import math
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

OUT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(OUT, "assets")
FONTDIR = os.environ.get("FONTDIR", "node_modules/@fontsource")
FACES = {
    "r": f"{FONTDIR}/geist-sans/files/geist-sans-latin-400-normal.woff2",
    "m": f"{FONTDIR}/geist-sans/files/geist-sans-latin-500-normal.woff2",
    "b": f"{FONTDIR}/geist-sans/files/geist-sans-latin-600-normal.woff2",
    "mono": f"{FONTDIR}/geist-mono/files/geist-mono-latin-400-normal.woff2",
}
_F = {k: TTFont(p) for k, p in FACES.items()}

# Text colours match GitHub's own so the images read as part of the page.
THEMES = {
    "light": dict(ink="#1F2328", sub="#59636E", faint="#D1D9E0", wash="#F6F8FA", acc="#6E40C9", acc2="#E9E1FB"),
    "dark": dict(ink="#E6EDF3", sub="#9198A1", faint="#30363D", wash="#151B23", acc="#B392F0", acc2="#2A2140"),
}
W = 720  # every image shares this width, so they line up on the page


# ------------------------------------------------------------------ type engine
def width(s, face, size, ls=0.0):
    f = _F[face]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    tot = 0
    for ch in s:
        if ord(ch) not in cmap:
            raise ValueError(f"glyph {ch!r} missing from {face}")
        tot += hmtx[cmap[ord(ch)]][0]
    return tot * size / upm + ls * max(len(s) - 1, 0)


def wrap(s, face, size, maxw):
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if width(t, face, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


class Svg:
    def __init__(self, h, title, desc, theme):
        self.h, self.title, self.desc, self.P = h, title, desc, THEMES[theme]
        self.els, self.defs, self.css, self.glyphs = [], [], [], {}

    def add(self, s):
        self.els.append(s)

    def text(self, x, y, s, face, size, fill, anchor="start", ls=0.0, cls=""):
        f = _F[face]
        cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
        w = width(s, face, size, ls)
        x0 = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
        k, pen, uses = size / upm, 0.0, []
        for ch in s:
            g = cmap[ord(ch)]
            if ch != " ":
                uses.append(f'<use href="#{self.glyph(face, g)}" x="{pen / k:.0f}"/>')
            pen += hmtx[g][0] * k + ls
        c = f' class="{cls}"' if cls else ""
        self.add(f'<g{c} fill="{fill}" transform="translate({x0:.2f} {y:.2f}) scale({k:.5f} {-k:.5f})">{"".join(uses)}</g>')
        return w

    def para(self, x, y, s, face, size, fill, maxw, lead):
        lines = wrap(s, face, size, maxw)
        for i, line in enumerate(lines):
            self.text(x, y + i * lead, line, face, size, fill)
        return y + (len(lines) - 1) * lead

    def glyph(self, face, g):
        if (face, g) not in self.glyphs:
            gs = _F[face].getGlyphSet()
            pen = SVGPathPen(gs)
            gs[g].draw(pen)
            gid = f"{face}{len(self.glyphs):x}"
            self.glyphs[(face, g)] = gid
            self.defs.append(f'<path id="{gid}" d="{pen.getCommands()}"/>')
        return self.glyphs[(face, g)]

    def render(self):
        t, d = html.escape(self.title), html.escape(self.desc)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" width="{W}" height="{self.h}" '
                f'role="img" aria-labelledby="t d"><title id="t">{t}</title><desc id="d">{d}</desc>'
                f'<style>{"".join(self.css)}</style><defs>{"".join(self.defs)}</defs>{"".join(self.els)}</svg>\n')


def chips(s, x, y, items):
    """Tech stack as quiet words separated by space, not dots."""
    P = s.P
    for it in items:
        x += s.text(x, y, it, "r", 12.5, P["sub"]) + 16


# ------------------------------------------------------------------ hero
HERO_FACTS = [
    ("8.9M", "messages a second,", "NASDAQ order book engine"),
    ("OpenCV", "C++ fix merged;", "ClickHouse PRs in review"),
    ("1986", "peak Codeforces rating,", "Candidate Master"),
    ("GSoC 2026", "Google Summer of Code", "with CCExtractor"),
]
HERO_ALT = ("Pulkit Chauhan. C++ systems engineer: order books, databases and open source. "
            "Final-year computer science student at UPES, graduating May 2027, open to software engineering roles "
            "from January 2027. 8.9 million messages a second through his NASDAQ order book engine. "
            "A C++ fix merged into OpenCV, with more work in review at ClickHouse. Peak Codeforces rating 1986, "
            "Candidate Master. Google Summer of Code 2026 with CCExtractor.")


def ladder(s, x0, y0):
    """A small live order book: asks above the spread, bids below.
    Bids are filled with the accent, asks are outlines. Bar lengths drift
    a little, like a book while the tape replays."""
    P = s.P
    asks = [(145.69, 0.48), (145.68, 0.74), (145.67, 0.40), (145.66, 0.62), (145.65, 0.30)]
    bids = [(145.64, 0.56), (145.63, 0.90), (145.62, 0.66), (145.61, 0.82), (145.60, 0.44)]
    row, gap, bx, bw = 15, 4, x0 + 54, 176
    s.css.append(
        ".lv{transform-box:fill-box;transform-origin:left center;animation:dr var(--d) ease-in-out infinite alternate}"
        "@keyframes dr{from{transform:scaleX(1)}to{transform:scaleX(var(--s))}}"
        ".tp{animation:tp 4.2s ease-in-out infinite}"
        "@keyframes tp{0%,70%,100%{opacity:1}80%{opacity:.35}}"
        "@media (prefers-reduced-motion:reduce){.lv,.tp{animation:none}}")
    drift = [(5.2, .82), (3.7, 1.12), (6.1, .9), (4.4, 1.08), (3.1, .7)]
    y = y0
    for i, (px, q) in enumerate(asks):
        s.text(x0, y + 11, f"{px:.2f}", "mono", 11, P["sub"])
        d, sc = drift[i]
        cls = "lv" + (" tp" if i == len(asks) - 1 else "")
        s.add(f'<rect class="{cls}" style="--d:{d}s;--s:{sc}" x="{bx}" y="{y + 1}" width="{bw * q:.1f}" height="{row - 2}" '
              f'rx="1.5" fill="none" stroke="{P["sub"]}" stroke-width="1"/>')
        y += row + gap
    # the spread
    s.add(f'<line x1="{bx}" y1="{y + 1.5}" x2="{bx + bw}" y2="{y + 1.5}" stroke="{P["faint"]}" stroke-width="1" stroke-dasharray="2 3"/>')
    y += 8
    for i, (px, q) in enumerate(bids):
        s.text(x0, y + 11, f"{px:.2f}", "mono", 11, P["sub"])
        d, sc = drift[(i + 2) % 5]
        cls = "lv" + (" tp" if i == 0 else "")
        op = 1 - i * 0.13
        s.add(f'<rect class="{cls}" style="--d:{d}s;--s:{sc}" x="{bx}" y="{y}" width="{bw * q:.1f}" height="{row - 1}" '
              f'rx="1.5" fill="{P["acc"]}" fill-opacity="{op:.2f}"/>')
        y += row + gap
    return y


def hero(theme):
    s = Svg(318, "Pulkit Chauhan", HERO_ALT, theme)
    P = s.P
    s.text(0, 52, "Pulkit Chauhan", "b", 44, P["ink"], ls=-1.3)
    y = s.para(0, 92, "C++ systems engineer. Order books, databases and open source.", "r", 19, P["ink"], 380, 26)
    y = s.para(0, y + 36, "Final-year computer science student at UPES, graduating May 2027. "
                          "Open to software engineering roles from January 2027.", "r", 14, P["sub"], 360, 21)
    ladder(s, 478, 6)
    s.add(f'<line x1="0" y1="222" x2="{W}" y2="222" stroke="{P["faint"]}" stroke-width="1"/>')
    col = W / 4
    for i, (fig, l1, l2) in enumerate(HERO_FACTS):
        x = i * col
        s.text(x, 262, fig, "b", 24, P["ink"], ls=-0.5)
        s.text(x, 286, l1, "r", 12.5, P["sub"])
        s.text(x, 304, l2, "r", 12.5, P["sub"])
    return s.render()


# ------------------------------------------------------------------ project cards
def card(theme, title, blurb, facts, stack, visual, alt, h=232):
    s = Svg(h, title, alt, theme)
    P = s.P
    s.text(0, 46, title, "b", 28, P["ink"], ls=-0.6)
    y = s.para(0, 78, blurb, "r", 15, P["ink"], 330, 22)
    y += 34
    for fig, cap in facts:
        w = s.text(0, y, fig, "m", 15, P["acc"])
        s.text(w + 8, y, cap, "r", 13, P["sub"])
        y += 22
    chips(s, 0, h - 16, stack)
    visual(s, 380, 30)
    return s.render()


# ITCH 5.0 "Add Order" message: field widths in bytes, from the spec.
ITCH_ADD = [("type", 1), ("locate", 2), ("track", 2), ("time", 6), ("order ref", 8),
            ("side", 1), ("shares", 4), ("stock", 8), ("price", 4)]


def vis_itch(s, x0, y0):
    """One 36-byte Add Order message, field by field, becoming a change in the book."""
    P = s.P
    span = W - x0
    unit = span / 36
    s.text(x0, y0 + 10, "One Add Order message, 36 bytes", "r", 12, P["sub"])
    y = y0 + 22
    x = x0
    hot = {"side", "shares", "price"}
    for name, n in ITCH_ADD:
        w = n * unit
        on = name in hot
        s.add(f'<rect x="{x + 0.5:.1f}" y="{y}" width="{w - 1:.1f}" height="26" rx="2" '
              f'fill="{P["acc2"] if on else "none"}" stroke="{P["acc"] if on else P["faint"]}" stroke-width="1"/>')
        if width(name, "r", 10) < w - 4:
            s.text(x + w / 2, y + 17, name, "r", 10, P["acc"] if on else P["sub"], anchor="middle")
        x += w
    # arrow down into the book
    ax = x0 + span * 0.78
    s.add(f'<path d="M{ax},{y + 34} V{y + 60}" stroke="{P["sub"]}" stroke-width="1" fill="none"/>'
          f'<path d="M{ax - 4},{y + 55} L{ax},{y + 61} L{ax + 4},{y + 55}" stroke="{P["sub"]}" stroke-width="1" fill="none"/>')
    by = y + 72
    s.text(x0, by - 4, "AAPL book", "r", 12, P["sub"])
    rows = [("145.66", 0.35, False), ("145.65", 0.55, False), ("145.64", 0.62, True), ("145.63", 0.80, False)]
    for i, (px, q, new) in enumerate(rows):
        yy = by + 6 + i * 17
        s.text(x0, yy + 11, px, "mono", 11, P["acc"] if new else P["sub"])
        bw = (span - 60) * q
        if i < 2:
            s.add(f'<rect x="{x0 + 52}" y="{yy}" width="{bw:.1f}" height="13" rx="1.5" fill="none" stroke="{P["sub"]}" stroke-width="1"/>')
        else:
            s.add(f'<rect x="{x0 + 52}" y="{yy}" width="{bw:.1f}" height="13" rx="1.5" fill="{P["acc"]}" fill-opacity="{0.95 if new else 0.55}"/>')
        if new:
            s.text(x0 + 52 + bw + 8, yy + 11, "+100", "mono", 11, P["acc"])


def vis_graph(s, x0, y0):
    """An app drawn as a graph. The new wire and node are the change waiting for approval."""
    P = s.P

    def node(x, y, label, new=False, w=96):
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="6" fill="{P["acc2"] if new else "none"}" '
              f'stroke="{P["acc"] if new else P["sub"]}" stroke-width="1"{" stroke-dasharray=\"3 3\"" if new else ""}/>')
        s.text(x + w / 2, y + 19.5, label, "m" if new else "r", 12, P["acc"] if new else P["ink"], anchor="middle")
        return (x, y, w)

    def wire(a, b, new=False):
        (ax, ay, aw), (bx, by, _) = a, b
        x1, y1, x2, y2 = ax + aw, ay + 15, bx, by + 15
        mx = (x1 + x2) / 2
        s.add(f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" '
              f'stroke="{P["acc"] if new else P["sub"]}" stroke-width="1"{" stroke-dasharray=\"3 3\"" if new else ""}/>')
        s.add(f'<circle cx="{x2}" cy="{y2}" r="2.2" fill="{P["acc"] if new else P["sub"]}"/>')

    ing = node(x0, y0 + 62, "Ingress", w=80)
    svc = node(x0 + 112, y0 + 62, "Service", w=82)
    dep = node(x0 + 226, y0 + 62, "Deployment", w=114)
    cfg = node(x0 + 112, y0 + 128, "ConfigMap", w=82, new=True)
    wire(ing, svc)
    wire(svc, dep)
    wire(cfg, dep, new=True)
    for i in range(3):
        px = x0 + 234 + i * 36
        s.add(f'<rect x="{px}" y="{y0 + 112}" width="26" height="20" rx="4" fill="none" stroke="{P["faint"]}" stroke-width="1"/>')
        s.add(f'<path d="M{x0 + 283},{y0 + 92} V{y0 + 112}" stroke="{P["faint"]}" stroke-width="1"/>')
    s.text(x0 + 234, y0 + 148, "3 pods", "r", 11, P["sub"])
    s.text(x0, y0 + 10, "Your app as a graph", "r", 12, P["sub"])
    s.text(x0 + 112, y0 + 178, "+ new, waits for your approval", "r", 11, P["acc"])


def vis_room(s, x0, y0):
    """Phones around the server. One vote goes in, the result goes out to everyone."""
    P = s.P
    cx, cy = x0 + 170, y0 + 98
    s.add(f'<circle cx="{cx}" cy="{cy}" r="30" fill="none" stroke="{P["ink"]}" stroke-width="1"/>')
    s.text(cx, cy + 4, "server", "m", 12, P["ink"], anchor="middle")
    n, r = 6, 86
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2) * (2 * math.pi / n)
        px, py = cx + r * 1.55 * math.cos(a), cy + r * 0.95 * math.sin(a)
        hot = i == 1
        x1, y1 = cx + 32 * math.cos(a), cy + 32 * math.sin(a)
        s.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="{P["acc"] if hot else P["faint"]}" stroke-width="1"/>')
        s.add(f'<rect x="{px - 9:.1f}" y="{py - 15:.1f}" width="18" height="30" rx="4" fill="{P["acc2"] if hot else "none"}" '
              f'stroke="{P["acc"] if hot else P["sub"]}" stroke-width="1"/>')
        if hot:
            s.text(px, py - 22, "vote", "m", 11, P["acc"], anchor="middle")
    s.text(x0, y0 + 10, "One room", "r", 12, P["sub"])


CARDS = {
    "pitchfork": dict(
        title="PitchFork",
        blurb="Rebuilds the live order book for every stock from a full day of raw NASDAQ data, then tests trading signals on it.",
        facts=[("8.9M msg/s", "on one laptop core"), ("46 KB", "WebAssembly build that runs in the browser")],
        stack=["C++17", "WebAssembly", "Linux"], visual=vis_itch,
        alt="PitchFork: rebuilds the live order book for every stock from a full day of raw NASDAQ ITCH 5.0 data, "
            "then tests trading signals on it. 8.9 million messages a second on one laptop core. A 46 KB WebAssembly "
            "build runs in the browser. The drawing shows one 36-byte Add Order message, field by field, turning into "
            "a new level in the AAPL book. Built with C++17, WebAssembly and Linux."),
    "k8n": dict(
        title="k8n",
        blurb="A visual IDE for Kubernetes. Draw your app as a graph; k8n writes the YAML, shows the diff and deploys only after you approve it.",
        facts=[("One binary", "for Windows, macOS and Linux"), ("AI assistant", "proposes fixes, you approve them")],
        stack=["Go", "Next.js", "Kubernetes"], visual=vis_graph,
        alt="k8n: a visual IDE for Kubernetes. Draw your app as a graph; k8n writes the YAML, shows the diff and "
            "deploys only after you approve it. One binary for Windows, macOS and Linux. An AI assistant proposes "
            "fixes that you approve. The drawing shows Ingress, Service and Deployment nodes, with a new ConfigMap "
            "waiting for approval. Built with Go, Next.js and Kubernetes."),
    "undercover": dict(
        title="Undercover",
        blurb="A real-time multiplayer party game. Friends join from their phones, and the server runs every round so nobody can cheat.",
        facts=[("Live rooms", "synced over Socket.IO"), ("Deployed", "playable from any phone browser")],
        stack=["TypeScript", "Socket.IO", "Redis"], visual=vis_room,
        alt="Undercover: a real-time multiplayer party game. Friends join from their phones, and the server runs "
            "every round so nobody can cheat. Live rooms synced over Socket.IO; deployed and "
            "playable from any phone browser. The drawing shows six phones around the server, one sending a vote. "
            "Built with TypeScript, Socket.IO and Redis."),
}

LINKS = {
    "pitchfork": [("Source", "https://github.com/pulk17/NASDAQ-ITCH-OrderBook"), ("Live demo", "https://pitchfork.pages.dev/")],
    "k8n": [("Source", "https://github.com/pulk17/k8n"), ("Try the editor", "https://k8n.pages.dev/")],
    "undercover": [("Source", "https://github.com/pulk17/undercover-game"), ("Play it", "https://undercover-game-client.vercel.app/")],
}


# ------------------------------------------------------------------ README
def picture(name, alt, href=None):
    pic = (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="./assets/{name}-dark.svg">\n'
           f'  <img alt="{html.escape(alt)}" src="./assets/{name}-light.svg" width="100%">\n</picture>')
    return f'<a href="{href}">\n{pic}\n</a>' if href else pic


def readme(contrib_block):
    parts = [picture("hero", HERO_ALT), "", "## Open source", "", contrib_block, "", "## Projects", ""]
    for key, c in CARDS.items():
        parts += [picture(key, c["alt"], LINKS[key][0][1]), "",
                  "&emsp;".join(f"[{t}]({u})" for t, u in LINKS[key]), "", ""]
    parts += [
        "**Also:** [Band-Former](https://github.com/pulk17/Band-Former) turns a song into guitar tab you can actually "
        "play. PyTorch models pick out the notes, then a C++ search chooses fingerings a real hand can reach.",
        "",
        "## Contact",
        "",
        "&emsp;".join([
            "[Email](mailto:chauhanpulkit1708@gmail.com)",
            "[LinkedIn](https://www.linkedin.com/in/pulk1t/)",
            "[Codeforces](https://codeforces.com/profile/pulk1t)",
            "[LeetCode](https://leetcode.com/u/pulk1tt/)",
            "[Website](https://pulk1t.vercel.app/)",
        ]),
        "",
    ]
    return "\n".join(parts)


def current_contrib_block():
    path = os.path.join(OUT, "README.md")
    start, end = "<!-- contrib:start -->", "<!-- contrib:end -->"
    if os.path.exists(path):
        t = open(path).read()
        if start in t and end in t:
            return t[t.index(start): t.index(end) + len(end)]
    return f"{start}\n_Run `python scripts/contrib.py` to fill this in._\n{end}"


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(ASSETS, f"hero-{theme}.svg"), "w") as f:
            f.write(hero(theme))
        for key, c in CARDS.items():
            with open(os.path.join(ASSETS, f"{key}-{theme}.svg"), "w") as f:
                f.write(card(theme, c["title"], c["blurb"], c["facts"], c["stack"], c["visual"], c["alt"]))
    block = current_contrib_block()
    with open(os.path.join(OUT, "README.md"), "w") as f:
        f.write(readme(block))
    print("built", sorted(os.listdir(ASSETS)))


if __name__ == "__main__":
    main()
