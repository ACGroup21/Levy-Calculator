#!/usr/bin/env python3
"""Phase 3 — generate a client tracker from the master template + a client config.

  master template (landmark-tracker.html, with //<<CONFIG>> / //<<DEMO>> markers)
  + clients/<id>.json
  + ksb-library.json (KSB slice for the client's standards)
  ->  dist/<clientId>-tracker.html   (isolated: own clientId, branding, standards, data)

Usage:  python generate-client.py landmark
        python generate-client.py <clientId>            # reads clients/<clientId>.json
        python generate-client.py --all
NOTE: palette is NOT swapped here — per-client palettes need a WCAG-AA contrast check
      (the agreed fast-follow). Clients currently share the validated default palette.
"""
import json, os, re, sys, base64

BASE     = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = r"C:\Users\omari\.claude\landmark-tracker.html"
LIB      = os.path.join(BASE, "ksb-library.json")
CLIENTS  = os.path.join(BASE, "clients")
DIST     = os.path.join(BASE, "dist")

def extract_ksb(codes):
    lib = json.load(open(LIB, encoding='utf-8'))['standards']
    out, missing = {}, []
    for c in codes:
        c = c.strip().upper(); e = lib.get(c)
        if not e: missing.append(c); continue
        out[c] = {k: e[k] for k in ('name', 'code', 'match', 'K', 'S', 'B')}
    if missing: sys.stderr.write("  WARNING missing standards: " + ", ".join(missing) + "\n")
    return out

def swap_block(html, name, new):
    s, e = '//<<' + name + '>>', '//<</' + name + '>>'
    a = html.index(s); b = html.index(e, a) + len(e)
    return html[:a] + s + '\n' + new + '\n' + e + html[b:]

def placeholder_logo(name):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 40">'
           '<text x="0" y="30" font-family="Georgia,serif" font-size="28" '
           'font-weight="600" fill="#FFFFFF">' + name + '</text></svg>')
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode()

def set_logo(html, cfg):
    logo = cfg['brand'].get('logo')
    if logo == 'keep':
        return html                                   # leave the template's <img> as-is
    src = logo if logo else placeholder_logo(cfg['brand'].get('clientName', ''))
    alt = cfg['brand'].get('logoAlt', '')
    return re.sub(r'(<img id="brandLogo" class="logo") alt="[^"]*" src="[^"]*"',
                  lambda m: m.group(1) + ' alt="' + alt + '" src="' + src + '"', html, count=1)

def generate(client_id):
    cfg = json.load(open(os.path.join(CLIENTS, client_id + ".json"), encoding='utf-8'))
    html = open(TEMPLATE, encoding='utf-8').read()

    # 1) CONFIG block (runtime logo forced null — logo is a build-time swap on the <img>)
    emitted = {'clientId': cfg['clientId'],
               'brand': {**cfg['brand'], 'logo': None},
               'provider': cfg['provider'],
               'standards': cfg['standards']}
    html = swap_block(html, 'CONFIG', 'const CONFIG=' + json.dumps(emitted, ensure_ascii=False) + ';')

    # 2) KSB_STANDARDS line (only this client's standards)
    lines = html.split('\n')
    for i, l in enumerate(lines):
        if l.startswith('const KSB_STANDARDS='):
            lines[i] = 'const KSB_STANDARDS=' + json.dumps(extract_ksb(cfg['standards']), ensure_ascii=False) + ';'
            break
    html = '\n'.join(lines)

    # 3) DEMO block
    demo = cfg.get('demo', 'keep')
    if demo != 'keep':
        data = demo if isinstance(demo, dict) else (
            json.load(open(os.path.join(CLIENTS, demo), encoding='utf-8')) if demo else {'reviews': [], 'provider': {}})
        html = swap_block(html, 'DEMO', 'const DEMO=' + json.dumps(data, ensure_ascii=False) + ';')

    # 4) logo <img>
    html = set_logo(html, cfg)

    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, cfg['clientId'] + "-tracker.html")
    open(out, 'w', encoding='utf-8').write(html)
    print(f"generated {out}  ({len(html.encode('utf-8')):,} bytes)  clientId={cfg['clientId']}  standards={cfg['standards']}")
    return out

if __name__ == '__main__':
    args = sys.argv[1:]
    if args == ['--all']:
        args = [f[:-5] for f in os.listdir(CLIENTS) if f.endswith('.json') and not f.endswith('-demo.json')]
    for cid in args:
        generate(cid)
