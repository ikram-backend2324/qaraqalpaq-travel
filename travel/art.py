"""Procedurally generated SVG illustrations (no stock photos needed)."""
import math
import random

SKIES = [
    ("#f6b26b", "#e06c3c", "#fde8c8"),   # sunset
    ("#9ad0ec", "#5aa9d6", "#fdf3dc"),   # day
    ("#1b2a4a", "#0d1630", "#c9b48a"),   # night
    ("#f7c59f", "#c96f8a", "#fbe3c7"),   # dusk pink
    ("#bfe3e0", "#7cc4c0", "#f8ecd4"),   # morning
    ("#2a1f4f", "#e07a5f", "#f1c40f"),   # violet sunset
    ("#a7d3f2", "#e9c46a", "#fff4dc"),   # golden
    ("#0f1f3d", "#28406b", "#d8c9a3"),   # deep night
]
SAND = ["#e9c58f", "#dcae6e", "#c98f4f", "#b97a3b"]
RED, BLUE, CREAM, INK = "#b6322a", "#1f5f8b", "#f7efe1", "#2b1d14"


def _wrap(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice">'
            f"<defs>{defs}</defs>{body}</svg>")


def _sky(w, h, i, gid="sky"):
    top, mid, low = SKIES[i % len(SKIES)]
    defs = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset=".55" stop-color="{mid}"/><stop offset="1" stop-color="{low}"/></linearGradient>')
    body = f'<rect width="{w}" height="{h}" fill="url(#{gid})"/>'
    night = i % len(SKIES) in (2, 7)
    rnd = random.Random(i * 31 + 7)
    if night:
        for _ in range(70):
            body += f'<circle cx="{rnd.randint(0, w)}" cy="{rnd.randint(0, int(h * .45))}" r="{rnd.choice([0.8, 1.1, 1.6])}" fill="#fff" opacity="{rnd.uniform(.4, 1):.2f}"/>'
        body += f'<circle cx="{w * .8:.0f}" cy="{h * .18:.0f}" r="26" fill="#f4f1de"/><circle cx="{w * .8 + 10:.0f}" cy="{h * .16:.0f}" r="24" fill="{top}"/>'
    else:
        body += f'<circle cx="{w * (.2 + (i % 3) * .3):.0f}" cy="{h * .3:.0f}" r="{38 + i % 3 * 6}" fill="#fff6d8" opacity=".9"/>'
    return defs, body


def _dunes(w, h, i, base=.62):
    rnd = random.Random(i)
    out = ""
    for k, col in enumerate(SAND):
        y = h * (base + k * .09)
        a = rnd.uniform(.03, .07) * h
        p = f"M0 {y:.0f} "
        for x in range(0, w + 100, 100):
            p += f"Q{x + 50} {y - a * (1 if (x // 100 + k) % 2 else -0.6):.0f} {x + 100} {y:.0f} "
        out += f'<path d="{p} L{w} {h} L0 {h} Z" fill="{col}"/>'
    return out


def _yurt(x, y, s, door=RED):
    return (f'<g transform="translate({x},{y}) scale({s})">'
            f'<path d="M-60 0 L-60 -40 Q0 -95 60 -40 L60 0 Z" fill="{CREAM}" stroke="#8a6a46" stroke-width="2"/>'
            f'<path d="M-60 -40 Q0 -95 60 -40" fill="none" stroke="{RED}" stroke-width="7"/>'
            f'<rect x="-60" y="-30" width="120" height="7" fill="{BLUE}"/>'
            f'<path d="M-60 -26 l10 -4 l10 4 l10 -4 l10 4 l10 -4 l10 4 l10 -4 l10 4 l10 -4 l10 4 l10 -4 l10 4" stroke="#fff" stroke-width="1.5" fill="none"/>'
            f'<rect x="-14" y="-28" width="28" height="28" rx="3" fill="{door}"/>'
            f'<circle cx="0" cy="-74" r="6" fill="#8a6a46"/></g>')


def _dome(x, y, s):
    lines = "".join(f'<path d="M{-50 + k * 20} 0 Q{-50 + k * 20} -55 0 -60" fill="none" stroke="#ffffff" stroke-width="1.6" opacity=".8"/>' for k in range(6))
    return (f'<g transform="translate({x},{y}) scale({s})">'
            f'<path d="M-55 0 A55 60 0 0 1 55 0 Z" fill="#ffffff" opacity=".35" stroke="#fff" stroke-width="2"/>{lines}'
            f'<path d="M-40 0 A40 30 0 0 1 40 0 Z" fill="#ffd27a" opacity=".55"/></g>')


