"""Rebuild the living parts of the profile README from real GitHub data.

  assets/ledger.svg   - header: projects as a SHA-256 hash chain, verified block by block
  assets/packets.svg  - recent public activity rendered as a packet capture

Standard library only. Runs nightly in .github/workflows/refresh.yml.
Set GITHUB_TOKEN for higher rate limits; GH_USER overrides the account.
"""
import hashlib, json, os, urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USER = os.environ.get('GH_USER', 'Chandankumar775')
TOKEN = os.environ.get('GITHUB_TOKEN', '')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
MAX_BLOCKS = 8

# Curated blocks: repo name -> (title, one line). New repos with a live demo are appended automatically.
CURATED = {
    'credtech-by-chandan-kumar-': ('CredTech', 'Explainable credit scores with feature-level reasons'),
    'CharityChain': ('CharityChain', 'On-chain charity donations anyone can audit'),
    'nagrik-setu': ('Nagrik Setu', 'Civic issue reporting for Jharkhand (SIH)'),
    'new-delhi-dashboard-eco-ward-': ('Eco-Ward', 'Ward-level air quality for New Delhi'),
    'emf-multiagent': ('EMF Agents', 'AI pipeline paid per step in USDC on Algorand'),
    'aura-cv': ('AURA-CV', 'Air-gapped integrity checks for vision models'),
    'tunnlescope': ('TunnelScope', 'Grades IPsec VPN tunnels from their traffic'),
    'model-analysis-for-the-arbitage-system-': ('Arbitrage 3D', 'Bellman-Ford arbitrage, explorable in 3D'),
}
LANG = {'TypeScript': 'TS', 'JavaScript': 'JS', 'Python': 'PY', 'HTML': 'WEB', 'Dart': 'DART', 'Solidity': 'SOL',
        'Jupyter Notebook': 'IPYNB', 'Java': 'JAVA', 'CSS': 'CSS'}


