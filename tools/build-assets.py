#!/usr/bin/env python3
"""Generates every animated SVG used by README.md.

Edit the content below, then run:  python tools/build-assets.py   (needs: pip install fonttools brotli)

Design system (v3) — matches thetechzeen.com:
  * palette: ink #05060a, cobalt #2b47ff (+ #6077ff / #96a6ff / ice #cdd5ff), emerald + amber as signals
  * type: Bricolage Grotesque (display) · Geist (sans) · Geist Mono · Instrument Serif italic — subset & embedded
  * two surfaces: VIVID cobalt panels (hero, numbers, build) so the profile pops on GitHub dark AND light,
    and blue-tinted DARK panels for the rest
  * mobile-first: every image is 1200px wide and GitHub shrinks it to ~350px on phones, so key text is
    ≥40px and nothing is under ~20px.
"""
import base64
import html
import io
import math
import os
import random
import re

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets')
FONT_DIR = os.path.join(HERE, 'fonts')

STREAK = '1,000+'
EMAIL = 'info@thetechzeen.com'

# ── Brand tokens ──────────────────────────────────────────────────────────────
INK, WHITE = '#05060a', '#ffffff'
BLUE, B300, B200, ICE = '#2b47ff', '#6077ff', '#96a6ff', '#cdd5ff'
EM, AMB = '#00d294', '#fcbb00'
SURF2, EDGE = '#141a38', '#27337a'
MUT, DIM = '#c0c8e6', '#8a95c0'
TERM_BG = '#090c1a'

FONTS = {  # key: (family, weight, file)
    'd8': ('TZ Display', 800, 'BricolageGrotesque-ExtraBold.ttf'),
    's4': ('TZ Sans', 400, 'Geist-Regular.ttf'),
    's6': ('TZ Sans', 600, 'Geist-SemiBold.ttf'),
    'm4': ('TZ Mono', 400, 'GeistMono-Regular.ttf'),
    'm7': ('TZ Mono', 700, 'GeistMono-Bold.ttf'),
    'i4': ('TZ Serif', 400, 'InstrumentSerif-Italic.ttf'),
}
CLASS_FAMILY = {'d': 'TZ Display', 's': 'TZ Sans', 'm': 'TZ Mono', 'i': 'TZ Serif'}
FALLBACK = {'d': "'Segoe UI Black', 'Arial Black', sans-serif",
            's': "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
            'm': "Consolas, Menlo, 'DejaVu Sans Mono', monospace",
            'i': "Georgia, 'Times New Roman', serif"}

BASE_CSS = (
    ''.join(f".{k}{{font-family:'{CLASS_FAMILY[k]}',{FALLBACK[k]}}}" for k in 'dsmi') +
    '@keyframes run{to{stroke-dashoffset:-1000}}'
    '@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}'
    '@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}'
    '.pulse{animation:pulse 1.6s ease-in-out infinite}'
)

COMMON_DEFS = f'''<linearGradient id="viv" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3d58ff"/><stop offset=".55" stop-color="{BLUE}"/><stop offset="1" stop-color="#1a2bc2"/></linearGradient>
<linearGradient id="drk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#121937"/><stop offset="1" stop-color="#0a0e20"/></linearGradient>
<radialGradient id="shW"><stop offset="0" stop-color="#ffffff" stop-opacity=".28"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>
<radialGradient id="shB"><stop offset="0" stop-color="{BLUE}" stop-opacity=".45"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
<pattern id="dotW" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="#ffffff" opacity=".13"/></pattern>
<pattern id="dotB" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="{B200}" opacity=".12"/></pattern>
<linearGradient id="sheenG" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .06 0"/></filter>'''


# ── Fonts: measuring + per-file subsetting ────────────────────────────────────
_tt = {}


def tt(k):
    if k not in _tt:
        _tt[k] = TTFont(os.path.join(FONT_DIR, FONTS[k][2]))
    return _tt[k]


def measure(text, k, size, ls=0.0):
    f = tt(k)
    cmap, hm, upm = f.getBestCmap(), f['hmtx'], f['head'].unitsPerEm
    return sum(hm[cmap.get(ord(ch), cmap[32])][0] for ch in text) * size / upm + ls * len(text)


def fit(text, k, size, ls, maxw, where):
    w = measure(text, k, size, ls)
    if w > maxw:
        print(f'  ! overflow in {where}: "{text}" {w:.0f}px > {maxw:.0f}px')
    return w


def cap_height(k, size):
    return tt(k)['OS/2'].sCapHeight * size / tt(k)['head'].unitsPerEm


def font_faces(body):
    used = set()
    for cls in re.findall(r'class="([^"]*)"', body):
        used.update(c for c in cls.split() if c in CLASS_FAMILY)
    chars = set(' ')
    for t in re.findall(r'>([^<>]+)<', body):
        chars.update(html.unescape(t))
    css = ''
    for k, (fam, wt, file) in FONTS.items():
        if not any(CLASS_FAMILY[c] == fam for c in used):
            continue
        opts = Options()
        opts.flavor = 'woff2'
        opts.layout_features = ['kern', 'liga', 'calt']
        opts.name_IDs = []
        opts.hinting = False
        opts.drop_tables += ['meta']
        f = TTFont(os.path.join(FONT_DIR, file))
        sub = Subsetter(opts)
        sub.populate(text=''.join(chars))
        sub.subset(f)
        f.flavor = 'woff2'
        buf = io.BytesIO()
        f.save(buf)
        css += (f"@font-face{{font-family:'{fam}';font-weight:{wt};"
                f"src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format('woff2')}}")
    return css


def esc(s):
    return html.escape(s, quote=False)


def doc(w, h, body, css='', defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">\n'
            f'<style>{font_faces(body)}{BASE_CSS}{css}</style>\n<defs>{COMMON_DEFS}{defs}</defs>\n{body}\n</svg>\n')


def write(name, content):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f'  {name:<22} {len(content) / 1024:6.1f} KB')


