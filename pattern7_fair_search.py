from datetime import date, timedelta
from itertools import combinations

start = date(2026, 4, 9)
TOTAL = 364

best = None
best_rows = []

def metrics(even, odd):
    arr = []
    for i in range(TOTAL):
        c = i // 14
        d = i % 14
        arr.append(even[d] if c % 2 == 0 else odd[d])

    a = sum(1 for x in arr if x == 0)
    r = sum(1 for x in arr if x == 1)
    o = sum(1 for x in arr if x is None)
    if (a, r, o) != (169, 169, 26):
        return None

    aw = sum(1 for i, x in enumerate(arr) if x == 0 and (start + timedelta(days=i)).weekday() >= 5)
    rw = sum(1 for i, x in enumerate(arr) if x == 1 and (start + timedelta(days=i)).weekday() >= 5)
    ad = sum(1 for i, x in enumerate(arr) if x == 0 and (start + timedelta(days=i)).weekday() < 5)
    rd = sum(1 for i, x in enumerate(arr) if x == 1 and (start + timedelta(days=i)).weekday() < 5)

    if aw != rw or ad != rd:
        return None

    def max_streak(wid):
        m = cur = 0
        for w in arr:
            if w == wid:
                cur += 1
                if cur > m:
                    m = cur
            else:
                cur = 0
        return m

    def min_gap(wid):
        gaps = []
        in_gap = False
        gap_len = 0
        for w in arr:
            if w == wid:
                if in_gap and gap_len > 0:
                    gaps.append(gap_len)
                in_gap = False
                gap_len = 0
            else:
                in_gap = True
                gap_len += 1
        return min(gaps) if gaps else 99

    mA = max_streak(0)
    mR = max_streak(1)
    gA = min_gap(0)
    gR = min_gap(1)
    off_days = sorted({(start + timedelta(days=i)).strftime('%a') for i, x in enumerate(arr) if x is None})

    return {
        'mA': mA, 'mR': mR, 'gA': gA, 'gR': gR,
        'aw': aw, 'rw': rw, 'ad': ad, 'rd': rd,
        'offDays': off_days
    }

for even_off in range(14):
    even_slots = [i for i in range(14) if i != even_off]
    for odd_off in range(14):
        odd_slots = [i for i in range(14) if i != odd_off]
        for pick in combinations(range(13), 7):
            picks = set(pick)
            even = [None] * 14
            odd = [None] * 14
            even[even_off] = None
            odd[odd_off] = None
            for idx, pos in enumerate(even_slots):
                even[pos] = 0 if idx in picks else 1
            for idx, pos in enumerate(odd_slots):
                odd[pos] = 1 if idx in picks else 0

            m = metrics(even, odd)
            if not m:
                continue

            score = (max(m['mA'], m['mR']), -min(m['gA'], m['gR']))
            row = (score, m, even, odd, even_off, odd_off)
            if best is None or score < best:
                best = score
                best_rows = [row]
            elif score == best and len(best_rows) < 10:
                best_rows.append(row)

print('best_score', best)
print('count_tied', len(best_rows))
for i, row in enumerate(best_rows[:5], 1):
    score, m, even, odd, even_off, odd_off = row
    print('---', i, 'offPos', even_off, odd_off, 'offDays', m['offDays'])
    print('streak', m['mA'], m['mR'], 'gap', m['gA'], m['gR'], 'weekend', m['aw'], m['rw'], 'weekday', m['ad'], m['rd'])
    print('even', even)
    print('odd ', odd)
