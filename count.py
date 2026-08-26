# -*- coding: utf-8 -*-
"""Count the board from the actual data, not from memory."""
import io
import re
import collections

s = io.open('roadmap-ac9f3k.html', encoding='utf-8').read()
rows = re.findall(r"\{t:'((?:[^'\\]|\\.)*)',cat:'(\w+)',stage:'(\w+)'", s)

by_stage = collections.Counter(r[2] for r in rows)
print('TOTAL ROWS: %d' % len(rows))
for k, v in by_stage.most_common():
    print('  %-10s %d' % (k, v))

q = [r for r in rows if r[2] == 'queued']
print('\nQUEUED by category:')
for cat, n in collections.Counter(r[1] for r in q).most_common():
    print('  %-10s %d' % (cat, n))

print('\nQUEUED - levy app itself:')
for t, cat, st in q:
    if cat == 'levy':
        print('  - ' + t.replace("\\'", "'")[:92])

print('\nQUEUED - everything else:')
for t, cat, st in q:
    if cat != 'levy':
        print('  [%s] %s' % (cat, t.replace("\\'", "'")[:82]))

print('\nPARKED:')
for t, cat, st in rows:
    if st == 'parked':
        print('  [%s] %s' % (cat, t.replace("\\'", "'")[:82]))
