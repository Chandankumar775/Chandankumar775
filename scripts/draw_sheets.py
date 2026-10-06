"""Draw the profile's hand-sketched sheets as self-contained SVGs.

Each sheet is pale-green engineering computation paper with marker ink,
highlighter swipes and taped corners. Kalam (Indian Type Foundry, OFL) is
subset and embedded so the lettering renders the same on every device.

Usage: python scripts/draw_sheets.py <fonts-dir>
"""
import base64, io, math, os, random, sys
from xml.sax.saxutils import escape
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'sheets')
FONTS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '.fonts')

PAPER, GRID, INK, INK2 = '#EAF2E3', '#B9A27A', '#16181B', '#3D4650'
HL = {'y': '#FFE45C', 'p': '#FF8FB1', 't': '#5CE1C6'}
W = 1200

# ---------------------------------------------------------------- content

HEADER = {
    'name': 'Chandan Kumar',
    'role': 'security + AI engineer',
    'line': 'I build systems that check whether data, models and network traffic can be trusted.',
    'flow': [('untrusted input', 'datasets · models · VPN traffic'), ('checks', 'hash · verify · explain'), ('trusted result', 'signed, with its reasons')],
    'domains': ['security', 'explainable AI', 'web3', '3D + data viz'],
    'foot': 'Delhi, India  ·  each sheet below opens its live demo or repo',
}

TOOLBOX = [
    ('daily drivers', ['TypeScript', 'Python', 'React', 'Next.js'], 'y'),
    ('3D + viz', ['Three.js', 'WebGL', 'Recharts'], 't'),
    ('crypto + trust', ['Ed25519', 'SHA-256', 'RFC 8785', 'IPsec'], 'p'),
    ('on-chain', ['Solidity', 'ethers.js', 'web3dart', 'Algorand'], 'y'),
    ('AI', ['Genkit', 'Gemini', 'Pydantic'], 't'),
    ('ship it', ['Vercel', 'Firebase', 'Docker', 'Flutter'], 'p'),
]

