"""
generate_linac_animation.py — electron acceleration in a disc-loaded RF
standing-wave structure. Cartoon style matched to xfel/undulator_wiggle, but viewed with the
camera turned only about the vertical axis so each disc projects to an
upright ellipse whose vertical axis is exactly the seam between halves.

Field: a pure standing wave (not travelling)
    E(z, t) = A sin(k (z - z0)) cos(w t),   k = pi / d
so the field's zero points sit exactly on the irises (discs) at z0 + n d,
with the oscillation peaking at each cell centre. The field is drawn only
between the first and last disc (zero at both ends).

Electron phasing: bunches move at v = w / k (one cell per half RF period)
and sit at z_e = z0 + d/2 + v t + m * 2d (shifted a quarter wavelength,
the same as the field). The field seen by each bunch is then
    E(z_e, t) = cos(w t) * cos(w t) = cos^2(w t) >= 0,
i.e. every bunch only ever sees the accelerating half of the RF: it sits
on the crest at each cell centre and passes through each disc exactly
when the whole field crosses zero. Bunches are spaced by a full RF
wavelength (2d) — a bunch one cell later would see -cos^2.

Disc occlusion trick: each disc is two C-shaped half-annuli split along
the vertical (x = 0) plane the wave lives in. The far half (x > 0) is
drawn behind the wave + electrons, the near half (x < 0) in front, so the
wave looks like it threads through the hole. Only the curved (outer and
inner) edges are stroked, so the two halves read as one complete disc.
"""
import json
import numpy as np

OUT = "interactives/linac_animation.html"

N_DISCS    = 8
CELL       = 1.0           # disc spacing d (= half RF wavelength)
R_OUT      = 0.62          # disc outer radius (R*X_FORESHORTEN < d/2 -> discs never overlap on screen)
R_HOLE     = 0.19          # iris (beam hole) radius
AMP        = 0.46          # RF field amplitude drawn (between hole and outer edge)
X_FORESHORTEN = 0.38       # camera turned about the vertical axis only: depth (x) maps to
                           # screen-horizontal, so discs are upright ellipses with a vertical seam
RF_PERIOD  = 2.2           # seconds per RF cycle
ENTRANCE   = 0.7           # drift length shown before first disc
EXIT       = 0.7           # drift length shown after last disc

N_PER_BUNCH = 26
rng = np.random.default_rng(3)
bunch = {
    "dz": [round(float(v), 4) for v in rng.normal(0, 0.055 * CELL, N_PER_BUNCH)],
    "dx": [round(float(v), 4) for v in rng.normal(0, 0.035, N_PER_BUNCH)],
    "dy": [round(float(v), 4) for v in rng.normal(0, 0.035, N_PER_BUNCH)],
}
data_json = json.dumps(bunch, separators=(",", ":"))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ height: 100%; }}
  body {{ font-family: 'Lato', sans-serif; background: white; padding: 0 8px;
         display: flex; align-items: center; }}   /* canvas centred in whatever height the iframe has */
  canvas {{ display: block; width: 100%; }}
</style>
</head>
<body>
<canvas id="scene"></canvas>
<script>
var B = {data_json};

var N_DISCS   = {N_DISCS};
var CELL      = {CELL};
var R_OUT     = {R_OUT};
var R_HOLE    = {R_HOLE};
var AMP       = {AMP};
var XF        = {X_FORESHORTEN};
var RF_PERIOD = {RF_PERIOD};
var ENTRANCE  = {ENTRANCE};
var EXIT      = {EXIT};

var Z0     = ENTRANCE;                          // first disc (field zero)
var Z_LAST = Z0 + (N_DISCS - 1) * CELL;         // last disc (field zero)
var F_MIN  = Z0, F_MAX = Z_LAST;               // field lives between first and last disc
var Z_FULL = Z_LAST + EXIT;
var K      = Math.PI / CELL;
var OMEGA  = 2 * Math.PI / RF_PERIOD;
var V_E    = OMEGA / K;                         // one cell per half RF period
var BUNCH_SPACING = 2 * CELL;                   // one RF wavelength

