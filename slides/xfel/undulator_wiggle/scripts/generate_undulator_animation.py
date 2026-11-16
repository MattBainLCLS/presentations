"""
generate_undulator_animation.py — undulator wiggle + microbunching + SASE
field growth.

Real physics still *informs* two pieces here, each computed with real math:

1. The transverse electron trajectory x(z) = A*sin(2*pi*z/lambda_u) -- the
   exact first-order Lorentz-force result in a sinusoidal planar-undulator
   field.

2. The *shape* of the fully-bunched microbunch pattern: a short run of the
   1D SASE "universal scaling" equations (Bonifacio-Pellegrini-Narducci
   1984), stopped at its own power peak (saturation), gives a real,
   slightly irregular (not a hand-drawn perfect grid) clustered pattern
   for each microbunch slot. That final pattern is the *target* electrons
   blend toward; its micro-structure comes straight out of the simulation.

Everything about *when*/*how fast* that blend happens, and the radiated
field's envelope, is a small number of hand-authored, monotonic curves --
deliberately not driven by the live, step-by-step simulation output. An
earlier version derived the field directly from a live, frame-by-frame
superposition of particle positions; it was more "physically derived" but
unusable for teaching: real particle-level phases churn chaotically during
the low-gain regime, so the live field popped in abruptly and jittered in
ways that read as bugs, and its pacing/length couldn't be adjusted directly
-- changing a knob that should have shortened it did nothing, because the
dominant visual behavior was coming from noise, not from the knob. Physics
informs the *shapes* used below (the trajectory, the final bunch pattern);
it does not dictate the pacing -- that is chosen directly for a clean,
teachable loop that matches a plain hand-sketch: electrons spread -> dots
loosely gathering with a short, low wiggle -> dots in clear separate
bunches under a tall, short, bell-enveloped wavepacket, both moving
together.
"""
import json
import numpy as np

OUT = "interactives/undulator_animation.html"

# ---- undulator / wiggle geometry (unchanged from the validated MVP) ------
N_PERIODS  = 8
LAMBDA_U   = 0.65
AX         = 0.20
GAP_Y      = 0.62
THICK_Y    = 0.30
HALF_W     = 0.42
BLOCK_FRAC = 0.84
DEPTH_DEG  = 30
Z_TOTAL    = N_PERIODS * LAMBDA_U

ENTRANCE_LEN = 1.4
EXIT_LEN     = 0.9
Z_FULL       = ENTRANCE_LEN + Z_TOTAL + EXIT_LEN

LAMBDA_R_DISPLAY = LAMBDA_U / 2.0   # schematic microbunch/carrier spacing
N_SLOTS  = 5                        # odd -> integer multiples of LAMBDA_R, narrower
PER_SLOT = 36                       # train than before so it pairs with a short field
N_DISPLAY = N_SLOTS * PER_SLOT

# ---- 1D SASE universal-scaling simulation: run once, keep only the ------
# ---- fully-bunched final pattern's shape ---------------------------------
rng = np.random.default_rng(7)
N_SIM = 4000
dz = 0.01
nsteps = int(14.0 / dz)

theta = rng.uniform(0, 2 * np.pi, N_SIM)
p = np.zeros(N_SIM)
A = 0.0 + 0.0j
disp_idx = np.arange(N_DISPLAY)
theta_hist = np.empty((nsteps, N_DISPLAY))
P_hist = np.empty(nsteps)

for i in range(nsteps):
    b = np.mean(np.exp(-1j * theta))
    dtheta = p
    dp = -2 * np.real(A * np.exp(1j * theta))
    dA = -b
    theta = theta + dtheta * dz
    p = p + dp * dz
    A = A + dA * dz
    theta_hist[i] = theta[disp_idx]
    P_hist[i] = np.abs(A) ** 2

peak_i = int(np.argmax(P_hist))
theta_final = theta_hist[peak_i]   # (N_DISPLAY,) -- the fully-bunched pattern's phases