# cols: list of columns, each a list of node labels; arrows converge into the next column's first node
PROJECTS = [
    {
        'slug': 'aura-cv', 'name': 'AURA-CV', 'hl': 'y', 'live': True,
        'pitch': 'integrity checks for computer-vision pipelines, fully air-gapped',
        'cols': [['contributed\ndataset', 'trained\nmodel', 'inference\nrecords'], ['check\nplugins'], ['findings +\ndisposition'], ['hash-chained\naudit log']],
        'notes': [(3, 'every entry is Ed25519-signed over\nRFC 8785 canonical JSON', 'p'), (1, 'runs offline: an outbound\nnetwork guard blocks every call', None)],
        'tools': ['Python', 'Pydantic', 'cryptography', 'rfc8785', 'Typer', 'React', 'Three.js'],
    },
    {
        'slug': 'tunnelscope', 'name': 'TunnelScope', 'hl': 't', 'live': True,
        'pitch': 'reads encrypted IPsec traffic and grades how safe the VPN is',
        'cols': [['encrypted\ncapture'], ['protocol\nidentification'], ['security\nassessment'], ['grade\nA to F'], ['fix\nsimulator']],
        'notes': [(4, 'toggle a fix: the score and grade\nrecompute live, then copy the\nstrongSwan config diff', 'y'), (0, 'what a passive observer\nstill learns is reported too', None)],
        'tools': ['TypeScript', 'React', 'Zustand', 'Recharts', 'Framer Motion', 'Firebase'],
    },
    {
        'slug': 'arbitrage-3d', 'name': 'Arbitrage System, in 3D', 'hl': 'p', 'live': True,
        'pitch': 'Bellman-Ford hunting forex arbitrage, explorable as a 3D model',
        'cols': [['live\nrates'], ['graph\nw = −log(rate)'], ['Bellman-Ford\nV − 1 rounds'], ['round V still\nrelaxes?'], ['negative cycle\n= arbitrage']],
        'notes': [(1, 'product > 1 becomes sum < 0:\nprofit turns into a negative cycle', 't'), (2, 'every relaxation is recorded\nand replayed in 3D', None)],
        'tools': ['Three.js', 'WebGL', 'JavaScript', 'Java / Spring Boot (modelled)'],
    },
    {
        'slug': 'credtech', 'name': 'CredTech', 'hl': 'y', 'live': False,
        'pitch': 'credit scores that explain themselves, feature by feature',
        'cols': [['financial\ndata', 'news +\nunstructured'], ['data\npipeline'], ['interpretable\nmodel'], ['credit\nscore'], ['feature-level\nreasons']],
        'notes': [(4, 'every score says WHY: which features\npushed it up or down', 'p'), (2, 'Gemini via Genkit for the\nunstructured side', None)],
        'tools': ['Next.js', 'TypeScript', 'Genkit', 'Gemini', 'Firebase', 'Radix UI'],
    },
    {
        'slug': 'emf-multiagent', 'name': 'EMF Multi-Agent', 'hl': 't', 'live': False,
        'pitch': 'one request pays a chain of AI services, step by step',
        'cols': [['one\nrequest'], ['Search\n0.01 USDC'], ['Scraper\n0.02 USDC'], ['Summarizer\n0.01 USDC'], ['Report\n0.03 USDC']],
        'notes': [(2, 'each step settles its own\nmicro-payment (x402-style,\nAlgorand testnet, simulated)', 'y'), (4, 'Pending → Paying → Settled', None)],
        'tools': ['Next.js', 'React', 'TypeScript', 'Recharts', 'Framer Motion', 'Algorand'],
    },
    {
        'slug': 'charitychain', 'name': 'CharityChain', 'hl': 'p', 'live': False,
        'pitch': 'charity donations anyone can audit, end to end',
        'cols': [['donor\nwallet'], ['smart\ncontract'], ['NGO\nverification'], ['funds\nreleased']],
        'notes': [(1, 'every donation is traceable\non-chain, by anyone', 't'), (2, 'admin panel controls\nwhich NGOs can receive', None)],
        'tools': ['Solidity', 'ethers.js', 'Next.js', 'Flutter', 'web3dart'],
    },
]

# ---------------------------------------------------------------- fonts

def collect_text():
    parts = [HEADER['name'], HEADER['role'], HEADER['line'], HEADER['foot'], 'my toolbox', 'built with', 'live demo', 'open repo',
             'Sheet of By CK Project Date', '0123456789 →↗✓·×−:+()/,.?!\'"&-', 'click the sheet', 'the clever bit']
    parts += HEADER['domains'] + [a + b for a, b in HEADER['flow']]
    for g, tools, _ in TOOLBOX:
        parts += [g] + tools
    for p in PROJECTS:
        parts += [p['name'], p['pitch']] + p['tools'] + sum(p['cols'], []) + [n[1] for n in p['notes']]
    return ''.join(parts) + 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '


def font_face(path, family, text):
    f = TTFont(path)
    opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['kern', 'liga']
    s = subset.Subsetter(opts); s.populate(text=text); s.subset(f)
    buf = io.BytesIO(); f.flavor = 'woff2'; f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}"


# ---------------------------------------------------------------- drawing primitives