var COLOR_RF       = '#D62728';
var RF_GLOW        = 'rgba(214,39,40,0.45)';
var COLOR_DISC     = '#D0935F';
var COLOR_DISC_EDGE= '#7A4522';
var COLOR_ELECTRON = '#FFC845';
var COLOR_AXIS     = '#AAB3BC';


var canvas = document.getElementById('scene');
var ctx = canvas.getContext('2d');
var bgCanvas = document.createElement('canvas'), bgCtx = bgCanvas.getContext('2d');
var fgCanvas = document.createElement('canvas'), fgCtx = fgCanvas.getContext('2d');

var SCALE = 60, ORIGIN_X = 40, ORIGIN_Y = 200, DPR = 1;

function project(x, y, z) {{
  return {{
    sx: ORIGIN_X + z * SCALE + x * SCALE * XF,
    sy: ORIGIN_Y - y * SCALE
  }};
}}

// Point on a circle of radius r in the transverse (x, y) plane at z.
// phi = 0 points to +y (up); x = -r sin(phi), so phi in [0, pi] is the
// near (x < 0, front) half and phi in [pi, 2pi] the far (back) half.
function ringPt(r, phi, z) {{
  return project(-r * Math.sin(phi), r * Math.cos(phi), z);
}}

function arcPath(c, r, a0, a1, z, moveFirst) {{
  var N = 48;
  for (var i = 0; i <= N; i++) {{
    var p = ringPt(r, a0 + (a1 - a0) * i / N, z);
    if (i === 0 && moveFirst) c.moveTo(p.sx, p.sy); else c.lineTo(p.sx, p.sy);
  }}
}}

// One C-shaped half annulus between angles a0..a1. Filled as a closed
// shape, but only the outer and inner arcs are stroked — the straight
// seam edges are left unstroked so two halves read as one disc.
function drawHalfDisc(c, z, a0, a1) {{
  c.beginPath();
  arcPath(c, R_OUT, a0, a1, z, true);
  arcPath(c, R_HOLE, a1, a0, z, false);
  c.closePath();
  c.fillStyle = COLOR_DISC;
  c.fill();

  c.strokeStyle = COLOR_DISC_EDGE;
  c.lineWidth = 1.5;
  c.beginPath(); arcPath(c, R_OUT, a0, a1, z, true); c.stroke();
  c.beginPath(); arcPath(c, R_HOLE, a0, a1, z, true); c.stroke();
}}

function layout() {{
  DPR = window.devicePixelRatio || 1;
  var w = canvas.clientWidth || 800;
  var marginX = 6;
  SCALE = (w - 2 * marginX) / (Z_FULL + 2 * R_OUT * XF);
  // canvas is trimmed to the drawing: tallest feature (disc or wave) + small pad
  var h = Math.round(2 * Math.max(R_OUT, AMP) * SCALE + 16);
  canvas.style.height = h + 'px';
  [canvas, bgCanvas, fgCanvas].forEach(function (cv) {{
    cv.width = w * DPR; cv.height = h * DPR;
  }});
  [ctx, bgCtx, fgCtx].forEach(function (c) {{ c.setTransform(DPR, 0, 0, DPR, 0, 0); }});

  ORIGIN_X = marginX + R_OUT * XF * SCALE;
  ORIGIN_Y = h / 2;

  renderLayers();
}}

