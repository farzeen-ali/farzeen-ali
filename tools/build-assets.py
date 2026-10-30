#!/usr/bin/env python3
"""Generates every animated SVG used by README.md.

Edit the text/content below, then run:  python tools/build-assets.py
All assets share one brand system (colors, fonts, motion) so the profile reads as one product.
"""
import html
import math
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# ── Brand tokens ──────────────────────────────────────────────────────────────
BODY = '#0a0614'
LINE, V, M, C, G, A = '#2b1a4a', '#8b3dff', '#ff3df2', '#22e4ff', '#5cffb0', '#ffb547'
TXT, MUT, DIM = '#f5efff', '#a596c4', '#6c5c8c'
SANS = "'Segoe UI', Inter, 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Cascadia Code', 'SF Mono', Consolas, Menlo, 'DejaVu Sans Mono', monospace"

BASE_CSS = (
    '.s{font-family:' + SANS + '}.m{font-family:' + MONO + '}'
    '@keyframes run{to{stroke-dashoffset:-1000}}'
    '@keyframes pulse{0%,100%{opacity:1}50%{opacity:.2}}'
    '@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}'
    '.pulse{animation:pulse 1.6s ease-in-out infinite}'
)

COMMON_DEFS = f'''<linearGradient id="brand" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C}"/><stop offset=".5" stop-color="{V}"/><stop offset="1" stop-color="{M}"/></linearGradient>
<linearGradient id="card" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#140a29"/><stop offset="1" stop-color="#080411"/></linearGradient>
<linearGradient id="ink" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#cdb2ff"/></linearGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'''


def esc(s):
    return html.escape(s, quote=False)


def doc(w, h, body, css='', defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">\n'
            f'<style>{BASE_CSS}{css}</style>\n<defs>{COMMON_DEFS}{defs}</defs>\n{body}\n</svg>\n')


def write(name, content):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f'  {name:<22} {len(content) / 1024:6.1f} KB')


def card(x, y, w, h, rx=22, delay=0.0, dur=8):
    """Glass card with a comet of light orbiting its border."""
    r = f'x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{rx}"'
    return (f'<rect {r} fill="url(#card)" stroke="{LINE}"/>'
            f'<rect {r} pathLength="1000" stroke="url(#brand)" stroke-width="2" stroke-linecap="round" '
            f'stroke-dasharray="70 930" style="animation:run {dur}s linear -{delay:.2f}s infinite"/>')


def hexmark(cx, cy, r, label='FA'):
    pts = ' '.join(f'{cx + r * math.cos(math.radians(-90 + 60 * k)):.1f},{cy + r * math.sin(math.radians(-90 + 60 * k)):.1f}'
                   for k in range(6))
    return (f'<circle cx="{cx}" cy="{cy}" r="{r * 1.38:.1f}" stroke="url(#brand)" stroke-width="1.2" stroke-dasharray="3 7" opacity=".7">'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="14s" repeatCount="indefinite"/></circle>'
            f'<polygon points="{pts}" fill="#0f0820" stroke="url(#brand)" stroke-width="2"/>'
            f'<text x="{cx}" y="{cy + r * .23:.1f}" text-anchor="middle" class="s" font-size="{r * .66:.0f}" font-weight="900" '
            f'letter-spacing="1" fill="url(#ink)">{label}</text>')


