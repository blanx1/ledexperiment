# Measuring Planck's Constant with LEDs

Static website for an LED experiment that measures Planck's constant from the turn-on
voltages of red, yellow, green and blue LEDs, logged with an ESP32.

**Result:** h = (7.9 ± 0.6) × 10⁻³⁴ J·s (accepted value 6.626 × 10⁻³⁴ J·s, +19%).

## Contents

- `index.html`: the website
- `figures/`: I-V fits and V0 vs 1/λ plot
- `data/`: raw CSVs per LED and the fitted threshold voltages
- `code/`: ESP32 firmware, live logger, analysis script

## Reproducing the analysis

Requires Python with `numpy` and `matplotlib`.

```
cd data
python ../code/led_analysis.py
```

This regenerates `led_iv_fits.png`, `led_v0_vs_inv_lambda.png` and `led_v0_results.csv`
in the `data` folder. Copy the PNGs into `figures/` to update the site.

## Hosting on GitHub Pages

1. Create a new repository on GitHub and upload the contents of this folder
   (with `index.html` at the top level).
2. In the repository, go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to *Deploy from a branch*, pick `main`
   and `/ (root)`, and save.
4. The site appears at `https://<your-username>.github.io/<repository-name>/` after a minute or two.
