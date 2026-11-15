"""
generate_slide.py — writes xray_experiments_overview.html: two inline SVG
panels side by side.

Left : X-ray core-level spectroscopy (RIXS) orbital/energy-level cartoon.
Right: X-ray scattering as a structural diagnostic (plane wave -> molecule
       -> spherical wavelets from each atom -> interference -> detector).
Everything is generated from the numbers below; edit those, not the HTML.
"""
import math

OUT = "xray_experiments_overview.html"
XRAY   = "#B9A3FF"     # x-ray colour: same pale violet as the undulator slide
WAVE_SHIFT = 122        # rightward shift of those wavefronts: ~40% of the molecule-to-detector gap (~306 units)
WAVE_SCALE = 2 / 5     # radius scale of the big wavefronts between molecule and detector (1 = original)
XRAY_TXT = "#6F55C9"   # darker shade of it for text legibility on white
INK    = "#222"
BLUE   = "#1F6FD1"     # X-ray in
GREEN  = "#2E9B4F"     # X-ray out
GREY   = "#9AA3AB"
CARBON = "#3a3d42"

# ---------------------------------------------------------------- left ----
def half_arrow(x, y, up=True, color=INK):
    """Half-headed (harpoon) electron-spin arrow centred on (x, y)."""
    L, b = 20, 10
    if up:
        return (f'<path d="M{x} {y+L} L{x} {y-L} L{x-b} {y-L+b}" '
                f'fill="none" stroke="{color}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>')
    return (f'<path d="M{x} {y-L} L{x} {y+L} L{x+b} {y+L-b}" '
            f'fill="none" stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')