th = theta_final.reshape(N_SLOTS, PER_SLOT)
gmean = np.angle(np.mean(np.exp(1j * th), axis=1))
rel = (th - gmean[:, None] + np.pi) % (2 * np.pi) - np.pi
offs_raw = rel / (2 * np.pi) * LAMBDA_R_DISPLAY   # (N_SLOTS, PER_SLOT)

# Floor every slot to the same tight-but-still-countable width: below
# roughly one dot-diameter of screen-space spread, overlapping circles
# stop reading as "many particles, very close together" and start reading
# as "one blob, i.e. fewer particles" -- a rendering legibility limit, not
# a physics one. Individual particles' relative positions/signs within
# their slot are preserved (just uniformly rescaled), keeping some organic
# irregularity rather than a perfectly even synthetic grid.
SIGMA_FLOOR = 0.05
sigma_raw = np.sqrt(np.mean(offs_raw ** 2, axis=1))
rescale = SIGMA_FLOOR / np.clip(sigma_raw, 1e-9, None)
offs_final = offs_raw * rescale[:, None]

slot_span = (N_SLOTS - 1) / 2.0
slot_center = (np.arange(N_SLOTS) - slot_span) * LAMBDA_R_DISPLAY
periodic_offset = (offs_final + slot_center[:, None]).flatten()   # (N_DISPLAY,)

# Independent fully-random starting position for each displayed particle,
# spanning the same overall extent the periodic structure will eventually
# occupy -- this is what makes the entrance state one unstructured cloud
# (no slot grouping visible at all), rather than several already-separate
# groups that just individually tighten.
HALF_SPAN = slot_span * LAMBDA_R_DISPLAY + LAMBDA_R_DISPLAY / 2
uniform_init = np.random.default_rng(42).uniform(-HALF_SPAN, HALF_SPAN, N_DISPLAY)

# Both distributions are shifted so their *leading* edge sits at 0 (i.e.
# zj = zNow + offset never exceeds zNow): the field can only ever trail
# behind zNow (it can't show radiation ahead of where the beam has
# reached -- a real causality constraint, not a style choice), so if the
# electron cloud is left straddling zNow symmetrically, the half of it
# ahead of zNow structurally can never have a matching field there. Both
# now trail behind the same leading edge instead.
uniform_init = uniform_init - HALF_SPAN
periodic_offset = periodic_offset - slot_span * LAMBDA_R_DISPLAY

bundle = {
    "periodic_offset": [round(float(v), 4) for v in periodic_offset],
    "uniform_init": [round(float(v), 4) for v in uniform_init],
}
data_json = json.dumps(bundle, separators=(",", ":"))

print(f"saturation at local step {peak_i}/{nsteps}, peak P={P_hist[peak_i]:.3f}")

# ---- HTML/JS template -------------------------------------------------
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Lato', sans-serif;
    background: white;
    padding: 6px 12px 4px;
  }}
  #wrap {{ position: relative; }}
  canvas {{ display: block; width: 100%; }}
</style>
</head>
<body>
<div id="wrap">
  <canvas id="scene"></canvas>
</div>
<script>
var D = {data_json};

var N_PERIODS   = {N_PERIODS};
var LAMBDA_U    = {LAMBDA_U};
var AX          = {AX};
var GAP_Y       = {GAP_Y};
var THICK_Y     = {THICK_Y};
var HALF_W      = {HALF_W};
var BLOCK_FRAC  = {BLOCK_FRAC};
var DEPTH_DEG   = {DEPTH_DEG};
var Z_TOTAL     = {Z_TOTAL};        // undulator-local length only
var ENTRANCE_LEN= {ENTRANCE_LEN};
var EXIT_LEN    = {EXIT_LEN};
var Z_FULL      = {Z_FULL};         // full beamline shown: entrance + undulator + exit
var LAMBDA_R    = {LAMBDA_R_DISPLAY};
var BEAM_SPEED  = Z_FULL / 8.4;     // world units / second -> ~8.4s per pass

