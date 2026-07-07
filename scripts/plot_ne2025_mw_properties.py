import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# Add pipeline directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / "pipeline"))

# Load matplotlib rc file
import matplotlib
rc_path = Path(__file__).resolve().parent.parent / "pipeline/matplotlibrc"
if rc_path.exists():
    matplotlib.rc_file(str(rc_path))

# Load data
data_path = Path(__file__).resolve().parent.parent / "docs/rse/specs/ne2025_mw_properties.csv"
df = pd.read_csv(data_path)

# Sort by absolute latitude for cleaner plotting/trends
df["abs_b"] = df["b_deg"].abs()
df = df.sort_values(by="abs_b")

# Create figure with 3 panels
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), sharex=True)

# Colors and marker styles
c_chime = "tab:orange"
c_dsa = "tab:blue"
c_dm = "tab:purple"

# 1. Left Panel: DM_MW vs |b|
ax0 = axes[0]
ax0.scatter(df["abs_b"], df["dm_mw_pc_cm3"], color=c_dm, s=60, edgecolor="k", zorder=3)
ax0.set_ylabel(r"$\mathrm{DM}_{\mathrm{MW}}$ ($\mathrm{pc\ cm}^{-3}$)")
ax0.grid(True, linestyle="--", alpha=0.5)

# 2. Middle Panel: tau vs |b|
ax1 = axes[1]
ax1.scatter(df["abs_b"], df["tau_chime_us"], color=c_chime, marker="o", s=60, edgecolor="k", label="CHIME (600 MHz)", zorder=3)
ax1.scatter(df["abs_b"], df["tau_dsa_us"], color=c_dsa, marker="s", s=60, edgecolor="k", label="DSA-110 (1.4 GHz)", zorder=3)
ax1.set_yscale("log")
ax1.set_ylabel(r"$\tau_{\mathrm{MW}}$ ($\mu\mathrm{s}$)")
ax1.legend(loc="upper right")
ax1.grid(True, linestyle="--", alpha=0.5, which="both")

# 3. Right Panel: bw vs |b|
ax2 = axes[2]
ax2.scatter(df["abs_b"], df["sbw_chime_khz"], color=c_chime, marker="o", s=60, edgecolor="k", label="CHIME (600 MHz)", zorder=3)
ax2.scatter(df["abs_b"], df["sbw_dsa_khz"], color=c_dsa, marker="s", s=60, edgecolor="k", label="DSA-110 (1.4 GHz)", zorder=3)
ax2.set_yscale("log")
ax2.set_ylabel(r"$\Delta\nu_{\mathrm{MW}}$ ($\mathrm{kHz}$)")
ax2.legend(loc="lower right")
ax2.grid(True, linestyle="--", alpha=0.5, which="both")

# Set common x-axis properties
for ax in axes:
    ax.set_xlabel(r"Galactic Latitude $|b|$ (deg)")
    ax.set_xlim(5, 50)

# Add text labels for bursts
texts0 = []
texts1 = []
texts2 = []
for idx, row in df.iterrows():
    name = row["burst"]
    disp_name = name.capitalize()
    
    texts0.append(ax0.text(row["abs_b"], row["dm_mw_pc_cm3"], f" {disp_name}", fontsize=10, zorder=4))
    texts1.append(ax1.text(row["abs_b"], row["tau_chime_us"], f" {disp_name}", fontsize=10, zorder=4))
    texts2.append(ax2.text(row["abs_b"], row["sbw_chime_khz"], f" {disp_name}", fontsize=10, zorder=4))

# Adjust text labels to avoid overlapping points/each other
try:
    from adjustText import adjust_text
    adjust_text(texts0, ax=ax0, arrowprops=dict(arrowstyle="->", color='gray', lw=0.5))
    adjust_text(texts1, ax=ax1, arrowprops=dict(arrowstyle="->", color='gray', lw=0.5))
    adjust_text(texts2, ax=ax2, arrowprops=dict(arrowstyle="->", color='gray', lw=0.5))
except ImportError:
    print("adjustText not available, using simple text alignment")

plt.tight_layout()
out_dir = Path(__file__).resolve().parent.parent / "figures"
out_dir.mkdir(exist_ok=True)

png_path = out_dir / "ne2025_mw_characterization.png"
pdf_path = out_dir / "ne2025_mw_characterization.pdf"

plt.savefig(png_path, dpi=300)
plt.savefig(pdf_path)
print(f"Figures saved to {png_path} and {pdf_path}")
