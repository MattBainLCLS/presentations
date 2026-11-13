"""
relabel_scattering.py — reproduce figures/CXI_Scattering.png from the pristine
paper schematic in data/CXI_Scattering_source.png (Stankus et al., Nat. Chem.
11, 716-721 (2019)), with the two beam labels rewritten to this experiment's
parameters:

  "9.5 keV X-ray / Probe pulse"  ->  "15 keV 5-6 fs X-ray / Probe pulse"
  "200 nm UV / Pump pulse"       ->  "210 nm 3 fs UV / Pump pulse"

The original labels are black centred Arial (~48 px) on white. We paint white
over the old text (verified to contain no beam/colorbar pixels) and redraw the
new two-line labels at the same font size, colour, line pitch (58 px) and
approximate position, nudged so the longer strings clear the colorbar (left of
x=1482) and the UV beam (right edge x~1403) and stay inside the frame.

Run with the slide folder as the working directory (build.py does this):
    python scripts/relabel_scattering.py
"""
from PIL import Image, ImageDraw, ImageFont

SRC = "data/CXI_Scattering_source.png"
OUT = "figures/CXI_Scattering.png"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_SIZE = 48          # matches the original label size
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)

im = Image.open(SRC).convert("RGBA")
draw = ImageDraw.Draw(im)
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

# Erase the original labels (boxes verified to be text-on-white only).
draw.rectangle((1598, 460, 1912, 575), fill=WHITE)   # 9.5 keV X-ray / Probe pulse
draw.rectangle((1412, 758, 1700, 878), fill=WHITE)   # 200 nm UV / Pump pulse


def centered_line(cx, cy, text):
    draw.text((cx, cy), text, font=font, fill=BLACK, anchor="mm")


# X-ray label: centre nudged left to 1715 so the longer line clears the frame.
centered_line(1715, 490, "15 keV 5-6 fs X-ray")
centered_line(1715, 548, "Probe pulse")

# UV label: centre 1590 keeps it clear of the UV beam on its left.
centered_line(1590, 786, "210 nm 3 fs UV")
centered_line(1590, 844, "Pump pulse")

# Blank the NMM molecular-structure inset (ball-and-stick, atom labels, "NMM"
# text and the dashed pointer). Two boxes preserve the CSPAD detector + text
# (left of x~712), the gas-jet cloud (above y~598) and the beams: the left box
# reaches higher to catch the "NMM" label (no cloud there); the right box stops
# at y=600 so the gas cloud is untouched.
draw.rectangle((742, 585, 900, 900), fill=WHITE)    # NMM label + left of molecule
draw.rectangle((895, 600, 1270, 900), fill=WHITE)   # molecule body, below the cloud

im.save(OUT)
print(f"Saved -> {OUT}")
