from datetime import date, timedelta
from itertools import combinations

start = date(2026, 4, 9)
TOTAL = 364

def eval_pattern(even, odd):
    arr = []
    for i in range(TOTAL):
        cycle = i // 14
        day = i % 14
        arr.append(even[day] if cycle % 2 == 0 else odd[day])

    a = sum(1 for x in arr if x == 0)
    r = sum(1 for x in arr if x == 1)
    o = sum(1 for x in arr if x is None)
    if (a, r, o) != (169, 169, 26):
        return None

    def max_streak(worker_id):
        longest = 0
        current = 0
        for w in arr:
            if w == worker_id:
                current += 1
                longest = max(longest, current)
            else:
                current = 0
        return longest

    def min_gap(worker_id):
        gaps = []
        in_gap = False
        gap_len = 0
        for w in arr:
            if w == worker_id:
                if in_gap and gap_len > 0:
                    gaps.append(gap_len)
                in_gap = False
                gap_len = 0
            else:
                in_gap = True
                gap_len += 1
        return min(gaps) if gaps else 99

    a_weekend = sum(1 for i, x in enumerate(arr) if x == 0 and (start + timedelta(days=i)).weekday() >= 5)
    r_weekend = sum(1 for i, x in enumerate(arr) if x == 1 and (start + timedelta(days=i)).weekday() >= 5)
    a_weekday = sum(1 for i, x in enumerate(arr) if x == 0 and (start + timedelta(days=i)).weekday() < 5)
    r_weekday = sum(1 for i, x in enumerate(arr) if x == 1 and (start + timedelta(days=i)).weekday() < 5)

    off_days = sorted({(start + timedelta(days=i)).strftime('%a') for i, x in enumerate(arr) if x is None})

    return {
        "mA": max_streak(0),
        "mR": max_streak(1),
        "gA": min_gap(0),
        "gR": min_gap(1),
        "wDiff": abs(a_weekend - r_weekend),
        "dDiff": abs(a_weekday - r_weekday),
        "aw": a_weekend,
        "rw": r_weekend,
        "ad": a_weekday,
        "rd": r_weekday,
        "offDays": off_days,
    }

candidates = []
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

            metrics = eval_pattern(even, odd)
            if not metrics:
                continue

            score = (
                max(metrics["mA"], metrics["mR"]),
                -min(metrics["gA"], metrics["gR"]),
                metrics["wDiff"] + metrics["dDiff"],
                metrics["wDiff"],
                -len(metrics["offDays"]),
            )
            candidates.append((score, metrics, even, odd, even_off, odd_off))

candidates.sort(key=lambda x: x[0])
print("candidates", len(candidates))
for rank, item in enumerate(candidates[:5], 1):
    score, m, even, odd, even_off, odd_off = item
    print("---", rank, "score", score, "offPos", even_off, odd_off, "offDays", m["offDays"])
    print("streak", m["mA"], m["mR"], "gap", m["gA"], m["gR"], "weekend", m["aw"], m["rw"], "weekday", m["ad"], m["rd"])
    print("even", even)
    print("odd ", odd)