# ── 1. HERO ───────────────────────────────────────────────────────────────────
def hero():
    W, H, HZ = 1200, 560, 392
    random.seed(7)
    roles = ['Solutions Architect', 'DevSecOps Engineer', 'AI Automation Engineer',
             'Offensive Security Specialist', 'Cloud Architect · AWS · Azure · GCP',
             'Tech Educator · 1,000+ Days Live']
    LH, TY = 46, 340
    n = len(roles)
    seg = 100 / n
    kf = []
    for i in range(n):
        kf.append(f'{i * seg:.3f}%{{transform:translateY({-i * LH}px)}}')
        kf.append(f'{(i + .8) * seg:.3f}%{{transform:translateY({-i * LH}px)}}')
    kf.append(f'100%{{transform:translateY({-n * LH}px)}}')

    css = (
        '.tw{animation:tw 4s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.1}50%{opacity:.9}}'
        '.fl{animation:fl 4s cubic-bezier(.55,0,1,.45) infinite}'
        f'@keyframes fl{{0%{{transform:translateY(0);opacity:0}}20%{{opacity:1}}100%{{transform:translateY({H - HZ}px);opacity:1}}}}'
        '.a1{animation:d1 14s ease-in-out infinite alternate}@keyframes d1{to{transform:translate(160px,50px)}}'
        '.a2{animation:d2 17s ease-in-out infinite alternate}@keyframes d2{to{transform:translate(-180px,30px)}}'
        '.a3{animation:d3 11s ease-in-out infinite alternate}@keyframes d3{to{transform:translate(60px,60px)}}'
        '.g1{animation:g1 6s steps(1) infinite}.g2{animation:g2 6s steps(1) infinite}'
        '@keyframes g1{0%,88%{transform:translate(0);opacity:0}89%{transform:translate(-7px,2px);opacity:.85}'
        '91%{transform:translate(6px,-1px);opacity:.85}93%{transform:translate(-3px,0);opacity:.85}95%,100%{transform:translate(0);opacity:0}}'
        '@keyframes g2{0%,88%{transform:translate(0);opacity:0}89%{transform:translate(7px,-2px);opacity:.85}'
        '91%{transform:translate(-5px,2px);opacity:.85}93%{transform:translate(4px,0);opacity:.85}95%,100%{transform:translate(0);opacity:0}}'
        '.tick{animation:tick 18s infinite}@keyframes tick{' + ''.join(kf) + '}'
        '.scan{animation:scan 7s linear infinite}@keyframes scan{from{transform:translateY(-20px)}to{transform:translateY(580px)}}'
        '.bob{animation:bob 4s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-6px)}}'
        '.halo{animation:halo 4s ease-in-out infinite}@keyframes halo{50%{opacity:.35}}'
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
<clipPath id="sliceA"><rect y="170" width="{W}" height="42"/></clipPath>
<clipPath id="sliceB"><rect y="222" width="{W}" height="40"/></clipPath>'''

    stars = ''.join(
        f'<circle cx="{random.uniform(20, 1180):.0f}" cy="{random.uniform(20, HZ - 20):.0f}" r="{random.choice([.7, 1, 1.2, 1.6])}" '
        f'fill="#fff" class="tw" style="animation-delay:-{random.uniform(0, 5):.1f}s;animation-duration:{random.uniform(2.5, 6):.1f}s"/>'
        for _ in range(80))
    radial = ''.join(f'<line x1="600" y1="{HZ}" x2="{x}" y2="{H}"/>' for x in range(-3000, 4201, 200))
    horiz = ''.join(f'<line x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" class="fl" style="animation-delay:-{i * .5}s"/>' for i in range(8))
    rings = ''.join(
        f'<circle cx="600" cy="225" r="{r}" stroke="{col}" stroke-width="1" stroke-dasharray="{da}" opacity=".22">'
        f'<animateTransform attributeName="transform" type="rotate" from="0 600 225" to="{sgn * 360} 600 225" dur="{d}s" repeatCount="indefinite"/></circle>'
        for r, col, da, sgn, d in [(175, V, '2 10', 1, 40), (212, C, '60 18 4 18', -1, 60), (250, M, '1 6', 1, 90)])

    name = 'FARZEEN ALI'
    name_attrs = 'x="600" y="255" text-anchor="middle" font-size="104" font-weight="900" letter-spacing="10"'
    ticker = ''.join(
        f'<text x="600" y="{TY + k * LH}" text-anchor="middle" class="s" font-size="27" font-weight="300" letter-spacing="1.5" fill="{TXT}">{esc(t)}</text>'
        for k, t in enumerate(roles + roles[:1]))

    chips_src = [('FULL-STACK', C), ('DEVSECOPS', V), ('CLOUD', C), ('AI AGENTS', M), ('OFFSEC', G), ('WEB3', A)]
    cw = [len(t) * 9.4 + 46 for t, _ in chips_src]
    gap = 16
    x = 600 - (sum(cw) + gap * (len(cw) - 1)) / 2
    chips = ''
    for i, ((t, col), w) in enumerate(zip(chips_src, cw)):
        chips += (f'<g class="bob" style="animation-delay:-{i * .6:.1f}s"><rect x="{x:.1f}" y="440" width="{w:.1f}" height="36" rx="18" fill="#0c0618" fill-opacity=".85" stroke="{col}" stroke-opacity=".45"/>'
                  f'<circle cx="{x + 20:.1f}" cy="458" r="4" fill="{col}" class="pulse" style="animation-delay:-{i * .3:.1f}s"/>'
                  f'<text x="{x + 33:.1f}" y="462.5" class="m" font-size="12" font-weight="700" letter-spacing="2" fill="{TXT}">{t}</text></g>')
        x += w + gap

    corners = ''.join(f'<path d="{d}" stroke="{C}" stroke-width="1.5" opacity=".6"/>' for d in
                      ['M24 60V24H60', f'M{W - 60} 24H{W - 24}V60', f'M24 {H - 60}V{H - 24}H60', f'M{W - 60} {H - 24}H{W - 24}V{H - 60}'])

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
<g transform="translate(70 56)">{hexmark(0, 0, 15)}</g>
<text x="104" y="61" class="m" font-size="13" font-weight="700" letter-spacing="4" fill="{TXT}">THE TECHZEEN</text>
<circle cx="1000" cy="56" r="4.5" fill="{G}" class="pulse"/>
<text x="1014" y="61" class="m" font-size="12" letter-spacing="3" fill="{MUT}">SYSTEM ONLINE</text>
<g><rect x="410" y="118" width="380" height="34" rx="17" fill="{V}" fill-opacity=".12" stroke="url(#brand)"/>
<text x="600" y="140" text-anchor="middle" class="m" font-size="12.5" font-weight="700" letter-spacing="4" fill="#e4d1ff">FOUNDER &amp; CEO · THE TECHZEEN</text></g>
<g>
<text {name_attrs} fill="{V}" filter="url(#soft)" opacity=".9" class="s halo">{name}</text>
<g clip-path="url(#sliceA)"><text {name_attrs} fill="{C}" class="s g1">{name}</text></g>
<g clip-path="url(#sliceB)"><text {name_attrs} fill="{M}" class="s g2">{name}</text></g>
<text {name_attrs} fill="url(#shine)" class="s">{name}</text>
</g>
<g><rect x="380" y="282" width="440" height="2" fill="url(#beam)"/>
<circle r="3.5" fill="#fff" filter="url(#glow)"><animateMotion path="M380 283H820" dur="3s" repeatCount="indefinite"/></circle>
<path d="M240 330H330M870 330H960" stroke="url(#beam)" stroke-width="1.5"/>
<g clip-path="url(#tickClip)"><g class="tick">{ticker}</g></g></g>
<g>{chips}</g>
<text x="40" y="{H - 34}" class="m" font-size="11" letter-spacing="3" fill="{DIM}">// BUILD · SECURE · AUTOMATE · TEACH</text>
<text x="{W - 40}" y="{H - 34}" text-anchor="end" class="m" font-size="11" letter-spacing="3" fill="{DIM}">MODE: GOD ▲ 1,000+ DAYS · 0 SKIPS</text>
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
    css = ('.sw{animation:sw 3.2s cubic-bezier(.6,0,.4,1) infinite}@keyframes sw{from{transform:translateX(0)}to{transform:translateX(420px)}}')
    defs = (f'<linearGradient id="hb" x1="0" x2="1"><stop offset="0" stop-color="{V}" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{M}" stop-opacity="0"/></linearGradient>'
            f'<pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{V}" opacity=".18"/></pattern>'
            f'<clipPath id="bc"><rect x="720" y="40" width="410" height="30"/></clipPath>')
    body = f'''{card(0, 0, W, H, 20, idx * 1.3, 10)}
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="url(#dots)"/>
<g><text x="40" y="76" class="m" font-size="54" font-weight="800" fill="none" stroke="url(#brand)" stroke-width="1.4">{num}</text>
<rect x="148" y="28" width="2" height="54" fill="url(#brand)"/>
<text x="176" y="62" class="s" font-size="30" font-weight="800" letter-spacing="5" fill="url(#ink)">{esc(title)}</text>
<text x="178" y="88" class="m" font-size="13" letter-spacing="1" fill="{MUT}">{esc(sub)}</text></g>
<rect x="720" y="54.5" width="410" height="1" fill="{LINE}"/>
<g clip-path="url(#bc)"><rect class="sw" x="620" y="54" width="100" height="2" fill="url(#hb)" style="animation-delay:-{idx * .5}s"/></g>
<circle cx="720" cy="55" r="3" fill="{V}"/>
<g transform="translate(1152 55)"><polygon points="0,-12 10.4,-6 10.4,6 0,12 -10.4,6 -10.4,-6" stroke="url(#brand)" stroke-width="1.5" fill="#0f0820">
<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="8s" repeatCount="indefinite"/></polygon>
<circle r="3" fill="{M}" class="pulse"/></g>'''
    return doc(W, H, body, css, defs)


# ── 3. STATS ──────────────────────────────────────────────────────────────────
ICONS = {
    'flame': f'<path d="M22 7c4 6 10 9.5 10 17.5a10 10 0 0 1-20 0c0-5 3-7.5 5-10.5 1 3 2 4.5 4 4.5-1-4 0-8.5 1-11.5z" stroke="{A}" stroke-width="2" stroke-linejoin="round"><animate attributeName="opacity" values="1;.55;1;.8;1" dur="1.2s" repeatCount="indefinite"/></path>',
    'play': f'<rect x="9" y="12" width="26" height="20" rx="5" stroke="{C}" stroke-width="2"/><path d="M19 17.5v9l7.5-4.5z" fill="{C}"/>',
    'layers': f'<path d="M22 9l13 7-13 7-13-7z" stroke="{V}" stroke-width="2" stroke-linejoin="round"/><path d="M9 22l13 7 13-7M9 28l13 7 13-7" stroke="{M}" stroke-width="2" stroke-linejoin="round"/>',
    'crown': f'<path d="M9 31l2-16 7 6 4-10 4 10 7-6 2 16z" stroke="{G}" stroke-width="2" stroke-linejoin="round"/><circle cx="22" cy="25" r="2" fill="{G}"/>',
}
STATS = [
    ('flame', '1,000+', 'Days Streak', 'ZERO SKIPS · DAILY CONTENT', A),
    ('play', '20+', 'Production Courses', 'TAUGHT LIVE · START → SHIP', C),
    ('layers', '4–5', 'Specialists in One', 'STACK · SECURITY · CLOUD · AI', V),
    ('crown', '#1', 'Tech Channel in PK', 'THE TECHZEEN · YOUTUBE', G),
]


def stats():
    W, H = 1200, 280
    css = ('.sp{animation:sp 4s ease-in-out infinite}@keyframes sp{0%{stroke-dashoffset:100;opacity:1}55%{stroke-dashoffset:0;opacity:1}85%{opacity:1}100%{stroke-dashoffset:0;opacity:0}}')
    random.seed(3)
    body = ''
    for i, (icon, num, label, sub, col) in enumerate(STATS):
        x, y, w, h = i * 306, 10, 282, 260
        pts = ' '.join(f'{x + 24 + k * (w - 48) / 23:.1f},{y + 236 - random.uniform(0, 1) ** 1.6 * 18 - k * .6:.1f}' for k in range(24))
        body += f'''{card(x, y, w, h, 22, i * 1.7, 9)}
<g transform="translate({x + 22} {y + 22})"><rect width="44" height="44" rx="12" fill="{col}" fill-opacity=".1" stroke="{col}" stroke-opacity=".4"/>{ICONS[icon]}</g>
<circle cx="{x + w - 70}" cy="{y + 44}" r="3.5" fill="{col}" class="pulse"/>
<text x="{x + w - 60}" y="{y + 48}" class="m" font-size="10.5" letter-spacing="2.5" fill="{MUT}">LIVE</text>
<g>
<text x="{x + 24}" y="{y + 146}" class="s" font-size="60" font-weight="800" fill="url(#ink)" letter-spacing="-1">{esc(num)}</text>
<text x="{x + 24}" y="{y + 178}" class="s" font-size="17" font-weight="600" fill="{TXT}">{esc(label)}</text>
<text x="{x + 24}" y="{y + 202}" class="m" font-size="10" letter-spacing="1.5" fill="{col}">{esc(sub)}</text></g>
<polyline points="{pts}" stroke="{col}" stroke-width="1.8" stroke-linejoin="round" pathLength="100" stroke-dasharray="100" class="sp" style="animation-delay:-{i * .7:.1f}s" opacity=".9"/>'''
    return doc(W, H, body, css)


# ── 4. ARSENAL (bento) ────────────────────────────────────────────────────────
def lemniscate(cx, cy, a, ys):
    pts = []
    for k in range(121):
        t = 2 * math.pi * k / 120
        d = 1 + math.sin(t) ** 2
        pts.append(f'{cx + a * math.cos(t) / d:.1f},{cy + ys * a * math.sin(t) * math.cos(t) / d:.1f}')
    return 'M' + ' L'.join(pts) + 'Z'


def text_block(x, y, tag, title, lines, tags, col, size=24):
    out = (f'<text x="{x}" y="{y}" class="m" font-size="11" font-weight="700" letter-spacing="3" fill="{col}">{esc(tag)}</text>'
           f'<text x="{x}" y="{y + 38}" class="s" font-size="{size}" font-weight="800" fill="url(#ink)">{esc(title)}</text>')
    for k, ln in enumerate(lines):
        out += f'<text x="{x}" y="{y + 70 + k * 23}" class="s" font-size="15" fill="{MUT}">{esc(ln)}</text>'
    return out, tags


def arsenal():
    W, H = 1200, 640
    random.seed(11)
    body = ''

    # A — AI agents: neural net with signal pulses
    body += card(0, 0, 590, 300, 24, 0, 10)
    t, _ = text_block(34, 52, '01 · AI', 'AI Agentic Automation',
                      ['Production LLM orchestration,', 'RAG pipelines & n8n workflows,', 'self-healing autonomous agents.'], '', M)
    body += t + f'<text x="34" y="262" class="m" font-size="11" letter-spacing="2" fill="{C}">LLM · RAG · N8N · AGENTS</text>'
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
    t, _ = text_block(644, 52, '02 · DEVSECOPS', 'DevSecOps & Cloud',
                      ['Zero-Trust cloud on AWS, Azure', '& GCP — declarative IaC with', 'security baked into every CI/CD.'], '', C)
    body += t + f'<text x="644" y="262" class="m" font-size="11" letter-spacing="2" fill="{C}">K8S · TERRAFORM · VAULT · TRIVY</text>'
    inf = lemniscate(1062, 150, 98, 1.6)
    body += (f'<path d="{inf}" stroke="{LINE}" stroke-width="14" stroke-linejoin="round"/>'
             f'<path d="{inf}" stroke="url(#brand)" stroke-width="2.5" opacity=".85"/>'
             f'<path d="{inf}" pathLength="1000" stroke="{M}" stroke-width="5" stroke-linecap="round" stroke-dasharray="110 890" filter="url(#glow)" style="animation:run 3.4s linear infinite"/>'
             f'<circle r="5" fill="#fff" filter="url(#glow)"><animateMotion path="{inf}" dur="3.4s" repeatCount="indefinite"/></circle>')
    for lx, ly, lab in [(1000, 88, 'CODE'), (1000, 222, 'BUILD'), (1124, 88, 'DEPLOY'), (1124, 222, 'MONITOR'), (1062, 108, 'SCAN')]:
        body += f'<text x="{lx}" y="{ly}" text-anchor="middle" class="m" font-size="10" font-weight="700" letter-spacing="2" fill="{MUT}">{lab}</text>'

    # Row 2
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
    t, _ = text_block(xs[0] + 30, gy + 166, '03 · OFFSEC', 'Offensive Security',
                      ['Pentesting, vuln management,', 'SIEM/SOC ops & hardening.'], '', G, 22)
    body += t + f'<text x="{xs[0] + 30}" y="{gy + 282}" class="m" font-size="10.5" letter-spacing="2" fill="{C}">NMAP · BURP · METASPLOIT · WAZUH</text>'

    # D — Full-stack & mobile: browser + phone with live code
    body += card(xs[1], gy, sw, 300, 24, 6.5, 10)
    bx0, by0 = xs[1] + 92, gy + 28
    body += (f'<rect x="{bx0}" y="{by0}" width="140" height="100" rx="9" fill="#0f0820" stroke="{LINE}" stroke-width="1.5"/>'
             f'<path d="M{bx0} {by0 + 18}h140" stroke="{LINE}"/>'
             + ''.join(f'<circle cx="{bx0 + 11 + k * 9}" cy="{by0 + 9}" r="2.6" fill="{c}"/>' for k, c in enumerate([M, A, G])))
    for k, (wd, c) in enumerate(zip([72, 104, 56, 88, 44], [V, C, M, V, G])):
        ind = 12 if k in (1, 2, 3) else 0
        body += (f'<rect x="{bx0 + 12 + ind}" y="{by0 + 28 + k * 13}" width="0" height="6" rx="3" fill="{c}" opacity=".85">'
                 f'<animate attributeName="width" values="0;{wd - ind};{wd - ind};0" keyTimes="0;.3;.85;1" dur="4s" begin="{k * .3:.1f}s" repeatCount="indefinite"/></rect>')
    px0 = bx0 + 156
    body += (f'<rect x="{px0}" y="{by0 - 2}" width="50" height="104" rx="11" fill="#0f0820" stroke="{V}" stroke-width="1.5"/>'
             f'<rect x="{px0 + 18}" y="{by0 + 4}" width="14" height="4" rx="2" fill="{LINE}"/>')
    for k in range(3):
        body += (f'<rect x="{px0 + 8}" y="{by0 + 16 + k * 26}" width="34" height="20" rx="5" fill="{[C, M, V][k]}" opacity=".25">'
                 f'<animate attributeName="opacity" values=".15;.7;.15" dur="2.4s" begin="{k * .8:.1f}s" repeatCount="indefinite"/></rect>')
    t, _ = text_block(xs[1] + 30, gy + 166, '04 · FULL-STACK', 'Full-Stack & Mobile',
                      ['High-throughput web & native', 'apps — Next.js, NestJS, RN.'], '', V, 22)
    body += t + f'<text x="{xs[1] + 30}" y="{gy + 282}" class="m" font-size="10.5" letter-spacing="2" fill="{C}">NEXT.JS · NESTJS · REACT NATIVE</text>'

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
    t, _ = text_block(xs[2] + 30, gy + 166, '05 · WEB3', 'Blockchain Engineering',
                      ['Solidity smart contracts &', 'decentralized systems.'], '', A, 22)
    body += t + f'<text x="{xs[2] + 30}" y="{gy + 282}" class="m" font-size="10.5" letter-spacing="2" fill="{C}">SOLIDITY · WEB3 · EVM</text>'
    return doc(W, H, body)


# ── 5. TERMINAL ───────────────────────────────────────────────────────────────
def terminal():
    W, H = 1200, 500
    CW, X0, Y0, LH = 9.6, 40, 98, 34
    prompt = [('farzeen', M, 700), ('@', MUT, 400), ('techzeen', C, 700), (':', MUT, 400), ('~', V, 700), ('$ ', TXT, 400)]
    plen = sum(len(t) for t, _, _ in prompt)
    lines = [
        ('cmd', 'whoami'),
        ('out', [('Farzeen Ali', TXT, 700), (' — Founder & CEO @ ', MUT, 400), ('The Techzeen', M, 700)]),
        ('cmd', 'cat ./mission.txt'),
        ('out', [('Build. Secure. Automate. Teach. — every single day.', TXT, 400)]),
        ('cmd', 'techzeen --stats'),
        ('out', [('streak ', MUT, 400), ('1,000+ days', A, 700), ('  ·  skips ', MUT, 400), ('0', G, 700),
                 ('  ·  courses ', MUT, 400), ('20+', C, 700), ('  ·  rank ', MUT, 400), ('#1 PK', M, 700)]),
        ('cmd', 'sudo deploy --mode=god'),
        ('bar', [('deploying ', MUT, 400), ('[' + '█' * 32 + ']', V, 400), (' 100%', G, 700)]),
        ('out', [('✔ ', G, 700), ('full-stack   ', TXT, 400), ('✔ ', G, 700), ('devsecops   ', TXT, 400), ('✔ ', G, 700), ('cloud   ', TXT, 400),
                 ('✔ ', G, 700), ('ai-agents   ', TXT, 400), ('✔ ', G, 700), ('offsec   ', TXT, 400), ('✔ ', G, 700), ('web3', TXT, 400)]),
        ('out', [('▲ all systems online — shipping to production', C, 700)]),
        ('idle', ''),
    ]

    # build the timeline (seconds)
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
{card(0, 0, W, H, 18, 0, 12).replace('fill="url(#card)"', 'fill="none"')}'''
    return doc(W, H, body, css, defs)


# ── 6. TECH STACK MARQUEE ─────────────────────────────────────────────────────
STACK = [
    ('FRONTEND', C, ['HTML', 'CSS', 'JavaScript', 'TypeScript', 'React', 'Next.js', 'Nuxt.js', 'Vue', 'Angular', 'Tailwind CSS', 'React Native', 'Expo']),
    ('BACKEND · DATA', V, ['Node.js', 'Express', 'NestJS', 'Microservices', 'GraphQL', 'REST', 'Prisma', 'Java', 'C++', 'PostgreSQL', 'MongoDB', 'MySQL', 'Redis', 'Supabase', 'Appwrite', 'Firebase']),
    ('DEVSECOPS · CLOUD', M, ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins', 'GitHub Actions', 'GitLab CI/CD', 'SonarQube', 'Vault', 'GitLeaks', 'Kyverno', 'DefectDojo', 'Syft', 'Grype', 'Trivy']),
    ('OFFENSIVE SEC', G, ['Kali Linux', 'Parrot OS', 'Wireshark', 'Nmap', 'Metasploit', 'Burp Suite', 'Nessus', 'Nikto', 'Hydra', 'Hashcat', 'Ghidra', 'Autopsy', 'Splunk', 'Wazuh', 'QRadar', 'Zero Trust']),
    ('AI · WEB3', A, ['LLMs', 'AI Agents', 'n8n', 'RAG', 'AI Data Eng', 'ELK Stack', 'Grafana', 'Prometheus', 'Solidity', 'Smart Contracts', 'Web3', 'DSA', 'OOP']),
]


def marquee():
    W, RH, TOP = 1200, 54, 26
    H = TOP + RH * len(STACK) + 18
    css, rows = '', ''
    for i, (label, col, items) in enumerate(STACK):
        y = TOP + i * RH
        pills, x = '', 0.0
        reps = []
        while x < W + 200:
            for it in items:
                w = len(it) * 7.8 + 42
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
        f'<text x="48" y="{TOP + i * RH + 22}" class="m" font-size="11" font-weight="700" letter-spacing="2.5" fill="{col}">{esc(label)}</text>'
        for i, (label, col, _) in enumerate(STACK))
    defs = (f'<clipPath id="mq"><rect width="{W}" height="{H}" rx="22"/></clipPath>'
            '<linearGradient id="fadeL" x1="0" x2="1"><stop offset=".7" stop-color="#0c0619"/><stop offset="1" stop-color="#0c0619" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="#0c0619" stop-opacity="0"/><stop offset="1" stop-color="#0c0619"/></linearGradient>')
    body = f'''<g clip-path="url(#mq)"><rect width="{W}" height="{H}" fill="#0c0619"/>
{rows}
<rect width="340" height="{H}" fill="url(#fadeL)"/><rect x="{W - 160}" width="160" height="{H}" fill="url(#fadeR)"/>
{labels}</g>
{card(0, 0, W, H, 22, 2, 11).replace('fill="url(#card)"', 'fill="none"')}'''
    return doc(W, H, body, css, defs)


# ── 7. CONNECT BUTTONS ────────────────────────────────────────────────────────
BUTTONS = [
    ('youtube', 'YOUTUBE', '@TheTechzeen', '#ff2d55',
     '<rect x="9" y="13" width="26" height="18" rx="6" fill="#ff2d55"/><path d="M19.5 17.5v9l7.5-4.5z" fill="#fff"/>'),
    ('website', 'WEBSITE', 'thetechzeen.com', V,
     f'<circle cx="22" cy="22" r="11" stroke="{V}" stroke-width="2"/><ellipse cx="22" cy="22" rx="5" ry="11" stroke="{V}" stroke-width="2"/><path d="M11 22h22" stroke="{V}" stroke-width="2"/>'),
    ('linkedin', 'LINKEDIN', 'Farzeen Ali', '#2f8fff',
     '<rect x="10" y="10" width="24" height="24" rx="6" fill="#2f8fff"/><path d="M16 20v8M16 16.2v.1M20.5 28v-8M20.5 23.5c0-2 1.5-3.5 3.5-3.5s3 1.4 3 3.5V28" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>'),
    ('email', 'EMAIL', 'techzeen10@gmail.com', M,
     f'<rect x="9" y="13" width="26" height="18" rx="4" stroke="{M}" stroke-width="2"/><path d="M10 15l12 9 12-9" stroke="{M}" stroke-width="2" stroke-linejoin="round"/>'),
]


def button(i, key, title, sub, col, icon):
    W, H = 290, 76
    css = '.sh{animation:sh 4.5s ease-in-out infinite}@keyframes sh{0%,55%{transform:translateX(-120px) skewX(-20deg)}100%{transform:translateX(420px) skewX(-20deg)}}'
    defs = (f'<clipPath id="b"><rect width="{W}" height="{H}" rx="20"/></clipPath>'
            '<linearGradient id="sg" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    body = f'''<g clip-path="url(#b)">{card(0, 0, W, H, 20, i * 2, 7)}
<g transform="translate(16 16)"><rect width="44" height="44" rx="12" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".45"/>{icon}</g>
<text x="76" y="36" class="s" font-size="15" font-weight="800" letter-spacing="3" fill="{TXT}">{title}</text>
<text x="76" y="56" class="m" font-size="11.5" fill="{MUT}">{esc(sub)}</text>
<path d="M258 30l10 8-10 8" stroke="{col}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><animateTransform attributeName="transform" type="translate" values="0 0;4 0;0 0" dur="1.6s" repeatCount="indefinite"/></path>
<rect class="sh" x="0" y="-20" width="70" height="120" fill="url(#sg)" style="animation-delay:{i * .4:.1f}s"/></g>'''
    return doc(W, H, body, css, defs)


# ── 8. FOOTER ─────────────────────────────────────────────────────────────────
def footer():
    W, H = 1200, 360

    def wave(amp, length, y, ph):
        d = f'M0 {y}'
        for x in range(0, 2 * W + 1, 20):
            d += f' L{x} {y + amp * math.sin(2 * math.pi * x / length + ph):.1f}'
        return d + f' L{2 * W} {H} L0 {H}Z'

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
<g><text x="600" y="160" text-anchor="middle" class="s" font-size="44" font-weight="800" fill="url(#ink)">1,000+ days. Zero days off.</text></g>
<g><text x="600" y="200" text-anchor="middle" class="s" font-size="19" fill="{MUT}">One mission — make complex tech actually build things.</text></g>
<g><text x="600" y="240" text-anchor="middle" class="m" font-size="12" font-weight="700" letter-spacing="3.5" fill="{C}">— FARZEEN ALI · MR. CONSISTENT · FOUNDER &amp; CEO, THE TECHZEEN</text></g>
<text x="600" y="{H - 22}" text-anchor="middle" class="m" font-size="10" letter-spacing="3" fill="{DIM}">© THE TECHZEEN — ENGINEERED IN PAKISTAN</text></g>
{card(0, 0, W, H, 28, 1, 12).replace('fill="url(#card)"', 'fill="none"')}'''
    return doc(W, H, body, css, defs)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    print('Building assets ->', os.path.normpath(OUT))
    write('hero.svg', hero())
    for i, (num, title, sub) in enumerate(SECTIONS):
        write(f'header-{num}.svg', header(num, title, sub, i))
    write('stats.svg', stats())
    write('arsenal.svg', arsenal())
    write('terminal.svg', terminal())
    write('stack.svg', marquee())
    for i, b in enumerate(BUTTONS):
        write(f'btn-{b[0]}.svg', button(i, *b))
    write('footer.svg', footer())
