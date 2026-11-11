"""
Planck's constant LED analysis, steps 1-3.

1. Wavelengths: typical values for each LED colour (no datasheet values given).
2. Threshold voltage V0 for each LED: clean the data, fit a straight line to the
   steep part of the I-V curve, extrapolate to I = 0.
3. Plot V0 against 1/lambda and fit a straight line.

Usage:  py led_analysis.py        (run from the folder holding the CSVs)
Writes: led_iv_fits.png, led_v0_vs_inv_lambda.png, led_v0_results.csv
"""

import csv

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---- Settings -------------------------------------------------------------
R_SENSE_KOHM = 0.100      # 100 ohm sense resistor, so anode V = V_led + 0.1 * I_mA
ADC_CLIP_V = 3.1          # ESP32 ADC tops out here; points with anode >= this are invalid
FIT_WINDOW_MA = (2.0, 3.5)  # same current window for every LED (blue's valid data ends ~4 mA)
ALT_WINDOWS_MA = [(2.0, 3.0), (2.5, 3.5), (2.0, 4.0)]  # sensitivity check

# Step 1: typical (inferred) peak wavelengths, in nm. Replace with datasheet values if you have them.
LEDS = [
    # name,    file,         wavelength_nm, plot colour
    ("Red",    "red.csv",    630, "#C62828"),
    ("Yellow", "yellow.csv", 590, "#C98A00"),
    ("Green",  "green.csv",  525, "#2E8B3E"),
    ("Blue",   "blue.csv",   470, "#1F5FBF"),
]


def load_clean(path):
    """Return (V, I) arrays with leftover pre-reset rows and clipped points removed."""
    with open(path, newline="") as f:
        rows = [(int(r["t_ms"]), float(r["V_led_V"]), float(r["I_mA"])) for r in csv.DictReader(f)]
    t = np.array([r[0] for r in rows])
    v = np.array([r[1] for r in rows])
    i = np.array([r[2] for r in rows])

    # Glitch rows: a single garbled serial line whose timestamp is out of sequence with BOTH
    # neighbours (e.g. "...,33792,..." arriving as "92,..."). Drop them before looking for resets.
    keep = np.ones(len(t), bool)
    for k in range(1, len(t) - 1):
        if t[k] < t[k - 1] and t[k + 1] >= t[k - 1]:
            keep[k] = False
    t, v, i = t[keep], v[keep], i[keep]
    n_glitch = int((~keep).sum())
    if n_glitch:
        print(f"{path}: dropped {n_glitch} garbled row(s)")

    # Leftover rows: anything before the last point where the ESP32 clock went backwards (reset).
    resets = np.where(np.diff(t) < 0)[0]
    start = resets[-1] + 1 if len(resets) else 0
    v, i = v[start:], i[start:]

    # Clipping: anode reading stuck at the ADC ceiling makes V_led wrong.
    ok = (v + R_SENSE_KOHM * i) < ADC_CLIP_V
    return v[ok], i[ok], start, int((~ok).sum())


def fit_v0(v, i, window):
    """Fit I = m V + b over the current window; return V0 = -b/m and its 1-sigma error."""
    sel = (i >= window[0]) & (i <= window[1])
    (m, b), cov = np.polyfit(v[sel], i[sel], 1, cov=True)
    v0 = -b / m
    # error propagation for -b/m
    dv0_dm, dv0_db = b / m**2, -1 / m
    sigma = np.sqrt(dv0_dm**2 * cov[0, 0] + dv0_db**2 * cov[1, 1] + 2 * dv0_dm * dv0_db * cov[0, 1])
    return v0, sigma, m, b, int(sel.sum())


results = []
fig, ax = plt.subplots(figsize=(8, 5.5))
for name, path, lam_nm, colour in LEDS:
    v, i, dropped_leftover, dropped_clipped = load_clean(path)
    n_in_window = int(((i >= FIT_WINDOW_MA[0]) & (i <= FIT_WINDOW_MA[1])).sum())
    if n_in_window < 10:
        print(f"SKIPPING {name}: only {n_in_window} points between {FIT_WINDOW_MA[0]} and "
              f"{FIT_WINDOW_MA[1]} mA (max current {i.max():.2f} mA) - re-record this LED.\n")
        continue
    v0, s_v0, m, b, n = fit_v0(v, i, FIT_WINDOW_MA)
    alts = [fit_v0(v, i, w)[0] for w in ALT_WINDOWS_MA]
    results.append(dict(name=name, colour=colour, lam_nm=lam_nm, v0=v0, s_v0=s_v0, slope=m, n_fit=n,
                        dropped_leftover=dropped_leftover, dropped_clipped=dropped_clipped,
                        alt_spread=max(alts) - min(alts), alts=alts))

    ax.plot(v, i, ".", ms=3, color=colour, alpha=0.35)
    vv = np.linspace(v0, (FIT_WINDOW_MA[1] + 1.0 - b) / m, 50)
    ax.plot(vv, m * vv + b, "-", lw=2, color=colour, label=f"{name} ({lam_nm} nm): V0 = {v0:.3f} V")
    label_y = 0.75 if len(results) % 2 == 0 else 0.25  # stagger so neighbouring labels don't collide
    ax.annotate(f"{name} {v0:.2f} V", (v0, 0), xytext=(v0 - 0.02, label_y), ha="right",
                fontsize=9, color="#333333")

