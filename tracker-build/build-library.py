#!/usr/bin/env python3
"""Phase 2 — build the MASTER KSB reference library from the apprenticeship scraper.

Reads the scraper output (standards-for-calculator.json) and produces
ksb-library.json: every standard that has KSBs, normalised and keyed by ST code.
This is the shared reference the generator pulls per-client subsets from.
"""
import json, re, os

SCRAPER = r"C:\Users\omari\apprenticeship-scraper\output\standards-for-calculator.json"
OUT     = os.path.join(os.path.dirname(__file__), "ksb-library.json")

def norm_code(c):
    m = re.match(r'([A-Za-z]+)0*(\d+)', c or '')
    return (m.group(1).upper() + m.group(2)) if m else c

def num_part(c):
    m = re.match(r'[A-Za-z]+(\d+)', c or '')
    return int(m.group(1)) if m else 0

def dic(items):
    pairs = [(norm_code(i.get('code')), i.get('description', '').strip()) for i in (items or [])]
    pairs = [(c, d) for c, d in pairs if c and d]
    pairs.sort(key=lambda p: num_part(p[0]))
    return {c: d for c, d in pairs}

def build():
    data = json.load(open(SCRAPER, encoding='utf-8'))
    stds = data.get('standards', [])
    lib = {}
    skipped_no_code, skipped_no_ksb = 0, 0
    for s in stds:
        k = s.get('ksbs') or {}
        K, S, B = dic(k.get('knowledge')), dic(k.get('skills')), dic(k.get('behaviours'))
        if not (K or S):                      # no usable KSBs -> not in the library
            skipped_no_ksb += 1; continue
        code = (s.get('reference_number') or '').strip().upper()
        if not code:
            skipped_no_code += 1; continue
        name = (s.get('name') or '').strip()
        # match: learner programme text is tested against this (lowercased). Name OR ST code.
        # re.escape special chars (&, (, ), /, - etc.) but keep spaces literal for readability.
        match = re.escape(name.lower()).replace('\\ ', ' ') + '|' + re.escape(code.lower())
        lib[code] = {
            'name': name, 'code': code, 'level': s.get('level') or 0,
            'match': match, 'K': K, 'S': S, 'B': B,
        }
    out = {
        'source': 'apprenticeship-scraper standards-for-calculator.json (scraped ' +
                  str(data.get('scraped_at', '?')) + ')',
        'note': 'Master KSB reference library. Keyed by ST reference code. Codes normalised (K001->K1), numeric-sorted. The generator embeds only each client CONFIG.standards subset.',
        'count': len(lib),
        'standards': lib,
    }
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"library: {len(lib)} standards  (skipped {skipped_no_ksb} no-KSB, {skipped_no_code} no-code)")
    print(f"bytes: {os.path.getsize(OUT):,}")
    # spot-check the 3 Landmark standards
    for c in ('ST0384', 'ST0070', 'ST0795'):
        e = lib.get(c)
        print(f"  {c}: {e['name'] if e else 'MISSING'}  K{len(e['K']) if e else '-'} S{len(e['S']) if e else '-'} B{len(e['B']) if e else '-'}  match={e['match'] if e else '-'}")

if __name__ == '__main__':
    build()
