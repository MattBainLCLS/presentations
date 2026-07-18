"""
generate_soliton_fiber_animation.py — animated variant of the library's
soliton_export.py: same real spectral/temporal propagation data (IFFT
reconstruction from soliton_propagation_hz.csv), but instead of a manual
"Propagation distance" slider, the plots auto-step and loop endlessly
(IntersectionObserver-driven, same pattern as spm_fiber_broadening), and a
Gaussian pulse marker travels the length of a schematic hollow-core fibre
in sync with the plots.

The marker's width/height are scaled directly from the *real* computed RMS
width of the actual simulated temporal profile at each z-step (not a guessed
narrowing schedule) -- scaleX = width(z)/width(0), scaleY = width(0)/width(z),
so the visual area (a stand-in for pulse energy) stays roughly constant as
it narrows, same energy-conserving idea as generate_pulse_gaussian.py.

Only the first 70 cm is looped (z_cm index 0-140 of 0-200): the real data
shows a clean, monotonic-ish narrowing to a minimum around z=27-30cm over
this range. Past the true compression point (~32.5cm using a half-max
width metric) the pulse undergoes soliton fission into a complex,
multi-peaked structure -- real physics, but a half-max width metric
degenerates there (returns ~the edges of the analysis window), so RMS
width is used throughout for a metric that stays meaningful and smooth
across the whole looped range instead of jumping discontinuously.
"""
import json
import numpy as np

# ── Load (identical to the library's soliton_export.py) ──────────────────────
data     = np.genfromtxt("data/soliton_propagation_hz.csv", delimiter=",")
freq_Hz  = data[:, 0]
spectra  = data[:, 1:]

wl_nm    = (3e8 / freq_Hz) * 1e9
N_f      = len(freq_Hz)
N_z      = spectra.shape[1]
z_cm     = np.linspace(0, 100, N_z)

df   = freq_Hz[1] - freq_Hz[0]
dt   = 1.0 / (N_f * df)
t_fs = (np.arange(N_f) - N_f // 2) * dt * 1e15

T_LIM  = 30.0
t_mask = np.abs(t_fs) <= T_LIM
t_disp = t_fs[t_mask]


def temporal(spec):
    A  = np.sqrt(np.maximum(spec, 0.0))
    Et = np.fft.fftshift(np.fft.ifft(A))
    return np.abs(Et) ** 2


def rms_width(intensity, t):
    """Real RMS (second-moment) width -- stays well-behaved for the
    complex multi-peaked profiles seen after the soliton fission point,
    unlike a half-max crossing width which degenerates there."""
    w = intensity / intensity.sum()
    mean_t = np.sum(t * w)
    var = np.sum(((t - mean_t) ** 2) * w)
    return float(np.sqrt(var))


# Only loop the first 50 cm -- see module docstring.
Z_MAX_CM = 70.0
N_LOOP = int(np.searchsorted(z_cm, Z_MAX_CM)) + 1

FISSION_LENGTH_CM = 55.0
FISSION_FRAC = FISSION_LENGTH_CM / Z_MAX_CM

spec_data, temp_data, width_fs = [], [], []
for i in range(N_LOOP):
    s = spectra[:, i]
    s_norm = s / s.max()
    spec_data.append([round(float(v), 6) for v in s_norm])

    It = temporal(s)
    It_disp = It[t_mask] / It.max()
    temp_data.append([round(float(v), 6) for v in It_disp])

    width_fs.append(round(rms_width(It_disp, t_disp), 4))

bundle = {
    "wl": [round(float(v), 3) for v in wl_nm],
    "t": [round(float(v), 4) for v in t_disp],
    "spectra": spec_data,
    "temporal": temp_data,
    "z_cm": [round(float(v), 2) for v in z_cm[:N_LOOP]],
    "width_fs": width_fs,
    "N_z": N_LOOP,
}
data_json = json.dumps(bundle, separators=(",", ":"))

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Lato', sans-serif;
    background: white;
    padding: 6px 10px 4px;
  }}
  #plot {{ width: 100%; height: 380px; }}

  #anim-canvas {{
    position: relative; height: 90px;
    margin: 4px 28px 0;
  }}
  #pulse-marker {{
    position: absolute; top: 0; left: 0; width: 44px;
    margin-left: -22px;
    z-index: 5;
    transform-origin: center bottom;
    transition: left 45ms linear;
  }}
  #fiber-track {{
    position: absolute; left: 0; top: 46px; height: 34px;
  }}
  .zone-label {{
    position: absolute; top: 84px; font-size: 12px; color: #44546A;
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
  #fission-marker {{
    position: absolute; top: 14px; height: 70px;
    border-left: 2px dashed #44546A;
    margin-left: -1px;
  }}
  #label-fission {{
    position: absolute; top: 0; font-size: 12px; color: #44546A; white-space: nowrap;
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
  <span class="zone-label" style="left: 2px;">Fibre input</span>
  <span class="zone-label" id="label-output" style="">Fibre output</span>
  <div id="fission-marker"></div>
  <span id="label-fission">Fission Length</span>
