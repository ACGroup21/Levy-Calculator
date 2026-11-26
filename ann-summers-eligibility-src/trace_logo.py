"""Trace the Ann Summers logo (small raster supplied by the client) into crisp vector paths.

Marching squares on an upscaled, lightly-smoothed coverage map -> closed contours ->
Douglas-Peucker simplify -> smooth quadratic curves. Letters are grouped (outer + holes)
and ordered left-to-right so the splash can run an LED spark around each one in turn.

Output: assets/as-logo.json  {vb:[w,h], letters:[{d, parts:[d...]}], apple:{d, parts:[d...]}}
Run:    python -I trace_logo.py <path-to-logo.png>
"""
import io, json, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
S = 4                                     # upscale factor
FRAME = (48, 28, 522, 138)                # crop in source px (same frame as the PNG assets)
APPLE_BOX = (158, 30, 212, 80)            # apple + stem + tick, source px
PLUM, APPLE = (156, 48, 100), (204, 40, 80)
lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

im = Image.open(SRC).convert('RGB')
big = im.resize((im.width * S, im.height * S), Image.LANCZOS)
a = np.asarray(big).astype(np.float64)
L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
H, W = L.shape
yy, xx = np.mgrid[0:H, 0:W]
in_apple = (xx / S >= APPLE_BOX[0]) & (xx / S < APPLE_BOX[2]) & (yy / S >= APPLE_BOX[1]) & (yy / S < APPLE_BOX[3])

def coverage(col, mask):
    c = np.clip((255 - L) / (255 - lum(col)), 0, 1) * mask
    img = Image.fromarray((c * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=2.2))
    c = np.asarray(img).astype(np.float64) / 255
    x0, y0, x1, y1 = [v * S for v in FRAME]
    c = c[y0:y1, x0:x1]
    return np.pad(c, 2)                    # zero border => every contour closes

def contours(f, level=0.5):
    b = f >= level
    idx = (b[:-1, :-1] * 8 + b[:-1, 1:] * 4 + b[1:, 1:] * 2 + b[1:, :-1] * 1).astype(int)
    def pt(e):
        k, i, j = e
        if k == 'h':
            f0, f1 = f[i, j], f[i, j + 1]; t = (level - f0) / (f1 - f0); return (j + t, i)
        f0, f1 = f[i, j], f[i + 1, j]; t = (level - f0) / (f1 - f0); return (j, i + t)
    adj = {}
    def seg(e1, e2):
        adj.setdefault(e1, []).append(e2); adj.setdefault(e2, []).append(e1)
    for i, j in np.argwhere((idx != 0) & (idx != 15)):
        c = idx[i, j]
        T, B, Lf, R = ('h', i, j), ('h', i + 1, j), ('v', i, j), ('v', i, j + 1)
        centre = (f[i, j] + f[i, j + 1] + f[i + 1, j] + f[i + 1, j + 1]) / 4 >= level
        table = {1: [(Lf, B)], 2: [(B, R)], 3: [(Lf, R)], 4: [(T, R)], 6: [(T, B)], 7: [(T, Lf)],
                 8: [(T, Lf)], 9: [(T, B)], 11: [(T, R)], 12: [(Lf, R)], 13: [(B, R)], 14: [(Lf, B)],
                 5: [(T, Lf), (B, R)] if centre else [(T, R), (Lf, B)],
                 10: [(T, R), (Lf, B)] if centre else [(T, Lf), (B, R)]}
        for e1, e2 in table[c]: seg(e1, e2)
    loops, seen = [], set()
    for start in adj:
        if start in seen: continue
        loop, prev, cur = [], None, start
        while True:
            seen.add(cur); loop.append(pt(cur))
            nxt = [n for n in adj[cur] if n != prev]
            nxt = nxt[0] if nxt else adj[cur][0]
            prev, cur = cur, nxt
            if cur == start or cur in seen: break
        if len(loop) > 8: loops.append(np.array(loop))
    return loops

def rdp(p, eps):
    if len(p) < 3: return p
    s, e = p[0], p[-1]; d = e - s; n = np.hypot(*d)
    dist = np.abs(np.cross(d, p - s)) / n if n else np.hypot(*(p - s).T)
    k = int(np.argmax(dist))
    if dist[k] > eps:
        return np.vstack([rdp(p[:k + 1], eps)[:-1], rdp(p[k:], eps)])
    return np.array([s, e])

def simplify_closed(p, eps=0.6):
    k = int(np.argmax(np.hypot(*(p - p[0]).T)))     # split at the farthest point so both halves are open
    q = np.vstack([rdp(p[:k + 1], eps)[:-1], rdp(np.vstack([p[k:], p[:1]]), eps)[:-1]])
    return q

def to_d(p):
    p = (p - 2) / S                                  # undo padding + scale -> frame units
    m = (p + np.roll(p, -1, axis=0)) / 2             # smooth: quadratic curves through edge midpoints
    f = lambda v: f'{v[0]:.2f} {v[1]:.2f}'
    d = f'M{f(m[-1])}' + ''.join(f'Q{f(p[i])} {f(m[i])}' for i in range(len(p))) + 'Z'
    return d

def area(p): x, y = p[:, 0], p[:, 1]; return 0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
def inside(pt, poly):
    x, y = pt; xs, ys = poly[:, 0], poly[:, 1]; x2, y2 = np.roll(xs, -1), np.roll(ys, -1)
    cond = ((ys > y) != (y2 > y)) & (x < (x2 - xs) * (y - ys) / (y2 - ys + 1e-12) + xs)
    return bool(np.count_nonzero(cond) % 2)

def group(loops, min_area=30 * S * S / 16):
    loops = [l for l in loops if abs(area(l)) > min_area]
    depth = [sum(inside(l[0], o) for o in loops if o is not l) for l in loops]
    outers = [l for l, dp in zip(loops, depth) if dp % 2 == 0]
    holes = [l for l, dp in zip(loops, depth) if dp % 2 == 1]
    out = []
    for o in sorted(outers, key=lambda l: l[:, 0].min()):
        hs = [h for h in holes if inside(h[0], o)]
        parts = [to_d(simplify_closed(c)) for c in [o] + hs]
        out.append({'d': ''.join(parts), 'parts': parts, 'x': float((o[:, 0].min() - 2) / S)})
    return out

letters = group(contours(coverage(PLUM, ~in_apple)))
apple_g = group(contours(coverage(APPLE, in_apple)))
apple = {'d': ''.join(g['d'] for g in apple_g), 'parts': [p for g in apple_g for p in g['parts']]}
vb = [FRAME[2] - FRAME[0], FRAME[3] - FRAME[1]]
json.dump({'vb': vb, 'letters': letters, 'apple': apple}, io.open(os.path.join(HERE, 'assets', 'as-logo.json'), 'w'))
print('letters', len(letters), [round(l['x']) for l in letters], 'apple parts', len(apple['parts']),
      'bytes', sum(len(l['d']) for l in letters) + len(apple['d']))
