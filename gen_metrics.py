#!/usr/bin/env python3
"""Build github-metrics.svg from contrib2026.json.

Portrait card on purpose: the README floats it left and lets the intro text
sit beside it. If the card is shorter than that text the text wraps back
underneath and the two columns fall apart, which is what the 480x200 version
did. Every number here is derived from the contribution file, nothing is
hand-typed.
"""

import json
import os
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "github-metrics.svg")

W = 480
M = 20                      # side margin
INNER = W - M * 2

BG, PANEL = "#0d1117", "#161b22"
LABEL, VALUE, DIM = "#8b949e", "#e6edf3", "#6e7681"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def stats():
    raw = json.load(open(os.path.join(HERE, "contrib2026.json"), encoding="utf-8-sig"))
    counts = {d["date"]: d["count"] for d in raw}
    days = sorted(counts)

    streak = best_streak = 0
    for d in days:
        streak = streak + 1 if counts[d] > 0 else 0
        best_streak = max(best_streak, streak)

    busiest = max(counts.items(), key=lambda kv: kv[1])
    months = [0] * 12
    for d, n in counts.items():
        months[int(d[5:7]) - 1] += n

    weekdays = [0] * 7          # Sunday first, to match the heatmap rows
    for d, n in counts.items():
        y, m, dd = (int(p) for p in d.split("-"))
        weekdays[(date(y, m, dd).weekday() + 1) % 7] += n

    active = [d for d in days if counts[d] > 0]
    return {
        "counts": counts,
        "total": sum(counts.values()),
        "active": len(active),
        "streak": best_streak,
        "busiest": busiest,
        "months": months,
        "weekdays": weekdays,
        "first": active[0],
        "last": active[-1],
    }


def level(n):
    if n <= 0:
        return 0
    if n <= 3:
        return 1
    if n <= 8:
        return 2
    if n <= 20:
        return 3
    return 4


def txt(x, y, s, size=11, fill=LABEL, weight=None, anchor=None):
    w = f' font-weight="{weight}"' if weight else ""
    a = f' text-anchor="{anchor}"' if anchor else ""
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}"{w}{a}>{s}</text>')


def pretty(iso):
    y, m, d = (int(p) for p in iso.split("-"))
    return f"{MONTHS[m - 1].title()} {d}"


def build():
    s = stats()
    out, y = [], 0

    # ---- header
    out.append(txt(M, 33, "GitHub Metrics", 16, "url(#g)", "bold"))
    out.append(txt(W - M, 33, "2026", 12, DIM, anchor="end"))
    header_h = 52

    # ---- 2x2 stat grid
    peak_month = max(range(12), key=lambda i: s["months"][i])
    cells = [
        ("TOTAL CONTRIBUTIONS", f"{s['total']:,}"),
        ("ACTIVE DAYS", str(s["active"])),
        ("LONGEST STREAK", f"{s['streak']} days"),
        ("BUSIEST DAY", str(s["busiest"][1])),
        ("AVG PER ACTIVE DAY", f"{s['total'] / s['active']:.1f}"),
        ("BEST MONTH", f"{MONTHS[peak_month].title()} {s['months'][peak_month]}"),
    ]
    y = header_h + 34
    for i, (cap, val) in enumerate(cells):
        cxp = M + (i % 2) * (INNER / 2)
        cyp = y + (i // 2) * 62
        out.append(txt(cxp, cyp, cap, 10))
        out.append(txt(cxp, cyp + 25, val, 23, VALUE, "bold"))
    y = y + 2 * 62 + 62

    # ---- monthly bars
    out.append(txt(M, y, "MONTHLY ACTIVITY", 10))
    y += 12
    bar_h, peak = 160, max(s["months"]) or 1
    pitch = INNER / 12
    bw = pitch - 10
    for i, n in enumerate(s["months"]):
        h = max(2, round(n / peak * bar_h))
        bx = M + i * pitch + (pitch - bw) / 2
        by = y + bar_h - h
        fill = LEVELS[4] if n == peak else (LEVELS[2] if n else PANEL)
        out.append(f'<rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="{h}" '
                   f'rx="2" fill="{fill}"/>')
        out.append(txt(bx + bw / 2, y + bar_h + 14, MONTHS[i][0], 8,
                       DIM, anchor="middle"))
    y += bar_h + 44

    # ---- weekday distribution, drawn as a horizontal meter per day
    out.append(txt(M, y, "ACTIVITY BY WEEKDAY", 10))
    y += 14
    wpeak = max(s["weekdays"]) or 1
    track_x, track_w = M + 34, INNER - 34
    for i, n in enumerate(s["weekdays"]):
        row_y = y + i * 22
        out.append(txt(M, row_y + 9, "SMTWTFS"[i], 9, DIM))
        out.append(f'<rect x="{track_x}" y="{row_y}" width="{track_w:.1f}" '
                   f'height="11" rx="5.5" fill="{PANEL}"/>')
        fill_w = max(4, n / wpeak * track_w)
        out.append(f'<rect x="{track_x}" y="{row_y}" width="{fill_w:.1f}" '
                   f'height="11" rx="5.5" fill="{LEVELS[4] if n == wpeak else LEVELS[2]}"/>')
    y += 7 * 22 + 38

    # ---- full year heatmap
    out.append(txt(M, y, "CONTRIBUTION HEATMAP", 10))
    y += 12
    cols, rows = 53, 7
    cp = INNER / cols
    cell = cp - 1.6
    start = date(2026, 1, 1)
    origin = start - timedelta(days=(start.weekday() + 1) % 7)
    for i in range(cols * rows):
        day = origin + timedelta(days=i)
        if day.year != 2026:
            continue
        col, row = i // 7, i % 7
        n = s["counts"].get(day.isoformat(), 0)
        out.append(f'<rect x="{M + col * cp:.1f}" y="{y + row * cp:.1f}" '
                   f'width="{cell:.1f}" height="{cell:.1f}" rx="1.5" '
                   f'fill="{LEVELS[level(n)]}"/>')
    y += rows * cp + 20

    # ---- heatmap legend
    out.append(txt(M, y + 9, "Less", 9, DIM))
    for i, colour in enumerate(LEVELS):
        out.append(f'<rect x="{M + 30 + i * 13}" y="{y + 1}" width="10" '
                   f'height="10" rx="2" fill="{colour}"/>')
    out.append(txt(M + 30 + len(LEVELS) * 13 + 4, y + 9, "More", 9, DIM))
    y += 40

    # ---- footer
    out.append(txt(M, y, f"{pretty(s['first'])} - {pretty(s['last'])}, 2026", 10, DIM))
    out.append(txt(W - M, y, f"peak {s['busiest'][1]} on {pretty(s['busiest'][0])}",
                   10, DIM, anchor="end"))
    height = round(y + 30)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" '
        f'aria-label="GitHub metrics for 2026: {s["total"]} contributions across '
        f'{s["active"]} active days, longest streak {s["streak"]} days">',
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="#1A5276"/>'
        '<stop offset="100%" stop-color="#16A085"/></linearGradient></defs>',
        f'<rect width="100%" height="100%" rx="12" fill="{BG}"/>',
        f'<rect width="100%" height="{header_h}" rx="12" fill="{PANEL}"/>',
        f'<rect y="{header_h - 12}" width="100%" height="12" fill="{PANEL}"/>',
    ] + out + ["</svg>"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(svg))
    print(f"{OUT}\n  {W}x{height} | {s['total']:,} contributions | "
          f"{s['active']} active days | streak {s['streak']} | "
          f"{os.path.getsize(OUT) / 1024:.1f} KB")


if __name__ == "__main__":
    build()