</div>

<script>
const D = {data_json};
const nSteps = D.N_z;

const traces = [
  {{
    x: D.wl, y: D.spectra[0],
    type: 'scatter', mode: 'lines',
    line: {{ color: '#8C1515', width: 1.8 }},
    fill: 'tozeroy', fillcolor: 'rgba(140,21,21,0.08)',
    xaxis: 'x', yaxis: 'y',
    hovertemplate: '%{{x:.1f}} nm  I=%{{y:.4f}}<extra></extra>',
  }},
  {{
    x: D.t, y: D.temporal[0],
    type: 'scatter', mode: 'lines',
    line: {{ color: '#8C1515', width: 1.8 }},
    fill: 'tozeroy', fillcolor: 'rgba(140,21,21,0.08)',
    xaxis: 'x2', yaxis: 'y2',
    hovertemplate: '%{{x:.1f}} fs  I=%{{y:.4f}}<extra></extra>',
  }},
];

const layout = {{
  annotations: [
    {{
      text: 'Spectral Domain',
      x: 0.5, y: 1.06, xref: 'x domain', yref: 'paper',
      showarrow: false,
      font: {{size: 13, color: '#44546A', family: 'Lato, sans-serif'}},
    }},
    {{
      text: 'Temporal Domain',
      x: 0.5, y: 1.06, xref: 'x2 domain', yref: 'paper',
      showarrow: false,
      font: {{size: 13, color: '#44546A', family: 'Lato, sans-serif'}},
    }},
  ],
  xaxis: {{
    domain: [0, 0.46],
    title: {{ text: 'Wavelength (nm)', font: {{size: 12}} }},
    showgrid: true, gridcolor: '#eeeeee',
    range: [200, 1400],
    zeroline: false,
  }},
  yaxis: {{
    title: {{ text: 'Intensity (norm.)', font: {{size: 11, color: '#8C1515'}} }},
    range: [-0.03, 1.15],
    showgrid: true, gridcolor: '#eeeeee',
    tickfont: {{size: 10, color: '#8C1515'}},
    fixedrange: true,
  }},
  xaxis2: {{
    domain: [0.54, 1.0],
    title: {{ text: 'Time (fs)', font: {{size: 12}} }},
    range: [-25, 25],
    showgrid: true, gridcolor: '#eeeeee',
    zeroline: true, zerolinecolor: '#cccccc',
  }},
  yaxis2: {{
    anchor: 'x2',
    title: {{ text: 'Intensity (norm.)', font: {{size: 11, color: '#8C1515'}} }},
    range: [-0.03, 1.15],
    showgrid: true, gridcolor: '#eeeeee',
    tickfont: {{size: 10, color: '#8C1515'}},
    fixedrange: true,
  }},
  margin: {{t: 55, b: 50, l: 65, r: 30}},
  paper_bgcolor: 'white',
  plot_bgcolor: 'white',
  showlegend: false,
}};