// Transverse wiggle only exists inside the undulator; straight before and
// after. N_PERIODS is an integer number of full periods, so AX*sin(...) is
// exactly 0 at both the entrance and exit boundary -- the straight and
// wiggling sections join with no artificial snap.
function wiggleX(zGlobal) {{
  var zu = zGlobal - ENTRANCE_LEN;
  if (zu < 0 || zu > Z_TOTAL) return 0;
  return AX * Math.sin(2 * Math.PI * zu / LAMBDA_U);
}}
// Undulator-local coordinate, clamped to [0, Z_TOTAL]: 0 before the
// entrance (nothing has happened yet), frozen at Z_TOTAL after the exit
// (bunching/field coast at their final state).
function undulatorLocal(zGlobal) {{
  var zu = zGlobal - ENTRANCE_LEN;
  return Math.max(0, Math.min(Z_TOTAL, zu));
}}

// Single hand-authored pacing curve driving *both* the electron blend and
// the field envelope, so they visibly move together. Smoothstep gives a
// zero-slope join at both ends -- no abrupt on/off snap -- and the
// start/end fractions are chosen directly for a clean, early-and-even
// buildup rather than the real simulation's own lethargy-heavy pacing.
function smoothstep(t) {{
  t = Math.max(0, Math.min(1, t));
  return t * t * (3 - 2 * t);
}}
var PROGRESS_START = 0.04, PROGRESS_END = 0.72;
function bunchProgress(zGlobal) {{
  var frac = undulatorLocal(zGlobal) / Z_TOTAL;
  return smoothstep((frac - PROGRESS_START) / (PROGRESS_END - PROGRESS_START));
}}
// Fixed world position where bunchFrac first becomes nonzero -- the
// field's spatial anchor point (see drawField below).
var Z_ORIGIN = ENTRANCE_LEN + PROGRESS_START * Z_TOTAL;

var COLOR_N_FRONT = '#8C1515', COLOR_N_TOP = '#B5453F', COLOR_N_END = darken('#8C1515', 0.68);
var COLOR_S_FRONT = '#2F4C68', COLOR_S_TOP = '#4F6E8C', COLOR_S_END = darken('#2F4C68', 0.68);
var COLOR_ELECTRON= '#FFC845';
var COLOR_AXIS    = '#AAB3BC';
var GLOW_RGB      = '185,163,255';   // SASE light (pale violet)

function darken(hex, factor) {{
  var r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
  r = Math.round(r * factor); g = Math.round(g * factor); b = Math.round(b * factor);
  return 'rgb(' + r + ',' + g + ',' + b + ')';
}}

var depthRad = DEPTH_DEG * Math.PI / 180;
var cosD = Math.cos(depthRad), sinD = Math.sin(depthRad);

var canvas = document.getElementById('scene');
var ctx = canvas.getContext('2d');
var bgCanvas = document.createElement('canvas');
var bgCtx = bgCanvas.getContext('2d');

var SCALE = 60, ORIGIN_X = 40, ORIGIN_Y = 260, DPR = 1;

function project(x, y, z) {{
  return {{
    sx: ORIGIN_X + z * SCALE + x * SCALE * cosD,
    sy: ORIGIN_Y - y * SCALE - x * SCALE * sinD
  }};
}}

function poly(c, pts, fill) {{
  c.beginPath();
  c.moveTo(pts[0].sx, pts[0].sy);
  for (var i = 1; i < pts.length; i++) c.lineTo(pts[i].sx, pts[i].sy);
  c.closePath();
  c.fillStyle = fill;
  c.fill();
}}

