"""Regenerate the portfolio figure: python -m pip install reportlab==4.4.9
Then run python docs/figures/plot_recovery.py from any working directory.
The study verifier and both quick starts need no plotting dependencies.
"""
import json
from pathlib import Path

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String
from reportlab.lib.colors import HexColor

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "research/conv-mnist-upgrade/two-mac/results.json"
data = json.loads(DATA.read_text())["prepared"]
points = data["after_request_5_adaptive_minus_fixed17"]
plot = Drawing(540, 228)
ink, quiet, teal, grid = map(HexColor, ["#162e39", "#445d67", "#006e64", "#cbd7d8"])
plot.add(Rect(0, 0, 540, 228, fillColor=HexColor("#f7faf9"), strokeColor=None))


def label(x, y, value, size=12, align="start", bold=False, color=ink):
    plot.add(String(x, y, value, fontName="Helvetica-Bold" if bold else "Helvetica",
                    fontSize=size, textAnchor=align, fillColor=color))


def line(x1, y1, x2, y2, color, width=1):
    plot.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width))


def coord(ms):
    return 115 + (ms + 150) * 0.8


label(15, 201, "Did the key upgrade pay off?", 23, bold=True)
label(15, 176, "Two Macs  /  time since request 5  /  upgrade minus fixed 17", 14, color=quiet)
for tick in [-100, 0, 100, 200]:
    x = coord(tick)
    line(x, 53, x, 151, ink if tick == 0 else grid, 1.5 if tick == 0 else 0.7)
    label(x, 36, str(tick), 13, "middle", color=quiet)
for request, y in [("12", 130), ("24", 78)]:
    row = points[request]
    lo, hi = row["paired_bootstrap_95_ms"]
    mean = row["mean_ms"]
    label(15, y-5, f"Request {request}", 15, bold=True)
    line(coord(lo), y, coord(hi), y, teal, 3)
    for val in [lo, hi]:
        line(coord(val), y-6, coord(val), y+6, teal, 2)
    plot.add(Circle(coord(mean), y, 5, strokeColor=teal, fillColor=teal))
    label(453, y-5, f"{mean:+.0f} ms", 15, bold=True)
label(15, 11, f"Positive = slower. Paired means and 95% intervals over {data['verified_blocks']} key sets.", 14, color=quiet)
# renderSVG otherwise writes literal ellipses as the standalone title/description.
svg = renderSVG.drawToString(plot)
svg = svg.replace("<title>...</title>", "<title>Two-Mac key upgrade recovery</title>")
svg = svg.replace("<desc>...</desc>", "<desc>Elapsed time from request five: positive differences mean upgrading was slower. Points show means and bars show 95% paired bootstrap intervals.</desc>")
(HERE / "two-mac-recovery.svg").write_text(svg, encoding="utf-8")