class Sheet:
    def __init__(self, h, seed):
        self.h, self.o, self.r, self.delay = h, [], random.Random(seed), 0.0

    def add(self, s):
        self.o.append(s)

    def t(self, x, y, s, size=22, weight='r', fill=INK, anchor='start', rot=0):
        fam = 'kb' if weight == 'b' else 'kr'
        tr = f' transform="rotate({rot} {x} {y})"' if rot else ''
        for i, line in enumerate(s.split('\n')):
            self.add(f'<text x="{x:.1f}" y="{y + i * size * 1.12:.1f}" class="{fam}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{tr}>{escape(line)}</text>')

    def step(self, d=0.18):
        self.delay += d
        return f'animation-delay:{self.delay:.2f}s'

    def highlight(self, x, y, w, h, col):
        jit = self.r.uniform(-1.5, 1.5)
        self.add(f'<path d="M{x - 6} {y + 4 + jit} L{x + w + 8} {y + jit} L{x + w + 4} {y + h} L{x - 4} {y + h + 3} Z" fill="{HL[col]}" opacity=".85" class="swipe" style="{self.step(0.25)};transform-origin:{x}px {y}px"/>')

    def box(self, x, y, w, h, label, size=20):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" stroke="{INK}" stroke-width="2.6" filter="url(#wob)" class="draw" pathLength="1" style="{self.step()}"/>')
        n = label.count('\n') + 1
        self.t(x + w / 2, y + h / 2 - (n - 1) * size * 0.56 + size * 0.36, label, size, 'r', INK, 'middle')

    def arrow(self, x1, y1, x2, y2, bend=0.0, col=INK):
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        cx, cy = mx - dy / L * bend, my + dx / L * bend
        st = self.step(0.12)
        self.add(f'<path d="M{x1:.1f} {y1:.1f} Q{cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linecap="round" filter="url(#wob)" class="draw" pathLength="1" style="{st}"/>')
        ang = math.atan2(y2 - cy, x2 - cx)
        for s in (0.5, -0.5):
            hx, hy = x2 - 13 * math.cos(ang + s), y2 - 13 * math.sin(ang + s)
            self.add(f'<path d="M{x2:.1f} {y2:.1f} L{hx:.1f} {hy:.1f}" stroke="{col}" stroke-width="2.4" stroke-linecap="round" class="draw" pathLength="1" style="{st}"/>')

    def circled(self, x, y, s, size=21, col=None):
        w = len(s) * size * 0.5 + 26
        if col:
            self.highlight(x - w / 2 + 10, y - size * 0.62, w - 20, size * 0.8, col)
        self.add(f'<ellipse cx="{x:.1f}" cy="{y - size * 0.3:.1f}" rx="{w / 2:.1f}" ry="{size * 0.95:.1f}" fill="none" stroke="{INK}" stroke-width="2" filter="url(#wob)" transform="rotate({self.r.uniform(-4, 4):.1f} {x:.1f} {y:.1f})" class="draw" pathLength="1" style="{self.step(0.07)}"/>')
        self.t(x, y, s, size, 'r', INK, 'middle')
        return w

    def tape(self, x, y, rot):
        self.add(f'<rect x="{x - 60}" y="{y - 16}" width="120" height="32" fill="#F3E9B8" opacity=".78" transform="rotate({rot} {x} {y})" filter="url(#wob)"/>')

    def svg(self, title, desc, fonts):
        h = self.h
        css = fonts + f"""
.kr{{font-family:'K','Segoe Print','Bradley Hand',cursive}}.kb{{font-family:'KB','Segoe Print','Bradley Hand',cursive;font-weight:700}}
.draw{{stroke-dasharray:1;stroke-dashoffset:1;animation:draw .7s ease-out forwards}}
.swipe{{transform:scaleX(0);animation:swipe .45s cubic-bezier(.2,.8,.2,1) forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}@keyframes swipe{{to{{transform:scaleX(1)}}}}
@media (prefers-reduced-motion: reduce){{.draw{{animation:none;stroke-dashoffset:0}}.swipe{{animation:none;transform:none}}}}"""
        return '\n'.join([
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-labelledby="t d">',
            f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>',
            '<defs>',
            '<filter id="wob" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="3.4"/></filter>',
            '<filter id="shadow" x="-5%" y="-5%" width="110%" height="115%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity=".28"/></filter>',
            f'<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="{GRID}" stroke-width=".7" opacity=".45"/></pattern>',
            '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="9"/><feColorMatrix values="0 0 0 0 .35  0 0 0 0 .3  0 0 0 0 .2  0 0 0 .06 0"/></filter>',
            f'<style>{css}</style></defs>',
            f'<g transform="rotate({self.r.uniform(-0.5, 0.5):.2f} 600 {h / 2})">',
            f'<rect x="18" y="18" width="{W - 36}" height="{h - 44}" rx="3" fill="{PAPER}" filter="url(#shadow)"/>',
            f'<rect x="18" y="18" width="{W - 36}" height="{h - 44}" fill="url(#grid)"/>',
            f'<rect x="18" y="18" width="{W - 36}" height="{h - 44}" filter="url(#grain)"/>',
            *self.o, '</g></svg>'])


def title_strip(s, project, sheet_no, total, hint='click the sheet to open it  ↗'):
    y = 34
    s.add(f'<path d="M30 {y + 34} H{W - 30} M430 {y} V{y + 34} M840 {y} V{y + 34} M1010 {y} V{y + 34}" stroke="{GRID}" stroke-width="1.4"/>')
    s.t(40, y + 24, 'Project', 15, 'r', INK2); s.t(110, y + 25, project, 19, 'b', INK)
    s.t(442, y + 24, hint, 15, 'r', INK2)
    s.t(852, y + 24, 'Sheet', 15, 'r', INK2); s.t(905, y + 25, f'{sheet_no:02d} of {total:02d}', 19, 'b', INK)
    s.t(1022, y + 24, 'By', 15, 'r', INK2); s.t(1050, y + 25, 'CK', 19, 'b', INK)


# ---------------------------------------------------------------- sheets

def header_sheet(fonts, total):
    s = Sheet(600, 11)
    title_strip(s, 'about me', 1, total, 'drawn by hand, one sheet per project')
    s.tape(150, 22, -6); s.tape(1050, 22, 5)
    s.t(64, 168, HEADER['name'], 92, 'b')
    s.highlight(66, 196, 404, 34, 'y')
    s.t(70, 222, HEADER['role'], 36, 'b')
    s.t(70, 270, HEADER['line'], 25, 'r', INK2)
    xs, y = [70, 450, 830], 330
    for i, (lab, sub) in enumerate(HEADER['flow']):
        s.box(xs[i], y, 300, 74, lab, 25)
        s.t(xs[i] + 150, y + 108, sub, 19, 'r', INK2, 'middle')
        if i < 2:
            s.arrow(xs[i] + 306, y + 37, xs[i + 1] - 8, y + 37, -14)
    s.add(f'<path d="M1078 352 l9 11 l18 -24" fill="none" stroke="#1F8A4C" stroke-width="4" stroke-linecap="round" class="draw" pathLength="1" style="{s.step()}"/>')
    x = 90
    for i, d in enumerate(HEADER['domains']):
        w = len(d) * 11 + 26
        s.circled(x + w / 2, 500, d, 22, ['p', 't', 'y', 'p'][i])
        x += w + 46
    s.t(70, 552, HEADER['foot'], 18, 'r', INK2)
    return s.svg('Chandan Kumar, security and AI engineer', 'A hand-drawn sheet: untrusted input goes through checks to a trusted, signed result.', fonts)


def toolbox_sheet(fonts, total):
    s = Sheet(640, 23)
    title_strip(s, 'my toolbox', 2, total, "read from each repo's real dependencies")
    s.tape(600, 22, -3)
    s.t(64, 140, 'my toolbox', 54, 'b')
    s.t(372, 140, '(what the projects below are actually built with)', 21, 'r', INK2)
    for gi, (group, tools, col) in enumerate(TOOLBOX):
        cx, cy = 70 + (gi % 3) * 372, 210 + (gi // 3) * 200
        s.highlight(cx, cy - 22, len(group) * 12 + 6, 26, col)
        s.t(cx + 2, cy, group, 26, 'b')
        x, ty = cx + 4, cy + 58
        for tool in tools:
            w = len(tool) * 9.6 + 22
            if x + w > cx + 345:
                x, ty = cx + 4, ty + 54
            s.circled(x + w / 2, ty, tool, 19)
            x += w + 12
    return s.svg('My toolbox', 'The languages, frameworks and libraries behind the projects, grouped by what they are for.', fonts)


def project_sheet(p, idx, total, fonts):
    s = Sheet(560, 100 + idx)
    title_strip(s, p['name'], idx, total)
    s.tape(130, 22, -5); s.tape(1070, 22, 4)
    s.t(64, 138, p['name'], 58, 'b')
    s.highlight(66, 160, min(1060, len(p['pitch']) * 12.9), 30, p['hl'])
    s.t(70, 184, p['pitch'], 27, 'r')
    tag = 'live demo  ↗' if p['live'] else 'open repo  ↗'
    s.t(1130, 138, tag, 24, 'b', '#C2185B' if p['live'] else INK2, 'end', -3)

    cols, n = p['cols'], len(p['cols'])
    bw, gap = (1060 - (n - 1) * 46) / n, 46
    top, bh = 236, 74
    centers = []
    for ci, col in enumerate(cols):
        x = 70 + ci * (bw + gap)
        k = len(col)
        ys = [top + (j - (k - 1) / 2) * (bh + 16) + (k - 1) * 0 for j in range(k)] if k > 1 else [top + 30]
        if k > 1:
            ys = [top - 26 + j * (bh * 0.66 + 9) for j in range(k)]
        hh = bh * 0.66 if k > 1 else bh
        pts = []
        for j, lab in enumerate(col):
            s.box(x, ys[j], bw, hh, lab, 19 if k > 1 else 20)
            pts.append((x, ys[j] + hh / 2, x + bw, ys[j] + hh / 2))
        centers.append(pts)
    for ci in range(n - 1):
        tx, ty = centers[ci + 1][0][0], centers[ci + 1][0][1]
        for (_, _, sx, sy) in centers[ci]:
            s.arrow(sx + 6, sy, tx - 8, ty, (sy - ty) * 0.15 - 6)
    # margin notes pointing at nodes
    for ni, (col_i, text, hl) in enumerate(p['notes']):
        nx = 70 + col_i * (bw + gap) + bw / 2
        node_bottom = max(y for (_, y, _, _) in centers[col_i]) + bh / 2
        ty = 410
        tx = 760 if hl else 70
        if hl:
            s.t(tx, ty - 6, 'the clever bit:', 17, 'b', '#C2185B')
        s.t(tx, ty + 20, text, 21, 'r', INK if hl else INK2)
        s.arrow(tx + 60, ty - 30 if hl else ty - 8, nx, node_bottom + 10, 18 if tx < nx else -18, '#C2185B' if hl else INK2)
    # built with
    s.t(64, 520, 'built with', 21, 'b')
    x = 186
    for tool in p['tools']:
        w = len(tool) * 9.4 + 22
        if x + w > 1150:
            break
        s.circled(x + w / 2, 520, tool, 18)
        x += w + 12
    return s.svg(f"{p['name']}: {p['pitch']}", 'Architecture sketch: ' + ' → '.join(' / '.join(c).replace('\n', ' ') for c in p['cols']) + '. Built with ' + ', '.join(p['tools']) + '.', fonts)


def main():
    os.makedirs(OUT, exist_ok=True)
    text = collect_text()
    fonts = font_face(os.path.join(FONTS, 'Kalam-Regular.ttf'), 'K', text) + font_face(os.path.join(FONTS, 'Kalam-Bold.ttf'), 'KB', text)
    total = 2 + len(PROJECTS)
    files = {'00-about.svg': header_sheet(fonts, total), '01-toolbox.svg': toolbox_sheet(fonts, total)}
    for i, p in enumerate(PROJECTS):
        files[f'{i + 2:02d}-{p["slug"]}.svg'] = project_sheet(p, i + 3, total, fonts)
    for name, svg in files.items():
        with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(svg)
        print(name, len(svg) // 1024, 'KB')


if __name__ == '__main__':
    main()
