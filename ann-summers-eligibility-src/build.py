"""Build index.html from src.html.
Injects: Fundable logo paths (light + dark), slim standards list, Ann Summers logo images (base64).
Run:  python -I build.py [--src demo-src.html] [extra output paths...]  (e.g. the Pages repo copy).
"""
import base64, io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
J = lambda *p: os.path.join(HERE, *p)

ARGS = sys.argv[1:]
TEMPLATE, DEFAULT_OUT = 'src.html', 'index.html'
if ARGS[:1] == ['--src']:                       # e.g. --src demo-src.html  -> demo.html
    TEMPLATE = ARGS[1]; DEFAULT_OUT = TEMPLATE.replace('-src', ''); ARGS = ARGS[2:]
src = io.open(J(TEMPLATE), encoding='utf-8').read()
logo = io.open(J('..', 'arthur-curtis-site', 'assets', 'fundable-logo.svg'), encoding='utf-8').read()
paths = ''.join(re.findall(r'<path[^>]*/>', logo))
stds = io.open(J('assets', 'standards-slim.json'), encoding='utf-8-sig').read().strip()

icon = io.open(J('..', 'arthur-curtis-site', 'assets', 'fundable-icon.svg'), encoding='utf-8').read()
ipaths = ''.join(re.findall(r'<path[^>]*/>', icon))
ACD = J('..', 'arthur-curtis-site', 'assets')

def img(name):
    return 'data:image/png;base64,' + base64.b64encode(open(J('assets', name), 'rb').read()).decode()
def svg(path):
    return 'data:image/svg+xml;base64,' + base64.b64encode(open(path, 'rb').read()).decode()

# Ann Summers logo as vectors (traced by trace_logo.py from the client's raster)
LG = json.load(io.open(J('assets', 'as-logo.json'), encoding='utf-8'))
vbw, vbh = LG['vb']
sp_parts, fills = [], []
for i, l in enumerate(LG['letters']):
    fills.append(f'<path class="lt" style="--i:{i}" fill-rule="evenodd" d="{l["d"]}"/>')
    for p in l['parts']:
        sp_parts.append(f'<path class="tr" style="--i:{i}" pathLength="100" d="{p}"/><path class="sp" style="--i:{i}" pathLength="100" d="{p}"/>')
ai = len(LG['letters'])
for p in LG['apple']['parts']:
    sp_parts.append(f'<path class="tr ap" style="--i:{ai}" pathLength="100" d="{p}"/><path class="sp ap" style="--i:{ai}" pathLength="100" d="{p}"/>')
splash_svg = (f'<svg class="aslogo" viewBox="0 0 {vbw} {vbh}" role="img" aria-label="Ann Summers">'
              f'<g>{"".join(fills)}</g><path class="apl" fill-rule="evenodd" d="{LG["apple"]["d"]}"/><g>{"".join(sp_parts)}</g></svg>')
all_letters = ''.join(l['d'] for l in LG['letters'])
header_svg = (f'<svg class="hlogo" viewBox="0 0 {vbw} {vbh}" role="img" aria-label="Ann Summers">'
              f'<path fill="#FFFFFF" fill-rule="evenodd" d="{all_letters}"/><path fill="#E8325E" fill-rule="evenodd" d="{LG["apple"]["d"]}"/></svg>')

out = (src.replace('__AS_SPLASH_SVG__', splash_svg).replace('__AS_HEADER_SVG__', header_svg).replace('__FUNDABLE_LOGO_PATHS_DARK__', paths.replace('#FFFFFF', '#1E1A1C'))
          .replace('__FUNDABLE_LOGO_PATHS__', paths)
          .replace('__FUNDABLE_ICON_PATHS_DARK__', ipaths.replace('#FFFFFF', '#1E1A1C'))
          .replace('__FUNDABLE_ICON_PATHS__', ipaths)
          .replace('__IMG_ACD_WHITE__', svg(os.path.join(ACD, 'ac-digital-lockup-white.svg')))
          .replace('__IMG_ACD__', svg(os.path.join(ACD, 'ac-digital-lockup.svg')))
          .replace('__STDS__', stds)
          )
left = re.findall(r'__[A-Z_]+__', out)
assert not left, left
targets = [J(DEFAULT_OUT)] + ARGS
for t in targets:
    io.open(t, 'w', encoding='utf-8').write(out)
print('built', len(out), 'bytes ->', ', '.join(targets))
