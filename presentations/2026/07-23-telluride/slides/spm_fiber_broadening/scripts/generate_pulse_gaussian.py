"""
generate_pulse_gaussian.py
Generates three mathematically exact Gaussian pulse-envelope silhouettes
(filled area under exp(-x^2/2 sigma^2)), used as the travelling pulse marker
in the SPM fibre-broadening animation:
  figures/pulse_gaussian.svg          -- in-fibre width (sigma = 1.0)
  figures/pulse_gaussian_bounce1.svg  -- after mirror 1 (sigma = 0.55)
  figures/pulse_gaussian_bounce2.svg  -- after mirror 2, final (sigma = 0.30)
Peak height scales as 1/sigma (energy-conserving compression: a shorter
pulse of the same energy has higher peak intensity), all drawn on the same
fixed canvas so the three swap in cleanly at a fixed display size.
Edit this script (not the SVGs) to change the marker's appearance.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VARIANTS = [
    ("figures/pulse_gaussian.svg",         1.00),
    ("figures/pulse_gaussian_bounce1.svg", 0.55),
    ("figures/pulse_gaussian_bounce2.svg", 0.30),
]

X_RANGE = 3.4

for out, sigma in VARIANTS:
    amplitude = 1.0 / sigma
    x = np.linspace(-X_RANGE, X_RANGE, 400)
    y = amplitude * np.exp(-x**2 / (2 * sigma**2))

    fig, ax = plt.subplots(figsize=(1.4, 0.85))
    ax.fill_between(x, 0, y, color="#8C1515", alpha=0.92, linewidth=0)
    ax.set_xlim(-X_RANGE, X_RANGE)
    ax.set_ylim(0, amplitude * 1.05)
    ax.axis("off")
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    fig.savefig(out, transparent=True)
    plt.close(fig)
    print(f"Saved -> {out}  (sigma={sigma})")