def api(path):
    req = urllib.request.Request('https://api.github.com' + path, headers={'Accept': 'application/vnd.github+json', 'User-Agent': USER})
    if TOKEN:
        req.add_header('Authorization', 'Bearer ' + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def wrap(text, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]; lines[1] = lines[1][: width - 1].rstrip() + '…'
    return lines


THEME = """
    .ink{fill:#1f2328}.mute{fill:#59636e}.line{stroke:#d1d9e0}.card{fill:#f6f8fa;stroke:#d1d9e0}
    .ok{stroke:#1a7f37}.okf{fill:#1a7f37}.acc{fill:#cf222e}.sel{fill:#ddf4ff}.alt{fill:#f6f8fa}
    @media (prefers-color-scheme: dark){
      .ink{fill:#e6edf3}.mute{fill:#9198a1}.line{stroke:#3d444d}.card{fill:#151b23;stroke:#3d444d}
      .ok{stroke:#3fb950}.okf{fill:#3fb950}.acc{fill:#ff7b72}.sel{fill:#0c2d4b}.alt{fill:#151b23}
    }
    .serif{font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif}
    .sans{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif}
    .mono{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace}
    @media (prefers-reduced-motion: reduce){*{animation:none!important}}
"""


def build_ledger(repos, now):
    by_name = {r['name']: r for r in repos}
    blocks = [(name, *CURATED[name]) for name in CURATED if name in by_name]
    # anything new with a live demo, pushed in the last 45 days, joins the chain
    fresh = [r for r in repos if r['name'] not in CURATED and r['name'] != USER and not r['fork'] and r.get('homepage') and r.get('description')
             and (now - datetime.fromisoformat(r['pushed_at'].replace('Z', '+00:00'))).days <= 45]
    for r in sorted(fresh, key=lambda r: r['pushed_at']):
        blocks.append((r['name'], r['name'].strip('-').replace('-', ' ').title(), r['description']))
    blocks.sort(key=lambda b: by_name[b[0]]['created_at'])
    blocks = blocks[-MAX_BLOCKS:]

    chain, prev = [], '0' * 64
    for i, (name, title, line) in enumerate(blocks):
        r = by_name[name]
        payload = json.dumps({'i': i, 'repo': name, 'title': title, 'line': line, 'created': r['created_at'], 'prev': prev}, sort_keys=True)
        h = hashlib.sha256(payload.encode()).hexdigest()
        chain.append({'title': title, 'line': line, 'prev': prev, 'hash': h, 'lang': LANG.get(r.get('language') or '', (r.get('language') or '—')[:5].upper()),
                      'date': r['created_at'][:10], 'stars': r['stargazers_count']})
        prev = h

    W, cw, ch, gap, top = 1200, 264, 138, 32, 196
    rows = (len(chain) + 3) // 4
    H = top + rows * ch + (rows - 1) * 46 + 74
    T = 0.55 * len(chain) + 3.2  # one verification sweep, in seconds
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">',
         '<title id="t">Chandan Kumar</title>',
         f'<desc id="d">I build security and AI tools. My projects shown as a SHA-256 hash chain of {len(chain)} blocks, verified one by one.</desc>',
         '<style>' + THEME + f"""
    .v{{animation:v {T:.1f}s ease-out infinite both}}
    .ck{{stroke-dasharray:24;stroke-dashoffset:24;animation:ck {T:.1f}s ease-out infinite both}}
    .link{{stroke-dasharray:6 6;animation:fl 1.2s linear infinite}}
    @keyframes v{{0%{{stroke-opacity:0}}6%{{stroke-opacity:1}}82%{{stroke-opacity:1}}92%,100%{{stroke-opacity:0}}}}
    @keyframes ck{{0%{{stroke-dashoffset:24}}6%,82%{{stroke-dashoffset:0}}92%,100%{{stroke-dashoffset:24}}}}
    @keyframes fl{{to{{stroke-dashoffset:-12}}}}
  </style>""",
         '<text x="24" y="86" class="ink serif" font-size="66" font-weight="600" letter-spacing="-1.4">Chandan Kumar</text>',
         '<text x="26" y="132" class="ink sans" font-size="23">I build security and AI tools: software that checks whether data, models and traffic can be trusted.</text>',
         f'<text x="26" y="166" class="mute mono" font-size="15">Delhi, India  ·  my projects as a SHA-256 hash chain  ·  {len(chain)} blocks</text>']

    def pos(i):
        r, c = divmod(i, 4)
        if r % 2:
            c = 3 - c
        return 24 + c * (cw + gap), top + r * (ch + 46)

    for i in range(len(chain) - 1):  # links between consecutive blocks
        (x1, y1), (x2, y2) = pos(i), pos(i + 1)
        if y1 == y2:
            a, b = (x1 + cw, x2) if x2 > x1 else (x1, x2 + cw)
            o.append(f'<line x1="{a}" y1="{y1 + ch / 2}" x2="{b}" y2="{y2 + ch / 2}" class="line link" stroke-width="2"/>')
        else:
            o.append(f'<line x1="{x1 + cw / 2}" y1="{y1 + ch}" x2="{x2 + cw / 2}" y2="{y2}" class="line link" stroke-width="2"/>')

    for i, b in enumerate(chain):
        x, y = pos(i)
        d = f'animation-delay:{i * 0.55:.2f}s'
        o.append(f'<g transform="translate({x},{y})">')
        o.append(f'<rect width="{cw}" height="{ch}" rx="10" class="card" stroke-width="1.2"/>')
        o.append(f'<rect width="{cw}" height="{ch}" rx="10" fill="none" class="ok v" stroke-width="2.2" style="{d}"/>')
        o.append(f'<text x="16" y="26" class="mute mono" font-size="12">#{i:02d}  ·  {escape(b["lang"])}  ·  {b["date"]}</text>')
        o.append(f'<circle cx="{cw - 24}" cy="22" r="10" fill="none" class="line" stroke-width="1.5"/>')
        o.append(f'<path d="M{cw - 29} 22 l4 4 l7 -8" fill="none" class="ok ck" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="{d}"/>')
        o.append(f'<text x="16" y="54" class="ink sans" font-size="19" font-weight="650">{escape(b["title"])}</text>')
        for k, ln in enumerate(wrap(b['line'], 33)):
            o.append(f'<text x="16" y="{76 + k * 17}" class="mute sans" font-size="13.5">{escape(ln)}</text>')
        o.append(f'<text x="16" y="{ch - 14}" class="mono" font-size="11.5"><tspan class="mute">prev </tspan><tspan class="ink">{b["prev"][:8]}</tspan><tspan class="mute">   hash </tspan><tspan class="okf">{b["hash"][:8]}</tspan></text>')
        o.append('</g>')

    head = chain[-1]['hash'] if chain else '0' * 64
    o.append(f'<text x="24" y="{H - 22}" class="mute mono" font-size="13">head {head[:16]}  ·  every hash covers the block before it  ·  rebuilt {now:%Y-%m-%d} UTC by GitHub Actions</text>')
    o.append('</svg>')
    return '\n'.join(o)


def commit_message(repo, sha):
    try:
        return api(f'/repos/{repo}/commits/{sha}')['commit']['message'].splitlines()[0]
    except Exception:
        return ''


