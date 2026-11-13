"""
crop_modes.py — composite the three key structural-mode decompositions from the
butadiene trajectory analysis into one figure (figures/mode_decompositions.png):

  1. rC1C2 - rC2C3 + rC3C4 (A)     [pyramidalization_vs_torsion, upper-left]
  2. C1 pyramidalization (deg)     [pyramidalization_vs_torsion, lower-left]
  3. C1-C2-C3-C4 dihedral (deg)    [distance_angle_dihedral, lower-right]

Panels are cropped from the two source analysis figures in data/, scaled to a
common height, and laid out side by side on white. Crop boxes include each
panel's title/axes/colorbar while excluding neighbours: the dihedral left edge
is 1185 px, in the clean gap between the middle column's colorbar labels
(<=1176 px) and the dihedral y-axis labels (>=1194 px).

Run with the slide folder as the working directory (build.py does this):
    python scripts/crop_modes.py
"""
from PIL import Image

PYR  = "data/pyramidalization_vs_torsion_analysis.png"   # 1300x1000, 2x2 grid
DIST = "data/distance_angle_dihedral_analysis.png"       # 1800x900,  2x3 grid
OUT  = "figures/mode_decompositions.png"

pyr  = Image.open(PYR).convert("RGB")
dist = Image.open(DIST).convert("RGB")

panels = [
    pyr.crop((0,     0,  655,  500)),   # rC1C2 - rC2C3 + rC3C4
    pyr.crop((0,   500,  655, 1000)),   # C1 pyramidalization
    dist.crop((1185, 455, 1800, 900)),  # C1-C2-C3-C4 dihedral
]

H, GAP = 470, 26
scaled = [p.resize((round(p.width * H / p.height), H), Image.LANCZOS) for p in panels]

W = sum(p.width for p in scaled) + GAP * (len(scaled) - 1)
canvas = Image.new("RGB", (W, H), "white")
x = 0
for p in scaled:
    canvas.paste(p, (x, 0))
    x += p.width + GAP
canvas.save(OUT)
print(f"Saved -> {OUT}  {canvas.size}")