function drawBlock(c, zMin, zMax, yBase, frontColor, topColor, endColor) {{
  var yTop = yBase + THICK_Y;
  var xNear = -HALF_W, xFar = HALF_W;

  var front = [
    project(xNear, yBase, zMin), project(xNear, yBase, zMax),
    project(xNear, yTop,  zMax), project(xNear, yTop,  zMin)
  ];
  var top = [
    project(xNear, yTop, zMin), project(xNear, yTop, zMax),
    project(xFar,  yTop, zMax), project(xFar,  yTop, zMin)
  ];
  var end = [
    project(xNear, yBase, zMax), project(xFar, yBase, zMax),
    project(xFar,  yTop,  zMax), project(xNear, yTop,  zMax)
  ];
  poly(c, end, endColor);
  poly(c, top, topColor);
  poly(c, front, frontColor);
}}

function layout() {{
  DPR = window.devicePixelRatio || 1;
  var w = canvas.clientWidth || 800;
  var h = Math.round(w * 0.46);
  canvas.style.height = h + 'px';
  [canvas, bgCanvas].forEach(function (cv) {{
    cv.width = w * DPR; cv.height = h * DPR;
  }});
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  bgCtx.setTransform(DPR, 0, 0, DPR, 0, 0);

  var marginX = 40;
  var spanX = Z_FULL + 2 * HALF_W * cosD;
  SCALE = (w - 2 * marginX) / spanX;
  ORIGIN_X = marginX + HALF_W * SCALE * cosD;
  ORIGIN_Y = h / 2 + (GAP_Y + THICK_Y) * SCALE * 0.15;

  renderBackground();
}}

function renderBackground() {{
  bgCtx.clearRect(0, 0, bgCanvas.width, bgCanvas.height);

  bgCtx.strokeStyle = COLOR_AXIS;
  bgCtx.setLineDash([4, 4]);
  bgCtx.lineWidth = 1;
  var a0 = project(0, 0, 0), a1 = project(0, 0, Z_FULL);
  bgCtx.beginPath();
  bgCtx.moveTo(a0.sx, a0.sy); bgCtx.lineTo(a1.sx, a1.sy);
  bgCtx.stroke();
  bgCtx.setLineDash([]);

  var halfPeriods = N_PERIODS * 2;
  var halfLen = LAMBDA_U / 2;
  for (var n = 0; n < halfPeriods; n++) {{
    var zMin = ENTRANCE_LEN + n * halfLen;
    var zMax = zMin + halfLen * BLOCK_FRAC;
    var topIsN = (n % 2 === 0);
    drawBlock(bgCtx, zMin, zMax, GAP_Y,
      topIsN ? COLOR_N_FRONT : COLOR_S_FRONT, topIsN ? COLOR_N_TOP : COLOR_S_TOP, topIsN ? COLOR_N_END : COLOR_S_END);
    drawBlock(bgCtx, zMin, zMax, -GAP_Y - THICK_Y,
      topIsN ? COLOR_S_FRONT : COLOR_N_FRONT, topIsN ? COLOR_S_TOP : COLOR_N_TOP, topIsN ? COLOR_S_END : COLOR_N_END);
  }}
}}

var PERIODIC_OFFSET = D.periodic_offset;   // (N_DISPLAY,) fixed fully-bunched target
var UNIFORM_INIT = D.uniform_init;         // (N_DISPLAY,) fixed fully-random start
var N_DISPLAY = UNIFORM_INIT.length;

function lerp(a, b, f) {{ return a + (b - a) * f; }}