def build_packets(events, repos, now):
    lang = {r['full_name']: r.get('language') or '' for r in repos}
    rows = []
    for e in events:
        repo, t = e['repo']['name'], e['created_at']
        short = repo.split('/', 1)[1]
        p = e.get('payload', {})
        if e['type'] == 'PushEvent':
            msg = ''
            if p.get('commits'):
                msg = p['commits'][-1]['message'].splitlines()[0]
            elif p.get('head') and len(rows) < 12:
                msg = commit_message(repo, p['head'])
            n = p.get('size') or len(p.get('commits') or []) or 1
            rows.append((t, short, LANG.get(lang.get(repo, ''), 'GIT'), n, msg or 'push to ' + p.get('ref', 'main').split('/')[-1]))
        elif e['type'] == 'CreateEvent' and p.get('ref_type') == 'repository':
            rows.append((t, short, 'SYN', 0, 'new repository opened'))
        elif e['type'] == 'PullRequestEvent':
            rows.append((t, short, 'PR', 1, f"{p.get('action', '')} #{p.get('number', '')}"))
        elif e['type'] == 'ReleaseEvent':
            rows.append((t, short, 'REL', 1, 'release ' + p.get('release', {}).get('tag_name', '')))
        if len(rows) >= 10:
            break
    if not rows:  # no public events in 90 days: fall back to latest pushes
        for r in repos[:10]:
            rows.append((r['pushed_at'], r['name'], LANG.get(r.get('language') or '', 'GIT'), 1, r.get('description') or 'push'))

    rows.sort(key=lambda r: r[0], reverse=True)
    W, rh, top = 1200, 30, 92
    H = top + len(rows) * rh + 54
    cols = [(24, 'No.'), (78, 'Time (UTC)'), (232, 'Source'), (392, 'Destination'), (690, 'Proto'), (768, 'Len'), (826, 'Info')]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="pt pd">',
         '<title id="pt">Recent activity, as a packet capture</title>',
         f'<desc id="pd">The {len(rows)} most recent public pushes and repository events by {USER}.</desc>',
         '<style>' + THEME + """
    .r{animation:in .5s ease-out both}
    @keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}
    .cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}
  </style>""",
         f'<text x="24" y="34" class="ink mono" font-size="15" font-weight="600">$ capture -i github0 -c {len(rows)} "user {USER}"</text>',
         f'<text x="24" y="56" class="mute mono" font-size="12.5">listening on github0, captured {now:%Y-%m-%d %H:%M} UTC<tspan class="cur"> ▌</tspan></text>',
         f'<line x1="24" y1="{top - 10}" x2="{W - 24}" y2="{top - 10}" class="line"/>']
    for x, label in cols:
        o.append(f'<text x="{x}" y="{top + 8}" class="mute mono" font-size="12" font-weight="600">{label}</text>')
    o.append(f'<line x1="24" y1="{top + 18}" x2="{W - 24}" y2="{top + 18}" class="line"/>')
    for i, (t, dest, proto, n, info) in enumerate(rows):
        y = top + 24 + i * rh
        o.append(f'<g class="r" style="animation-delay:{0.15 + i * 0.12:.2f}s">')
        if i == 0:
            o.append(f'<rect x="20" y="{y}" width="{W - 40}" height="{rh - 4}" rx="4" class="sel"/>')
        elif i % 2:
            o.append(f'<rect x="20" y="{y}" width="{W - 40}" height="{rh - 4}" rx="4" class="alt"/>')
        ty = y + 18
        info = info if len(info) <= 54 else info[:53] + '…'
        dest = dest if len(dest) <= 34 else dest[:33] + '…'
        cells = [(24, str(i + 1), 'ink'), (78, t[5:16].replace('T', ' '), 'mute'), (232, 'chandan@delhi', 'ink'), (392, dest, 'ink'),
                 (690, proto, 'acc'), (768, str(n), 'mute'), (826, info, 'ink')]
        for x, val, cls in cells:
            o.append(f'<text x="{x}" y="{ty}" class="{cls} mono" font-size="12.5">{escape(val)}</text>')
        o.append('</g>')
    o.append(f'<text x="24" y="{H - 16}" class="mute mono" font-size="12">{len(rows)} packets captured · 0 dropped · refreshed nightly</text>')
    o.append('</svg>')
    return '\n'.join(o)


def main():
    now = datetime.now(timezone.utc)
    repos = api(f'/users/{USER}/repos?per_page=100&sort=pushed')
    try:
        events = api(f'/users/{USER}/events/public?per_page=100')
    except Exception:
        events = []
    os.makedirs(ASSETS, exist_ok=True)
    for name, svg in (('ledger.svg', build_ledger(repos, now)), ('packets.svg', build_packets(events, repos, now))):
        with open(os.path.join(ASSETS, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(svg + '\n')
        print('wrote', name, len(svg), 'bytes')


if __name__ == '__main__':
    main()
