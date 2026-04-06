from datetime import date, timedelta
from pathlib import Path

START_DATE = date(2026, 4, 9)
TOTAL_DAYS = 364

# Proposed Schedule with Transition
TRANSITION_DAYS = 28
MANAGER_SEQUENCE84 = [
    0,0,0,0,1,1,1,1,0,0,0,1,1,1,0,0,0,0,1,1,1,1,0,0,0,1,1,1,
    1,0,0,0,1,1,1,1,0,0,0,None,None,0,0,1,1,1,0,0,0,0,1,1,1,1,0,
    0,0,1,1,1,0,0,0,0,1,1,1,None,0,0,0,1,1,1,0,0,0,None,1,1,1,1,
    None,None
]
FULL_EVEN = [1,None,0,0,0,1,1,0,0,1,1,1,0,0]
FULL_ODD = [0,1,1,1,None,0,0,1,1,0,0,0,1,1]

# Visual crossed-out dates to exclude from Randall's ICS only
RANDALL_EXCLUDE = {
    date(2026, 4, 13),
    date(2026, 4, 14),
    date(2026, 4, 15),
    date(2026, 4, 16),
    date(2026, 4, 20),
    date(2026, 4, 21),
    date(2026, 4, 22),
}


def worker_for_day(index: int):
    if index < TRANSITION_DAYS:
        return MANAGER_SEQUENCE84[index % len(MANAGER_SEQUENCE84)]
    cycle = index // 14
    day_in_cycle = index % 14
    return FULL_EVEN[day_in_cycle] if cycle % 2 == 0 else FULL_ODD[day_in_cycle]


def fmt_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def build_events(worker_id: int, calendar_name: str, exclude_dates=None):
    if exclude_dates is None:
        exclude_dates = set()

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Lvl2Calendar//Proposed Transition//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{calendar_name}",
    ]

    for i in range(TOTAL_DAYS):
        day = START_DATE + timedelta(days=i)
        worker = worker_for_day(i)
        if worker != worker_id:
            continue
        if day in exclude_dates:
            continue

        next_day = day + timedelta(days=1)
        person = "Aaron" if worker_id == 0 else "Randall"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{person.lower()}-{fmt_date(day)}@lvl2calendar",
            f"DTSTAMP:{fmt_date(START_DATE)}T000000Z",
            f"DTSTART;VALUE=DATE:{fmt_date(day)}",
            f"DTEND;VALUE=DATE:{fmt_date(next_day)}",
            f"SUMMARY:{person} Work Shift (Proposed Schedule with Transition)",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\n".join(lines) + "\n"


base = Path(__file__).parent
aaron_ics = base / "aaron_proposed_transition.ics"
randall_ics = base / "randall_proposed_transition.ics"

aaron_ics.write_text(build_events(0, "Aaron - Proposed Schedule with Transition"), encoding="utf-8")
randall_ics.write_text(
    build_events(1, "Randall - Proposed Schedule with Transition", exclude_dates=RANDALL_EXCLUDE),
    encoding="utf-8",
)

print(f"Wrote: {aaron_ics.name}")
print(f"Wrote: {randall_ics.name}")
