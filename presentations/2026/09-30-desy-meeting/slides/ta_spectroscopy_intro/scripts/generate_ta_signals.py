"""
generate_ta_signals.py
Transient absorption spectroscopy: the three signal types.

Top row: three energy-level diagrams (Ground State Bleach, Stimulated
Emission, Excited State Absorption), each showing the pump-excited
population and the probe transition responsible for that signal.
Bottom row: a schematic broadband TA spectrum (Delta-OD vs probe energy)
with each contribution shaded in its corresponding color and labelled.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Lato', 'Arial', 'Helvetica Neue', 'Helvetica', 'DejaVu Sans'],
})
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

BORDER  = "#44546A"   # dark blue-grey — ground state / axes
GSB_C   = "#7F7776"   # STONE          — ground state bleach
SE_C    = "#4298B5"   # SKY            — stimulated emission
ESA_C   = "#8C1515"   # SLAC red       — excited state absorption
PROBE_C = "#B8860B"   # muted gold     — probe photon arrows

fig = plt.figure(figsize=(13, 7.2))
fig.patch.set_facecolor("white")
gs = gridspec.GridSpec(2, 3, figure=fig, height_ratios=[1.05, 0.85],
                        hspace=0.5, wspace=0.35)

LEVEL_LW = 2.4
S0_Y, S1_Y, SN_Y = 0.0, 1.0, 1.85


def draw_levels(ax, show_sn=False):
    ax.hlines(S0_Y, 0.15, 0.85, color=BORDER, lw=LEVEL_LW, zorder=3)
    ax.hlines(S1_Y, 0.15, 0.85, color=BORDER, lw=LEVEL_LW, zorder=3)
    ax.text(0.06, S0_Y, r"$S_0$", fontsize=13, color=BORDER, ha='right', va='center')
    ax.text(0.06, S1_Y, r"$S_1$", fontsize=13, color=BORDER, ha='right', va='center')
    if show_sn:
        ax.hlines(SN_Y, 0.15, 0.85, color=BORDER, lw=LEVEL_LW, zorder=3)
        ax.text(0.06, SN_Y, r"$S_n$", fontsize=13, color=BORDER, ha='right', va='center')


def population_dots(ax, y, n, color, x0=0.30, x1=0.70, r=0.045):
    xs = np.linspace(x0, x1, n)
    for x in xs:
        ax.add_patch(mpatches.Circle((x, y), r, fc=color, ec='none', zorder=4))


def style_panel(ax, title, title_color):
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.35, 2.35)
    ax.axis('off')
    ax.set_title(title, fontsize=12.5, color=title_color, pad=10, fontweight='bold')


# ── Panel 1: Ground State Bleach ─────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
draw_levels(ax1)
population_dots(ax1, S0_Y, 2, BORDER)      # depleted ground population
population_dots(ax1, S1_Y, 3, "#E04F39")   # pump-excited population
ax1.annotate('', xy=(0.5, S1_Y - 0.08), xytext=(0.5, S0_Y + 0.08),
             arrowprops=dict(arrowstyle='->', color=PROBE_C, lw=2.4, mutation_scale=16),
             zorder=5)
ax1.text(0.62, (S0_Y + S1_Y) / 2, "probe", fontsize=9, color=PROBE_C,
         ha='left', va='center', style='italic')
ax1.text(0.5, S0_Y - 0.28, "fewer ground-state\nmolecules to absorb",
         fontsize=9, color=BORDER, ha='center', va='top')
style_panel(ax1, "Ground State Bleach", GSB_C)

# ── Panel 2: Stimulated Emission ─────────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
draw_levels(ax2)
population_dots(ax2, S1_Y, 3, "#E04F39")
ax2.annotate('', xy=(0.5, S0_Y + 0.08), xytext=(0.5, S1_Y - 0.08),
             arrowprops=dict(arrowstyle='->', color=SE_C, lw=2.4, mutation_scale=16),
             zorder=5)
ax2.annotate('', xy=(0.72, S0_Y + 0.30), xytext=(0.5, S1_Y - 0.08),
             arrowprops=dict(arrowstyle='->', color=PROBE_C, lw=1.6, mutation_scale=12,
                              linestyle=(0, (3, 2))),
             zorder=5)
ax2.text(0.78, S0_Y + 0.30, "probe-stimulated\nphoton (extra light)",
         fontsize=8.5, color=SE_C, ha='left', va='center')
ax2.text(0.5, S0_Y - 0.28, "probe stimulates\nemission down to $S_0$",
         fontsize=9, color=BORDER, ha='center', va='top')
style_panel(ax2, "Stimulated Emission", SE_C)

# ── Panel 3: Excited State Absorption ────────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
draw_levels(ax3, show_sn=True)
population_dots(ax3, S1_Y, 3, "#E04F39")
ax3.annotate('', xy=(0.5, SN_Y - 0.08), xytext=(0.5, S1_Y + 0.08),
             arrowprops=dict(arrowstyle='->', color=ESA_C, lw=2.4, mutation_scale=16),
             zorder=5)
ax3.text(0.62, (S1_Y + SN_Y) / 2, "probe", fontsize=9, color=PROBE_C,
         ha='left', va='center', style='italic')
ax3.text(0.5, S0_Y - 0.28, "new absorption from\nthe populated $S_1$ state",
         fontsize=9, color=BORDER, ha='center', va='top')
style_panel(ax3, "Excited State Absorption", ESA_C)

# ═══════════════════════════════════════════════════════════════════════════════
# Bottom: schematic broadband TA spectrum
# ═══════════════════════════════════════════════════════════════════════════════
axs = fig.add_subplot(gs[1, :])

x = np.linspace(0, 10, 2000)


def gauss(x, c, w, a):
    return a * np.exp(-0.5 * ((x - c) / w) ** 2)


esa = gauss(x, 2.0, 0.85, 1.0) + gauss(x, 7.6, 0.7, 0.55)
gsb = -gauss(x, 4.6, 0.55, 1.15)
se = -gauss(x, 5.9, 0.5, 0.85)
total = esa + gsb + se

axs.axhline(0, color=BORDER, lw=1.1)
axs.fill_between(x, esa, 0, where=(esa > 1e-3), color=ESA_C, alpha=0.28, lw=0)
axs.fill_between(x, gsb, 0, where=(gsb < -1e-3), color=GSB_C, alpha=0.35, lw=0)
axs.fill_between(x, se, 0, where=(se < -1e-3), color=SE_C, alpha=0.32, lw=0)
axs.plot(x, total, color="#222222", lw=2.2)

axs.text(2.0, 1.08, "ESA", fontsize=11, color=ESA_C, ha='center', va='bottom', fontweight='bold')
axs.text(7.6, 0.62, "ESA", fontsize=11, color=ESA_C, ha='center', va='bottom', fontweight='bold')
axs.text(4.6, -1.28, "GSB", fontsize=11, color=GSB_C, ha='center', va='top', fontweight='bold')
axs.text(5.9, -0.98, "SE", fontsize=11, color=SE_C, ha='center', va='top', fontweight='bold')

axs.set_xlim(0, 10)
axs.set_ylim(-1.55, 1.4)
axs.set_xlabel("Probe Energy (schematic)", fontsize=10.5, color=BORDER)
axs.set_ylabel(r"$\Delta$OD", fontsize=11, color=BORDER)
axs.set_xticks([])
axs.set_yticks([0])
axs.spines[['top', 'right']].set_visible(False)
axs.spines[['left', 'bottom']].set_color(BORDER)
axs.tick_params(colors=BORDER, labelsize=9)
axs.set_title("A Transient Absorption Spectrum Is a Sum of All Three",
              fontsize=11.5, color=BORDER, pad=10)

out = "figures/ta_signals.svg"
plt.savefig(out, format="svg", bbox_inches="tight", facecolor="white")
print(f"Saved -> {out}")
