import os
import sys
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from multiprocessing import Pool

# Ignore all warnings to keep stdout clean
warnings.filterwarnings("ignore")

# Add pipeline directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / "pipeline"))

# Load matplotlib rc file
import matplotlib
rc_path = Path(__file__).resolve().parent.parent / "pipeline/matplotlibrc"
if rc_path.exists():
    matplotlib.rc_file(str(rc_path))

import healpy as hp
from mwprop.nemod.NE2025 import ne2025


def add_mollweide_degree_labels():
    label_style = dict(
        fontsize=8,
        color="0.18",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.65),
    )

    for lon in [0, 60, 120, 180, 240, 300]:
        hp.projtext(
            lon,
            -8,
            rf"${lon}^\circ$",
            lonlat=True,
            zorder=20,
            **label_style,
        )

    for lat in [-60, -30, 30, 60]:
        hp.projtext(
            0,
            lat,
            rf"${lat:+d}^\circ$",
            lonlat=True,
            zorder=20,
            **label_style,
        )


def run_pixel(args):
    gl, gb = args
    Dk, Dv, Du, Dd = ne2025(ldeg=gl, bdeg=gb, dmd=30.0, ndir=-1, classic=False, dmd_only=False, do_analysis=False, verbose=False)
    return Dv["DM"], Dv["TAU"], Dv["SBW"]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="NE2025 Milky Way all-sky characterization figure")
    parser.add_argument("--nside", type=int, default=8,
                        help="HEALPix nside for the all-sky maps (default: 8 => 7.3 deg pixels)")
    parser.add_argument("--nproc", type=int, default=os.cpu_count(),
                        help="Number of worker processes for the sightline sweep (default: all cores)")
    parser.add_argument("--xsize", type=int, default=None,
                        help="mollview raster width in px (default: 2000 for nside>8, else healpy default)")
    args = parser.parse_args()

    # 1. Precompute All-Sky Maps using HEALPix in parallel, with caching
    nside = args.nside
    npix = hp.nside2npix(nside)
    theta, phi = hp.pix2ang(nside, np.arange(npix))
    gls = np.degrees(phi)
    gbs = 90.0 - np.degrees(theta)

    # nside-keyed cache so different resolutions don't clobber each other
    suffix = "" if nside == 8 else f"_nside{nside}"
    cache_path = Path(__file__).resolve().parent / f"ne2025_allsky_cache{suffix}.npz"
    if cache_path.exists():
        print(f"Loading precomputed NE2025 all-sky maps from cache: {cache_path}")
        cache = np.load(cache_path)
        dm_map = cache["dm_map"]
        tau_map = cache["tau_map"]
        sbw_map = cache["sbw_map"]
    else:
        print(f"Precomputing NE2025 all-sky maps for {npix} pixels using {args.nproc} processes...")
        inputs = list(zip(gls, gbs))
        with Pool(args.nproc) as pool:
            results = pool.map(run_pixel, inputs)
        
        dm_map = np.array([r[0] for r in results])
        tau_map = np.array([r[1] for r in results])
        sbw_map = np.array([r[2] for r in results])
        
        np.savez_compressed(cache_path, dm_map=dm_map, tau_map=tau_map, sbw_map=sbw_map)
        print(f"Saved precomputed maps to cache: {cache_path}")

    # Raster width for mollview: bump for finer maps so the display doesn't undersample
    mollview_xsize = args.xsize if args.xsize is not None else (2000 if nside > 8 else 800)

    # Convert tau from ms to us for better scale
    tau_map_us = tau_map * 1000.0

    # 2. Load bursts data
    data_path = Path(__file__).resolve().parent.parent / "data/ne2025_mw_properties.csv"
    df = pd.read_csv(data_path)

    # Sort by absolute latitude for cleaner plotting/trends
    df["abs_b"] = df["b_deg"].abs()
    df_sorted = df.sort_values(by="abs_b")

    # Colors
    c_chime = "tab:orange"
    c_dsa = "tab:blue"
    c_dm = "tab:purple"

    # Create a 2x3 grid figure
    fig = plt.figure(figsize=(18, 11))

    # Set up healpy subplots in the top row
    # Left map: DM_MW
    hp.mollview(
        dm_map,
        fig=fig,
        sub=(2, 3, 1),
        title="",
        coord="G",
        cmap="Purples",
        cbar=True,
        notext=True,
        xsize=mollview_xsize,
        unit=r"$\mathrm{DM}_{\mathrm{MW}}\ (\mathrm{pc\ cm}^{-3})$"
    )
    hp.graticule(dpar=30, dmer=60, color="gray", lw=0.5, alpha=0.5)
    add_mollweide_degree_labels()
    hp.projscatter(
        df["l_deg"],
        df["b_deg"],
        lonlat=True,
        marker="*",
        s=40,
        color="yellow",
        edgecolor="black",
        zorder=10
    )

    # Middle map: log10(tau_1GHz_us)
    hp.mollview(
        np.log10(tau_map_us),
        fig=fig,
        sub=(2, 3, 2),
        title="",
        coord="G",
        cmap="Oranges",
        cbar=True,
        notext=True,
        xsize=mollview_xsize,
        unit=r"$\log_{10}(\tau_{1\mathrm{GHz}} / \mu\mathrm{s})$"
    )
    hp.graticule(dpar=30, dmer=60, color="gray", lw=0.5, alpha=0.5)
    add_mollweide_degree_labels()
    hp.projscatter(
        df["l_deg"],
        df["b_deg"],
        lonlat=True,
        marker="*",
        s=40,
        color="yellow",
        edgecolor="black",
        zorder=10
    )

    # Right map: log10(sbw_1GHz_MHz)
    hp.mollview(
        np.log10(sbw_map),
        fig=fig,
        sub=(2, 3, 3),
        title="",
        coord="G",
        cmap="Blues",
        cbar=True,
        notext=True,
        xsize=mollview_xsize,
        unit=r"$\log_{10}(\Delta\nu_{1\mathrm{GHz}} / \mathrm{MHz})$"
    )
    hp.graticule(dpar=30, dmer=60, color="gray", lw=0.5, alpha=0.5)
    add_mollweide_degree_labels()
    hp.projscatter(
        df["l_deg"],
        df["b_deg"],
        lonlat=True,
        marker="*",
        s=40,
        color="yellow",
        edgecolor="black",
        zorder=10
    )

    # Bottom row plots: standard matplotlib subplots
    ax0 = fig.add_subplot(2, 3, 4)
    ax0.scatter(df_sorted["abs_b"], df_sorted["dm_mw_pc_cm3"], color=c_dm, s=60, edgecolor="k", zorder=3)
    ax0.set_ylabel(r"$\mathrm{DM}_{\mathrm{MW}}$ ($\mathrm{pc\ cm}^{-3}$)")
    ax0.grid(True, linestyle="--", alpha=0.5)

    ax1 = fig.add_subplot(2, 3, 5)
    ax1.scatter(df_sorted["abs_b"], df_sorted["tau_chime_us"], color=c_chime, marker="o", s=60, edgecolor="k", label="CHIME (600 MHz)", zorder=3)
    ax1.scatter(df_sorted["abs_b"], df_sorted["tau_dsa_us"], color=c_dsa, marker="s", s=60, edgecolor="k", label="DSA-110 (1.4 GHz)", zorder=3)
    ax1.set_yscale("log")
    ax1.set_ylabel(r"$\tau_{\mathrm{MW}}$ ($\mu\mathrm{s}$)")
    ax1.legend(loc="upper right")
    ax1.grid(True, linestyle="--", alpha=0.5, which="both")

    ax2 = fig.add_subplot(2, 3, 6)
    ax2.scatter(df_sorted["abs_b"], df_sorted["sbw_chime_khz"], color=c_chime, marker="o", s=60, edgecolor="k", label="CHIME (600 MHz)", zorder=3)
    ax2.scatter(df_sorted["abs_b"], df_sorted["sbw_dsa_khz"], color=c_dsa, marker="s", s=60, edgecolor="k", label="DSA-110 (1.4 GHz)", zorder=3)
    ax2.set_yscale("log")
    ax2.set_ylabel(r"$\Delta\nu_{\mathrm{MW}}$ ($\mathrm{kHz}$)")
    ax2.legend(loc="lower right")
    ax2.grid(True, linestyle="--", alpha=0.5, which="both")

    # Set common bottom row properties
    for ax in [ax0, ax1, ax2]:
        ax.set_xlabel(r"Galactic Latitude $|b|$ (deg)")
        ax.set_xlim(5, 50)

    # Add text labels for bursts on bottom row plots
    texts0 = []
    texts1 = []
    texts2 = []
    for idx, row in df_sorted.iterrows():
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

    plt.tight_layout(h_pad=4.5, w_pad=2.0)
    out_dir = Path(__file__).resolve().parent.parent / "figures"
    out_dir.mkdir(exist_ok=True)

    png_path = out_dir / f"ne2025_mw_characterization{suffix}.png"
    pdf_path = out_dir / f"ne2025_mw_characterization{suffix}.pdf"

    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    print(f"Figures saved to {png_path} and {pdf_path}")