# ── Shared building blocks ────────────────────────────────────────────────────
def frame(W, H, kind, inner, delay=0.0, rx=36):
    """A whole section panel. kind: 'viv' (cobalt) or 'drk' (blue-tinted dark). Returns (defs, body)."""
    viv = kind == 'viv'
    glow = (f'<ellipse cx="{W * .2:.0f}" cy="-80" rx="{W * .7:.0f}" ry="380" fill="url(#shW)"/>' if viv
            else f'<ellipse cx="{W * .9:.0f}" cy="-60" rx="640" ry="360" fill="url(#shB)"/>')
    r = f'x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="{rx}"'
    defs = f'<clipPath id="pc"><rect width="{W}" height="{H}" rx="{rx}"/></clipPath>'
    body = (f'<g clip-path="url(#pc)"><rect width="{W}" height="{H}" fill="url(#{kind})"/>{glow}'
            f'<rect width="{W}" height="{H}" fill="url(#{"dotW" if viv else "dotB"})"/>{inner}'
            f'<rect width="{W}" height="{H}" filter="url(#grain)"/></g>'
            f'<rect {r} stroke="{"#6a82ff" if viv else EDGE}" stroke-width="3"/>'
            f'<rect {r} pathLength="1000" stroke="{WHITE if viv else B300}" stroke-opacity="{.8 if viv else 1}" stroke-width="4" '
            f'stroke-linecap="round" stroke-dasharray="70 930" style="animation:run 14s linear -{delay:.1f}s infinite"/>')
    return defs, body


def kicker(x, y, num, label, viv=False, anchor='start'):
    t = f'{num} — {label}'
    w = measure(t, 'm7', 22, 4) + 26
    sx = x if anchor == 'start' else x - w / 2
    return (f'<rect x="{sx:.1f}" y="{y - 17}" width="15" height="15" rx="3" fill="{INK if viv else BLUE}"/>'
            f'<text x="{sx + 27:.1f}" y="{y}" class="m" font-size="22" font-weight="700" letter-spacing="4" fill="{ICE if viv else B200}">{esc(t)}</text>')


def headline(x, y, a, b, size=60, col_b=B200, anchor='start', maxw=1072):
    """Bricolage statement + Instrument Serif italic tail — the website's type pairing."""
    ls = -size * .02
    wa = measure(a, 'd8', size, ls)
    wb = measure(b, 'i4', size * 1.15)
    if wa + wb > maxw:
        print(f'  ! overflow in headline: "{a}{b}" {wa + wb:.0f}px > {maxw}px')
    sx = x if anchor == 'start' else x - (wa + wb) / 2
    return (f'<text x="{sx:.1f}" y="{y}" class="d" font-size="{size}" font-weight="800" letter-spacing="{ls:.1f}" fill="{WHITE}">{esc(a)}'
            f'<tspan class="i" font-size="{size * 1.15:.1f}" font-weight="400" letter-spacing="0" fill="{col_b}">{esc(b)}</tspan></text>')


def band(y, h, items, size, W, name, speed, sep_col=BLUE):
    """Full-width ink band with a big scrolling marquee (the website's signature band)."""
    toks, x = [], 0.0
    while x < W + 500:
        for t in items:
            toks.append((x, t, 'd'))
            x += measure(t, 'd8', size, -.5) + 34
            toks.append((x, '</>', 'm'))
            x += measure('</>', 'm7', size * .75) + 34
    cw = x
    base = y + h / 2 + cap_height('d8', size) / 2
    txt = ''
    for off in (0, cw):
        for px, t, k in toks:
            if k == 'd':
                txt += f'<text x="{px + off:.1f}" y="{base:.1f}" class="d" font-size="{size}" font-weight="800" letter-spacing="-.5" fill="{WHITE}">{esc(t)}</text>'
            else:
                txt += f'<text x="{px + off:.1f}" y="{base:.1f}" class="m" font-size="{size * .75:.1f}" font-weight="700" fill="{sep_col}">&lt;/&gt;</text>'
    css = f'.{name}{{animation:{name} {cw / speed:.1f}s linear infinite}}@keyframes {name}{{to{{transform:translateX({-cw:.1f}px)}}}}'
    return f'<rect y="{y}" width="{W}" height="{h}" fill="{INK}"/><g class="{name}">{txt}</g>', css


def chips(labels, cx, y, size, maxw, prefix, h=62, pad=30, gap=14, step=2.6):
    """Centered ink pills (wrapping if needed); one at a time flips to white — a calm, readable highlight."""
    ws = [measure(l, 's6', size) + 2 * pad for l in labels]
    rows, cur, cw = [], [], 0.0
    for l, w in zip(labels, ws):
        if cur and cw + gap + w > maxw:
            rows.append(cur)
            cur, cw = [], 0.0
        cw += (gap if cur else 0) + w
        cur.append((l, w))
    rows.append(cur)
    n, T = len(labels), len(labels) * step
    p = 100 / n * .92
    out, k = '', 0
    css = (f'@keyframes {prefix}r{{0%,{p:.2f}%{{fill:#ffffff}}{p + .01:.2f}%,100%{{fill:{INK}}}}}'
           f'@keyframes {prefix}t{{0%,{p:.2f}%{{fill:{BLUE}}}{p + .01:.2f}%,100%{{fill:#ffffff}}}}')
    for r, row in enumerate(rows):
        tw = sum(w for _, w in row) + gap * (len(row) - 1)
        x = cx - tw / 2
        yy = y + r * (h + gap)
        for l, w in row:
            out += (f'<g class="{prefix}{k}"><rect x="{x:.1f}" y="{yy}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{INK}"/>'
                    f'<text x="{x + w / 2:.1f}" y="{yy + h / 2 + cap_height("s6", size) / 2:.1f}" text-anchor="middle" class="s" '
                    f'font-size="{size}" font-weight="600" fill="{WHITE}">{esc(l)}</text></g>')
            css += (f'.{prefix}{k} rect{{animation:{prefix}r {T:.1f}s {k * step:.1f}s infinite}}'
                    f'.{prefix}{k} text{{animation:{prefix}t {T:.1f}s {k * step:.1f}s infinite}}')
            x += w + gap
            k += 1
    return out, css, len(rows) * (h + gap) - gap


def sheen(W, H, name='sh', dur=8):
    css = f'.{name}{{animation:{name} {dur}s ease-in-out infinite}}@keyframes {name}{{0%{{transform:translateX(0)}}55%,100%{{transform:translateX({W + 900}px)}}}}'
    return (f'<g transform="rotate(18 {W / 2} {H / 2})"><rect class="{name}" x="-600" y="{-H}" width="300" height="{H * 3}" fill="url(#sheenG)"/></g>', css)


