"""
generate_spm_fiber_animation.py
Generates interactives/spm_fiber_animation.html -- an auto-playing animation
(not a manual slider, unlike the library's spm_interactive) showing:
  1. SPM spectral broadening co-timed with a Gaussian pulse travelling the
     length of a schematic fibre. Broadening freezes the moment the pulse
     reaches the fibre exit.
  2. The pulse then leaves the fibre travelling along its axis, hits mirror 1
     (on-axis with the fibre, tilted a few degrees clockwise), bounces up and
     back to mirror 2 (positioned just above the fibre exit), bounces again,
     then continues horizontally ("parallel to the bottom of the page") to
     the right as the final compressed pulse -- swapping to a progressively
     narrower, taller Gaussian at each bounce (see generate_pulse_gaussian.py).
The marker moves at one constant on-screen speed throughout (fibre + both
diagonal legs), computed from the fibre-phase timing.
Visual style (color/font/plot chrome) matches
slides/solitons/soliton_self_compression/interactives/soliton_interactive.html.
Same underlying SPM physics/parameters as
slides/nonlinear-optics/spm_interactive/scripts/spm_export.py.
"""
import json
import numpy as np

# ── Physical constants & pulse parameters (matches library spm_interactive) ──
c_nm_THz = 2.99792458e5    # nm·THz  (speed of light)
lambda0  = 1030.0           # nm  (Yb laser)
nu0_THz  = c_nm_THz / lambda0

tau_fwhm = 223.0            # fs  (pulse FWHM)
tau      = tau_fwhm / (2 * np.sqrt(np.log(2)))

B_max    = 5 * np.pi        # max B-integral (full fibre length)

N      = 8192
t      = np.linspace(-1200.0, 1200.0, N)
dt     = t[1] - t[0]

E0 = np.exp(-t**2 / (2 * tau**2))
I0 = E0**2

freq_rel_THz = np.fft.fftshift(np.fft.fftfreq(N, d=dt)) * 1e3
nu_THz       = nu0_THz + freq_rel_THz
lam_nm       = c_nm_THz / nu_THz

lam_min, lam_max = 900.0, 1200.0
mask     = (lam_nm >= lam_min) & (lam_nm <= lam_max)
lam_disp = np.sort(lam_nm[mask])
sort_idx = np.argsort(lam_nm[mask])


def compute_spectrum(I_norm: float) -> np.ndarray:
    B  = I_norm * B_max
    E  = E0 * np.exp(1j * B * I0)
    S  = np.abs(np.fft.fftshift(np.fft.fft(E))) ** 2
    S /= S.max()
    return S[mask][sort_idx]


# Position along the fibre, 0 (input) -> 1 (output), in step with B-integral.
N_STEPS  = 60
positions = np.linspace(0, 1, N_STEPS)
spectra   = [compute_spectrum(p).tolist() for p in positions]
x_data    = lam_disp.tolist()

# Unified horizontal coordinate, 0 (fibre input) -> 1 (final exit).
FIBER_END  = 0.55   # fibre occupies [0, FIBER_END]
MIRROR_1_X = 0.78   # on-axis with the fibre, further along
MIRROR_2_X = 0.58   # just to the right of (above) the fibre exit
EXIT_X     = 1.0

# Vertical pixel coordinates within #anim-canvas (bottom edge of the marker
# is placed here). Y_AXIS is the fibre's own centreline: the pulse travels
# on-axis from fibre input straight through to mirror 1, bounces up to
# mirror 2 (elevated, just above the fibre exit), then travels horizontally
# ("parallel to the bottom of the page") at that same elevated height.
Y_AXIS     = 101
Y_MIRROR_2 = 56
MIRROR_TILT_DEG = 8   # "a few degrees clockwise" from vertical, both mirrors

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Lato', sans-serif;
    background: white;
    padding: 6px 10px 4px;
  }}
  #plot {{ width: 100%; height: 250px; }}

  #anim-canvas {{
    position: relative; height: 118px;
    margin: 6px 28px 0;
  }}
  #pulse-marker {{
    position: absolute; top: 0; left: 0; width: 44px;
    margin-left: -22px;
    transition: left 66ms linear, top 66ms linear;
    z-index: 5;
  }}
  #fiber-track {{
    position: absolute; left: 0; top: 84px; height: 34px;
  }}
  .zone-label {{
    position: absolute; top: 122px; font-size: 12px; color: #44546A;
  }}
  #label-mirrors {{
    position: absolute; font-size: 12px; color: #44546A; white-space: nowrap;
  }}
  .fiber-cap {{
    position: absolute; top: 0; width: 18px; height: 34px;
    border-radius: 50%;
    background: #eef1f3; border: 1px solid #9aa7ae;
  }}
  .fiber-cap-left  {{ box-shadow: inset -2px 0 4px rgba(0,0,0,0.15); }}
  .fiber-cap-right {{ box-shadow: inset  2px 0 4px rgba(0,0,0,0.15); }}
  .fiber-body {{
    position: absolute; top: 0; height: 34px;
    background: #eef1f3; border-top: 1px solid #b7c0c6; border-bottom: 1px solid #b7c0c6;
  }}
  .mirror {{
    position: absolute; width: 8px; height: 44px;
    background: #dfe6ea; border: 1px solid #7c8a92; border-radius: 2px;
    margin-left: -4px; margin-top: -22px;
  }}
