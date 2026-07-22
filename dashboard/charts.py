"""Tiny dependency-free SVG line chart renderer — no JS/CDN required, so the
dashboard works fully offline and renders identically for screenshots/video."""
from __future__ import annotations

from greenledger.models import TrendPoint

WIDTH = 640
HEIGHT = 220
PAD_LEFT = 50
PAD_RIGHT = 20
PAD_TOP = 20
PAD_BOTTOM = 30

COLORS = {
    "electricity": "#f5a623",
    "natural_gas": "#4a90d9",
    "water": "#3fb27f",
}


def render_trend_svg(points: list[TrendPoint], utility_type: str) -> str:
    series = [p for p in points if p.utility_type == utility_type]
    if not series:
        return ""
    series.sort(key=lambda p: p.period_start)

    values = [p.usage for p in series]
    max_val = max(values) * 1.15 if values else 1
    min_val = 0

    plot_w = WIDTH - PAD_LEFT - PAD_RIGHT
    plot_h = HEIGHT - PAD_TOP - PAD_BOTTOM
    n = len(series)

    def x_for(i: int) -> float:
        return PAD_LEFT + (plot_w * i / max(1, n - 1)) if n > 1 else PAD_LEFT + plot_w / 2

    def y_for(v: float) -> float:
        span = max_val - min_val or 1
        return PAD_TOP + plot_h - (plot_h * (v - min_val) / span)

    color = COLORS.get(utility_type, "#888")
    path_points = " ".join(f"{x_for(i):.1f},{y_for(p.usage):.1f}" for i, p in enumerate(series))

    circles = []
    labels = []
    for i, p in enumerate(series):
        cx, cy = x_for(i), y_for(p.usage)
        spike = p.pct_vs_rolling_avg is not None and p.pct_vs_rolling_avg >= 15
        r = 5 if spike else 3.5
        fill = "#e0453c" if spike else color
        circles.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" />')
        labels.append(
            f'<text x="{cx:.1f}" y="{HEIGHT - 8}" font-size="10" text-anchor="middle" fill="#555">'
            f"{p.period_start:%b}</text>"
        )

    gridlines = []
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        y = PAD_TOP + plot_h * (1 - frac)
        val = max_val * frac
        gridlines.append(
            f'<line x1="{PAD_LEFT}" y1="{y:.1f}" x2="{WIDTH - PAD_RIGHT}" y2="{y:.1f}" '
            f'stroke="#e5e5e5" stroke-width="1" />'
            f'<text x="{PAD_LEFT - 8}" y="{y + 4:.1f}" font-size="10" text-anchor="end" fill="#888">'
            f"{val:.0f}</text>"
        )

    return f'''
<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" class="trend-chart">
  {''.join(gridlines)}
  <polyline points="{path_points}" fill="none" stroke="{color}" stroke-width="2.5" />
  {''.join(circles)}
  {''.join(labels)}
</svg>
'''.strip()