ICONS = {  # drawn in a 44×44 box
    'flame': f'<path d="M22 7c4 6 10 9.5 10 17.5a10 10 0 0 1-20 0c0-5 3-7.5 5-10.5 1 3 2 4.5 4 4.5-1-4 0-8.5 1-11.5z" stroke="{AMB}" stroke-width="2" stroke-linejoin="round"><animate attributeName="opacity" values="1;.55;1;.8;1" dur="1.2s" repeatCount="indefinite"/></path>',
    'play': f'<rect x="9" y="12" width="26" height="20" rx="5" stroke="{B200}" stroke-width="2"/><path d="M19 17.5v9l7.5-4.5z" fill="{B200}"/>',
    'layers': f'<path d="M22 9l13 7-13 7-13-7z" stroke="{B200}" stroke-width="2" stroke-linejoin="round"/><path d="M9 22l13 7 13-7M9 28l13 7 13-7" stroke="{B300}" stroke-width="2" stroke-linejoin="round"/>',
    'crown': f'<path d="M9 31l2-16 7 6 4-10 4 10 7-6 2 16z" stroke="{EM}" stroke-width="2" stroke-linejoin="round"/><circle cx="22" cy="25" r="2" fill="{EM}"/>',
}


def icon_tile(x, y, icon, col, s=2.0):
    return (f'<g transform="translate({x} {y}) scale({s})"><rect width="44" height="44" rx="12" fill="{col}" fill-opacity=".14" '
            f'stroke="{col}" stroke-opacity=".5"/>{ICONS[icon]}</g>')


# ── 1. HERO ───────────────────────────────────────────────────────────────────
def hero():
    W, H = 1200, 780
    css = ''

    name, NLS = 'FARZEEN ALI', -.03
    NS = min(196.0, 1080 / (measure(name, 'd8', 1) + NLS * len(name)))
    ls = NS * NLS
    NB = 410

    # rotating website badge, top-right
    BCX, BCY, BR = 1096, 118, 66
    ring = f'M{BCX - 50},{BCY} a50,50 0 1,1 100,0 a50,50 0 1,1 -100,0'

    mc_w = measure('Mr. Consistent', 'i4', 70)
    MY = NB + 92
    ch, chcss, chh = chips(['Founder & CEO', 'Solutions Architect', 'DevSecOps & Cloud', 'AI Automation'],
                           600, MY + 40, 25, 1100, 'hc', h=64, pad=28)
    css += chcss
    bnd, bcss = band(H - 110, 110, ['BUILD', 'SECURE', 'AUTOMATE', 'TEACH', f'{STREAK} DAYS NON-STOP'], 44, W, 'hb', 70)
    css += bcss
    sh, shcss = sheen(W, H)
    css += shcss

    kick = 'FOUNDER & CEO · THE TECHZEEN'
    inner = f'''{sh}
<text x="64" y="104" class="d" font-size="42" font-weight="800" letter-spacing="-1"><tspan fill="{INK}">&lt;/&gt;</tspan><tspan fill="{WHITE}">TechZeen</tspan></text>
<path id="ring" d="{ring}"/>
<circle cx="{BCX}" cy="{BCY}" r="{BR}" fill="{INK}"/>
<g><animateTransform attributeName="transform" type="rotate" from="0 {BCX} {BCY}" to="360 {BCX} {BCY}" dur="18s" repeatCount="indefinite"/>
<text class="m" font-size="12.5" font-weight="700" fill="{WHITE}"><textPath href="#ring" textLength="312" lengthAdjust="spacing">THE TECHZEEN • {STREAK} DAYS NON-STOP • </textPath></text></g>
<text x="{BCX}" y="{BCY + 9}" text-anchor="middle" class="m" font-size="26" font-weight="700" fill="{B200}">&lt;/&gt;</text>
<text x="600" y="232" text-anchor="middle" class="m" font-size="24" font-weight="700" letter-spacing="6" fill="{ICE}">{esc(kick)}</text>
<text x="{600 + 8}" y="{NB + 10}" text-anchor="middle" class="d" font-size="{NS:.1f}" font-weight="800" letter-spacing="{ls:.1f}" fill="{INK}" opacity=".85">{name}</text>
<text x="600" y="{NB}" text-anchor="middle" class="d" font-size="{NS:.1f}" font-weight="800" letter-spacing="{ls:.1f}" fill="{WHITE}">{name}</text>
<path d="M{600 - mc_w / 2 - 150:.0f} {MY - 22}h110M{600 + mc_w / 2 + 40:.0f} {MY - 22}h110" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>
<text x="600" y="{MY}" text-anchor="middle" class="i" font-size="70" fill="{WHITE}">Mr. Consistent</text>
{ch}
{bnd}'''
    fdefs, body = frame(W, H, 'viv', inner)
    return doc(W, H, body, css, fdefs)


# ── 2. CONNECT BUTTONS ────────────────────────────────────────────────────────
BUTTONS = [
    ('youtube', 'YouTube', '@TheTechzeen', '#ff2d55',
     '<rect x="9" y="13" width="26" height="18" rx="6" fill="#ff2d55"/><path d="M19.5 17.5v9l7.5-4.5z" fill="#fff"/>'),
    ('website', 'Website', 'thetechzeen.com', B200,
     f'<circle cx="22" cy="22" r="11" stroke="{B200}" stroke-width="2"/><ellipse cx="22" cy="22" rx="5" ry="11" stroke="{B200}" stroke-width="2"/><path d="M11 22h22" stroke="{B200}" stroke-width="2"/>'),
    ('linkedin', 'LinkedIn', 'Farzeen Ali', '#3b8cff',
     '<rect x="10" y="10" width="24" height="24" rx="6" fill="#3b8cff"/><path d="M16 20v8M16 16.2v.1M20.5 28v-8M20.5 23.5c0-2 1.5-3.5 3.5-3.5s3 1.4 3 3.5V28" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>'),
    ('email', 'Email', EMAIL, AMB,
     f'<rect x="9" y="13" width="26" height="18" rx="4" stroke="{AMB}" stroke-width="2"/><path d="M10 15l12 9 12-9" stroke="{AMB}" stroke-width="2" stroke-linejoin="round"/>'),
]


def button(i, key, title, sub, col, icon):
    W, H = 600, 150
    fit(title, 'd8', 46, -1, 360, 'button title')
    fit(sub, 'm4', 24, 0, 380, 'button sub')
    sh, css = sheen(W, H, 'bs', 6 + i * .7)
    inner = (f'{sh}<g transform="translate(30 31) scale(2)"><rect width="44" height="44" rx="12" fill="{col}" fill-opacity=".14" stroke="{col}" stroke-opacity=".5"/>{icon}</g>'
             f'<text x="146" y="74" class="d" font-size="46" font-weight="800" letter-spacing="-1" fill="{WHITE}">{title}</text>'
             f'<text x="148" y="112" class="m" font-size="24" fill="{MUT}">{esc(sub)}</text>'
             f'<path d="M530 56l22 19-22 19" stroke="{col}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;6 0;0 0" dur="1.6s" repeatCount="indefinite"/></path>')
    fdefs, body = frame(W, H, 'drk', inner, i * 3, rx=28)
    return doc(W, H, body, css, fdefs)