</style>
</head>
<body>
  <div id="plot"></div>
  <div id="anim-canvas">
    <img id="pulse-marker" src="../figures/pulse_gaussian.svg" alt="">
    <div id="fiber-track">
      <div class="fiber-cap fiber-cap-left"></div>
      <div class="fiber-body" id="fiber-body"></div>
      <div class="fiber-cap fiber-cap-right" id="fiber-cap-right"></div>
    </div>
    <div class="mirror" id="mirror-1"></div>
    <div class="mirror" id="mirror-2"></div>
    <span class="zone-label" style="left: 2px;">Fibre input</span>
    <span id="label-mirrors">Chirped Mirrors</span>
  </div>

<script>
var xData     = {json.dumps(x_data)};
var spectra   = {json.dumps(spectra)};
var positions = {json.dumps([round(float(p), 4) for p in positions])};
var nSteps    = positions.length;

var FIBER_END  = {FIBER_END};
var MIRROR_1_X = {MIRROR_1_X};
var MIRROR_2_X = {MIRROR_2_X};
var EXIT_X     = {EXIT_X};
var Y_AXIS     = {Y_AXIS};
var Y_MIRROR_2 = {Y_MIRROR_2};
var MIRROR_TILT_DEG = {MIRROR_TILT_DEG};

var STEP_MS = 66;
var FIBER_TIME_MS = (nSteps - 1) * STEP_MS;

var layout = {{
  xaxis: {{
    title: {{ text: "Wavelength (nm)", font: {{size: 12}} }},
    range: [900, 1200],
    showgrid: true, gridcolor: "#eeeeee",
    zeroline: false,
  }},
  yaxis: {{
    title: {{ text: "Intensity (norm.)", font: {{size: 11, color: "#8C1515"}} }},
    range: [-0.03, 1.15],
    showgrid: true, gridcolor: "#eeeeee",
    tickfont: {{size: 10, color: "#8C1515"}},
    fixedrange: true,
  }},
  annotations: [{{
    text: "SPM Broadening, then Mirror-Bounce Compression",
    x: 0.5, y: 1.1, xref: "paper", yref: "paper",
    showarrow: false,
    font: {{size: 13, color: "#44546A", family: "Lato, sans-serif"}},
  }}],
  margin: {{ t: 40, b: 50, l: 60, r: 20 }},
  paper_bgcolor: "white",
  plot_bgcolor: "white",
  showlegend: false,
}};

var plotReady = false;
try {{
  Plotly.newPlot("plot", [{{
    x: xData,
    y: spectra[0],
    mode: "lines",
    line: {{ color: "#8C1515", width: 1.8 }},
    fill: "tozeroy", fillcolor: "rgba(140,21,21,0.08)",
  }}], layout, {{ responsive: true, displayModeBar: false }});
  plotReady = true;
}} catch (e) {{ /* Plotly failed to load (e.g. offline) -- animation still runs */ }}

function restyleSpectrum(i) {{
  if (plotReady) Plotly.restyle("plot", {{ y: [spectra[i]] }}, [0]);
}}

var marker   = document.getElementById("pulse-marker");
var canvas   = document.getElementById("anim-canvas");
var fiberCap = document.getElementById("fiber-cap-right");
var fiberBody = document.getElementById("fiber-body");
var fiberTrack = document.getElementById("fiber-track");
var mirror1  = document.getElementById("mirror-1");
var mirror2  = document.getElementById("mirror-2");
var labelMirrors = document.getElementById("label-mirrors");

// Both mirrors tilt the same small amount clockwise from vertical -- for
// this fold geometry they come out parallel (mirror 1 redirects the
// on-axis beam up-and-back to mirror 2; mirror 2 redirects it to
// horizontal), same as two parallel mirrors in a real periscope fold.
mirror1.style.transform = "rotate(" + MIRROR_TILT_DEG + "deg)";
mirror2.style.transform = "rotate(" + MIRROR_TILT_DEG + "deg)";

function layoutTrack() {{
  var w = canvas.clientWidth;
  fiberTrack.style.width = (FIBER_END * w) + "px";
  fiberBody.style.left  = "9px";
  fiberBody.style.width = (FIBER_END * w - 18) + "px";
  fiberCap.style.left   = (FIBER_END * w - 18) + "px";
  mirror1.style.left = (MIRROR_1_X * w) + "px";
  mirror1.style.top  = Y_AXIS + "px";
  mirror2.style.left = (MIRROR_2_X * w) + "px";
  mirror2.style.top  = Y_MIRROR_2 + "px";
  labelMirrors.style.left = (MIRROR_1_X * w + 10) + "px";
  labelMirrors.style.top  = (Y_AXIS - 8) + "px";
}}