// Field window: anchored at Z_ORIGIN -- the fixed point where bunchFrac
// first turns on -- not at zNow. The right edge tracks zNow directly
// (the wave's own propagation speed, i.e. literal distance travelled
// since it first appeared, not the hand-authored amplitude pacing curve),
// so the window starts at exactly zero width at the same moment the
// amplitude does (synchronized -- no silent background growth) and then
// widens at a constant rate: new cycles genuinely appear at the leading
// (direction-of-travel) edge, like ripples spreading from a source sitting
// at the entrance. Once the span reaches WINDOW_WIDTH the left edge
// detaches from Z_ORIGIN and starts trailing at that fixed distance, so
// it becomes a fixed-width packet riding along rather than an
// ever-lengthening continuous wave. A raised-cosine (Hann) taper across
// whatever the current span is gives a bell shape at every stage,
// including while it's still widening. Only the *amplitude* (height)
// tracks bunchFrac (the separate, hand-authored S-curve); opacity/line-
// weight/glow are fixed and solid throughout. Carrier crests are phase-
// registered to LAMBDA_R, landing exactly on the microbunch slot centres
// -- the SASE coherence condition (bunches radiate in phase with the
// field that bunched them).
var WINDOW_WIDTH = 1.3;
var AMP_MAX = GAP_Y * 0.82;

function drawField(zNow, bunchFrac) {{
  if (bunchFrac <= 0.002) return;
  var amp = AMP_MAX * bunchFrac;
  var rightEdge = Math.min(zNow, Z_FULL);
  var leftEdge = Math.max(Z_ORIGIN, rightEdge - WINDOW_WIDTH);
  var span = rightEdge - leftEdge;
  if (span <= 0.001) return;

  ctx.save();
  ctx.strokeStyle = 'rgba(' + GLOW_RGB + ',0.9)';
  ctx.lineWidth = 2;
  ctx.shadowColor = 'rgba(' + GLOW_RGB + ',0.55)';
  ctx.shadowBlur = 8;
  ctx.beginPath();
  var N_PTS = 120;
  for (var i = 0; i <= N_PTS; i++) {{
    var z = leftEdge + span * i / N_PTS;
    var u = (z - leftEdge) / span;
    var bell = Math.sin(Math.PI * u);
    var env = bell * bell;
    // Field displacement is along x, the electrons' wiggle direction: a planar
    // undulator radiates linearly polarised light in the wiggle plane.
    var xf = amp * env * Math.cos(2 * Math.PI * (z - zNow) / LAMBDA_R);
    var pp = project(xf, 0, z);
    if (i === 0) ctx.moveTo(pp.sx, pp.sy); else ctx.lineTo(pp.sx, pp.sy);
  }}
  ctx.stroke();
  ctx.restore();
}}

function drawFrame(zNow) {{
  var w = canvas.clientWidth, h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(bgCanvas, 0, 0, w, h);

  var bunchFrac = bunchProgress(zNow);

  drawField(zNow, bunchFrac);

  ctx.fillStyle = COLOR_ELECTRON;
  ctx.globalAlpha = 0.72;
  for (var j = 0; j < N_DISPLAY; j++) {{
    var zj = zNow + lerp(UNIFORM_INIT[j], PERIODIC_OFFSET[j], bunchFrac);
    if (zj < 0 || zj > Z_FULL) continue;
    var xj = wiggleX(zj);
    var pe = project(xj, 0, zj);
    ctx.beginPath(); ctx.arc(pe.sx, pe.sy, 2.6, 0, 2 * Math.PI); ctx.fill();
  }}
  ctx.globalAlpha = 1;
}}

// running/cancelToken pattern: a hidden slide stops cleanly instead of
// continuing to tick or corrupting the next play-through.
var running = false;
var cancelToken = 0;
var t0 = null;

function frame(myToken, now) {{
  if (myToken !== cancelToken) return;
  if (t0 === null) t0 = now;
  var elapsed = (now - t0) / 1000;
  var zNow = (elapsed * BEAM_SPEED) % Z_FULL;
  drawFrame(zNow);
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

function stopAnimation() {{
  cancelToken++;
  running = false;
}}

var observer = new IntersectionObserver(function (entries) {{
  entries.forEach(function (entry) {{
    if (entry.isIntersecting) play();
    else stopAnimation();
  }});
}}, {{ threshold: 0.5 }});
observer.observe(document.documentElement);

window.addEventListener('resize', function () {{ layout(); drawFrame(0); }});
layout();
drawFrame(0);
</script>
</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"wrote {OUT}")