# ── 3. ABOUT ──────────────────────────────────────────────────────────────────
def about():
    W, H = 1200, 660
    QS = 68
    ls = -QS * .02
    sw = measure('4–5 specialists', 'd8', QS, ls)
    facts = ['Founder & CEO, The Techzeen', 'Faculty @ Denning', '20+ courses taught live']
    fx, fy = 64, 566
    fchips = ''
    for t in facts:
        w = measure(t, 's6', 24) + 64
        fchips += (f'<rect x="{fx:.1f}" y="{fy}" width="{w:.1f}" height="58" rx="29" fill="{SURF2}" stroke="{EDGE}" stroke-width="2"/>'
                   f'<circle cx="{fx + 28:.1f}" cy="{fy + 29}" r="6" fill="{BLUE}"/>'
                   f'<text x="{fx + 46:.1f}" y="{fy + 37.5}" class="s" font-size="24" font-weight="600" fill="{WHITE}">{esc(t)}</text>')
        fx += w + 14
    if fx > W - 50:
        print('  ! overflow in about facts')
    bio = ['Solutions Architect, DevSecOps Engineer & Tech Educator —',
           'building security-first systems, from one HTML tag to the cloud.']
    for b_ in bio:
        fit(b_, 's4', 30, 0, 1072, 'about bio')
    inner = f'''{kicker(64, 96, '01', 'ABOUT')}
<text x="1150" y="420" text-anchor="end" class="i" font-size="520" fill="{B300}" opacity=".13">“</text>
<text x="64" y="206" class="d" font-size="{QS}" font-weight="800" letter-spacing="{ls:.1f}" fill="{WHITE}">Most startups hire</text>
<rect x="54" y="{290 - QS * .8:.0f}" width="{sw + 26:.0f}" height="{QS * 1.04:.0f}" rx="16" fill="{BLUE}"/>
<text x="67" y="290" class="d" font-size="{QS}" font-weight="800" letter-spacing="{ls:.1f}" fill="{WHITE}">4–5 specialists</text>
<text x="64" y="374" class="d" font-size="{QS}" font-weight="800" letter-spacing="{ls:.1f}" fill="{WHITE}">for what I do <tspan class="i" font-size="{QS * 1.18:.0f}" font-weight="400" letter-spacing="0" fill="{B200}">in one.</tspan></text>
<text x="64" y="462" class="s" font-size="30" fill="{MUT}">{esc(bio[0])}</text>
<text x="64" y="504" class="s" font-size="30" fill="{MUT}">{esc(bio[1])}</text>
{fchips}'''
    fdefs, body = frame(W, H, 'drk', inner, 2)
    return doc(W, H, body, '', fdefs)


# ── 4. NUMBERS ────────────────────────────────────────────────────────────────
STATS = [
    ('flame', STREAK, 'Days non-stop', 'ZERO SKIPS · DAILY CONTENT', AMB),
    ('play', '20+', 'Production courses', 'TAUGHT LIVE', B200),
    ('layers', '4–5', 'Specialists in one', 'STACK · SECURITY · CLOUD · AI', B300),
    ('crown', '#1', 'Tech channel in PK', 'THE TECHZEEN · YOUTUBE', EM),
]