// yBottom is where the marker's bottom edge should sit (e.g. the fibre's
// own centreline while on-axis), not its top-left corner -- this keeps the
// Gaussian visually anchored to the beam axis as it changes height.
function setMarkerPos(xFrac, yBottom) {{
  var w = canvas.clientWidth;
  marker.style.left = (xFrac * w) + "px";
  marker.style.top  = (yBottom - marker.offsetHeight) + "px";
}}

// ── Phase 1: SPM broadening while traversing the fibre (discrete, precomputed) ──
var idx = 0;
var timer = null;

function setStep(i) {{
  idx = i;
  restyleSpectrum(idx);
  setMarkerPos(positions[idx] * FIBER_END, Y_AXIS);
}}

// running/cancelToken let a hidden slide stop cleanly: every in-flight
// timer/tween checks its captured token against the live one and aborts
// if a stop (or a fresh play) has invalidated it since it started.
var running = false;
var cancelToken = 0;

function stopAnimation() {{
  cancelToken++;
  if (timer) {{ clearInterval(timer); timer = null; }}
  running = false;
}}

function fiberStep(myToken) {{
  if (myToken !== cancelToken) return;
  if (idx >= nSteps - 1) {{
    clearInterval(timer);
    timer = null;
    startCompressor(myToken);
    return;
  }}
  setStep(idx + 1);
}}

// ── Phase 2: bounce off two tilted mirrors, narrowing at each bounce ──────
function tween(from, to, durationMs, myToken, onDone) {{
  var start = null;
  function frame(ts) {{
    if (myToken !== cancelToken) return;
    if (start === null) start = ts;
    var t = Math.min((ts - start) / durationMs, 1);
    setMarkerPos(from.x + (to.x - from.x) * t, from.y + (to.y - from.y) * t);
    if (t < 1) {{
      requestAnimationFrame(frame);
    }} else if (onDone) {{
      onDone();
    }}
  }}
  requestAnimationFrame(frame);
}}

function legDuration(from, to, speedPxPerMs, w) {{
  var dxPx = (to.x - from.x) * w;
  var dyPx = to.y - from.y;
  var distPx = Math.sqrt(dxPx * dxPx + dyPx * dyPx);
  return distPx / speedPxPerMs;
}}

function startCompressor(myToken) {{
  marker.style.transition = "none";
  var w = canvas.clientWidth;
  var speedPxPerMs = (FIBER_END * w) / FIBER_TIME_MS;   // constant on-screen speed

  // On-axis with the fibre until mirror 1; up to mirror 2 (just above the
  // fibre exit); then horizontal ("parallel to the bottom of the page").
  var pFiberExit = {{ x: FIBER_END,  y: Y_AXIS }};
  var pMirror1   = {{ x: MIRROR_1_X, y: Y_AXIS }};
  var pMirror2   = {{ x: MIRROR_2_X, y: Y_MIRROR_2 }};
  var pExit      = {{ x: EXIT_X,     y: Y_MIRROR_2 }};

  tween(pFiberExit, pMirror1, legDuration(pFiberExit, pMirror1, speedPxPerMs, w), myToken, function() {{
    marker.src = "../figures/pulse_gaussian_bounce1.svg";
    tween(pMirror1, pMirror2, legDuration(pMirror1, pMirror2, speedPxPerMs, w), myToken, function() {{
      marker.src = "../figures/pulse_gaussian_bounce2.svg";
      tween(pMirror2, pExit, legDuration(pMirror2, pExit, speedPxPerMs, w), myToken, function() {{
        // loop indefinitely while the slide stays visible
        running = false;
        play();
      }});
    }});
  }});
}}

function play() {{
  if (running) return;
  running = true;
  cancelToken++;
  var myToken = cancelToken;
  marker.style.transition = "left 66ms linear, top 66ms linear";
  marker.src = "../figures/pulse_gaussian.svg";
  setStep(0);
  timer = setInterval(function() {{ fiberStep(myToken); }}, STEP_MS);
}}

// Auto-play the moment this slide (the iframe's containing <section>)
// scrolls/transitions into view, and stop cleanly the moment it leaves --
// works cross-document since the iframe is same-origin with the deck.
var observer = new IntersectionObserver(function(entries) {{
  entries.forEach(function(entry) {{
    if (entry.isIntersecting) {{
      play();
    }} else {{
      stopAnimation();
    }}
  }});
}}, {{ threshold: 0.5 }});
observer.observe(document.documentElement);

window.addEventListener("resize", function() {{ layoutTrack(); setMarkerPos(positions[idx] * FIBER_END, Y_AXIS); }});
layoutTrack();
setStep(0);
</script>
</body>
</html>"""

out = "interactives/spm_fiber_animation.html"
with open(out, "w") as f:
    f.write(html)
print(f"Saved -> {out}")
