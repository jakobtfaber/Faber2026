#!/usr/bin/env python
"""Legacy-table arithmetic recomputation + robustness audit for V3 energies.

This script deliberately audits the current mixed-legacy table only. It is
not the verifier for the adopted CHIME+DSA data-driven estimator: that verifier
must use the regenerated artifact's data-fluence statistical uncertainties and
must not read joint-fit c0/gamma posterior widths.

Independent of pipeline code (only reads its pinned artifacts):
  1. Re-derive E_iso for all 8 rows from the stored calibrated band integrals
     (I_*_jy_ms_hz), Planck18 D_L, and the (1+z) k-correction; compare against
     the stored E_iso_* columns.
  2. Re-derive the quoted uncertainty from the joint-JSON c0 posterior widths
     plus the BAND_SYS_DEX systematics; compare against E_iso_erg_err.
  3. Closed-form band integral vs dense numerical quadrature (math check).
  4. gamma_D-rail sensitivity, two ways:
     a. analytic: band-shape factor r(gamma) = <(nu/ref)^gamma> over the DSA
        band, gamma = -5 vs -10 (c0 anchored at mid-band);
     b. empirical: model-based I_DSA_jy_ms_hz (burst_energies.json) vs the
        data-driven per-channel on-pulse integral (dsa_fluences.csv), which
        uses NO fitted parameters.
  5. gamma_D pile-up census across all 12 joint fits (prior-bound check).

Run: python3 recompute_energies.py   (from anywhere; paths resolved relative
to this file: ../../pipeline)
"""

import csv
import json
from pathlib import Path

import numpy as np
from astropy.cosmology import Planck18
import astropy.units as u

HERE = Path(__file__).resolve().parent
PIPE = HERE.parents[1] / "pipeline"
BE = PIPE / "analysis" / "burst_energies"
JOINT = PIPE / "analysis" / "scattering-refit-2026-06" / "joint_json"
PROVENANCE = BE / "burst_energies.provenance.json"

JY_MS_HZ_TO_ERG_CM2 = 1e-29 * 1e7  # 1 Jy*ms*Hz = 1e-29 J/m^2 ; J->erg
BAND_SYS_DEX = {"C": 0.25, "D": 0.20}
# DSA band edges (configs/telescopes.yaml)
NU1_D, NU2_D = 1.31125e9, 1.49875e9
NU1_C, NU2_C = 0.40019e9, 0.80019e9

