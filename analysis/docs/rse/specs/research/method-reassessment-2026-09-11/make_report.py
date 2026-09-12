"""Summarise injection_recovery.py and production_path_injection.py outputs.

Writes, next to results/:
  injection-recovery-results.md   per-case table plus arm verdicts
  fig-arm-a-recovery.svg          recovered beta vs truth (arm a)
  fig-arm-b-mismatch.svg          shape posteriors under F1 and F2 for mismatch truths (arm b)
  fig-arm-c-sensitivity.svg       beta / alpha vs S/N and gain-prior scale (arm c)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
RES = HERE / "results"

plt.rcParams.update({"font.size": 9, "svg.fonttype": "none", "figure.dpi": 100})


def load() -> list[dict]:
    recs = []
    for p in sorted(RES.glob("*.json")):
        if p.name.startswith("kernel"):
            continue
        recs.append(json.loads(p.read_text()))
    return recs


def load_prod() -> list[dict]:
    d = RES / "production-path"
    return [json.loads(p.read_text()) for p in sorted(d.glob("*.json")) if ".v1" not in p.name] if d.exists() else []


def fmt(x: float, n: int = 3) -> str:
    return f"{x:.{n}f}" if np.isfinite(x) else "–"


def table(recs: list[dict]) -> str:
    lines = [
        "| id | arm | truth | true shape | true α | model | fitted shape (p16, p50, p84) | rail class | truth in 95% | log10 τ (true / p50) | τ in 95% | other parameters at a prior edge (>5% mass within 1% of span) | ln Z |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in recs:
        c, cs, res = r["classification"], r["case"], r["result"]
        tr = cs["truth"]
        truth = "heavy-tail stress (legacy thick)" if tr["kind"] == "thick" else tr["kind"]
        if tr["kind"] == "twoscreen":
            truth += f" (exp α={tr['shape']} ⊛ thin β={tr['beta_b']})"
        elif tr["kind"] == "thin2comp":
            truth += f" (+{tr['comp2_ratio']:.0%} comp at +{tr['comp2_offset']*1e3:.2f} ms)"
        ts = "–" if not np.isfinite(c["true_shape"]) else fmt(c["true_shape"], 2)
        cov = "–" if c["shape_covered_95"] is None else ("yes" if c["shape_covered_95"] else "no")
        others = [
            f"{n} ({'low' if v['low'] > 0.05 else 'high'}, {max(v['low'], v['high']):.0%})"
            for n, v in res["edge_mass"].items()
            if n != c["shape_param"] and max(v["low"], v["high"]) > 0.05
        ]
        lines.append(
            f"| {cs['id']} | {cs['arm']} | {truth} | {ts} | {fmt(c['true_alpha'], 2)} | {cs['model']} | "
            f"{c['shape_param']} = {fmt(c['shape_p16'])}, {fmt(c['shape_p50'])}, {fmt(c['shape_p84'])} | "
            f"{c['rail_class']} | {cov} | {fmt(c['log10_tau_true'], 2)} / {fmt(c['log10_tau_p50'], 2)} | "
            f"{'–' if c['tau_covered_95'] is None else ('yes' if c['tau_covered_95'] else 'no')} | {', '.join(others) if others else 'none'} | {res['logz']:.1f} ± {res['logzerr']:.1f} |"
        )
    return "\n".join(lines)


def prod_table(prod: list[dict]) -> str:
    if not prod:
        return "_No production-path results found._"
    lines = [
        "| case | truth kernel | true α | β median (−, +) | mass β≥3.99 (production rail rule) | mass β≥3.95 | mass β≥3.98 (exponential branch) | rail class | derived α | ln Z | calls |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in prod:
        b = r["beta"]; ma = r.get("mass_above", {})
        lines.append(
            f"| {r['case']} | {r['kernel']} | {r['alpha_true']:.2f} | {b['median']:.3f} (−{b['err_minus']:.3f}, +{b['err_plus']:.3f}) | "
            f"{r['edge_mass_beta']['high']:.2f} | {ma.get('3.95', float('nan')):.2f} | {ma.get('3.98', float('nan')):.2f} | {r['rail_class']} | {r['alpha_derived']:.2f} | {r['log_evidence']:.1f} ± {r['log_evidence_err']:.1f} | {r['ncall']} |"
        )
    return "\n".join(lines)


def kernel_switch_section() -> list[str]:
    disc_p = RES / "kernel-branch-discontinuity.json"; prof_p = RES / "kernel-switch-check.json"
    if not disc_p.exists() or not prof_p.exists():
        return ["_Kernel-switch check not run._"]
    disc = json.loads(disc_p.read_text()); prof = json.loads(prof_p.read_text())
    out = [
        "Production forward model with other parameters fixed, β = 3.979 (FFT power-law branch) against β = 3.981 (analytic exponential branch, α := 4):",
        "",
        "| band | Δt [ms] | τ at band centre [ms] | max diff / peak, 3.979 vs 3.981 | max diff / peak, 3.90 vs 3.981 | centroid offset FFT − analytic [samples] | max diff / peak after sampling analytic at t + Δt/2 |",
        "|---|---|---|---|---|---|---|",
    ] + [
        f"| {d['band']} | {d['dt_ms']:.4f} | {d['tau_centre_ms']:.4f} | {d['max_diff_over_peak_3979_vs_3981']:.3f} | {d['max_diff_over_peak_390_vs_3981']:.3f} | {d['centroid_offset_samples_fft_minus_analytic']:+.3f} | {d['max_diff_over_peak_fft_vs_analytic_at_bin_centre']:.3f} |"
        for d in disc
    ] + [
        "",
        "The alpha law also jumps at the switch. Raw all-channel maximum errors and area-normalized middle-channel shifted errors are different metrics, not a before/after sampling-only comparison.",
        "",
        "Profile log-likelihood in β (τ profiled on a grid; ζ, x_ζ, t0 fixed at the injected truth, ΔDM = 0):",
        "",
        "| case | best β on grid | ln L(best, β ≥ 3.98) − ln L(best, β < 3.98) |",
        "|---|---|---|",
    ] + [f"| {r['case']} | {r['beta_at_max']:.3f} | {r['step_lnL']:+.1f} |" for r in prof]
    free_p = RES / "kernel-switch-free-t0.json"
    if free_p.exists():
        free = json.loads(free_p.read_text())
        out += [
            "",
            "Same comparison with τ, t0_C and t0_D re-optimised on each side of the switch (ζ, x_ζ at truth, ΔDM = 0), so that the arrival-time offset between the two conventions is absorbed:",
            "",
            "| case | ln L(β = 3.981, analytic) − ln L(β = 3.979, FFT), free t0 | t0 shift C [samples] | t0 shift D [samples] |",
            "|---|---|---|---|",
        ] + [f"| {r['case']} | {r['step_lnL_free_t0']:+.1f} | {r['t0_shift_C_samples']:+.2f} | {r['t0_shift_D_samples']:+.2f} |" for r in free]
    flip_p = RES / "kernel-switch-posterior-flip.json"
    if flip_p.exists() and json.loads(flip_p.read_text()):
        flip = json.loads(flip_p.read_text())
        out += [
            "",
            "Production-path posteriors: start from the posterior-median vector, flip β to either side of 3.98, re-optimise τ and both t0:",
            "",
            "| case | β median | ln L at median | ln L(3.981) − ln L(3.979), free t0 | mass β ≥ 3.95 | production rail class |",
            "|---|---|---|---|---|---|",
        ] + [f"| {r['case']} | {r['beta_median']:.3f} | {r['lnL_at_median']:.1f} | {r['step_lnL_free_t0']:+.1f} | {(r.get('mass_above') or {}).get('3.95', float('nan')):.2f} | {r['rail_class']} |" for r in flip]
    out += ["", "Figure: `fig-kernel-switch.svg`."]
    return out


def fig_arm_a(recs):
    a = [r for r in recs if r["case"]["arm"] == "a"]
    if not a:
        return
    fig, ax = plt.subplots(figsize=(4.2, 3.4))
    for r in a:
        c = r["classification"]
        tr = r["case"]["truth"]
        x = c["true_shape"] if tr["kind"] == "thin" else 4.0
        marker = "o" if tr["tau_1ghz"] >= 5e-4 else "s"
        ax.errorbar(x, c["shape_p50"], yerr=[[c["shape_p50"] - c["shape_p16"]], [c["shape_p84"] - c["shape_p50"]]],
                    fmt=marker, ms=4, capsize=2, color="k" if c["rail_class"] == "interior" else "C3")
    ax.plot([3, 4], [3, 4], "--", color="0.6", lw=0.8)
    ax.axhspan(3.99, 4.0, color="C3", alpha=0.15, lw=0)
    ax.set_xlabel(r"$\beta_{\rm true}$")
    ax.set_ylabel(r"$\beta$ posterior (p16, p50, p84)")
    ax.set_xlim(3.15, 4.05); ax.set_ylim(3.15, 4.05)
    ax.text(3.2, 3.95, r"circle: $\tau_{1\rm GHz}=1$ ms; square: $0.15$ ms (near one sample)", fontsize=7)
    fig.tight_layout(); fig.savefig(HERE / "fig-arm-a-recovery.svg"); plt.close(fig)


def fig_arm_b(recs):
    b = [r for r in recs if r["case"]["arm"] == "b"]
    if not b:
        return
    tags = sorted({r["case"]["id"].rsplit("-", 1)[0] for r in b})
    fig, axes = plt.subplots(len(tags), 2, figsize=(6.4, 1.5 * len(tags)), sharex="col")
    axes = np.atleast_2d(axes)
    for i, tag in enumerate(tags):
        for j, model in enumerate(("F1", "F2")):
            ax = axes[i, j]
            rr = [r for r in b if r["case"]["id"] == f"{tag}-{model}"]
            if not rr:
                ax.set_visible(False); continue
            r = rr[0]
            s = np.asarray(r["result"]["shape_samples"])
            lo, hi = (3.0, 4.0) if model == "F1" else (2.0, 6.0)
            ax.hist(s, bins=np.linspace(lo, hi, 61), color="0.3")
            ta = r["classification"]["true_alpha"]
            if model == "F1":
                if 4 < ta <= 6:
                    ax.axvline(2 * ta / (ta - 2), color="C3", lw=1)
            elif np.isfinite(ta):
                ax.axvline(ta, color="C3", lw=1)
            ax.set_yticks([])
            ax.text(0.02, 0.8, f"{tag} / {model}: {r['classification']['rail_class']}", transform=ax.transAxes, fontsize=7)
    axes[-1, 0].set_xlabel(r"$\beta$ (F1, thin-screen coupled)")
    axes[-1, 1].set_xlabel(r"$\alpha$ (F2, exponential, free index)")
    fig.tight_layout(); fig.savefig(HERE / "fig-arm-b-mismatch.svg"); plt.close(fig)


def fig_arm_c(recs):
    c = [r for r in recs if r["case"]["arm"] == "c"]
    base = [r for r in recs if r["case"]["id"] == "a-thin-b3.67-tau1e-03-F1"]
    if not c:
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.4, 3.0))
    snr_pts = [(r["case"]["snr"], r["classification"]) for r in c + base if "snr" in r["case"]["id"] or r in base]
    for snr, cl in snr_pts:
        ax1.errorbar(snr, cl["shape_p50"], yerr=[[cl["shape_p50"] - cl["shape_p16"]], [cl["shape_p84"] - cl["shape_p50"]]],
                     fmt="o", ms=4, capsize=2, color="k")
    ax1.axhline(3.67, color="C3", lw=0.8); ax1.set_xscale("log")
    ax1.set_xlabel("band-summed peak S/N"); ax1.set_ylabel(r"$\beta$ (F1)")
    for r in c + base:
        if "s2x" in r["case"]["id"] or r in base:
            cl = r["classification"]; k = r["case"]["s2_factor"]; m = r["case"]["model"]
            ax2.errorbar(k, cl["shape_p50"] if m == "F1" else cl["alpha_p50"],
                         yerr=[[cl["shape_p50"] - cl["shape_p16"]], [cl["shape_p84"] - cl["shape_p50"]]],
                         fmt="o" if m == "F1" else "s", ms=4, capsize=2, color="k" if m == "F1" else "C0")
    ax2.axhline(3.67, color="k", lw=0.8, ls=":"); ax2.axhline(2 * 3.67 / 1.67, color="C0", lw=0.8, ls=":")
    ax2.set_xscale("log"); ax2.set_xlabel(r"gain-prior scale $s / g_{\rm rms}$")
    ax2.set_ylabel(r"$\beta$ (F1, black) or $\alpha$ (F2, blue)")
    fig.tight_layout(); fig.savefig(HERE / "fig-arm-c-sensitivity.svg"); plt.close(fig)


def verdicts(recs, prod) -> str:
    a = [r for r in recs if r["case"]["arm"] == "a" and r["case"]["truth"]["kind"] == "thin"]
    a_ok = [r for r in a if r["classification"]["rail_class"] == "interior" and r["classification"]["shape_covered_95"]]
    a_cov68 = [r for r in a if r["classification"]["shape_p16"] <= r["classification"]["true_shape"] <= r["classification"]["shape_p84"]]
    b1 = [r for r in recs if r["case"]["arm"] == "b" and r["case"]["model"] == "F1"]
    b1_rail = [r for r in b1 if r["classification"]["rail_class"] != "interior"]
    b2 = [r for r in recs if r["case"]["arm"] == "b" and r["case"]["model"] == "F2"]
    b2_defined = [r for r in b2 if r["classification"]["shape_covered_95"] is not None]
    b2_ok = [r for r in b2_defined if r["classification"]["shape_covered_95"]]
    out = [
        f"- Arm a (limited harness recovery): {len(a_ok)}/{len(a)} interior thin-screen truths recovered interior with the truth inside the 95% interval; "
        f"{len(a_cov68)}/{len(a)} inside the 68% interval.",
        f"- Arm b (model class), F1: {len(b1_rail)}/{len(b1)} mismatch truths produce a rail "
        f"({', '.join(r['case']['id'] + ':' + r['classification']['rail_class'] for r in b1)}).",
        f"- Arm b (model class), F2: {len(b2_ok)}/{len(b2_defined)} cases with a defined input scale exponent have that α inside the 95% interval "
        f"({', '.join(r['case']['id'] + ':' + r['classification']['rail_class'] for r in b2)}).",
    ]
    if prod:
        out.append("- Production path: " + "; ".join(
            f"{r['case']} → {r['rail_class']} (β={r['beta']['median']:.3f}; mass β≥3.95 = {r.get('mass_above', {}).get('3.95', float('nan')):.2f})" for r in prod) + ".")
    return "\n".join(out)


def main():
    recs, prod = load(), load_prod()
    fig_arm_a(recs); fig_arm_b(recs); fig_arm_c(recs)
    kc = json.loads((RES / "kernel-check.json").read_text()) if (RES / "kernel-check.json").exists() else []
    md = [
        "# Injection-recovery results",
        "",
        f"Generated by `make_report.py` from `results/` ({len(recs)} harness cases, {len(prod)} production-path cases).",
        "Sampler: dynesty static nested sampling, random-walk proposals, multi-ellipsoid bounds, stopping tolerance 0.5 in ln Z; "
        "rail rule = production rule (more than 5% of posterior mass within 1% of the prior span of an edge).",
        "",
        "The legacy thick case is a generic heavy-tail stress kernel, with integral 2 and infinite mean; its scale is not a mean delay. The composite has no single mean-delay exponent. Composite shape coverage and heavy-tail/composite tau coverage are undefined (dash). Original injected arrays and fit outputs are retained.",
        "The 9/9 recovery count is not interval calibration or production validation. Historical equal-weight resampling was unseeded; future runs seed it, so exact old quantiles are not promised. Near-switch mass columns use finite equal-weight resampling; zero is not proof of no original samples.",
        "",
        "## Verdicts",
        "",
        verdicts(recs, prod),
        "",
        "## Harness cases",
        "",
        table(recs),
        "",
        "## Production-path cases (`fit_joint_scattering`, shared-ζ, β ∈ [3, 4])",
        "",
        prod_table(prod),
        "",
        "## Production kernel-switch check (`kernel_switch_check.py`)",
        "",
    ] + kernel_switch_section() + [
        "",
        "## Kernel check (FFT convolution vs analytic `gaussian_power_law_density`)",
        "",
        "| β | τ [s] | σ [s] | max relative error at peak | L1 error |",
        "|---|---|---|---|---|",
    ] + [f"| {k['beta']} | {k['tau_s']:.0e} | {k['sigma_s']:.0e} | {k['max_rel_err']:.2e} | {k['l1_err']:.2e} |" for k in kc] + [
        "",
        "Figures: `fig-arm-a-recovery.svg`, `fig-arm-b-mismatch.svg`, `fig-arm-c-sensitivity.svg`, `fig-kernel-switch.svg`.",
    ]
    (HERE / "injection-recovery-results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:12]))


if __name__ == "__main__":
    main()