ax.axhspan(*FIT_WINDOW_MA, color="#888888", alpha=0.08, lw=0)
ax.axhline(0, color="#999999", lw=0.8)
ax.axhline(1.42, color="#999999", lw=0.8, ls=":")
ax.text(0.02, 1.52, "ESP32 measurement floor (1.42 mA)", fontsize=8, color="#666666")
ax.text(0.02, FIT_WINDOW_MA[1] + 0.1, f"fit window {FIT_WINDOW_MA[0]}-{FIT_WINDOW_MA[1]} mA",
        fontsize=8, color="#666666")
ax.set_xlim(0, 3.0)
ax.set_ylim(-0.2, 6.6)
ax.set_xlabel("LED voltage (V)")
ax.set_ylabel("LED current (mA)")
ax.set_title("LED I-V curves with linear fits extrapolated to I = 0")
ax.grid(True, alpha=0.25)
ax.legend(loc="upper left", fontsize=9, frameon=False)
fig.tight_layout()
fig.savefig("led_iv_fits.png", dpi=150)

# ---- Step 3: V0 vs 1/lambda ------------------------------------------------
inv_lam = np.array([1 / (r["lam_nm"] * 1e-9) for r in results])  # 1/m
v0s = np.array([r["v0"] for r in results])
sig = np.array([r["s_v0"] for r in results])
(k, c0), cov = np.polyfit(inv_lam, v0s, 1, cov=True)
s_k, s_c0 = np.sqrt(np.diag(cov))
pred = k * inv_lam + c0
r2 = 1 - np.sum((v0s - pred) ** 2) / np.sum((v0s - v0s.mean()) ** 2)

fig2, ax2 = plt.subplots(figsize=(7, 5))
xx = np.linspace(inv_lam.min() * 0.97, inv_lam.max() * 1.03, 50)
ax2.plot(xx / 1e6, k * xx + c0, "-", lw=2, color="#555555",
         label=f"fit: V0 = ({k:.3e} V*m)(1/lambda) + ({c0:.3f} V)")
for r, x in zip(results, inv_lam):
    colour = r["colour"]
    ax2.errorbar(x / 1e6, r["v0"], yerr=r["s_v0"], fmt="o", ms=8, color=colour,
                 mec="white", mew=2, capsize=3)
    ax2.annotate(f'{r["name"]} ({r["lam_nm"]} nm)', (x / 1e6, r["v0"]), xytext=(8, -12),
                 textcoords="offset points", fontsize=9, color="#333333")
ax2.set_xlabel("1/wavelength (1/um)")
ax2.set_ylabel("Threshold voltage V0 (V)")
ax2.set_title("Threshold voltage vs 1/wavelength")
ax2.grid(True, alpha=0.25)
ax2.legend(loc="upper left", fontsize=9, frameon=False)
fig2.tight_layout()
fig2.savefig("led_v0_vs_inv_lambda.png", dpi=150)

with open("led_v0_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["LED", "wavelength_nm", "inv_lambda_per_m", "V0_V", "V0_sigma_V", "points_in_fit"])
    for r, x in zip(results, inv_lam):
        w.writerow([r["name"], r["lam_nm"], f"{x:.6e}", f"{r['v0']:.4f}", f"{r['s_v0']:.4f}", r["n_fit"]])

# ---- Report ----------------------------------------------------------------
print(f"Fit window: {FIT_WINDOW_MA[0]}-{FIT_WINDOW_MA[1]} mA\n")
print(f"{'LED':7}{'lambda':>8}{'V0 (V)':>10}{'+/-':>8}{'n':>5}{'dropped':>14}   V0 in alt windows {ALT_WINDOWS_MA}")
for r in results:
    dropped = f"{r['dropped_leftover']}L/{r['dropped_clipped']}C"
    alts = ", ".join(f"{a:.3f}" for a in r["alts"])
    print(f"{r['name']:7}{r['lam_nm']:>6}nm{r['v0']:>10.3f}{r['s_v0']:>8.3f}{r['n_fit']:>5}{dropped:>14}   {alts}")
print("\n(dropped: L = leftover rows before ESP32 reset, C = clipped points)")
print(f"\nV0 vs 1/lambda fit:  slope = {k:.4e} +/- {s_k:.1e} V*m,  intercept = {c0:.3f} +/- {s_c0:.3f} V,  R^2 = {r2:.4f}")
print("Saved led_iv_fits.png, led_v0_vs_inv_lambda.png, led_v0_results.csv")
