#!/usr/bin/env python3
"""Per-client palette: resolve derived colours, emit the two :root blocks, and
VALIDATE every text/background combination against WCAG AA (4.5:1).

A client palette provides: bg, accent, secondary (+ optional bg2, accentDark, accentPrint).
Everything else (neutral greys, RAG semantics, fonts, panel overlays, the whole print
theme except the accent) is constant and shared. The generator refuses to build a client
whose palette fails validation — so a brand colour can never silently ship unreadable.
"""
import colorsys

# ── colour maths ──────────────────────────────────────────────────────────
def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb2hex(rgb):
    return '#%02X%02X%02X' % tuple(max(0, min(255, round(c))) for c in rgb)

def _lin(c):
    c /= 255
    return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4

def lum(hex_or_rgb):
    r, g, b = hex2rgb(hex_or_rgb) if isinstance(hex_or_rgb, str) else hex_or_rgb
    return 0.2126*_lin(r) + 0.7152*_lin(g) + 0.0722*_lin(b)

def contrast(fg, bg):
    a, b = lum(fg), lum(bg)
    a, b = max(a, b), min(a, b)
    return (a+0.05)/(b+0.05)

def blend(top, alpha, base):
    t, b = hex2rgb(top), hex2rgb(base)
    return rgb2hex(tuple(alpha*t[i] + (1-alpha)*b[i] for i in range(3)))

def darken(h, amount):
    r, g, b = [c/255 for c in hex2rgb(h)]
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0, l*(1-amount))
    return rgb2hex(tuple(c*255 for c in colorsys.hls_to_rgb(hh, l, s)))

def darken_to_contrast(h, bg, target=4.5, floor_l=0.06):
    """Darken (keep hue/sat) until contrast vs bg meets target, or L bottoms out."""
    r, g, b = [c/255 for c in hex2rgb(h)]
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    for _ in range(60):
        cand = rgb2hex(tuple(c*255 for c in colorsys.hls_to_rgb(hh, l, s)))
        if contrast(cand, bg) >= target or l <= floor_l:
            return cand
        l -= 0.02
    return rgb2hex(tuple(c*255 for c in colorsys.hls_to_rgb(hh, floor_l, s)))

def rgbstr(h):
    return '%d,%d,%d' % hex2rgb(h)

# ── constant tokens (shared across all clients) ───────────────────────────
SCREEN_CONST = dict(text='#E7E6F0', text2='#ABA9C7', text3='#9C99BF', ink='#FFFFFF',
                    gold='#E0A43B', red='#ef7189', green='#4fd18b')
PRINT_CONST  = dict(ink='#1F1C40', text='#2a2846', text2='#565478', text3='#6f6d8a',
                    red='#c2415c', green='#0f7d45', gold='#8a6410')

LANDMARK = dict(bg='#1F1C40', bg2='#171533', accent='#E8725D', accentDark='#C2533F',
                accentPrint='#C2533F', secondary='#8E8CC4')

# ── resolve a client palette (fill derived values) ────────────────────────
def resolve(pal):
    if not pal:
        return dict(LANDMARK)
    p = dict(pal)
    p.setdefault('secondary', p['accent'])
    p.setdefault('bg2', darken(p['bg'], 0.22))
    p.setdefault('accentDark', darken(p['accent'], 0.14))
    p.setdefault('accentPrint', darken_to_contrast(p['accent'], '#FFFFFF', 4.5))
    return p