def _house(x, y, s):
    orn = "".join(f'<path d="M{-58 + k * 14} -52 l7 -7 l7 7 l-7 7 Z" fill="{RED}"/>' for k in range(9))
    return (f'<g transform="translate({x},{y}) scale({s})">'
            f'<rect x="-65" y="-70" width="130" height="70" fill="#efd9b4" stroke="#8a6a46" stroke-width="2"/>{orn}'
            f'<rect x="-15" y="-38" width="30" height="38" fill="{BLUE}"/><rect x="-52" y="-36" width="22" height="18" fill="#7cc4c0"/>'
            f'<rect x="30" y="-36" width="22" height="18" fill="#7cc4c0"/><rect x="-70" y="-76" width="140" height="8" fill="#8a6a46"/></g>')


def stay_svg(kind, palette, w=800, h=500):
    defs, body = _sky(w, h, palette)
    wide = w / h > 1.8
    body += _dunes(w, h, palette, .5 if wide else .62)
    gy = h * (.6 if wide else .78)
    if kind == "yurt" and w / h > 1.8:
        body += _yurt(w * .72, gy, 1.6) + _yurt(w * .85, gy + 12, 1.3, BLUE) + _yurt(w * .95, gy - 4, 1.0)
    elif kind == "yurt":
        body += _yurt(w * .30, gy, 1.25) + _yurt(w * .58, gy + 10, 1.0, BLUE) + _yurt(w * .80, gy - 6, .8)
        body += f'<g transform="translate({w * .12},{gy + 20})"><path d="M0 0 l10 -26 l12 0 l8 26" fill="#c25b1d"/><path d="M5 -10 q10 -30 20 0" fill="#ffb347"/></g>'
    elif kind == "glamping":
        body += _dome(w * .35, gy, 1.5) + _dome(w * .68, gy + 8, 1.2)
    else:
        body += _house(w * .5, gy + 10, 1.6)
    return _wrap(w, h, body, defs)


def _fort_ruins(w, h, col="#c99a5f"):
    p = (f"M{w * .1} {h * .8} L{w * .1} {h * .55} L{w * .16} {h * .52} L{w * .2} {h * .6} L{w * .3} {h * .5} "
         f"L{w * .38} {h * .58} L{w * .45} {h * .48} L{w * .55} {h * .56} L{w * .62} {h * .47} L{w * .72} {h * .57} "
         f"L{w * .8} {h * .5} L{w * .9} {h * .6} L{w * .9} {h * .8} Z")
    cracks = "".join(f'<path d="M{w * x} {h * .62} l8 22 l-6 18" stroke="#8a6034" stroke-width="2" fill="none"/>' for x in (.25, .42, .6, .77))
    return f'<path d="{p}" fill="{col}" stroke="#8a6034" stroke-width="3"/>{cracks}'


def _fort_full(w, h, col="#d9a96b"):
    out = f'<rect x="{w * .1}" y="{h * .42}" width="{w * .8}" height="{h * .38}" fill="{col}" stroke="#7a4e22" stroke-width="3"/>'
    for k in range(9):
        x = w * .1 + k * w * .1
        out += f'<rect x="{x - 14}" y="{h * .34}" width="28" height="{h * .46}" rx="6" fill="#cf9a59" stroke="#7a4e22" stroke-width="3"/>'
        out += f'<rect x="{x - 4}" y="{h * .44}" width="8" height="16" fill="#5a3714"/>'
    for k in range(40):
        out += f'<rect x="{w * .1 + k * w * .02}" y="{h * .40}" width="{w * .012}" height="10" fill="#7a4e22"/>'
    out += f'<path d="M{w * .45} {h * .8} L{w * .45} {h * .62} Q{w * .5} {h * .55} {w * .55} {h * .62} L{w * .55} {h * .8} Z" fill="#5a3714"/>'
    out += f'<rect x="{w * .40}" y="{h * .18}" width="{w * .2}" height="{h * .24}" fill="#e2b77c" stroke="#7a4e22" stroke-width="3"/>'
    out += f'<path d="M{w * .38} {h * .18} L{w * .5} {h * .10} L{w * .62} {h * .18} Z" fill="{RED}"/>'
    return out


