#!/usr/bin/env python3
"""Phase 3 generator — master template + clients/<id>.json -> dist/<id>-tracker.html.

Swaps the marker blocks (CONFIG, DEMO, PALETTE, PALETTE-PRINT), the KSB line, and the
logo <img>. Palettes are VALIDATED against WCAG AA (via palette.py) — a client whose
brand colours fail contrast will NOT build.

Usage:  python generate-client.py landmark
        python generate-client.py --all
"""
import json, os, re, sys, base64
import palette as pal_mod

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

def swap_block(html, start, end, new):
    a = html.index(start); b = html.index(end, a) + len(end)
    return html[:a] + start + '\n' + new + '\n' + end + html[b:]

def placeholder_logo(name):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 40">'
           '<text x="0" y="30" font-family="Georgia,serif" font-size="28" '
           'font-weight="600" fill="#FFFFFF">' + name + '</text></svg>')
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode()

def set_logo(html, cfg):
    logo = cfg['brand'].get('logo')
    if logo == 'keep':
        return html
    src = logo if logo else placeholder_logo(cfg['brand'].get('clientName', ''))
    alt = cfg['brand'].get('logoAlt', '')
    return re.sub(r'(<img id="brandLogo" class="logo") alt="[^"]*" src="[^"]*"',
                  lambda m: m.group(1) + ' alt="' + alt + '" src="' + src + '"', html, count=1)

def check_palette(client_id, cfg):
    pal = cfg.get('palette')
    v = pal_mod.validate(pal)
    label = 'default (Landmark)' if not pal else 'custom'
    print(f"  palette [{label}] accent={v['resolved']['accent']} bg={v['resolved']['bg']} "
          f"accentPrint={v['resolved']['accentPrint']}")
    for c in v['soft_fail']:
        print(f"    warn: {c['name']} = {c['ratio']} (< {c['need']})")
    if not v['ok']:
        lines = [f"    {c['name']} = {c['ratio']} (needs {c['need']})" for c in v['hard_fail']]
        raise SystemExit(f"PALETTE FAILS WCAG AA for client '{client_id}':\n" + "\n".join(lines) +
                         "\n  -> choose a darker background and/or a higher-contrast accent.")
    return pal

def generate(client_id):
    cfg = json.load(open(os.path.join(CLIENTS, client_id + ".json"), encoding='utf-8'))
    html = open(TEMPLATE, encoding='utf-8').read()

    # palette — validate FIRST (blocks the build if brand colours fail AA)
    pal = check_palette(client_id, cfg)
    html = swap_block(html, '/*<<PALETTE>>*/', '/*<</PALETTE>>*/', pal_mod.emit_screen_root(pal))
    html = swap_block(html, '/*<<PALETTE-PRINT>>*/', '/*<</PALETTE-PRINT>>*/', pal_mod.emit_print_root(pal))

    # CONFIG (runtime logo forced null — logo is a build-time swap on the <img>)
    emitted = {'clientId': cfg['clientId'], 'brand': {**cfg['brand'], 'logo': None},
               'provider': cfg['provider'], 'standards': cfg['standards']}
    html = swap_block(html, '//<<CONFIG>>', '//<</CONFIG>>',
                      'const CONFIG=' + json.dumps(emitted, ensure_ascii=False) + ';')

    # KSB_STANDARDS line
    lines = html.split('\n')
    for i, l in enumerate(lines):
        if l.startswith('const KSB_STANDARDS='):
            lines[i] = 'const KSB_STANDARDS=' + json.dumps(extract_ksb(cfg['standards']), ensure_ascii=False) + ';'
            break
    html = '\n'.join(lines)

    # DEMO
    demo = cfg.get('demo', 'keep')
    if demo != 'keep':
        data = demo if isinstance(demo, dict) else (
            json.load(open(os.path.join(CLIENTS, demo), encoding='utf-8')) if demo else {'reviews': [], 'provider': {}})
        html = swap_block(html, '//<<DEMO>>', '//<</DEMO>>', 'const DEMO=' + json.dumps(data, ensure_ascii=False) + ';')

    # logo
    html = set_logo(html, cfg)

    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, cfg['clientId'] + "-tracker.html")
    open(out, 'w', encoding='utf-8').write(html)
    print(f"  -> {out}  ({len(html.encode('utf-8')):,} bytes)  clientId={cfg['clientId']}  standards={cfg['standards']}")
    return out

if __name__ == '__main__':
    args = sys.argv[1:]
    if args == ['--all']:
        args = [f[:-5] for f in os.listdir(CLIENTS) if f.endswith('.json') and not f.endswith('-demo.json')]
    for cid in args:
        print(f"[{cid}]")
        generate(cid)