function renderLayers() {{
  bgCtx.clearRect(0, 0, bgCanvas.width, bgCanvas.height);
  fgCtx.clearRect(0, 0, fgCanvas.width, fgCanvas.height);

  // beam axis
  bgCtx.strokeStyle = COLOR_AXIS;
  bgCtx.setLineDash([4, 4]);
  bgCtx.lineWidth = 1;
  var a0 = project(0, 0, 0), a1 = project(0, 0, Z_FULL);
  bgCtx.beginPath(); bgCtx.moveTo(a0.sx, a0.sy); bgCtx.lineTo(a1.sx, a1.sy); bgCtx.stroke();
  bgCtx.setLineDash([]);

  // Back halves extend a hair past the seam so the front half fully
  // covers the join — no anti-aliasing hairline between the two fills.
  var EPS = 0.04;
  for (var n = 0; n < N_DISCS; n++) {{
    var z = Z0 + n * CELL;
    drawHalfDisc(bgCtx, z, Math.PI - EPS, 2 * Math.PI + EPS);
    drawHalfDisc(fgCtx, z, 0, Math.PI);
  }}
}}

function fieldAt(z, t) {{
  if (z < F_MIN || z > F_MAX) return 0;
  return AMP * Math.sin(K * (z - Z0)) * Math.cos(OMEGA * t);
}}

function drawField(t) {{
  ctx.save();
  ctx.strokeStyle = COLOR_RF;
  ctx.lineWidth = 2.4;
  ctx.shadowColor = RF_GLOW;
  ctx.shadowBlur = 8;
  ctx.beginPath();
  var N = 400;
  for (var i = 0; i <= N; i++) {{
    var z = F_MIN + (F_MAX - F_MIN) * i / N;
    var p = project(0, fieldAt(z, t), z);
    if (i === 0) ctx.moveTo(p.sx, p.sy); else ctx.lineTo(p.sx, p.sy);
  }}
  ctx.stroke();
  ctx.restore();
}}

function drawElectrons(t) {{
  ctx.fillStyle = COLOR_ELECTRON;
  ctx.strokeStyle = 'rgba(150,110,0,0.55)';
  ctx.lineWidth = 0.6;
  // Bunch centres: Z0 + CELL/2 + V_E t + m * BUNCH_SPACING for all integers m.
  var base = Z0 + CELL / 2 + V_E * t;
  var mMin = Math.floor((-0.5 - base) / BUNCH_SPACING);
  var mMax = Math.ceil((Z_FULL + 0.5 - base) / BUNCH_SPACING);
  for (var m = mMin; m <= mMax; m++) {{
    var zc = base + m * BUNCH_SPACING;
    for (var j = 0; j < B.dz.length; j++) {{
      var z = zc + B.dz[j];
      if (z < 0 || z > Z_FULL) continue;
      var p = project(B.dx[j], B.dy[j], z);
      ctx.beginPath(); ctx.arc(p.sx, p.sy, 2.6, 0, 2 * Math.PI);
      ctx.fill(); ctx.stroke();
    }}
  }}
}}

function drawFrame(t) {{
  var w = canvas.clientWidth, h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(bgCanvas, 0, 0, w, h);   // axis + far disc halves
  drawField(t);
  drawElectrons(t);
  ctx.drawImage(fgCanvas, 0, 0, w, h);   // near disc halves
}}

var cancelToken = 0, running = false, t0 = null, lastT = 0;

function frame(myToken, now) {{
  if (myToken !== cancelToken) return;
  if (t0 === null) t0 = now;
  lastT = (now - t0) / 1000;
  drawFrame(lastT);
  requestAnimationFrame(function (n) {{ frame(myToken, n); }});
}}

function play() {{
  if (running) return;
  running = true;
  cancelToken++;
  var myToken = cancelToken;
  t0 = null;
  requestAnimationFrame(function (n) {{ frame(myToken, n); }});
}}

function stopAnimation() {{ cancelToken++; running = false; }}

var observer = new IntersectionObserver(function (entries) {{
  entries.forEach(function (entry) {{
    if (entry.isIntersecting) play(); else stopAnimation();
  }});
}}, {{ threshold: 0.5 }});
observer.observe(document.documentElement);

// Re-fit whenever the iframe's size changes (e.g. slide laid out after load).
new ResizeObserver(function () {{ layout(); drawFrame(lastT); }}).observe(document.body);
window.addEventListener('resize', function () {{ layout(); drawFrame(lastT); }});
layout();
drawFrame(0);
</script>
</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"wrote {OUT}")
