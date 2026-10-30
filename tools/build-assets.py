#!/usr/bin/env python3
"""Generates every animated SVG used by README.md.

Edit the content below, then run:  python tools/build-assets.py   (needs: pip install fonttools brotli)

All assets share one brand system — colors, motion and three embedded typefaces (subset per file,
so they render identically on every OS):
  TZ Display = Unbounded · TZ Sans = Space Grotesk · TZ Mono = JetBrains Mono   (fonts: tools/fonts, OFL)
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

# ── Brand tokens ──────────────────────────────────────────────────────────────
BODY = '#0a0614'
LINE, V, M, C, G, A = '#2b1a4a', '#8b3dff', '#ff3df2', '#22e4ff', '#5cffb0', '#ffb547'
TXT, MUT, DIM = '#f5efff', '#cfc4ea', '#a493cc'


def tc(col):
    """Text-safe tint: deep violet is too dark for small text on the dark cards."""
    return '#bf9bff' if col == V else col

FONTS = {  # key: (family, weight, file)
    'd8': ('TZ Display', 800, 'Unbounded-ExtraBold.ttf'),
    'd5': ('TZ Display', 500, 'Unbounded-Medium.ttf'),
    's4': ('TZ Sans', 400, 'SpaceGrotesk-Regular.ttf'),
    's6': ('TZ Sans', 600, 'SpaceGrotesk-SemiBold.ttf'),
    'm4': ('TZ Mono', 400, 'JetBrainsMono-Regular.ttf'),
    'm7': ('TZ Mono', 700, 'JetBrainsMono-Bold.ttf'),
}
CLASS_FAMILY = {'d': 'TZ Display', 's': 'TZ Sans', 'm': 'TZ Mono'}
FALLBACK = {'d': "'Segoe UI Black', 'Arial Black', sans-serif",
            's': "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
            'm': "Consolas, Menlo, 'DejaVu Sans Mono', monospace"}

BASE_CSS = (
    ''.join(f".{k}{{font-family:'{CLASS_FAMILY[k]}',{FALLBACK[k]}}}" for k in 'dsm') +
    '@keyframes run{to{stroke-dashoffset:-1000}}'
    '@keyframes pulse{0%,100%{opacity:1}50%{opacity:.2}}'
    '@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}'
    '.pulse{animation:pulse 1.6s ease-in-out infinite}'
)

COMMON_DEFS = f'''<linearGradient id="brand" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C}"/><stop offset=".5" stop-color="{V}"/><stop offset="1" stop-color="{M}"/></linearGradient>
<linearGradient id="hot" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{C}"/><stop offset=".45" stop-color="#b98cff"/><stop offset="1" stop-color="{M}"/></linearGradient>
<linearGradient id="card" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#140a29"/><stop offset="1" stop-color="#080411"/></linearGradient>
<linearGradient id="ink" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#cdb2ff"/></linearGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .07 0"/></filter>'''


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


# ── Shared pieces ─────────────────────────────────────────────────────────────
def card(x, y, w, h, rx=22, delay=0.0, dur=8, fill='url(#card)'):
    """Glass card with a comet of light orbiting its border."""
    r = f'x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{rx}"'
    return (f'<rect {r} fill="{fill}" stroke="{LINE}"/>'
            f'<rect {r} pathLength="1000" stroke="url(#brand)" stroke-width="2" stroke-linecap="round" '
            f'stroke-dasharray="70 930" style="animation:run {dur}s linear -{delay:.2f}s infinite"/>')


def hexmark(cx, cy, r, label='FA'):
    pts = ' '.join(f'{cx + r * math.cos(math.radians(-90 + 60 * k)):.1f},{cy + r * math.sin(math.radians(-90 + 60 * k)):.1f}'
                   for k in range(6))
    size = r * .6
    return (f'<circle cx="{cx}" cy="{cy}" r="{r * 1.38:.1f}" stroke="url(#brand)" stroke-width="1.2" stroke-dasharray="3 7" opacity=".7">'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="14s" repeatCount="indefinite"/></circle>'
            f'<polygon points="{pts}" fill="#0f0820" stroke="url(#brand)" stroke-width="2"/>'
            f'<text x="{cx}" y="{cy + cap_height("d8", size) / 2:.1f}" text-anchor="middle" class="d" font-size="{size:.1f}" font-weight="800" fill="url(#ink)">{label}</text>')


ICONS = {  # drawn in a 44×44 box
    'flame': f'<path d="M22 7c4 6 10 9.5 10 17.5a10 10 0 0 1-20 0c0-5 3-7.5 5-10.5 1 3 2 4.5 4 4.5-1-4 0-8.5 1-11.5z" stroke="{A}" stroke-width="2" stroke-linejoin="round"><animate attributeName="opacity" values="1;.55;1;.8;1" dur="1.2s" repeatCount="indefinite"/></path>',
    'play': f'<rect x="9" y="12" width="26" height="20" rx="5" stroke="{C}" stroke-width="2"/><path d="M19 17.5v9l7.5-4.5z" fill="{C}"/>',
    'layers': f'<path d="M22 9l13 7-13 7-13-7z" stroke="{V}" stroke-width="2" stroke-linejoin="round"/><path d="M9 22l13 7 13-7M9 28l13 7 13-7" stroke="{M}" stroke-width="2" stroke-linejoin="round"/>',
    'crown': f'<path d="M9 31l2-16 7 6 4-10 4 10 7-6 2 16z" stroke="{G}" stroke-width="2" stroke-linejoin="round"/><circle cx="22" cy="25" r="2" fill="{G}"/>',
    'cap': f'<path d="M5 18l17-8 17 8-17 8z" stroke="{V}" stroke-width="2" stroke-linejoin="round"/><path d="M12 22v7c3 3 7 4 10 4s7-1 10-4v-7M37 19v9" stroke="{V}" stroke-width="2" stroke-linecap="round"/>',
    'blueprint': f'<rect x="9" y="9" width="26" height="26" rx="4" stroke="{C}" stroke-width="2"/><path d="M9 18h26M18 18v17" stroke="{C}" stroke-width="2"/><rect x="22" y="22" width="9" height="9" rx="2" fill="{C}"><animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></rect>',
    'shield': f'<path d="M22 7l13 5v9c0 8-6 13-13 16-7-3-13-8-13-16v-9z" stroke="{V}" stroke-width="2" stroke-linejoin="round"/><rect x="17" y="20" width="10" height="8" rx="2" fill="{V}"/><path d="M19 20v-3a3 3 0 0 1 6 0v3" stroke="{V}" stroke-width="2"/>',
    'bolt': f'<path d="M24 6L12 25h9l-2 13 13-20h-9z" stroke="{M}" stroke-width="2" stroke-linejoin="round"><animate attributeName="fill" values="{M};none;none" dur="1.8s" repeatCount="indefinite"/></path>',
    'target': f'<circle cx="22" cy="22" r="12" stroke="{G}" stroke-width="2"/><circle cx="22" cy="22" r="5" stroke="{G}" stroke-width="2"/><path d="M22 5v8M22 31v8M5 22h8M31 22h8" stroke="{G}" stroke-width="2"/><circle cx="22" cy="22" r="1.8" fill="{G}" class="pulse"/>',
}


def icon_tile(x, y, icon, col):
    return (f'<g transform="translate({x} {y})"><rect width="44" height="44" rx="12" fill="{col}" fill-opacity=".1" '
            f'stroke="{col}" stroke-opacity=".4"/>{ICONS[icon]}</g>')


# ── 1. HERO ───────────────────────────────────────────────────────────────────
def hero():
    W, H, HZ = 1200, 600, 420
    random.seed(7)
    roles = ['Solutions Architect', 'DevSecOps Engineer', 'AI Automation Engineer',
             'Offensive Security Specialist', 'Cloud Architect · AWS · Azure · GCP',
             f'Tech Educator · {STREAK} Days Live']
    LH, TY = 46, 360
    n = len(roles)
    seg = 100 / n
    kf = []
    for i in range(n):
        kf.append(f'{i * seg:.3f}%{{transform:translateY({-i * LH}px)}}')
        kf.append(f'{(i + .8) * seg:.3f}%{{transform:translateY({-i * LH}px)}}')
    kf.append(f'100%{{transform:translateY({-n * LH}px)}}')
    for r in roles:
        fit(r, 's4', 27, 1, 560, 'hero ticker')

    name, NLS = 'FARZEEN ALI', 4
    NS = min(96.0, 1010 / (measure(name, 'd8', 1) + NLS * len(name) / 96))
    NB = 290
    ch = cap_height('d8', NS)
    name_attrs = f'x="600" y="{NB}" text-anchor="middle" font-size="{NS:.1f}" font-weight="800" letter-spacing="{NLS}"'

    css = (
        '.tw{animation:tw 4s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.1}50%{opacity:.9}}'
        '.fl{animation:fl 4s cubic-bezier(.55,0,1,.45) infinite}'
        f'@keyframes fl{{0%{{transform:translateY(0);opacity:0}}20%{{opacity:1}}100%{{transform:translateY({H - HZ}px);opacity:1}}}}'
        '.a1{animation:d1 14s ease-in-out infinite alternate}@keyframes d1{to{transform:translate(160px,50px)}}'
        '.a2{animation:d2 17s ease-in-out infinite alternate}@keyframes d2{to{transform:translate(-180px,30px)}}'
        '.a3{animation:d3 11s ease-in-out infinite alternate}@keyframes d3{to{transform:translate(60px,60px)}}'
        '.g1{animation:g1 6s steps(1) infinite}.g2{animation:g2 6s steps(1) infinite}'
        '@keyframes g1{0%,88%{transform:translate(0);opacity:0}89%{transform:translate(-8px,2px);opacity:.9}'
        '91%{transform:translate(7px,-1px);opacity:.9}93%{transform:translate(-3px,0);opacity:.9}95%,100%{transform:translate(0);opacity:0}}'
        '@keyframes g2{0%,88%{transform:translate(0);opacity:0}89%{transform:translate(8px,-2px);opacity:.9}'
        '91%{transform:translate(-6px,2px);opacity:.9}93%{transform:translate(4px,0);opacity:.9}95%,100%{transform:translate(0);opacity:0}}'
        '.tick{animation:tick 18s infinite}@keyframes tick{' + ''.join(kf) + '}'
        '.scan{animation:scan 7s linear infinite}@keyframes scan{from{transform:translateY(-20px)}to{transform:translateY(620px)}}'
        '.bob{animation:bob 4s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-6px)}}'
        '.halo{animation:halo 4s ease-in-out infinite}@keyframes halo{50%{opacity:.35}}'
        '.e1,.e2,.e3{animation:ec 5s ease-in-out infinite}.e2{animation-delay:-.4s}.e3{animation-delay:-.8s}'
        '@keyframes ec{50%{transform:translateY(-7px)}}'
    )
    defs = f'''<clipPath id="frame"><rect width="{W}" height="{H}" rx="28"/></clipPath>
<radialGradient id="au1"><stop offset="0" stop-color="{V}" stop-opacity=".55"/><stop offset="1" stop-color="{V}" stop-opacity="0"/></radialGradient>
<radialGradient id="au2"><stop offset="0" stop-color="{M}" stop-opacity=".38"/><stop offset="1" stop-color="{M}" stop-opacity="0"/></radialGradient>
<radialGradient id="au3"><stop offset="0" stop-color="{C}" stop-opacity=".28"/><stop offset="1" stop-color="{C}" stop-opacity="0"/></radialGradient>
<radialGradient id="hz"><stop offset="0" stop-color="{M}" stop-opacity=".8"/><stop offset=".4" stop-color="{V}" stop-opacity=".35"/><stop offset="1" stop-color="{V}" stop-opacity="0"/></radialGradient>
<linearGradient id="floorFade" x1="0" y1="{HZ}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#000"/><stop offset=".35" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff"/></linearGradient>
<mask id="floorMask"><rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#floorFade)"/></mask>
<linearGradient id="shine" x1="0" y1="0" x2="700" y2="0" gradientUnits="userSpaceOnUse" spreadMethod="repeat">
<stop offset="0" stop-color="#ffffff"/><stop offset=".3" stop-color="#e4d1ff"/><stop offset=".5" stop-color="#ff9cf6"/><stop offset=".7" stop-color="#e4d1ff"/><stop offset="1" stop-color="#ffffff"/>
<animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="700 0" dur="5s" repeatCount="indefinite"/></linearGradient>
<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{C}" stop-opacity="0"/><stop offset=".5" stop-color="{C}"/><stop offset="1" stop-color="{M}" stop-opacity="0"/></linearGradient>
<linearGradient id="scanG" x1="0" x2="1"><stop offset="0" stop-color="{V}" stop-opacity="0"/><stop offset=".5" stop-color="#d9c2ff" stop-opacity=".55"/><stop offset="1" stop-color="{V}" stop-opacity="0"/></linearGradient>
<filter id="soft" x="-30%" y="-80%" width="160%" height="260%"><feGaussianBlur stdDeviation="22"/></filter>
<clipPath id="tickClip"><rect x="0" y="{TY - 32}" width="{W}" height="44"/></clipPath>
<clipPath id="sliceA"><rect y="{NB - ch - 4:.0f}" width="{W}" height="{ch / 2 + 4:.0f}"/></clipPath>
<clipPath id="sliceB"><rect y="{NB - ch / 2 + 6:.0f}" width="{W}" height="{ch / 2:.0f}"/></clipPath>'''

    stars = ''.join(
        f'<circle cx="{random.uniform(20, 1180):.0f}" cy="{random.uniform(20, HZ - 20):.0f}" r="{random.choice([.7, 1, 1.2, 1.6])}" '
        f'fill="#fff" class="tw" style="animation-delay:-{random.uniform(0, 5):.1f}s;animation-duration:{random.uniform(2.5, 6):.1f}s"/>'
        for _ in range(80))
    radial = ''.join(f'<line x1="600" y1="{HZ}" x2="{x}" y2="{H}"/>' for x in range(-3000, 4201, 200))
    horiz = ''.join(f'<line x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" class="fl" style="animation-delay:-{i * .5}s"/>' for i in range(8))
    rings = ''.join(
        f'<circle cx="600" cy="245" r="{r}" stroke="{col}" stroke-width="1" stroke-dasharray="{da}" opacity=".22">'
        f'<animateTransform attributeName="transform" type="rotate" from="0 600 245" to="{sgn * 360} 600 245" dur="{d}s" repeatCount="indefinite"/></circle>'
        for r, col, da, sgn, d in [(185, V, '2 10', 1, 40), (225, C, '60 18 4 18', -1, 60), (265, M, '1 6', 1, 90)])
    echoes = ''.join(
        f'<text {name_attrs} transform="translate(0 {-k * 13})" class="d" stroke="{col}" stroke-width="1.2" opacity="{op}"><tspan class="e{k}">{name}</tspan></text>'
        for k, col, op in [(3, M, .18), (2, V, .32), (1, C, .5)])
    ticker = ''.join(
        f'<text x="600" y="{TY + k * LH}" text-anchor="middle" class="s" font-size="27" letter-spacing="1" fill="{TXT}">{esc(t)}</text>'
        for k, t in enumerate(roles + roles[:1]))

    chips_src = [('AGENTIC AI', M), ('AI ENGINEERING', C), ('DEVSECOPS', V), ('DEVOPS', C), ('CLOUD', V), ('FULL-STACK', G), ('OFFSEC', A)]
    cw = [measure(t, 'm7', 12, 2) + 50 for t, _ in chips_src]
    gap = 12
    if sum(cw) + gap * (len(cw) - 1) > 1120:
        print('  ! overflow in hero chips')
    x = 600 - (sum(cw) + gap * (len(cw) - 1)) / 2
    chips = ''
    for i, ((t, col), w) in enumerate(zip(chips_src, cw)):
        chips += (f'<g class="bob" style="animation-delay:-{i * .6:.1f}s"><rect x="{x:.1f}" y="478" width="{w:.1f}" height="36" rx="18" fill="#0c0618" fill-opacity=".85" stroke="{col}" stroke-opacity=".45"/>'
                  f'<circle cx="{x + 21:.1f}" cy="496" r="4" fill="{col}" class="pulse" style="animation-delay:-{i * .3:.1f}s"/>'
                  f'<text x="{x + 34:.1f}" y="500.5" class="m" font-size="12" font-weight="700" letter-spacing="2" fill="{TXT}">{t}</text></g>')
        x += w + gap

    corners = ''.join(f'<path d="{d}" stroke="{C}" stroke-width="1.5" opacity=".6"/>' for d in
                      ['M24 60V24H60', f'M{W - 60} 24H{W - 24}V60', f'M24 {H - 60}V{H - 24}H60', f'M{W - 60} {H - 24}H{W - 24}V{H - 60}'])
    pill = 'FOUNDER &amp; CEO · THE TECHZEEN'
    pw = measure('FOUNDER & CEO · THE TECHZEEN', 'm7', 12.5, 4) + 52
    live = f'{STREAK} DAYS LIVE'
    lw = measure(live, 'm4', 12, 3)

    body = f'''<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="#06020d"/>
<ellipse class="a1" cx="260" cy="120" rx="420" ry="230" fill="url(#au1)"/>
<ellipse class="a2" cx="980" cy="150" rx="420" ry="220" fill="url(#au2)"/>
<ellipse class="a3" cx="620" cy="30" rx="320" ry="140" fill="url(#au3)"/>
{stars}
{rings}
<ellipse cx="600" cy="{HZ}" rx="620" ry="70" fill="url(#hz)" class="halo"/>
<g mask="url(#floorMask)" stroke="{V}" stroke-width="1.2" opacity=".75">{radial}{horiz}</g>
<rect x="0" y="{HZ - 1}" width="{W}" height="2" fill="url(#beam)" opacity=".9"/>
<rect class="scan" x="0" y="0" width="{W}" height="2" fill="url(#scanG)"/>
{corners}
<g transform="translate(72 60)">{hexmark(0, 0, 16)}</g>
<text x="108" y="66" class="d" font-size="14" font-weight="500" letter-spacing="3" fill="{TXT}">THE TECHZEEN</text>
<circle cx="{W - 48 - lw - 16:.1f}" cy="60" r="4.5" fill="{G}" class="pulse"/>
<text x="{W - 48}" y="64.5" text-anchor="end" class="m" font-size="12" letter-spacing="3" fill="{MUT}">{live}</text>
<rect x="{600 - pw / 2:.1f}" y="134" width="{pw:.1f}" height="36" rx="18" fill="{V}" fill-opacity=".12" stroke="url(#brand)"/>
<circle cx="{600 - pw / 2 + 22:.1f}" cy="152" r="3.5" fill="{M}" class="pulse"/>
<text x="{600 + 8}" y="156.5" text-anchor="middle" class="m" font-size="12.5" font-weight="700" letter-spacing="4" fill="#e4d1ff">{pill}</text>
<text {name_attrs} fill="{V}" filter="url(#soft)" opacity=".9" class="d halo">{name}</text>
{echoes}
<g clip-path="url(#sliceA)"><text {name_attrs} fill="{C}" class="d g1">{name}</text></g>
<g clip-path="url(#sliceB)"><text {name_attrs} fill="{M}" class="d g2">{name}</text></g>
<text {name_attrs} fill="url(#shine)" class="d">{name}</text>
<rect x="360" y="{NB + 24}" width="480" height="2" fill="url(#beam)"/>
<circle r="3.5" fill="#fff" filter="url(#glow)"><animateMotion path="M360 {NB + 25}H840" dur="3s" repeatCount="indefinite"/></circle>
<path d="M230 {TY - 10}H320M880 {TY - 10}H970" stroke="url(#beam)" stroke-width="1.5"/>
<g clip-path="url(#tickClip)"><g class="tick">{ticker}</g></g>
{chips}
<text x="40" y="{H - 36}" class="m" font-size="11" letter-spacing="3" fill="{MUT}">// BUILD · SECURE · AUTOMATE · TEACH</text>
<text x="{W - 40}" y="{H - 36}" text-anchor="end" class="m" font-size="11" letter-spacing="3" fill="{MUT}">{STREAK} DAYS · 0 SKIPS</text>
<rect width="{W}" height="{H}" filter="url(#grain)"/>
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="28" stroke="{LINE}" stroke-width="1.5"/>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="28" pathLength="1000" stroke="url(#brand)" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="120 880" style="animation:run 9s linear infinite"/>'''
    return doc(W, H, body, css, defs)


# ── 2. SECTION HEADERS ────────────────────────────────────────────────────────
SECTIONS = [
    ('01', 'IDENTITY', "// who's behind the terminal"),
    ('02', 'BY THE NUMBERS', '// consistency, quantified'),
    ('03', 'ARSENAL', '// five domains · one engineer'),
    ('04', 'TECH STACK', '// the tools of the trade'),
    ('05', 'LIVE GRID', '// every commit, devoured'),
    ('06', "LET'S BUILD", '// your roadmap, deployed'),
]


def header(num, title, sub, idx):
    W, H = 1200, 110
    tw = fit(title, 'd8', 28, 3, 560, 'header')
    bx = max(720, round(176 + tw + 60))
    css = (f'.sw{{animation:sw 3.2s cubic-bezier(.6,0,.4,1) infinite}}@keyframes sw{{from{{transform:translateX(0)}}to{{transform:translateX({1130 - bx + 100}px)}}}}')
    defs = (f'<linearGradient id="hb" x1="0" x2="1"><stop offset="0" stop-color="{V}" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{M}" stop-opacity="0"/></linearGradient>'
            f'<pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{V}" opacity=".18"/></pattern>'
            f'<clipPath id="bc"><rect x="{bx}" y="40" width="{1130 - bx}" height="30"/></clipPath>')
    body = f'''{card(0, 0, W, H, 20, idx * 1.3, 10)}
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="url(#dots)"/>
<text x="36" y="76" class="d" font-size="50" font-weight="800" fill="none" stroke="url(#brand)" stroke-width="1.3">{num}</text>
<rect x="148" y="28" width="2" height="54" fill="url(#brand)"/>
<text x="176" y="63" class="d" font-size="28" font-weight="800" letter-spacing="3" fill="url(#ink)">{esc(title)}</text>
<text x="177" y="88" class="m" font-size="13" letter-spacing="1" fill="{MUT}">{esc(sub)}</text>
<rect x="{bx}" y="54.5" width="{1130 - bx}" height="1" fill="{LINE}"/>
<g clip-path="url(#bc)"><rect class="sw" x="{bx - 100}" y="54" width="100" height="2" fill="url(#hb)" style="animation-delay:-{idx * .5}s"/></g>
<circle cx="{bx}" cy="55" r="3" fill="{V}"/>
<g transform="translate(1152 55)"><polygon points="0,-12 10.4,-6 10.4,6 0,12 -10.4,6 -10.4,-6" stroke="url(#brand)" stroke-width="1.5" fill="#0f0820">
<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="8s" repeatCount="indefinite"/></polygon>
<circle r="3" fill="{M}" class="pulse"/></g>'''
    return doc(W, H, body, css, defs)


# ── 3. IDENTITY (bento) ───────────────────────────────────────────────────────
ROLES = [
    ('crown', G, 'Founder & CEO', "THE TECHZEEN · PK'S #1 TECH CHANNEL"),
    ('cap', V, 'Program Manager & Faculty', 'DENNING · UOL & GREENWICH CURRICULA'),
    ('play', C, '20+ Production Courses', 'TAUGHT LIVE · ZERO → PRODUCTION'),
    ('flame', A, f'{STREAK} Day Streak', 'DAILY CONTENT · ZERO SKIPS'),
]


def identity():
    W, H = 1200, 440
    css = ('.ul{animation:ul 3.5s cubic-bezier(.7,0,.3,1) infinite}@keyframes ul{0%{transform:scaleX(0)}45%,80%{transform:scaleX(1);opacity:1}100%{transform:scaleX(1);opacity:0}}'
           '.eq{animation:eq 1.1s ease-in-out infinite alternate;transform-origin:bottom;transform-box:fill-box}@keyframes eq{from{transform:scaleY(.25)}to{transform:scaleY(1)}}')
    body = card(0, 0, 740, H, 26, 0, 11)
    body += f'<text x="690" y="200" text-anchor="end" class="d" font-size="230" font-weight="800" fill="{V}" opacity=".08">“</text>'
    body += f'<text x="44" y="62" class="m" font-size="11.5" font-weight="700" letter-spacing="3.5" fill="{C}">◆ MANIFESTO</text>'
    q = [('Most startups hire', 'url(#ink)'), ('4–5 specialists', 'url(#hot)'), ('for what I do in one.', 'url(#ink)')]
    for k, (ln, fill) in enumerate(q):
        fit(ln, 'd8', 38, 0, 650, 'identity quote')
        body += f'<text x="44" y="{128 + k * 54}" class="d" font-size="38" font-weight="800" fill="{fill}">{esc(ln)}</text>'
    uw = measure(q[1][0], 'd8', 38)
    body += f'<rect class="ul" x="44" y="{128 + 54 + 14}" width="{uw:.0f}" height="4" rx="2" fill="url(#hot)" style="transform-origin:44px 0"/>'
    bio = ['Solutions Architect, DevSecOps Engineer & Tech Educator —',
           'building elite, security-first infrastructure, from a single',
           'HTML tag to distributed cloud systems.']
    for k, ln in enumerate(bio):
        fit(ln, 's4', 17, 0, 650, 'identity bio')
        body += f'<text x="44" y="{276 + k * 27}" class="s" font-size="17" fill="{MUT}">{esc(ln)}</text>'
    body += f'<text x="44" y="{H - 40}" class="m" font-size="11.5" letter-spacing="3" fill="{MUT}">— FARZEEN ALI · MR. CONSISTENT</text>'
    for k in range(7):
        body += f'<rect class="eq" x="{640 + k * 9}" y="{H - 62}" width="5" height="26" rx="2" fill="url(#brand)" style="animation-delay:-{k * .23:.2f}s"/>'

    rh, gap = (H - 3 * 16) / 4, 16
    for k, (icon, col, title, sub) in enumerate(ROLES):
        y = k * (rh + gap)
        body += card(760, y, 440, rh, 20, 2 + k * 1.6, 9)
        body += icon_tile(784, y + rh / 2 - 22, icon, col)
        fit(title, 's6', 19, 0, 330, 'identity role')
        fit(sub, 'm4', 10.5, 1.6, 330, 'identity role sub')
        body += (f'<text x="846" y="{y + rh / 2 - 2:.1f}" class="s" font-size="19" font-weight="600" fill="{TXT}">{esc(title)}</text>'
                 f'<text x="846" y="{y + rh / 2 + 20:.1f}" class="m" font-size="10.5" letter-spacing="1.6" fill="{tc(col)}">{esc(sub)}</text>'
                 f'<text x="1176" y="{y + 28:.1f}" text-anchor="end" class="m" font-size="10" fill="{DIM}">0{k + 1}</text>')
    return doc(W, H, body, css)


# ── 4. STATS ──────────────────────────────────────────────────────────────────
STATS = [
    ('flame', STREAK, 'Days Streak', 'ZERO SKIPS · DAILY CONTENT', A),
    ('play', '20+', 'Production Courses', 'TAUGHT LIVE · START → SHIP', C),
    ('layers', '4–5', 'Specialists in One', 'STACK · SECURITY · CLOUD · AI', V),
    ('crown', '#1', 'Tech Channel in PK', 'THE TECHZEEN · YOUTUBE', G),
]


def stats():
    W, H = 1200, 280
    css = '.sp{animation:sp 4s ease-in-out infinite}@keyframes sp{0%{stroke-dashoffset:100;opacity:1}55%{stroke-dashoffset:0;opacity:1}85%{opacity:1}100%{stroke-dashoffset:0;opacity:0}}'
    random.seed(3)
    body = ''
    for i, (icon, num, label, sub, col) in enumerate(STATS):
        x, y, w, h = i * 306, 10, 282, 260
        fit(num, 'd8', 50, 0, w - 48, 'stats number')
        pts = ' '.join(f'{x + 24 + k * (w - 48) / 23:.1f},{y + 236 - random.uniform(0, 1) ** 1.6 * 18 - k * .6:.1f}' for k in range(24))
        body += f'''{card(x, y, w, h, 22, i * 1.7, 9)}
{icon_tile(x + 22, y + 22, icon, col)}
<circle cx="{x + w - 70}" cy="{y + 44}" r="3.5" fill="{col}" class="pulse"/>
<text x="{x + w - 60}" y="{y + 48}" class="m" font-size="10.5" letter-spacing="2.5" fill="{MUT}">LIVE</text>
<text x="{x + 24}" y="{y + 144}" class="d" font-size="50" font-weight="800" fill="url(#ink)">{esc(num)}</text>
<text x="{x + 24}" y="{y + 178}" class="s" font-size="18" font-weight="600" fill="{TXT}">{esc(label)}</text>
<text x="{x + 24}" y="{y + 202}" class="m" font-size="10" letter-spacing="1.5" fill="{tc(col)}">{esc(sub)}</text>
<polyline points="{pts}" stroke="{col}" stroke-width="1.8" stroke-linejoin="round" pathLength="100" stroke-dasharray="100" class="sp" style="animation-delay:-{i * .7:.1f}s" opacity=".9"/>'''
    return doc(W, H, body, css)


# ── 5. ARSENAL (bento) ────────────────────────────────────────────────────────
def lemniscate(cx, cy, a, ys):
    pts = []
    for k in range(121):
        t = 2 * math.pi * k / 120
        d = 1 + math.sin(t) ** 2
        pts.append(f'{cx + a * math.cos(t) / d:.1f},{cy + ys * a * math.sin(t) * math.cos(t) / d:.1f}')
    return 'M' + ' L'.join(pts) + 'Z'


def text_block(x, y, tag, title, lines, col, maxw, size=26):
    fit(title, 's6', size, 0, maxw, 'arsenal title')
    out = (f'<text x="{x}" y="{y}" class="m" font-size="11" font-weight="700" letter-spacing="3" fill="{tc(col)}">{esc(tag)}</text>'
           f'<text x="{x}" y="{y + 38}" class="s" font-size="{size}" font-weight="600" fill="url(#ink)">{esc(title)}</text>')
    for k, ln in enumerate(lines):
        fit(ln, 's4', 15.5, 0, maxw, 'arsenal desc')
        out += f'<text x="{x}" y="{y + 70 + k * 23}" class="s" font-size="15.5" fill="{MUT}">{esc(ln)}</text>'
    return out


def tags_line(x, y, text):
    return f'<text x="{x}" y="{y}" class="m" font-size="10.5" letter-spacing="2" fill="{C}">{esc(text)}</text>'


def arsenal():
    W, H = 1200, 620
    random.seed(11)
    body = ''

    # A — AI agents: neural net with signal pulses
    body += card(0, 0, 590, 300, 24, 0, 10)
    body += text_block(34, 52, '01 · AI', 'AI Agentic Automation',
                       ['Agentic AI with LangChain &', 'LangGraph, RAG, FastAPI & n8n —', 'AI engineering & automation.'], M, 300)
    body += tags_line(34, 262, 'LANGCHAIN · LANGGRAPH · FASTAPI · RAG')
    layers = [[(370, 95), (370, 150), (370, 205)], [(440, 70), (440, 123), (440, 177), (440, 230)], [(505, 105), (505, 195)], [(552, 150)]]
    for la, lb in zip(layers, layers[1:]):
        for p in la:
            for q in lb:
                body += f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="{LINE}" stroke-width="1.2"/>'
    for k in range(7):
        path = 'M' + ' L'.join(f'{p[0]},{p[1]}' for p in [random.choice(l) for l in layers])
        col = [M, C, V][k % 3]
        body += (f'<circle r="3.2" fill="{col}" filter="url(#glow)" opacity="0"><animateMotion path="{path}" dur="2.4s" begin="-{k * .34:.2f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.85;1" dur="2.4s" begin="-{k * .34:.2f}s" repeatCount="indefinite"/></circle>')
    for l in layers:
        for (px, py) in l:
            body += (f'<circle cx="{px}" cy="{py}" r="8" fill="#0f0820" stroke="{V}" stroke-width="1.5"/>'
                     f'<circle cx="{px}" cy="{py}" r="3" fill="{M}"><animate attributeName="r" values="2;4.2;2" dur="{random.uniform(1.4, 2.6):.1f}s" repeatCount="indefinite"/></circle>')

    # B — DevSecOps: infinity CI/CD loop
    body += card(610, 0, 590, 300, 24, 3, 10)
    body += text_block(644, 52, '02 · DEVSECOPS', 'DevSecOps & Cloud',
                       ['Zero-Trust cloud on AWS, Azure', '& GCP — declarative IaC with', 'security baked into every CI/CD.'], C, 290)
    body += tags_line(644, 262, 'DEVOPS · K8S · TERRAFORM · VAULT')
    inf = lemniscate(1066, 150, 96, 1.6)
    body += (f'<path d="{inf}" stroke="{LINE}" stroke-width="14" stroke-linejoin="round"/>'
             f'<path d="{inf}" stroke="url(#brand)" stroke-width="2.5" opacity=".85"/>'
             f'<path d="{inf}" pathLength="1000" stroke="{M}" stroke-width="5" stroke-linecap="round" stroke-dasharray="110 890" filter="url(#glow)" style="animation:run 3.4s linear infinite"/>'
             f'<circle r="5" fill="#fff" filter="url(#glow)"><animateMotion path="{inf}" dur="3.4s" repeatCount="indefinite"/></circle>')
    for lx, ly, lab in [(1004, 88, 'CODE'), (1004, 222, 'BUILD'), (1128, 88, 'DEPLOY'), (1128, 222, 'MONITOR'), (1066, 108, 'SCAN')]:
        body += f'<text x="{lx}" y="{ly}" text-anchor="middle" class="m" font-size="10" font-weight="700" letter-spacing="2" fill="{MUT}">{lab}</text>'

    sw, gy = 386, 320
    xs = [0, 407, 814]

    # C — Offensive security: radar
    body += card(xs[0], gy, sw, 300, 24, 5, 10)
    cx, cy = xs[0] + sw / 2, gy + 78
    body += ''.join(f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{LINE}" stroke-width="1.2"/>' for r in (20, 40, 58))
    body += f'<path d="M{cx - 64} {cy}H{cx + 64}M{cx} {cy - 64}V{cy + 64}" stroke="{LINE}"/>'
    a0 = math.radians(-50)
    body += (f'<g><path d="M{cx} {cy}L{cx + 58 * math.cos(a0):.1f} {cy + 58 * math.sin(a0):.1f}A58 58 0 0 1 {cx + 58} {cy}Z" fill="{G}" opacity=".22"/>'
             f'<path d="M{cx} {cy}H{cx + 58}" stroke="{G}" stroke-width="2" filter="url(#glow)"/>'
             f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="4s" repeatCount="indefinite"/></g>')
    for ang, rr in [(35, 36), (150, 48), (255, 28), (310, 50)]:
        bx, by = cx + rr * math.cos(math.radians(ang)), cy + rr * math.sin(math.radians(ang))
        body += (f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="4" fill="{M}" filter="url(#glow)" opacity="0">'
                 f'<animate attributeName="opacity" values="1;0" dur="4s" begin="{ang / 90:.2f}s" repeatCount="indefinite"/></circle>')
    body += f'<path d="M{cx} {cy - 10}l8 3v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10v-6z" fill="#0f0820" stroke="{G}" stroke-width="1.6"/>'
    body += text_block(xs[0] + 30, gy + 166, '03 · OFFSEC', 'Offensive Security',
                       ['Pentesting, vuln management,', 'SIEM/SOC ops & hardening.'], G, 326, 23)
    body += tags_line(xs[0] + 30, gy + 280, 'NMAP · BURP · METASPLOIT · WAZUH')

    # D — Full-stack & mobile: browser + phone with live code
    body += card(xs[1], gy, sw, 300, 24, 6.5, 10)
    bx0, by0 = xs[1] + 92, gy + 28
    body += (f'<rect x="{bx0}" y="{by0}" width="140" height="100" rx="9" fill="#0f0820" stroke="{LINE}" stroke-width="1.5"/>'
             f'<path d="M{bx0} {by0 + 18}h140" stroke="{LINE}"/>'
             + ''.join(f'<circle cx="{bx0 + 11 + k * 9}" cy="{by0 + 9}" r="2.6" fill="{c}"/>' for k, c in enumerate([M, A, G])))
    for k, (wd, c) in enumerate(zip([72, 104, 56, 88, 44], [V, C, M, V, G])):
        ind = 12 if k in (1, 2, 3) else 0
        body += (f'<rect x="{bx0 + 12 + ind}" y="{by0 + 28 + k * 13}" width="{wd - ind}" height="6" rx="3" fill="{c}" opacity=".85">'
                 f'<animate attributeName="width" values="{wd - ind};0;{wd - ind};{wd - ind}" keyTimes="0;.15;.45;1" dur="4s" begin="{k * .3:.1f}s" repeatCount="indefinite"/></rect>')
    px0 = bx0 + 156
    body += (f'<rect x="{px0}" y="{by0 - 2}" width="50" height="104" rx="11" fill="#0f0820" stroke="{V}" stroke-width="1.5"/>'
             f'<rect x="{px0 + 18}" y="{by0 + 4}" width="14" height="4" rx="2" fill="{LINE}"/>')
    for k in range(3):
        body += (f'<rect x="{px0 + 8}" y="{by0 + 16 + k * 26}" width="34" height="20" rx="5" fill="{[C, M, V][k]}" opacity=".25">'
                 f'<animate attributeName="opacity" values=".15;.7;.15" dur="2.4s" begin="{k * .8:.1f}s" repeatCount="indefinite"/></rect>')
    body += text_block(xs[1] + 30, gy + 166, '04 · FULL-STACK', 'Full-Stack & Mobile',
                       ['High-throughput web & native', 'apps — Next.js, NestJS, RN.'], V, 326, 23)
    body += tags_line(xs[1] + 30, gy + 280, 'NEXT.JS · NESTJS · REACT NATIVE')

    # E — Blockchain: chain of isometric blocks
    body += card(xs[2], gy, sw, 300, 24, 8, 10)
    s, cyb = 20, gy + 80
    centers = [xs[2] + sw / 2 + (k - 1.5) * 70 for k in range(4)]
    for k, x in enumerate(centers[:-1]):
        body += (f'<line x1="{x + s * .87 + 6:.1f}" y1="{cyb}" x2="{centers[k + 1] - s * .87 - 6:.1f}" y2="{cyb}" stroke="{V}" stroke-width="2" stroke-dasharray="4 4">'
                 f'<animate attributeName="stroke-dashoffset" values="16;0" dur=".8s" repeatCount="indefinite"/></line>')
    for k, x in enumerate(centers):
        top = f'{x},{cyb - s} {x + s * .87:.1f},{cyb - s / 2} {x},{cyb} {x - s * .87:.1f},{cyb - s / 2}'
        left = f'{x - s * .87:.1f},{cyb - s / 2} {x},{cyb} {x},{cyb + s} {x - s * .87:.1f},{cyb + s / 2}'
        right = f'{x},{cyb} {x + s * .87:.1f},{cyb - s / 2} {x + s * .87:.1f},{cyb + s / 2} {x},{cyb + s}'
        body += (f'<polygon points="{left}" fill="#1c0e38" stroke="{V}" stroke-width="1"/>'
                 f'<polygon points="{right}" fill="#2a1550" stroke="{V}" stroke-width="1"/>'
                 f'<polygon points="{top}" fill="#3b1d70" stroke="{V}" stroke-width="1">'
                 f'<animate attributeName="fill" values="#3b1d70;{M};#3b1d70;#3b1d70" keyTimes="0;.1;.3;1" dur="3.2s" begin="{k * .8:.1f}s" repeatCount="indefinite"/></polygon>'
                 f'<text x="{x}" y="{cyb + 44}" text-anchor="middle" class="m" font-size="9" fill="{DIM}">#{k:02d}·0x{random.randrange(16 ** 3):03x}</text>')
    body += text_block(xs[2] + 30, gy + 166, '05 · WEB3', 'Blockchain Engineering',
                       ['Solidity smart contracts &', 'decentralized systems.'], A, 326, 23)
    body += tags_line(xs[2] + 30, gy + 280, 'SOLIDITY · WEB3 · EVM')
    return doc(W, H, body)


# ── 6. TERMINAL ───────────────────────────────────────────────────────────────
def terminal():
    W, H = 1200, 500
    X0, Y0, LH = 40, 98, 34
    CW = measure('0', 'm4', 16)
    prompt = [('farzeen', M, 700), ('@', MUT, 400), ('techzeen', C, 700), (':', MUT, 400), ('~', V, 700), ('$ ', TXT, 400)]
    plen = sum(len(t) for t, _, _ in prompt)
    ok = [('■ ', G, 700)]
    lines = [
        ('cmd', 'whoami'),
        ('out', [('Farzeen Ali', TXT, 700), (' — Founder & CEO @ ', MUT, 400), ('The Techzeen', M, 700)]),
        ('cmd', 'cat ./mission.txt'),
        ('out', [('Build. Secure. Automate. Teach. — every single day.', TXT, 400)]),
        ('cmd', 'techzeen --stats'),
        ('out', [('streak ', MUT, 400), (f'{STREAK} days', A, 700), ('  ·  skips ', MUT, 400), ('0', G, 700),
                 ('  ·  courses ', MUT, 400), ('20+', C, 700), ('  ·  rank ', MUT, 400), ('#1 PK', M, 700)]),
        ('cmd', 'sudo deploy --mode=god'),
        ('bar', [('deploying ', MUT, 400), ('[' + '█' * 32 + ']', V, 400), (' 100%', G, 700)]),
        ('out', ok + [('full-stack   ', TXT, 400)] + ok + [('devsecops   ', TXT, 400)] + ok + [('cloud   ', TXT, 400)]
         + ok + [('agentic-ai   ', TXT, 400)] + ok + [('devops   ', TXT, 400)] + ok + [('offsec   ', TXT, 400)] + ok + [('web3', TXT, 400)]),
        ('out', [('▲ all systems online — shipping to production', C, 700)]),
        ('idle', ''),
    ]

    t, ev = .8, []
    for kind, content in lines:
        if kind == 'cmd':
            s, e = t + .45, t + .45 + len(content) * .075
            ev.append((t, s, e))
            t = e + .55
        elif kind in ('out', 'bar'):
            dur = 1.8 if kind == 'bar' else .3
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
        segs = prompt + ([(content, TXT, 400)] if kind == 'cmd' else []) if kind in ('cmd', 'idle') else content
        body_lines += f'<text x="{X0}" y="{y}" class="m" font-size="16" xml:space="preserve">' + ''.join(
            f'<tspan fill="{c}" font-weight="{w}">{esc(tx)}</tspan>' for tx, c, w in segs) + '</text>'
        cx = X0 + plen * CW
        if kind in ('cmd', 'idle'):
            css += f'.p{i}{{animation:p{i} {T:.2f}s linear infinite}}@keyframes p{i}{{0%,{pct(p - .001)}{{opacity:1}}{pct(p)},100%{{opacity:0}}}}'
            covers += f'<rect class="p{i}" x="{X0 - 4}" y="{y - 23}" width="{plen * CW + 4:.1f}" height="32" fill="{BODY}"/>'
        if kind == 'cmd':
            n = len(content)
            css += (f'.c{i}{{animation:c{i} {T:.2f}s infinite}}@keyframes c{i}{{0%{{transform:translateX(0)}}'
                    f'{pct(s)}{{transform:translateX(0);animation-timing-function:steps({n},end)}}'
                    f'{pct(e)}{{transform:translateX({n * CW:.1f}px);animation-timing-function:steps(1,end)}}'
                    f'{pct(e + .01)},100%{{transform:translateX(1200px)}}}}'
                    f'.k{i}{{animation:k{i} {T:.2f}s infinite}}@keyframes k{i}{{0%,{pct(p - .001)}{{opacity:0}}{pct(p)},{pct(e)}{{opacity:1}}{pct(e + .01)},100%{{opacity:0}}}}')
            covers += (f'<g class="c{i}"><rect x="{cx:.1f}" y="{y - 23}" width="{W}" height="32" fill="{BODY}"/>'
                       f'<rect class="k{i}" x="{cx + 1:.1f}" y="{y - 17}" width="{CW:.1f}" height="21" fill="{V}"/></g>')
        elif kind in ('out', 'bar'):
            steps = 34 if kind == 'bar' else 6
            css += (f'.c{i}{{animation:c{i} {T:.2f}s infinite}}@keyframes c{i}{{0%{{transform:translateX(0)}}'
                    f'{pct(s)}{{transform:translateX(0);animation-timing-function:steps({steps},end)}}'
                    f'{pct(e)},100%{{transform:translateX({W - X0 + 8}px)}}}}')
            covers += f'<rect class="c{i}" x="{X0 - 4}" y="{y - 23}" width="{W}" height="32" fill="{BODY}"/>'
        else:
            css += f'.k{i}{{animation:k{i} {T:.2f}s infinite}}@keyframes k{i}{{0%,{pct(p - .001)}{{opacity:0}}{pct(p)},100%{{opacity:1}}}}'
            covers += f'<g class="k{i}"><rect class="blk" x="{cx + 1:.1f}" y="{y - 17}" width="{CW:.1f}" height="21" fill="{V}"/></g>'

    css = css.replace(f'{T:.2f}s infinite}}', f'{T:.2f}s -{D:.2f}s infinite}}').replace(f'{T:.2f}s linear infinite}}', f'{T:.2f}s linear -{D:.2f}s infinite}}')
    defs = f'<clipPath id="win"><rect width="{W}" height="{H}" rx="18"/></clipPath>'
    body = f'''<g clip-path="url(#win)">
<rect width="{W}" height="{H}" fill="{BODY}"/>
<rect width="{W}" height="48" fill="#120a22"/><path d="M0 48.5H{W}" stroke="{LINE}"/>
<circle cx="28" cy="24" r="6.5" fill="#ff5f57"/><circle cx="50" cy="24" r="6.5" fill="#febc2e"/><circle cx="72" cy="24" r="6.5" fill="#28c840"/>
<text x="600" y="29" text-anchor="middle" class="m" font-size="13" fill="{MUT}">farzeen@techzeen: ~ — zsh — 120×32</text>
<circle cx="1110" cy="24" r="4" fill="{M}" class="pulse"/><text x="1122" y="28.5" class="m" font-size="11" letter-spacing="2" fill="{MUT}">LIVE</text>
<g class="all">{body_lines}{covers}</g>
</g>
{card(0, 0, W, H, 18, 0, 12, fill='none')}'''
    return doc(W, H, body, css, defs)


# ── 7. TECH STACK MARQUEE ─────────────────────────────────────────────────────
STACK = [
    ('FRONTEND', C, ['HTML', 'CSS', 'JavaScript', 'TypeScript', 'React', 'Next.js', 'Nuxt.js', 'Vue', 'Angular', 'Tailwind CSS', 'React Native', 'Expo']),
    ('BACKEND · DATA', V, ['Node.js', 'Express', 'NestJS', 'FastAPI', 'Microservices', 'GraphQL', 'REST', 'Prisma', 'Java', 'C++', 'PostgreSQL', 'MongoDB', 'MySQL', 'Redis', 'Supabase', 'Appwrite', 'Firebase']),
    ('DEVSECOPS · CLOUD', M, ['DevSecOps', 'DevOps', 'Cloud', 'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins', 'GitHub Actions', 'GitLab CI/CD', 'SonarQube', 'Vault', 'GitLeaks', 'Kyverno', 'DefectDojo', 'Syft', 'Grype', 'Trivy']),
    ('OFFENSIVE SEC', G, ['Kali Linux', 'Parrot OS', 'Wireshark', 'Nmap', 'Metasploit', 'Burp Suite', 'Nessus', 'Nikto', 'Hydra', 'Hashcat', 'Ghidra', 'Autopsy', 'Splunk', 'Wazuh', 'QRadar', 'Zero Trust']),
    ('AI · WEB3', A, ['Agentic AI', 'AI Engineering', 'AI Automation', 'LangChain', 'LangGraph', 'LLMs', 'AI Agents', 'n8n', 'RAG', 'AI Data Eng', 'ELK Stack', 'Grafana', 'Prometheus', 'Solidity', 'Smart Contracts', 'Web3', 'DSA', 'OOP']),
]


def marquee():
    W, RH, TOP = 1200, 54, 26
    H = TOP + RH * len(STACK) + 18
    css, rows = '', ''
    for i, (label, col, items) in enumerate(STACK):
        y = TOP + i * RH
        pills, x, reps = '', 0.0, []
        while x < W + 200:
            for it in items:
                w = measure(it, 'm4', 13) + 44
                reps.append((x, it, w))
                x += w + 12
        copy_w = x
        for off in (0, copy_w):
            for px, it, w in reps:
                pills += (f'<rect x="{px + off:.1f}" y="{y}" width="{w:.1f}" height="36" rx="18" fill="#120a24" stroke="{col}" stroke-opacity=".28"/>'
                          f'<circle cx="{px + off + 18:.1f}" cy="{y + 18}" r="3.5" fill="{col}"/>'
                          f'<text x="{px + off + 30:.1f}" y="{y + 22.5}" class="m" font-size="13" fill="{TXT}">{esc(it)}</text>')
        dur = copy_w / 38
        frm, to = (0, -copy_w) if i % 2 == 0 else (-copy_w, 0)
        css += f'.row{i}{{animation:row{i} {dur:.1f}s linear infinite}}@keyframes row{i}{{from{{transform:translateX({frm:.1f}px)}}to{{transform:translateX({to:.1f}px)}}}}'
        rows += f'<g class="row{i}">{pills}</g>'
    labels = ''.join(
        f'<circle cx="34" cy="{TOP + i * RH + 18}" r="4" fill="{col}" class="pulse" style="animation-delay:-{i * .3:.1f}s"/>'
        f'<text x="48" y="{TOP + i * RH + 22}" class="m" font-size="11" font-weight="700" letter-spacing="2.5" fill="{tc(col)}">{esc(label)}</text>'
        for i, (label, col, _) in enumerate(STACK))
    defs = (f'<clipPath id="mq"><rect width="{W}" height="{H}" rx="22"/></clipPath>'
            '<linearGradient id="fadeL" x1="0" x2="1"><stop offset=".7" stop-color="#0c0619"/><stop offset="1" stop-color="#0c0619" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="#0c0619" stop-opacity="0"/><stop offset="1" stop-color="#0c0619"/></linearGradient>')
    body = f'''<g clip-path="url(#mq)"><rect width="{W}" height="{H}" fill="#0c0619"/>
{rows}
<rect width="340" height="{H}" fill="url(#fadeL)"/><rect x="{W - 160}" width="160" height="{H}" fill="url(#fadeR)"/>
{labels}</g>
{card(0, 0, W, H, 22, 2, 11, fill='none')}'''
    return doc(W, H, body, css, defs)


# ── 8. SERVICES ───────────────────────────────────────────────────────────────
SERVICES = [
    ('blueprint', C, 'ARCHITECT', ['Production web', 'architectures & native', 'cross-platform apps.']),
    ('shield', V, 'HARDEN', ['DevSecOps pipelines,', 'automated compliance', '& cloud hardening.']),
    ('bolt', M, 'AUTOMATE', ['Self-correcting AI', 'workflows, multi-agent', 'systems & RAG.']),
    ('target', G, 'AUDIT', ['Offensive pentesting,', 'vuln assessments &', 'red-team simulations.']),
    ('cap', A, 'TRAIN', ['Team upskilling across', 'full-stack, DevSecOps', '& AI engineering.']),
]


def services():
    W, H = 1200, 290
    w, gap = 228, 15
    body = ''
    for i, (icon, col, title, lines) in enumerate(SERVICES):
        x = i * (w + gap)
        body += card(x, 0, w, H, 22, i * 1.4, 9)
        body += icon_tile(x + 24, 30, icon, col)
        body += f'<text x="{x + w - 24}" y="56" text-anchor="end" class="m" font-size="11" fill="{DIM}">0{i + 1}</text>'
        fit(title, 'd8', 19, 2, w - 48, 'services title')
        body += f'<text x="{x + 24}" y="126" class="d" font-size="19" font-weight="800" letter-spacing="2" fill="url(#ink)">{title}</text>'
        body += f'<rect x="{x + 24}" y="142" width="28" height="3" rx="1.5" fill="{col}"/>'
        for k, ln in enumerate(lines):
            fit(ln, 's4', 15, 0, w - 44, 'services desc')
            body += f'<text x="{x + 24}" y="{180 + k * 23}" class="s" font-size="15" fill="{MUT}">{esc(ln)}</text>'
        body += f'<text x="{x + 24}" y="{H - 24}" class="m" font-size="10.5" font-weight="700" letter-spacing="2" fill="{tc(col)}">DEPLOY →</text>'
    return doc(W, H, body)


# ── 9. CONNECT BUTTONS ────────────────────────────────────────────────────────
BUTTONS = [
    ('youtube', 'YOUTUBE', '@TheTechzeen', '#ff2d55',
     '<rect x="9" y="13" width="26" height="18" rx="6" fill="#ff2d55"/><path d="M19.5 17.5v9l7.5-4.5z" fill="#fff"/>'),
    ('website', 'WEBSITE', 'thetechzeen.com', V,
     f'<circle cx="22" cy="22" r="11" stroke="{V}" stroke-width="2"/><ellipse cx="22" cy="22" rx="5" ry="11" stroke="{V}" stroke-width="2"/><path d="M11 22h22" stroke="{V}" stroke-width="2"/>'),
    ('linkedin', 'LINKEDIN', 'Farzeen Ali', '#2f8fff',
     '<rect x="10" y="10" width="24" height="24" rx="6" fill="#2f8fff"/><path d="M16 20v8M16 16.2v.1M20.5 28v-8M20.5 23.5c0-2 1.5-3.5 3.5-3.5s3 1.4 3 3.5V28" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>'),
    ('email', 'EMAIL', 'info@thetechzeen.com', M,
     f'<rect x="9" y="13" width="26" height="18" rx="4" stroke="{M}" stroke-width="2"/><path d="M10 15l12 9 12-9" stroke="{M}" stroke-width="2" stroke-linejoin="round"/>'),
]


def button(i, key, title, sub, col, icon):
    W, H = 290, 76
    fit(sub, 'm4', 11.5, 0, 175, 'button sub')
    css = '.sh{animation:sh 4.5s ease-in-out infinite}@keyframes sh{0%,55%{transform:translateX(-120px) skewX(-20deg)}100%{transform:translateX(420px) skewX(-20deg)}}'
    defs = (f'<clipPath id="b"><rect width="{W}" height="{H}" rx="20"/></clipPath>'
            '<linearGradient id="sg" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    body = f'''<g clip-path="url(#b)">{card(0, 0, W, H, 20, i * 2, 7)}
<g transform="translate(16 16)"><rect width="44" height="44" rx="12" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".45"/>{icon}</g>
<text x="76" y="37" class="d" font-size="14" font-weight="500" letter-spacing="2" fill="{TXT}">{title}</text>
<text x="76" y="56" class="m" font-size="11.5" fill="{MUT}">{esc(sub)}</text>
<path d="M258 30l10 8-10 8" stroke="{col}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><animateTransform attributeName="transform" type="translate" values="0 0;4 0;0 0" dur="1.6s" repeatCount="indefinite"/></path>
<rect class="sh" x="0" y="-20" width="70" height="120" fill="url(#sg)" style="animation-delay:{i * .4:.1f}s"/></g>'''
    return doc(W, H, body, css, defs)


# ── 10. FOOTER ────────────────────────────────────────────────────────────────
def footer():
    W, H = 1200, 360

    def wave(amp, length, y, ph):
        d = f'M0 {y}'
        for x in range(0, 2 * W + 1, 20):
            d += f' L{x} {y + amp * math.sin(2 * math.pi * x / length + ph):.1f}'
        return d + f' L{2 * W} {H} L0 {H}Z'

    line1 = f'{STREAK} days. Zero days off.'
    s1 = min(44.0, 1000 / measure(line1, 'd8', 1))
    css = ('.w1{animation:wv 12s linear infinite}.w2{animation:wv 18s linear infinite reverse}.w3{animation:wv 9s linear infinite}'
           '@keyframes wv{from{transform:translateX(0)}to{transform:translateX(-1200px)}}')
    defs = (f'<clipPath id="ft"><rect width="{W}" height="{H}" rx="28"/></clipPath>'
            f'<radialGradient id="fg" cx=".5" cy="1"><stop offset="0" stop-color="{V}" stop-opacity=".45"/><stop offset="1" stop-color="{V}" stop-opacity="0"/></radialGradient>')
    body = f'''<g clip-path="url(#ft)"><rect width="{W}" height="{H}" fill="#06020d"/>
<ellipse cx="600" cy="{H}" rx="700" ry="260" fill="url(#fg)"/>
<path class="w1" d="{wave(14, 600, 290, 0)}" fill="{V}" opacity=".22"/>
<path class="w2" d="{wave(18, 400, 305, 1)}" fill="{M}" opacity=".14"/>
<path class="w3" d="{wave(10, 300, 322, 2)}" fill="{C}" opacity=".12"/>
<g transform="translate(600 62)">{hexmark(0, 0, 22)}</g>
<text x="600" y="164" text-anchor="middle" class="d" font-size="{s1:.1f}" font-weight="800" fill="url(#ink)">{esc(line1)}</text>
<text x="600" y="204" text-anchor="middle" class="s" font-size="20" fill="{MUT}">One mission — make complex tech actually build things.</text>
<text x="600" y="242" text-anchor="middle" class="m" font-size="12" font-weight="700" letter-spacing="3.5" fill="{C}">— FARZEEN ALI · MR. CONSISTENT · FOUNDER &amp; CEO, THE TECHZEEN</text>
<text x="600" y="{H - 22}" text-anchor="middle" class="m" font-size="10" letter-spacing="3" fill="{MUT}">© THE TECHZEEN — ENGINEERED IN PAKISTAN</text>
<rect width="{W}" height="{H}" filter="url(#grain)"/></g>
{card(0, 0, W, H, 28, 1, 12, fill='none')}'''
    return doc(W, H, body, css, defs)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    print('Building assets ->', os.path.normpath(OUT))
    write('hero.svg', hero())
    for i, (num, title, sub) in enumerate(SECTIONS):
        write(f'header-{num}.svg', header(num, title, sub, i))
    write('identity.svg', identity())
    write('stats.svg', stats())
    write('arsenal.svg', arsenal())
    write('terminal.svg', terminal())
    write('stack.svg', marquee())
    write('services.svg', services())
    for i, b in enumerate(BUTTONS):
        write(f'btn-{b[0]}.svg', button(i, *b))
    write('footer.svg', footer())