def place_svg(kind, palette, w=800, h=500):
    defs, body = _sky(w, h, palette)
    if kind == "aral":
        body += f'<rect y="{h * .62}" width="{w}" height="{h * .38}" fill="#e3c08a"/>'
        body += _ship(w * .45, h * .8, 1.3, "#9b4a2c") + _ship(w * .75, h * .86, .9, "#6d4a3a")
    elif kind == "museum":
        body += _dunes(w, h, palette, .72)
        body += (f'<rect x="{w * .2}" y="{h * .38}" width="{w * .6}" height="{h * .4}" fill="#f2e6cf" stroke="#8a6a46" stroke-width="3"/>'
                 + "".join(f'<rect x="{w * (.24 + k * .08)}" y="{h * .46}" width="{w * .04}" height="{h * .28}" fill="{BLUE}" opacity=".8"/>' for k in range(7))
                 + f'<rect x="{w * .18}" y="{h * .33}" width="{w * .64}" height="{h * .06}" fill="{RED}"/>')
    elif kind == "nature":
        body += (f'<path d="M0 {h * .45} L{w * .25} {h * .42} L{w * .4} {h * .5} L{w * .6} {h * .44} L{w} {h * .48} L{w} {h} L0 {h} Z" fill="#efe6d2"/>'
                 f'<path d="M0 {h * .55} L{w} {h * .58} L{w} {h} L0 {h} Z" fill="#d6b98a"/>'
                 + "".join(f'<path d="M{w * x} {h * .5} l6 {h * .06}" stroke="#bfae90" stroke-width="3"/>' for x in (.15, .3, .45, .6, .75, .9)))
    elif kind == "sacred":
        body += _dunes(w, h, palette, .7)
        body += (f'<path d="M{w * .3} {h * .72} Q{w * .5} {h * .52} {w * .7} {h * .72} Z" fill="#d1aa73"/>'
                 f'<ellipse cx="{w * .5}" cy="{h * .55}" rx="{w * .12}" ry="{h * .05}" fill="#b98a52"/>'
                 f'<rect x="{w * .38}" y="{h * .45}" width="{w * .24}" height="{h * .1}" fill="#c99a5f" stroke="#8a6034" stroke-width="3"/>')
    else:
        body += _dunes(w, h, palette, .74) + _fort_ruins(w, h)
    return _wrap(w, h, body, defs)


def _ship(x, y, s, col):
    return (f'<g transform="translate({x},{y}) scale({s})"><path d="M-80 -10 L80 -10 L60 15 L-70 15 Z" fill="{col}"/>'
            f'<rect x="-30" y="-40" width="50" height="30" fill="#7d3b22"/><rect x="-5" y="-75" width="6" height="35" fill="#5a2c18"/>'
            f'<path d="M-80 -10 L80 -10" stroke="#3b1d10" stroke-width="3"/></g>')


def ar_layer(scene, layer, w=1000, h=1000):
    """Transparent overlay for the AR viewer. layer: now | past | bg (demo background)."""
    if scene == "aral":
        if layer == "past":
            waves = "".join(
                f'<path class="wave" d="M0 {h * .55 + k * 40} q50 -18 100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0" '
                f'stroke="#e6f7ff" stroke-width="4" fill="none" opacity=".8" style="animation-delay:{k * .4}s"/>' for k in range(8))
            style = "<style>.wave{animation:wv 3s linear infinite}@keyframes wv{to{transform:translateX(-100px)}}</style>"
            return _wrap(w, h, f'{style}<rect y="{h * .45}" width="{w}" height="{h * .55}" fill="#2f88b9" opacity=".85"/>{waves}'
                         + _ship(w * .5, h * .5, 1.6, "#ffffff"))
        if layer == "bg":
            defs, body = _sky(w, h, 6)
            return _wrap(w, h, body + f'<rect y="{h * .55}" width="{w}" height="{h * .45}" fill="#e3c08a"/>' + _ship(w * .45, h * .78, 2.2, "#9b4a2c"), defs)
        return _wrap(w, h, "")
    # fortress
    if layer == "past":
        return _wrap(w, h, _fort_full(w, h))
    if layer == "bg":
        defs, body = _sky(w, h, 0)
        return _wrap(w, h, body + _dunes(w, h, 0, .76) + _fort_ruins(w, h), defs)
    return _wrap(w, h, "")