def numbers():
    W, H = 1200, 720
    cw, chh, gx, gy, X0, Y0 = 528, 254, 16, 16, 64, 140
    css = ''
    cells = ''
    for i, (icon, num, label, sub, col) in enumerate(STATS):
        x = X0 + (i % 2) * (cw + gx)
        y = Y0 + (i // 2) * (chh + gy)
        fit(num, 'd8', 120, -3, cw - 160, 'numbers value')
        fit(sub, 'm4', 19, 2, cw - 72, 'numbers sub')
        cells += (f'<rect x="{x}" y="{y}" width="{cw}" height="{chh}" rx="28" fill="{INK}" fill-opacity=".9" stroke="#3d55ff" stroke-width="2"/>'
                  f'{icon_tile(x + cw - 124, y + 32, icon, col)}'
                  f'<text x="{x + 36}" y="{y + 136}" class="d" font-size="120" font-weight="800" letter-spacing="-3" fill="{WHITE}">{esc(num)}</text>'
                  f'<text x="{x + 38}" y="{y + 180}" class="s" font-size="32" font-weight="600" fill="{WHITE}">{esc(label)}</text>'
                  f'<text x="{x + 38}" y="{y + 212}" class="m" font-size="19" letter-spacing="2" fill="{col}">{esc(sub)}</text>'
                  )
    inner = f'''{kicker(64, 96, '02', 'BY THE NUMBERS', viv=True)}
<text x="{W - 64}" y="96" text-anchor="end" class="m" font-size="20" letter-spacing="3" fill="{ICE}">NO SUBSCRIBER COUNTS · ONLY WORK</text>
{cells}'''
    fdefs, body = frame(W, H, 'viv', inner, 4)
    return doc(W, H, body, css, fdefs)


# ── 5. THE STREAK ─────────────────────────────────────────────────────────────
def streak():
    """1,000 days drawn as 1,000 lit squares — no blanks — with a wave of light sweeping through."""
    W, H = 1200, 820
    COLS, ROWS, CELL, GAP = 50, 20, 19, 3
    step = CELL + GAP
    gw, gh = COLS * step - GAP, ROWS * step - GAP
    X0, Y0 = (W - gw) / 2, 232
    random.seed(21)
    shades = ['#1b2a9e', '#2239e0', BLUE, B300, B200]
    css = ('.wv{animation:wv 6s ease-in-out infinite}@keyframes wv{0%,30%,100%{opacity:.5}12%{opacity:1}}'
           f'.scan{{animation:scan 6s ease-in-out infinite}}@keyframes scan{{0%{{transform:translateX(0);opacity:0}}5%{{opacity:1}}50%{{transform:translateX({gw + 60:.0f}px);opacity:1}}55%,100%{{transform:translateX({gw + 60:.0f}px);opacity:0}}}}'
           '.ring{animation:ring 1.8s ease-out infinite;transform-box:fill-box;transform-origin:center}@keyframes ring{from{transform:scale(1);opacity:.9}to{transform:scale(2.6);opacity:0}}')
    defs = (f'<linearGradient id="beamV" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="gridc"><rect x="{X0}" y="{Y0}" width="{gw}" height="{gh}"/></clipPath>')
    cols = ''
    for c in range(COLS):
        cells = ''.join(f'<rect x="{X0 + c * step:.1f}" y="{Y0 + r * step:.1f}" width="{CELL}" height="{CELL}" rx="4" '
                        f'fill="{random.choices(shades, weights=[2, 4, 5, 3, 1])[0]}"/>' for r in range(ROWS))
        cols += f'<g class="wv" style="animation-delay:{c * .06:.2f}s">{cells}</g>'
    lx, ly = X0 + (COLS - 1) * step + CELL / 2, Y0 + (ROWS - 1) * step + CELL / 2
    inner = f'''{kicker(X0, 96, '03', 'THE STREAK')}
{headline(X0, 176, f'{STREAK} days. ', 'Every one shipped.', 62)}
{cols}
<g clip-path="url(#gridc)"><rect class="scan" x="{X0 - 60}" y="{Y0}" width="60" height="{gh}" fill="url(#beamV)"/></g>
<rect x="{lx - CELL / 2:.1f}" y="{ly - CELL / 2:.1f}" width="{CELL}" height="{CELL}" rx="4" fill="#fff"/>
<circle class="ring" cx="{lx:.1f}" cy="{ly:.1f}" r="9" stroke="#fff" stroke-width="2.5"/>
<text x="{X0}" y="{Y0 + gh + 44:.0f}" class="m" font-size="22" letter-spacing="3" fill="{DIM}">DAY 001</text>
<text x="{X0 + gw:.0f}" y="{Y0 + gh + 44:.0f}" text-anchor="end" class="m" font-size="22" font-weight="700" letter-spacing="3" fill="{WHITE}">TODAY ▲</text>
<line x1="{X0}" y1="{H - 98}" x2="{X0 + gw:.0f}" y2="{H - 98}" stroke="{EDGE}" stroke-width="2"/>
<text x="{X0}" y="{H - 52}" class="m" font-size="22" letter-spacing="3" fill="{MUT}">1 SQUARE = 1 DAY · 0 SKIPS · 0 RERUNS</text>
<text x="{X0 + gw:.0f}" y="{H - 52}" text-anchor="end" class="m" font-size="22" font-weight="700" letter-spacing="3" fill="{B200}">STILL GOING →</text>'''
    fdefs, body = frame(W, H, 'drk', inner, 6)
    return doc(W, H, body, css, fdefs + defs)


# ── 6. ARSENAL ────────────────────────────────────────────────────────────────
def lemniscate(cx, cy, a, ys):
    pts = []
    for k in range(121):
        t = 2 * math.pi * k / 120
        d = 1 + math.sin(t) ** 2
        pts.append(f'{cx + a * math.cos(t) / d:.1f},{cy + ys * a * math.sin(t) * math.cos(t) / d:.1f}')
    return 'M' + ' L'.join(pts) + 'Z'


def vis_neural(cx, cy):
    random.seed(11)
    L = [[(-46, -32), (-46, 0), (-46, 32)], [(-16, -44), (-16, -15), (-16, 15), (-16, 44)], [(16, -24), (16, 24)], [(46, 0)]]
    L = [[(cx + a, cy + b) for a, b in l] for l in L]
    out = ''
    for la, lb in zip(L, L[1:]):
        for p in la:
            for q in lb:
                out += f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="{EDGE}" stroke-width="1.5"/>'
    for k in range(6):
        path = 'M' + ' L'.join(f'{p[0]},{p[1]}' for p in [random.choice(l) for l in L])
        out += (f'<circle r="3.5" fill="{[B200, WHITE, B300][k % 3]}" filter="url(#glow)" opacity="0"><animateMotion path="{path}" dur="2.4s" begin="-{k * .4:.1f}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.85;1" dur="2.4s" begin="-{k * .4:.1f}s" repeatCount="indefinite"/></circle>')
    for l in L:
        for px, py in l:
            out += f'<circle cx="{px}" cy="{py}" r="6.5" fill="{SURF2}" stroke="{B300}" stroke-width="2"/>'
    return out


def vis_inf(cx, cy):
    p = lemniscate(cx, cy, 54, 1.55)
    return (f'<path d="{p}" stroke="{EDGE}" stroke-width="12" stroke-linejoin="round"/><path d="{p}" stroke="{BLUE}" stroke-width="3"/>'
            f'<path d="{p}" pathLength="1000" stroke="{B200}" stroke-width="5" stroke-linecap="round" stroke-dasharray="120 880" filter="url(#glow)" style="animation:run 3.4s linear infinite"/>'
            f'<circle r="5.5" fill="#fff" filter="url(#glow)"><animateMotion path="{p}" dur="3.4s" repeatCount="indefinite"/></circle>')


def vis_radar(cx, cy):
    out = ''.join(f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{EDGE}" stroke-width="2"/>' for r in (18, 36, 52))
    out += f'<path d="M{cx - 56} {cy}H{cx + 56}M{cx} {cy - 56}V{cy + 56}" stroke="{EDGE}" stroke-width="1.5"/>'
    a0 = math.radians(-50)
    out += (f'<g><path d="M{cx} {cy}L{cx + 52 * math.cos(a0):.1f} {cy + 52 * math.sin(a0):.1f}A52 52 0 0 1 {cx + 52} {cy}Z" fill="{EM}" opacity=".25"/>'
            f'<path d="M{cx} {cy}H{cx + 52}" stroke="{EM}" stroke-width="2.5" filter="url(#glow)"/>'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="4s" repeatCount="indefinite"/></g>')
    for ang, rr in [(35, 32), (150, 44), (255, 24), (310, 46)]:
        bx, by = cx + rr * math.cos(math.radians(ang)), cy + rr * math.sin(math.radians(ang))
        out += (f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="4.5" fill="{B200}" filter="url(#glow)" opacity="0">'
                f'<animate attributeName="opacity" values="1;0" dur="4s" begin="{ang / 90:.2f}s" repeatCount="indefinite"/></circle>')
    return out


def vis_code(cx, cy):
    x0, y0 = cx - 56, cy - 42
    out = (f'<rect x="{x0}" y="{y0}" width="112" height="84" rx="10" fill="{SURF2}" stroke="{EDGE}" stroke-width="2"/>'
           f'<path d="M{x0} {y0 + 18}h112" stroke="{EDGE}" stroke-width="2"/>'
           + ''.join(f'<circle cx="{x0 + 12 + k * 10}" cy="{y0 + 9}" r="3" fill="{c}"/>' for k, c in enumerate(['#ff5f57', '#febc2e', '#28c840'])))
    for k, (wd, c) in enumerate(zip([60, 84, 46, 72], [B200, BLUE, EM, B300])):
        ind = 12 if k in (1, 2) else 0
        out += (f'<rect x="{x0 + 12 + ind}" y="{y0 + 28 + k * 13}" width="{wd - ind}" height="7" rx="3.5" fill="{c}">'
                f'<animate attributeName="width" values="{wd - ind};0;{wd - ind};{wd - ind}" keyTimes="0;.15;.45;1" dur="4s" begin="{k * .3:.1f}s" repeatCount="indefinite"/></rect>')
    return out


def vis_chain(cx, cy):
    s, out = 15, ''
    xs = [cx - 40, cx, cx + 40]
    for a, b in zip(xs, xs[1:]):
        out += (f'<line x1="{a + s * .87 + 3:.1f}" y1="{cy}" x2="{b - s * .87 - 3:.1f}" y2="{cy}" stroke="{B300}" stroke-width="2.5" stroke-dasharray="4 4">'
                f'<animate attributeName="stroke-dashoffset" values="16;0" dur=".8s" repeatCount="indefinite"/></line>')
    for k, x in enumerate(xs):
        top = f'{x},{cy - s} {x + s * .87:.1f},{cy - s / 2} {x},{cy} {x - s * .87:.1f},{cy - s / 2}'
        left = f'{x - s * .87:.1f},{cy - s / 2} {x},{cy} {x},{cy + s} {x - s * .87:.1f},{cy + s / 2}'
        right = f'{x},{cy} {x + s * .87:.1f},{cy - s / 2} {x + s * .87:.1f},{cy + s / 2} {x},{cy + s}'
        out += (f'<polygon points="{left}" fill="#0a1248" stroke="{B300}"/><polygon points="{right}" fill="#2239e0" stroke="{B300}"/>'
                f'<polygon points="{top}" fill="#3a55ff" stroke="{B300}"><animate attributeName="fill" values="#3a55ff;#ffffff;#3a55ff;#3a55ff" '
                f'keyTimes="0;.1;.3;1" dur="2.4s" begin="{k * .8:.1f}s" repeatCount="indefinite"/></polygon>')
    return out


DOMAINS = [
    ('AI Agentic Automation', 'LangChain & LangGraph agents, RAG, FastAPI & n8n.', 'LANGCHAIN · LANGGRAPH · RAG · N8N', vis_neural),
    ('DevSecOps & Cloud', 'Zero-Trust AWS, Azure & GCP — security in every pipeline.', 'DEVOPS · K8S · TERRAFORM · VAULT', vis_inf),
    ('Offensive Security', 'Pentesting, vulnerability management & SOC hardening.', 'NMAP · BURP · METASPLOIT · WAZUH', vis_radar),
    ('Full-Stack & Mobile', 'High-throughput web & native apps at production scale.', 'NEXT.JS · NESTJS · REACT NATIVE', vis_code),
    ('Blockchain Engineering', 'Solidity smart contracts & decentralized systems.', 'SOLIDITY · WEB3 · EVM', vis_chain),
]


def arsenal():
    RH, Y0 = 176, 226
    W, H = 1200, Y0 + RH * len(DOMAINS) + 40
    rows = ''
    for i, (title, desc, tags, vis) in enumerate(DOMAINS):
        y = Y0 + i * RH
        fit(title, 'd8', 46, -1, 880, 'arsenal title')
        fit(desc, 's4', 27, 0, 900, 'arsenal desc')
        fit(tags, 'm4', 19, 2, 900, 'arsenal tags')
        rows += (f'<line x1="64" y1="{y}" x2="{W - 64}" y2="{y}" stroke="{EDGE}" stroke-width="2"/>'
                 f'<rect x="64" y="{y + 22}" width="132" height="132" rx="24" fill="{SURF2}" stroke="{EDGE}" stroke-width="2"/>'
                 f'{vis(130, y + 88)}'
                 f'<text x="232" y="{y + 70}" class="d" font-size="46" font-weight="800" letter-spacing="-1" fill="{WHITE}">{esc(title)}</text>'
                 f'<text x="{W - 64}" y="{y + 66}" text-anchor="end" class="m" font-size="22" font-weight="700" fill="{B200}">0{i + 1}</text>'
                 f'<text x="234" y="{y + 112}" class="s" font-size="27" fill="{MUT}">{esc(desc)}</text>'
                 f'<text x="234" y="{y + 148}" class="m" font-size="19" letter-spacing="2" fill="{B200}">{esc(tags)}</text>')
    inner = f'''{kicker(64, 96, '04', 'ARSENAL')}
{headline(64, 176, 'Five domains. ', 'One engineer.', 62)}
{rows}'''
    fdefs, body = frame(W, H, 'drk', inner, 8)
    return doc(W, H, body, '', fdefs)


# ── 7. TECH STACK MARQUEE ─────────────────────────────────────────────────────
STACK = [
    ('FRONTEND', B200, ['HTML', 'CSS', 'JavaScript', 'TypeScript', 'React', 'Next.js', 'Nuxt.js', 'Vue', 'Angular', 'Tailwind CSS', 'React Native', 'Expo']),
    ('BACKEND · DATA', B300, ['Node.js', 'Express', 'NestJS', 'FastAPI', 'Microservices', 'GraphQL', 'REST', 'Prisma', 'Java', 'C++', 'PostgreSQL', 'MongoDB', 'MySQL', 'Redis', 'Supabase', 'Appwrite', 'Firebase']),
    ('DEVSECOPS · CLOUD', BLUE, ['DevSecOps', 'DevOps', 'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins', 'GitHub Actions', 'GitLab CI/CD', 'SonarQube', 'Vault', 'GitLeaks', 'Kyverno', 'DefectDojo', 'Trivy']),
    ('OFFENSIVE SECURITY', EM, ['Kali Linux', 'Parrot OS', 'Wireshark', 'Nmap', 'Metasploit', 'Burp Suite', 'Nessus', 'Nikto', 'Hydra', 'Hashcat', 'Ghidra', 'Splunk', 'Wazuh', 'QRadar', 'Zero Trust']),
    ('AI · WEB3', AMB, ['Agentic AI', 'AI Engineering', 'AI Automation', 'LangChain', 'LangGraph', 'LLMs', 'RAG', 'n8n', 'ELK Stack', 'Grafana', 'Prometheus', 'Solidity', 'Web3']),
]


def stack():
    RB, Y0 = 118, 226
    W, H = 1200, Y0 + RB * len(STACK) + 36
    css, rows = '', ''
    for i, (label, col, items) in enumerate(STACK):
        y = Y0 + i * RB
        reps, x = [], 0.0
        while x < W + 400:
            for it in items:
                w = measure(it, 'm4', 25) + 76
                reps.append((x, it, w))
                x += w + 14
        cw = x
        pills = ''
        for off in (0, cw):
            for px, it, w in reps:
                pills += (f'<rect x="{px + off:.1f}" y="{y + 26}" width="{w:.1f}" height="64" rx="32" fill="{SURF2}" stroke="{col}" stroke-opacity=".45" stroke-width="2"/>'
                          f'<circle cx="{px + off + 30:.1f}" cy="{y + 58}" r="6" fill="{col}"/>'
                          f'<text x="{px + off + 50:.1f}" y="{y + 67}" class="m" font-size="25" fill="{WHITE}">{esc(it)}</text>')
        frm, to = (0, -cw) if i % 2 == 0 else (-cw, 0)
        css += f'.row{i}{{animation:row{i} {cw / 42:.1f}s linear infinite}}@keyframes row{i}{{from{{transform:translateX({frm:.1f}px)}}to{{transform:translateX({to:.1f}px)}}}}'
        rows += (f'<text x="64" y="{y + 10}" class="m" font-size="20" font-weight="700" letter-spacing="4" fill="{col if col != BLUE else B300}">{esc(label)}</text>'
                 f'<g mask="url(#fade)"><g class="row{i}">{pills}</g></g>')
    defs = ('<linearGradient id="fadeG" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset=".05" stop-color="#fff"/>'
            '<stop offset=".95" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
            f'<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#fadeG)"/></mask>')
    inner = f'''{kicker(64, 96, '05', 'TECH STACK')}
{headline(64, 176, 'The toolkit ', 'that ships.', 62)}
{rows}'''
    fdefs, body = frame(W, H, 'drk', inner, 10)
    return doc(W, H, body, css, fdefs + defs)


# ── 8. TERMINAL ───────────────────────────────────────────────────────────────
def terminal():
    W, FS = 1200, 26
    X0, Y0, LH = 56, 148, 52
    CW = measure('0', 'm4', FS)
    prompt = [('farzeen', B200, 700), ('@tz', MUT, 400), (':~', B300, 700), ('$ ', WHITE, 400)]
    plen = sum(len(t) for t, _, _ in prompt)
    ok = [('● ', EM, 700)]
    lines = [
        ('cmd', 'whoami'),
        ('out', [('Farzeen Ali', WHITE, 700), (' · Founder & CEO, ', MUT, 400), ('The Techzeen', B200, 700)]),
        ('cmd', 'techzeen --streak'),
        ('out', [(f'{STREAK} days', AMB, 700), ('  ·  ', MUT, 400), ('0 skips', EM, 700), ('  ·  ', MUT, 400), ('20+ courses', B200, 700)]),
        ('cmd', 'sudo deploy --mode=prod'),
        ('bar', [('deploying ', MUT, 400), ('[' + '█' * 24 + ']', BLUE, 400), (' 100%', EM, 700)]),
        ('out', ok + [('devsecops  ', WHITE, 400)] + ok + [('cloud  ', WHITE, 400)] + ok + [('ai-agents  ', WHITE, 400)] + ok + [('web3', WHITE, 400)]),
        ('out', [('▲ all systems online — shipping to prod', B200, 700)]),
        ('idle', ''),
    ]
    H = Y0 + (len(lines) - 1) * LH + 56
    for kind, content in lines:
        txt = content if kind == 'cmd' else ''.join(t for t, _, _ in content) if kind in ('out', 'bar') else ''
        if (plen if kind == 'cmd' else 0) * CW + measure(txt, 'm4', FS) > W - 2 * X0:
            print(f'  ! overflow in terminal line: "{txt}"')

    t, ev = .8, []
    for kind, content in lines:
        if kind == 'cmd':
            s, e = t + .45, t + .45 + len(content) * .075
            ev.append((t, s, e))
            t = e + .55
        elif kind in ('out', 'bar'):
            dur = 1.6 if kind == 'bar' else .3
            ev.append((t, t, t + dur))
            t += dur + (.25 if kind == 'bar' else .5)
        else:
            ev.append((t, t, t))
    T = t + 5
    D = t + 1.5  # start offset: first frame shows the finished session
    pct = lambda s: f'{s / T * 100:.3f}%'

    css = (f'.all{{animation:all {T:.2f}s linear infinite}}'
           f'@keyframes all{{0%,{pct(T - 1.3)}{{opacity:1}}{pct(T - .5)},100%{{opacity:0}}}}'
           '.blk{animation:blink 1s infinite}')
    body_lines, covers = '', ''
    for i, ((kind, content), (p, s, e)) in enumerate(zip(lines, ev)):
        y = Y0 + i * LH
        segs = prompt + ([(content, WHITE, 400)] if kind == 'cmd' else []) if kind in ('cmd', 'idle') else content
        body_lines += f'<text x="{X0}" y="{y}" class="m" font-size="{FS}" xml:space="preserve">' + ''.join(
            f'<tspan fill="{c}" font-weight="{w}">{esc(tx)}</tspan>' for tx, c, w in segs) + '</text>'
        cx = X0 + plen * CW
        top, hh = y - 36, 48
        if kind in ('cmd', 'idle'):
            css += f'.p{i}{{animation:p{i} {T:.2f}s linear infinite}}@keyframes p{i}{{0%,{pct(p - .001)}{{opacity:1}}{pct(p)},100%{{opacity:0}}}}'
            covers += f'<rect class="p{i}" x="{X0 - 6}" y="{top}" width="{plen * CW + 6:.1f}" height="{hh}" fill="{TERM_BG}"/>'
        if kind == 'cmd':
            n = len(content)
            css += (f'.c{i}{{animation:c{i} {T:.2f}s infinite}}@keyframes c{i}{{0%{{transform:translateX(0)}}'
                    f'{pct(s)}{{transform:translateX(0);animation-timing-function:steps({n},end)}}'
                    f'{pct(e)}{{transform:translateX({n * CW:.1f}px);animation-timing-function:steps(1,end)}}'
                    f'{pct(e + .01)},100%{{transform:translateX(1300px)}}}}'
                    f'.k{i}{{animation:k{i} {T:.2f}s infinite}}@keyframes k{i}{{0%,{pct(p - .001)}{{opacity:0}}{pct(p)},{pct(e)}{{opacity:1}}{pct(e + .01)},100%{{opacity:0}}}}')
            covers += (f'<g class="c{i}"><rect x="{cx:.1f}" y="{top}" width="{W}" height="{hh}" fill="{TERM_BG}"/>'
                       f'<rect class="k{i}" x="{cx + 1:.1f}" y="{y - 26}" width="{CW:.1f}" height="33" fill="{BLUE}"/></g>')
        elif kind in ('out', 'bar'):
            steps = 26 if kind == 'bar' else 6
            css += (f'.c{i}{{animation:c{i} {T:.2f}s infinite}}@keyframes c{i}{{0%{{transform:translateX(0)}}'
                    f'{pct(s)}{{transform:translateX(0);animation-timing-function:steps({steps},end)}}'
                    f'{pct(e)},100%{{transform:translateX({W}px)}}}}')
            covers += f'<rect class="c{i}" x="{X0 - 6}" y="{top}" width="{W}" height="{hh}" fill="{TERM_BG}"/>'
        else:
            css += f'.k{i}{{animation:k{i} {T:.2f}s infinite}}@keyframes k{i}{{0%,{pct(p - .001)}{{opacity:0}}{pct(p)},100%{{opacity:1}}}}'
            covers += f'<g class="k{i}"><rect class="blk" x="{cx + 1:.1f}" y="{y - 26}" width="{CW:.1f}" height="33" fill="{BLUE}"/></g>'
    css = css.replace(f'{T:.2f}s infinite}}', f'{T:.2f}s -{D:.2f}s infinite}}').replace(f'{T:.2f}s linear infinite}}', f'{T:.2f}s linear -{D:.2f}s infinite}}')

    inner = f'''<rect width="{W}" height="{H}" fill="{TERM_BG}"/>
<rect width="{W}" height="80" fill="#10152e"/><path d="M0 80H{W}" stroke="{EDGE}" stroke-width="2"/>
<circle cx="44" cy="40" r="10" fill="#ff5f57"/><circle cx="76" cy="40" r="10" fill="#febc2e"/><circle cx="108" cy="40" r="10" fill="#28c840"/>
<text x="600" y="48" text-anchor="middle" class="m" font-size="22" fill="{MUT}">farzeen@techzeen — zsh</text>
<circle cx="{W - 120}" cy="40" r="6" fill="{EM}" class="pulse"/><text x="{W - 104}" y="48" class="m" font-size="20" font-weight="700" letter-spacing="3" fill="{MUT}">LIVE</text>
<g class="all">{body_lines}{covers}</g>'''
    fdefs, body = frame(W, H, 'drk', inner, 3, rx=30)
    return doc(W, H, body, css, fdefs)


# ── 9. LIVE GRID HEADER (the snake image follows it in the README) ────────────
def grid_header():
    W, H = 1200, 220
    inner = f'''{kicker(64, 96, '06', 'LIVE GRID')}
{headline(64, 174, 'Every commit, ', 'devoured.', 62)}
<circle cx="{W - 170}" cy="88" r="7" fill="{EM}" class="pulse"/>
<text x="{W - 64}" y="96" text-anchor="end" class="m" font-size="22" font-weight="700" letter-spacing="3" fill="{WHITE}">LIVE</text>'''
    fdefs, body = frame(W, H, 'drk', inner, 5)
    return doc(W, H, body, '', fdefs)


# ── 10. LET'S BUILD (services + sign-off) ─────────────────────────────────────
def build():
    W, H = 1200, 800
    css = ''
    l1, l2 = "Let's build something", 'that actually ships.'
    s1 = min(84.0, 1072 / measure(l1, 'd8', 1, -.02))
    fit(l2, 'i4', 92, 0, 1072, 'build line 2')
    sub = 'Founders, enterprise leads & fast-moving startups — let’s deploy together.'
    fit(sub, 's4', 27, 0, 1072, 'build sub')
    ch, chcss, chh = chips(['Architect', 'Harden', 'Automate', 'Audit', 'Train'], 600, 406, 28, 1100, 'bc', h=66, pad=34)
    css += chcss
    cta = f'→  {EMAIL}'
    cw = measure(cta, 'm7', 28) + 72
    bnd, bcss = band(H - 110, 110, [f'{STREAK} DAYS. ZERO DAYS OFF.', 'FARZEEN ALI — MR. CONSISTENT', 'THE TECHZEEN'], 42, W, 'fb', 70)
    css += bcss
    sh, shcss = sheen(W, H, 'bsh', 9)
    css += shcss
    inner = f'''{sh}
{kicker(600, 96, '07', "LET'S BUILD", viv=True, anchor='middle')}
<text x="600" y="208" text-anchor="middle" class="d" font-size="{s1:.1f}" font-weight="800" letter-spacing="{-s1 * .02:.1f}" fill="{WHITE}">{esc(l1)}</text>
<text x="600" y="294" text-anchor="middle" class="i" font-size="92" fill="{WHITE}">{esc(l2)}</text>
<text x="600" y="358" text-anchor="middle" class="s" font-size="27" fill="{ICE}">{esc(sub)}</text>
{ch}
<rect x="{600 - cw / 2:.1f}" y="510" width="{cw:.1f}" height="76" rx="38" fill="{WHITE}"/>
<text x="600" y="{548 + cap_height('m7', 28) / 2:.1f}" text-anchor="middle" class="m" font-size="28" font-weight="700" fill="{BLUE}">{esc(cta)}</text>
<circle cx="{600 - measure('AVAILABLE FOR COLLABORATIONS', 'm7', 20, 3) / 2 - 22:.1f}" cy="633" r="7" fill="{EM}" class="pulse"/>
<text x="600" y="640" text-anchor="middle" class="m" font-size="20" font-weight="700" letter-spacing="3" fill="{WHITE}">AVAILABLE FOR COLLABORATIONS</text>
{bnd}'''
    fdefs, body = frame(W, H, 'viv', inner, 7)
    return doc(W, H, body, css, fdefs)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    print('Building assets ->', os.path.normpath(OUT))
    write('hero.svg', hero())
    for i, b in enumerate(BUTTONS):
        write(f'btn-{b[0]}.svg', button(i, *b))
    write('about.svg', about())
    write('terminal.svg', terminal())
    write('numbers.svg', numbers())
    write('streak.svg', streak())
    write('arsenal.svg', arsenal())
    write('stack.svg', stack())
    write('grid-header.svg', grid_header())
    write('build.svg', build())