var plotReady = false;
try {{
  Plotly.newPlot('plot', traces, layout, {{ responsive: true, displayModeBar: false }});
  plotReady = true;
}} catch (e) {{ /* Plotly failed to load (e.g. offline) -- animation still runs */ }}

var marker     = document.getElementById('pulse-marker');
var canvas     = document.getElementById('anim-canvas');
var fiberCap   = document.getElementById('fiber-cap-right');
var fiberBody  = document.getElementById('fiber-body');
var fiberTrack = document.getElementById('fiber-track');
var labelOutput = document.getElementById('label-output');
var fissionMarker = document.getElementById('fission-marker');
var labelFission   = document.getElementById('label-fission');

var FISSION_FRAC = {FISSION_FRAC};   // {FISSION_LENGTH_CM:.0f} cm / {Z_MAX_CM:.0f} cm looped range

function layoutTrack() {{
  var w = canvas.clientWidth;
  fiberTrack.style.width = w + "px";
  fiberBody.style.left  = "9px";
  fiberBody.style.width = (w - 18) + "px";
  fiberCap.style.left   = (w - 18) + "px";
  labelOutput.style.left = (w - 78) + "px";
  fissionMarker.style.left = (FISSION_FRAC * w) + "px";
  labelFission.style.left  = (FISSION_FRAC * w + 6) + "px";
}}

var width0 = D.width_fs[0];
var Y_AXIS = 63;   // fibre-track centreline (top:46px + height:34px / 2)

function setStep(iz) {{
  if (plotReady) {{
    Plotly.restyle('plot', {{ y: [D.spectra[iz]] }}, [0]);
    Plotly.restyle('plot', {{ y: [D.temporal[iz]] }}, [1]);
  }}
  var w = canvas.clientWidth;
  var frac = iz / (nSteps - 1);
  marker.style.left = (frac * w) + "px";
  marker.style.top  = (Y_AXIS - marker.offsetHeight) + "px";

  // Real data drives the width: scaleX from the actual RMS-width ratio at
  // this step vs. the input, scaleY inverse so the marker's area (a
  // stand-in for pulse energy) stays roughly constant as it narrows.
  // transform-origin: center bottom (set in CSS) keeps the bottom edge
  // anchored to the fibre's centreline regardless of the scale factor.
  var ratio = D.width_fs[iz] / width0;
  marker.style.transform = "scale(" + ratio + ", " + (1 / ratio) + ")";
}}

// running/cancelToken: a hidden slide stops cleanly instead of continuing
// to tick or corrupting the next play-through (same pattern as
// spm_fiber_broadening).
var running = false;
var cancelToken = 0;
var timer = null;
var idx = 0;
var STEP_MS = 45;

function tick(myToken) {{
  if (myToken !== cancelToken) return;
  idx += 1;
  if (idx >= nSteps) idx = 0;   // loop
  setStep(idx);
}}

function play() {{
  if (running) return;
  running = true;
  cancelToken++;
  var myToken = cancelToken;
  idx = 0;
  setStep(0);
  timer = setInterval(function() {{ tick(myToken); }}, STEP_MS);
}}

function stopAnimation() {{
  cancelToken++;
  if (timer) {{ clearInterval(timer); timer = null; }}
  running = false;
}}

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

window.addEventListener('resize', function() {{ layoutTrack(); setStep(idx); }});
layoutTrack();
setStep(0);
</script>
</body>
</html>
"""

out = "interactives/soliton_interactive_animated.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

width_arr = np.array(width_fs)
min_i = int(width_arr.argmin())
print(f"Saved -> {out}")
print(f"  {N_LOOP} z-steps over 0-{Z_MAX_CM:.0f} cm")
print(f"  input width {width_fs[0]:.2f} fs -> min {width_fs[min_i]:.2f} fs at z={z_cm[min_i]:.1f} cm -> "
      f"width at {Z_MAX_CM:.0f}cm {width_fs[-1]:.2f} fs")
