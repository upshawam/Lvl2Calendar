from datetime import date, timedelta
from itertools import product
import random

start = date(2026, 4, 9)
N = 364
weekend_idx = {2, 3, 9, 10}
nonweek = [i for i in range(14) if i not in weekend_idx]
all_dates = [start + timedelta(days=i) for i in range(N)]
all_dow = [d.weekday() for d in all_dates]


def build_workers(even, odd, overrides=None):
    workers = []
    for i in range(N):
        arr = even if ((i // 14) % 2 == 0) else odd
        w = arr[i % 14]
        if overrides and i in overrides:
            w = overrides[i]
        workers.append(w)
    return workers


def metrics(workers):
    a = r = o = 0
    a_wknd = r_wknd = 0
    max0 = max1 = cur0 = cur1 = 0

    for i, w in enumerate(workers):
        dow = all_dow[i]
        if w == 0:
            a += 1
            if dow >= 5:
                a_wknd += 1
            cur0 += 1
            cur1 = 0
        elif w == 1:
            r += 1
            if dow >= 5:
                r_wknd += 1
            cur1 += 1
            cur0 = 0
        else:
            o += 1
            cur0 = 0
            cur1 = 0
        if cur0 > max0:
            max0 = cur0
        if cur1 > max1:
            max1 = cur1

    def count_exact4(worker):
        count = 0
        streak = 0
        for w in workers + [worker]:
            if w != worker:
                streak += 1
            else:
                if streak == 4:
                    count += 1
                streak = 0
        return count

    paired = split = offwk = 0
    for k in range(0, N, 7):
        sat = workers[k + 2]
        sun = workers[k + 3]
        if sat is None or sun is None:
            offwk += 1
        elif sat == sun:
            paired += 1
        else:
            split += 1

    return {
        'totals': (a, r, o),
        'max': (max0, max1),
        'exact4': (count_exact4(0), count_exact4(1)),
        'weekend_counts': (a_wknd, r_wknd),
        'paired': (paired, split, offwk),
    }


def gen_arrays():
    arrays = []
    for null_pos in nonweek:
        others = [i for i in range(14) if i != null_pos and i not in weekend_idx]
        for wp1, wp2 in product([0, 1], [0, 1]):
            for bits in product([0, 1], repeat=len(others)):
                arr = [None] * 14
                arr[2] = arr[3] = wp1
                arr[9] = arr[10] = wp2
                arr[null_pos] = None
                for idx, b in zip(others, bits):
                    arr[idx] = b
                arrays.append(tuple(arr))
    return arrays


arrays = gen_arrays()
by_zero = {}
for arr in arrays:
    z = sum(1 for x in arr if x == 0)
    by_zero.setdefault(z, []).append(arr)

pairs = []
random.seed(7)
for z, evens in by_zero.items():
    target = 13 - z
    if target not in by_zero:
        continue
    odds = by_zero[target]
    for _ in range(500):
        pairs.append((random.choice(evens), random.choice(odds)))

best = []
for even, odd in pairs:
    null_days = []
    for i in range(N):
        arr = even if ((i // 14) % 2 == 0) else odd
        if arr[i % 14] is None:
            null_days.append(i)
    if len(null_days) != 26:
        continue

    local_best = None
    for _ in range(150):
        d1, d2 = random.sample(null_days, 2)
        for a, b in [(0, 1), (1, 0)]:
            overrides = {d1: a, d2: b}
            m = metrics(build_workers(even, odd, overrides))
            if m['totals'] != (170, 170, 24):
                continue
            diff = abs(m['exact4'][0] - m['exact4'][1])
            penalty = max(0, m['max'][0] - 3) + max(0, m['max'][1] - 3)
            score = (diff, penalty, m['paired'][1], m['exact4'][0] + m['exact4'][1])
            rec = (score, even, odd, overrides, m)
            if local_best is None or score < local_best[0]:
                local_best = rec

    if local_best is not None:
        best.append(local_best)

best.sort(key=lambda x: x[0])
seen = set()
chosen = []
for rec in best:
    key = (rec[1], rec[2])
    if key in seen:
        continue
    seen.add(key)
    chosen.append(rec)
    if len(chosen) == 10:
        break

print('CANDIDATES', len(best))
for i, (score, even, odd, overrides, m) in enumerate(chosen, 1):
    ov = {str(all_dates[k]): v for k, v in sorted(overrides.items())}
    print('---')
    print('rank', i, 'score', score)
    print('even', list(even))
    print('odd', list(odd))
    print('overrides', ov)
    print('metrics', m)