FAILURES = []


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def main():
    provenance = json.loads(PROVENANCE.read_text())
    lineages = set(provenance.get("c0gamma_pbf", {}).values())
    if lineages != {"mixed-legacy"}:
        print(
            "[FAIL] this audit accepts only the mixed-legacy artifact; "
            "use the data-driven verifier required by the V3 runbook"
        )
        raise SystemExit(1)

    rows = json.loads((BE / "burst_energies.json").read_text())
    print(f"mode: legacy arithmetic audit ({provenance['git_sha']})")
    print(f"loaded {len(rows)} rows from burst_energies.json\n")

    # ---- 1+2: E_iso and error re-derivation ------------------------------
    print("== E_iso re-derivation (Planck18, k-corrected) ==")
    for r in rows:
        z = r["z"]
        d_l_m = Planck18.luminosity_distance(z).to(u.m).value
        d_l_mpc = Planck18.luminosity_distance(z).to(u.Mpc).value
        # D_L check
        check(
            f"{r['burst']}: D_L",
            abs(d_l_mpc - r["D_L_Mpc"]) / r["D_L_Mpc"] < 1e-6,
            f"{d_l_mpc:.2f} vs stored {r['D_L_Mpc']:.2f} Mpc",
        )
        pref = 4.0 * np.pi * d_l_m**2 * JY_MS_HZ_TO_ERG_CM2
        e_c = pref * r["I_CHIME_jy_ms_hz"] / (1 + z)
        e_d = pref * r["I_DSA_jy_ms_hz"] / (1 + z)
        check(
            f"{r['burst']}: E_C + E_D vs stored",
            abs(e_c - r["E_iso_CHIME_erg"]) / r["E_iso_CHIME_erg"] < 1e-9
            and abs(e_d - r["E_iso_DSA_erg"]) / r["E_iso_DSA_erg"] < 1e-9
            and abs((e_c + e_d) - r["E_iso_erg"]) / r["E_iso_erg"] < 1e-9,
            f"E_iso = {e_c + e_d:.3e} erg",
        )
        check(
            f"{r['burst']}: k-correction identity",
            abs(r["E_iso_erg_no_kcorr"] - r["E_iso_erg"] * (1 + z)) / r["E_iso_erg_no_kcorr"]
            < 1e-9,
        )
        # error re-derivation from joint JSON c0 widths
        pct = json.loads(
            (JOINT / f"{'johndoeII' if r['burst']=='johndoeii' else r['burst']}_joint_fit.json").read_text()
        )["percentiles"]
        err2 = 0.0
        for tag, e_band in (("C", e_c), ("D", e_d)):
            e = pct[f"c0_{tag}"]
            f_stat = 0.5 * (e["err_plus"] + e["err_minus"]) / e["median"]
            f_sys = np.log(10.0) * BAND_SYS_DEX[tag]
            err2 += (e_band * np.hypot(f_stat, f_sys)) ** 2
        check(
            f"{r['burst']}: error propagation",
            abs(np.sqrt(err2) - r["E_iso_erg_err"]) / r["E_iso_erg_err"] < 1e-6,
            f"{np.sqrt(err2):.3e} vs stored {r['E_iso_erg_err']:.3e}",
        )

    # ---- 3: closed-form vs quadrature ------------------------------------
    print("\n== band-integral math check ==")
    def band_integral(c0, g, ref, n1, n2):
        if abs(g + 1.0) < 1e-9:
            return c0 * ref * np.log(n2 / n1)
        gg = g + 1.0
        return c0 * ref / gg * ((n2 / ref) ** gg - (n1 / ref) ** gg)

    ok = True
    for c0, g in ((2.0, -3.4), (0.18, -4.95), (1.0, -1.0), (3.0, 0.5), (0.5, -9.9)):
        nu = np.linspace(NU1_D, NU2_D, 400_001)
        num = np.trapezoid(c0 * (nu / 1.405e9) ** g, nu)
        ana = band_integral(c0, g, 1.405e9, NU1_D, NU2_D)
        ok &= abs(ana - num) / abs(num) < 1e-6
    check("closed-form == quadrature (5 cases incl. gamma=-9.9)", ok)

    # ---- 4a: analytic gamma-rail sensitivity ------------------------------
    print("\n== gamma_D-rail sensitivity ==")
    ref = 0.5 * (NU1_D + NU2_D)
    def shape(g):
        return band_integral(1.0, g, ref, NU1_D, NU2_D) / (NU2_D - NU1_D)

    for g in (-3, -5, -7, -9, -10):
        print(f"  band-shape factor r(gamma={g:+d}) = {shape(g):.4f}")
    delta = abs(shape(-10) - shape(-5)) / shape(-5)
    print(
        f"  max shift gamma -5 -> -10 (c0 anchored mid-band): {100*delta:.1f}% "
        f"(vs {100*(10**BAND_SYS_DEX['D']-1):.0f}% DSA 0.20-dex scale systematic)"
    )

    # ---- 4b: empirical model-vs-data DSA fluence --------------------------
    data_driven = {}
    with (BE / "dsa_fluences.csv").open() as f:
        for row in csv.DictReader(f):
            data_driven[row["burst"]] = float(row["I_jy_ms_hz"])
    print("\n  model-based vs data-driven DSA band fluence [Jy*ms*Hz]:")
    print(f"  {'burst':12s} {'model':>12s} {'data':>12s} {'model/data':>10s}")
    ratios = {}
    for r in rows:
        m = r["I_DSA_jy_ms_hz"]
        d = data_driven.get(r["burst"])
        if d:
            ratios[r["burst"]] = m / d
            print(f"  {r['burst']:12s} {m:12.4g} {d:12.4g} {m/d:10.2f}")
    rat = np.array(list(ratios.values()))
    print(
        f"  ratio median {np.median(rat):.2f}, range {rat.min():.2f}-{rat.max():.2f} "
        f"(0.20 dex = factor {10**0.20:.2f})"
    )

    # ---- 5: gamma_D pile-up census ----------------------------------------
    print("\n== gamma_D pile-up census (all joint fits) ==")
    for p in sorted(JOINT.glob("*_joint_fit.json")):
        pct = json.loads(p.read_text())["percentiles"]
        gd = pct.get("gamma_D", {}).get("median")
        gc = pct.get("gamma_C", {}).get("median")
        if gd is not None:
            near = "  <-- at -5 prior bound" if gd < -4.5 else ""
            print(f"  {p.stem.replace('_joint_fit',''):12s} gamma_C {gc:+.2f}  gamma_D {gd:+.2f}{near}")

    print(
        f"\n{'ALL LEGACY-AUDIT CHECKS PASSED' if not FAILURES else 'FAILURES: ' + ', '.join(FAILURES)}"
    )
    if FAILURES:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