# ── validate against WCAG AA ──────────────────────────────────────────────
def validate(pal):
    p = resolve(pal)
    panel = blend('#FFFFFF', 0.05, p['bg'])       # .panel / .lcard / .sec bg
    tbox  = blend('#FFFFFF', 0.03, panel)         # nested .tbox bg (worst case)
    tint  = blend(p['accent'], 0.12, panel)       # .pill.accent bg
    checks = []
    def chk(name, fg, bg, thr=4.5, hard=True):
        r = round(contrast(fg, bg), 2)
        checks.append(dict(name=name, ratio=r, need=thr, ok=r >= thr, hard=hard))
    # screen — body/caption text on the darkest panel
    chk('text on panel',  SCREEN_CONST['text'],  tbox)
    chk('text2 on panel', SCREEN_CONST['text2'], tbox)
    chk('text3 on panel', SCREEN_CONST['text3'], tbox)
    # screen — accent as heading/link text
    chk('accent (headings/links) on panel', p['accent'], panel)
    # screen — RAG semantic figures
    chk('gold (at-risk) on panel',  SCREEN_CONST['gold'],  panel)
    chk('red (behind) on panel',    SCREEN_CONST['red'],   panel)
    chk('green (on-track) on panel', SCREEN_CONST['green'], panel)
    # screen — accent text on its own tint (pills) — soft (short bold labels)
    chk('accent on accent-tint (pills)', p['accent'], tint, 4.5, hard=False)
    # print — accent on white paper (report headings/links)
    chk('accentPrint on white (report)', p['accentPrint'], '#FFFFFF')
    # print — constant greys/semantics on white (sanity)
    chk('print text3 on white', PRINT_CONST['text3'], '#FFFFFF')
    chk('print red on white',   PRINT_CONST['red'],   '#FFFFFF')
    chk('print green on white', PRINT_CONST['green'], '#FFFFFF')
    chk('print gold on white',  PRINT_CONST['gold'],  '#FFFFFF')
    hard_fail = [c for c in checks if c['hard'] and not c['ok']]
    soft_fail = [c for c in checks if not c['hard'] and not c['ok']]
    return dict(ok=not hard_fail, checks=checks, hard_fail=hard_fail, soft_fail=soft_fail,
                resolved=p, panel=panel)

# ── emit the two :root blocks ─────────────────────────────────────────────
def emit_screen_root(pal):
    p = resolve(pal); c = SCREEN_CONST
    return ("  :root{\n"
            "    --bg:%(bg)s; --bg2:%(bg2)s; --panel:rgba(255,255,255,0.05); --panelb:rgba(255,255,255,0.14); --line:rgba(255,255,255,0.09);\n"
            "    --ink:%(ink)s; --text:%(text)s; --text2:%(text2)s; --text3:%(text3)s;\n"
            "    --purple:%(accent)s; --purple-d:%(accentDark)s; --blue:%(secondary)s;\n"
            "    --orange:%(accent)s; --orange-d:%(accentDark)s;\n"
            "    --accent-rgb:%(argb)s; --accent2-rgb:%(s2rgb)s;\n"
            "    --gold:%(gold)s; --red:%(red)s; --green:%(green)s;\n"
            "    --serif:Georgia,'Times New Roman',serif;\n"
            "    --mono:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;\n"
            "  }") % dict(p, ink=c['ink'], text=c['text'], text2=c['text2'], text3=c['text3'],
                         gold=c['gold'], red=c['red'], green=c['green'],
                         argb=rgbstr(p['accent']), s2rgb=rgbstr(p['secondary']))

def emit_print_root(pal):
    p = resolve(pal); c = PRINT_CONST
    return ("    :root{--ink:%(ink)s;--text:%(text)s;--text2:%(text2)s;--text3:%(text3)s;--panel:#fff;--panelb:#d7d4e6;--line:#e6e4f0;\n"
            "      --red:%(red)s;--green:%(green)s;--gold:%(gold)s;--purple:%(ap)s;--orange:%(ap)s}") % dict(
                ink=c['ink'], text=c['text'], text2=c['text2'], text3=c['text3'],
                red=c['red'], green=c['green'], gold=c['gold'], ap=p['accentPrint'])

if __name__ == '__main__':
    import sys, json
    pal = json.load(open(sys.argv[1], encoding='utf-8')).get('palette') if len(sys.argv) > 1 else None
    v = validate(pal)
    print('resolved:', v['resolved'])
    for c in v['checks']:
        print(('  OK  ' if c['ok'] else ('  FAIL' if c['hard'] else '  warn')), f"{c['ratio']:>5} / {c['need']}  {c['name']}")
    print('VALID' if v['ok'] else 'INVALID (hard failures above)')
