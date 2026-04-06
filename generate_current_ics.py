import re
from datetime import date, timedelta
from pathlib import Path

base = Path(__file__).parent
html = (base / "index.html").read_text(encoding="utf-8")
match = re.search(r"const CURRENT_BASELINE_SEQUENCE364 = \[(.*?)\];", html, re.S)
values = [v.strip() for v in match.group(1).replace("\n", " ").split(",") if v.strip()]
sequence = [None if v == "null" else int(v) for v in values]
start = date(2026, 4, 9)


def make_ics(worker_id: int, name: str, file_name: str) -> None:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Lvl2Calendar//Current Schedule//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{name}",
    ]

    for index, worker in enumerate(sequence):
        if worker != worker_id:
            continue

        shift_date = start + timedelta(days=index)
        next_date = shift_date + timedelta(days=1)
        uid_name = name.lower().replace(" ", "-")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid_name}-{shift_date:%Y%m%d}@lvl2calendar",
            f"DTSTAMP:{start:%Y%m%d}T000000Z",
            f"DTSTART;VALUE=DATE:{shift_date:%Y%m%d}",
            f"DTEND;VALUE=DATE:{next_date:%Y%m%d}",
            f"SUMMARY:{name} Work Shift (Current Schedule)",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    (base / file_name).write_text("\n".join(lines) + "\n", encoding="utf-8")


make_ics(0, "Aaron", "aaron_current_schedule.ics")
make_ics(1, "Randall", "randall_current_schedule.ics")

print("Created aaron_current_schedule.ics")
print("Created randall_current_schedule.ics")
