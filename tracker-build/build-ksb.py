#!/usr/bin/env python3
"""Phase 2 — extract a per-client KSB subset from the master library.

Given a list of ST codes, emit the `const KSB_STANDARDS={...};` JS block to embed
in a client's tracker. Only the standards the client's cohort uses (never all 257
= 2.6MB). Used standalone and by the Phase 3 generator.

Usage:  python build-ksb.py ST0384 ST0070 ST0795
        python build-ksb.py --json ST0384          # object literal only
"""
import json, os, sys

LIB = os.path.join(os.path.dirname(__file__), "ksb-library.json")

def extract(codes):
    lib = json.load(open(LIB, encoding='utf-8'))['standards']
    out, missing = {}, []
    for c in codes:
        c = c.strip().upper()
        e = lib.get(c)
        if not e:
            missing.append(c); continue
        out[c] = {'name': e['name'], 'code': e['code'], 'match': e['match'],
                  'K': e['K'], 'S': e['S'], 'B': e['B']}
    if missing:
        sys.stderr.write("WARNING missing from library: " + ", ".join(missing) + "\n")
    return out

def emit_js(codes):
    obj = extract(codes)
    return "const KSB_STANDARDS=" + json.dumps(obj, ensure_ascii=False) + ";"

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--json']
    only_json = '--json' in sys.argv
    obj = extract(args)
    if only_json:
        print(json.dumps(obj, ensure_ascii=False))
    else:
        js = "const KSB_STANDARDS=" + json.dumps(obj, ensure_ascii=False) + ";"
        sys.stderr.write(f"extracted {len(obj)} standards, {len(js.encode('utf-8')):,} bytes\n")
        for k, v in obj.items():
            sys.stderr.write(f"  {k} {v['name']}: K{len(v['K'])} S{len(v['S'])} B{len(v['B'])}\n")
        print(js)