def _qosqulaq(cx, cy, r, col):
    """Ram's-horn (qosqulaq) inspired curl pair — an original simplified motif."""
    return (f'<path d="M{cx} {cy + r} L{cx} {cy - r * .2} M{cx} {cy - r * .2} q{-r * .9} {-r * .2} {-r * .7} {-r * .9} '
            f'q{r * .3} {-r * .4} {r * .45} 0 M{cx} {cy - r * .2} q{r * .9} {-r * .2} {r * .7} {-r * .9} q{-r * .3} {-r * .4} {-r * .45} 0" '
            f'stroke="{col}" stroke-width="{max(2, r * .16):.1f}" fill="none" stroke-linecap="round"/>')


def product_svg(cat, palette, w=600, h=600):
    bgs = ["#f7efe1", "#f3e3cf", "#efe8dc", "#f6e9d8"]
    cols = [(RED, BLUE), (BLUE, RED), ("#2f6b4f", RED), (RED, "#d69a2d"), ("#5a2c6e", "#d69a2d"), (BLUE, "#d69a2d"), (RED, "#2f6b4f"), ("#1d3557", RED)]
    c1, c2 = cols[palette % len(cols)]
    bg = bgs[palette % len(bgs)]
    body = f'<rect width="{w}" height="{h}" fill="{bg}"/>'
    if cat == "embroidery":
        body += f'<rect x="60" y="60" width="{w - 120}" height="{h - 120}" fill="{c1}" rx="10"/>'
        body += f'<rect x="85" y="85" width="{w - 170}" height="{h - 170}" fill="{bg}" rx="6"/>'
        for gx in range(3):
            for gy in range(3):
                cx, cy = 165 + gx * 135, 165 + gy * 135
                body += f'<path d="M{cx} {cy - 50} L{cx + 50} {cy} L{cx} {cy + 50} L{cx - 50} {cy} Z" fill="{c2}" opacity=".18"/>'
                body += _qosqulaq(cx, cy + 10, 36, c1)
    elif cat == "carpet":
        body += f'<rect x="70" y="40" width="{w - 140}" height="{h - 80}" fill="{c1}"/>'
        body += f'<rect x="100" y="70" width="{w - 200}" height="{h - 140}" fill="{c2}"/>'
        body += f'<rect x="125" y="95" width="{w - 250}" height="{h - 190}" fill="{c1}"/>'
        for k in range(3):
            cy = 175 + k * 125
            body += f'<path d="M{w / 2} {cy - 50} L{w / 2 + 75} {cy} L{w / 2} {cy + 50} L{w / 2 - 75} {cy} Z" fill="{bg}"/>'
            body += _qosqulaq(w / 2, cy + 8, 28, c1)
        body += "".join(f'<line x1="{80 + k * 22}" y1="20" x2="{80 + k * 22}" y2="40" stroke="#e9d9bf" stroke-width="3"/>' for k in range(20))
        body += "".join(f'<line x1="{80 + k * 22}" y1="{h - 40}" x2="{80 + k * 22}" y2="{h - 20}" stroke="#e9d9bf" stroke-width="3"/>' for k in range(20))
    elif cat == "silver":
        body += f'<circle cx="{w / 2}" cy="{h / 2}" r="190" fill="none" stroke="#b8bcc4" stroke-width="40"/>'
        body += f'<circle cx="{w / 2}" cy="{h / 2}" r="190" fill="none" stroke="#e7eaee" stroke-width="10" stroke-dasharray="6 18"/>'
        for k in range(8):
            a = k * math.pi / 4
            x, y = w / 2 + 190 * math.cos(a), h / 2 + 190 * math.sin(a)
            body += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{22 if k % 2 == 0 else 12}" fill="{c1 if k % 2 == 0 else "#d9dde3"}" stroke="#8d939c" stroke-width="3"/>'
        body += _qosqulaq(w / 2, h / 2 + 30, 60, "#8d939c")
    else:  # ceramics
        body += f'<circle cx="{w / 2}" cy="{h / 2}" r="230" fill="#fbfbf7" stroke="{c1}" stroke-width="10"/>'
        for k in range(12):
            a = k * math.pi / 6
            x, y = w / 2 + 150 * math.cos(a), h / 2 + 150 * math.sin(a)
            body += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="34" ry="16" transform="rotate({k * 30} {x:.0f} {y:.0f})" fill="{c1}" opacity=".85"/>'
        body += f'<circle cx="{w / 2}" cy="{h / 2}" r="80" fill="{c2}" opacity=".9"/>' + _qosqulaq(w / 2, h / 2 + 18, 42, "#fff")
    return _wrap(w, h, body)