def spectroscopy_svg():
    IN_BULGE = 165         # control-point offset of the X-ray-in arc (smaller = flatter)
    W, H = 700, 540
    cx, half = 330, 62
    levels = [("LUMO", 90, False), ("HOMO", 190, True),
              ("HOMO−1", 290, True), ("Core", 470, True)]
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block" font-family="Lato, sans-serif">']
    s.append('<defs>'
             f'<marker id="ah_in" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{BLUE}"/></marker>'
             f'<marker id="ah_out" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{GREEN}"/></marker>'
             f'<marker id="ah_g" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{GREY}"/></marker>'
             '</defs>')
    # energy axis: grey arrow with a break aligned with the Core -> HOMO-1 gap
    ax, ybreak = 40, (290 + 470) / 2
    s.append(f'<line x1="{ax}" y1="{ybreak+14}" x2="{ax}" y2="500" stroke="{GREY}" stroke-width="5"/>')
    s.append(f'<line x1="{ax}" y1="{ybreak-14}" x2="{ax}" y2="68" stroke="{GREY}" stroke-width="5" marker-end="url(#ah_g)"/>')
    for dy in (-14, 14):   # the two slashes of the break
        s.append(f'<line x1="{ax-11}" y1="{ybreak+dy+6}" x2="{ax+11}" y2="{ybreak+dy-6}" stroke="{GREY}" stroke-width="3.5"/>')
    s.append(f'<text transform="translate({ax-14},{(90+290)/2}) rotate(-90)" text-anchor="middle" font-size="22" fill="{GREY}">Energy</text>')
    # orbitals
    for name, y, filled in levels:
        s.append(f'<line x1="{cx-half}" y1="{y}" x2="{cx+half}" y2="{y}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
        s.append(f'<text x="{cx}" y="{y+48}" text-anchor="middle" font-size="24" font-weight="700" fill="{INK}">{name}</text>')
        if filled:
            s.append(half_arrow(cx-18, y, True) + half_arrow(cx+18, y, False))
    # RIXS: Core -> LUMO (absorption) and HOMO -> Core (emission), decorative
    s.append(f'<path d="M{cx-half-6} 460 C {cx-IN_BULGE} 400, {cx-IN_BULGE} 160, {cx-half-6} 92" fill="none" stroke="{BLUE}" stroke-width="3.5" stroke-dasharray="11 8" marker-end="url(#ah_in)"/>')
    s.append(f'<path d="M{cx+half+6} 200 C {cx+140} 270, {cx+140} 400, {cx+half-6} 466" fill="none" stroke="{GREEN}" stroke-width="3.5" stroke-dasharray="11 8" marker-end="url(#ah_out)"/>')
    s.append(f'<text x="{cx-IN_BULGE-95}" y="262" font-size="22" font-weight="700" fill="{BLUE}">X-ray in</text>')
    s.append(f'<text x="{cx+140}" y="350" font-size="22" font-weight="700" fill="{GREEN}">X-ray out</text>')
    s.append('</svg>')
    return "\n".join(s)

# --------------------------------------------------------------- right ----
def scattering_svg():
    W, H = 720, 520
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block" font-family="Lato, sans-serif">']
    s.append('<style>.halo{paint-order:stroke;stroke:#fff;stroke-width:7px;stroke-linejoin:round}</style><defs>'
             '<radialGradient id="gC" cx="35%" cy="32%" r="75%"><stop offset="0" stop-color="#8b9097"/><stop offset="0.5" stop-color="#3a3d42"/><stop offset="1" stop-color="#14161a"/></radialGradient>'
             '<radialGradient id="gH" cx="35%" cy="32%" r="75%"><stop offset="0" stop-color="#ffffff"/><stop offset="0.6" stop-color="#e3e5e8"/><stop offset="1" stop-color="#9a9fa6"/></radialGradient>'
             '<clipPath id="clipW"><rect x="0" y="0" width="650" height="520"/></clipPath>'
             '<marker id="ah_k" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#111"/></marker>'
             '</defs>')
    # incoming plane wave
    s.append(f'<text x="22" y="62" font-size="27" font-weight="700" fill="{INK}">Hard X-rays</text>')
    s.append(f'<line x1="22" y1="84" x2="170" y2="84" stroke="#111" stroke-width="5" marker-end="url(#ah_k)"/>')
    for x in (30, 70, 110, 150):
        s.append(f'<line x1="{x}" y1="140" x2="{x}" y2="470" stroke="{XRAY}" stroke-width="5"/>')

    # trans-butadiene, zig-zag (x, y) carbons
    C = [(238, 185), (306, 263), (238, 345), (306, 423)]
    bonds = []
    def unit(a, b):
        dx, dy = b[0]-a[0], b[1]-a[1]; n = math.hypot(dx, dy); return dx/n, dy/n
    def rot(v, deg):
        t = math.radians(deg); return (v[0]*math.cos(t)-v[1]*math.sin(t), v[0]*math.sin(t)+v[1]*math.cos(t))
    H_LEN = 56
    Hs = []
    for i, c in enumerate(C):
        nb = [C[j] for j in (i-1, i+1) if 0 <= j < 4]
        if len(nb) == 2:  # internal carbon: H opposite the bisector of its C-C bonds
            u1, u2 = unit(c, nb[0]), unit(c, nb[1])
            bx, by = -(u1[0]+u2[0]), -(u1[1]+u2[1]); n = math.hypot(bx, by)
            Hs.append((c, (bx/n, by/n)))
        else:             # terminal carbon: two H at +-120 deg from the C-C bond
            u = unit(c, nb[0])
            for ang in (120, -120):
                Hs.append((c, rot(u, ang)))
    pairs = [(C[i], C[i+1]) for i in range(3)] + [(c, (c[0]+d[0]*H_LEN, c[1]+d[1]*H_LEN)) for c, d in Hs]
    # scattering wavelets: small rings on every atom + large interfering arcs from the carbons
    atoms = list(C) + [(c[0]+d[0]*H_LEN, c[1]+d[1]*H_LEN) for c, d in Hs]
    def arcs(cx, cy, radii, a0, a1, op, w):
        out = []
        for r in radii:
            x0, y0 = cx + r*math.cos(math.radians(a0)), cy + r*math.sin(math.radians(a0))
            x1, y1 = cx + r*math.cos(math.radians(a1)), cy + r*math.sin(math.radians(a1))
            out.append(f'<path d="M{x0:.1f} {y0:.1f} A{r} {r} 0 0 1 {x1:.1f} {y1:.1f}" fill="none" stroke="{XRAY}" stroke-width="{w}" stroke-opacity="{op}" stroke-linecap="round"/>')
        return out
    big = []
    for (x, y) in C:
        big += arcs(x + WAVE_SHIFT, y, [r * WAVE_SCALE for r in range(120, 330, 52)], -50, 50, 0.8, 3)
    s.append('<g clip-path="url(#clipW)">' + ''.join(big) + '</g>')
    # molecule on top of the waves (bonds, then atoms, back-to-front)
    for a, b in pairs:
        s.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#6d7279" stroke-width="9" stroke-linecap="round"/>')
    for x, y in atoms[len(C):]:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="19" fill="url(#gH)"/>')
    for x, y in C:
        s.append(f'<circle cx="{x}" cy="{y}" r="25" fill="url(#gC)"/>')
    # local scattering rings right at the atoms
    for x, y in atoms:
        s += arcs(x+8, y, (34, 44), -55, 55, 0.9, 3) if (x, y) in C else []
    s.append(f'<text x="215" y="62" font-size="25" font-weight="700" fill="{INK}" class="halo">Scattering from</text><text x="215" y="92" font-size="25" font-weight="700" fill="{INK}" class="halo">atoms</text>')

    # detector + structure-dependent pattern
    s.append('<rect x="676" y="30" width="30" height="470" fill="#111"/>')
    pts = []
    for i in range(0, 101):
        y = 40 + 450*i/100; dy = y-265
        I = 105*math.exp(-(dy/62)**2) + 32*math.exp(-(dy/140)**2)*(0.5+0.5*math.cos(dy/21)) + 6
        pts.append((668 - I, y))
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    s.append(f'<path d="{d}" fill="none" stroke="{XRAY}" stroke-width="4.5" stroke-linejoin="round"/>')
    s.append(f'<text x="525" y="60" class="halo" font-size="23" font-weight="700" fill="{INK}" text-anchor="middle">Structure-dependent</text>')
    s.append(f'<text x="525" y="88" class="halo" font-size="23" font-weight="700" fill="{INK}" text-anchor="middle">scattering</text>')
    s.append('</svg>')
    return "\n".join(s)

html = f"""        <section>
          <h3 style="margin: 0 0 0.3em;">Two Complementary X-ray Probes</h3>
          <div style="display: flex; gap: 1.2em; align-items: flex-start;">
            <div style="flex: 70 1 0; min-width: 0;">
              <div style="font-size: 0.62em; font-weight: 700; color: #8C1515; text-align: center; margin-bottom: 0.2em;">Core-level spectroscopy (RIXS)</div>
              {spectroscopy_svg()}
            </div>
            <div style="flex: 72 1 0; min-width: 0;">
              <div style="font-size: 0.62em; font-weight: 700; color: #8C1515; text-align: center; margin-bottom: 0.2em;">Scattering as a structural diagnostic</div>
              {scattering_svg()}
            </div>
          </div>
          <aside class="notes">
            <ul>
              <li>Placeholder: left, electronic structure via core-level spectroscopy (core to LUMO excitation, HOMO fills the core hole); right, nuclear structure via hard X-ray scattering.</li>
            </ul>
          </aside>
        </section>
"""
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", OUT)
