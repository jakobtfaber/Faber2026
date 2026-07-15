#!/usr/bin/env python3
"""Build explicitly provisional joint-fit/scintillation manuscript tables."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOINT = ROOT / "pipeline/analysis/scattering-dm-locked-2026-07-14/results"
SCINT = ROOT / "pipeline/analysis/scintillation-dsa-lorentzian-2026-07-07/results"
OUT = ROOT / "analysis/provisional_propagation"
SINGLE_SCREEN_MAX = 2.0
FOREGROUND = ROOT / "pipeline/galaxies/foreground"
BUDGET_PATH = FOREGROUND / "budget_table_data.json"
FOREGROUND_PATH = FOREGROUND / "foreground_table_data.json"
CONTRIBUTORS_PATH = ROOT / "scripts/dm_budget_intervening_systems.csv"
TAU_CONSISTENCY_PATH = FOREGROUND / "data/tau_consistency_catalog.csv"
TAU_CONSISTENCY_DIR = FOREGROUND / "data/tau_consistency"


def screen_product(tau_1ghz_ms, tau_err_ms, alpha, alpha_err,
                   center_freq_mhz, dnu_mhz, dnu_err_mhz):
    """Return tau(nu)*dnu and independent first-order 1-sigma uncertainty.

    The dimensionless product uses tau[ms] * dnu[MHz] * 1e3.  This is
    tau[s] * dnu[Hz].  Marginal-fit covariance is unavailable, so the error is
    deliberately labeled approximate in every emitted product.
    """
    nu_ghz = center_freq_mhz / 1000.0
    tau_nu = tau_1ghz_ms * nu_ghz ** (-alpha)
    product = tau_nu * dnu_mhz * 1000.0
    terms = []
    if tau_1ghz_ms:
        terms.append((tau_err_ms / tau_1ghz_ms) ** 2)
    if dnu_mhz:
        terms.append((dnu_err_mhz / dnu_mhz) ** 2)
    terms.append((math.log(nu_ghz) * alpha_err) ** 2)
    return product, product * math.sqrt(sum(terms))


def classify_products(products):
    """Favor two screens only if every component is >2 at one sigma."""
    return ("two-screen favored" if products and
            all(value - error > SINGLE_SCREEN_MAX for value, error in products)
            else "indeterminate")


def classify_foreground_alignment(adjudication, eligible_count,
                                  coverage_limited, tau_ratio):
    """Return a deliberately non-causal foreground/propagation reading."""
    if adjudication != "accepted_physical":
        if tau_ratio is not None and tau_ratio > 1:
            return "fit unusable; foreground prediction exceeds fit"
        return "fit unusable; comparison deferred"
    if eligible_count:
        if tau_ratio is not None and tau_ratio >= 0.1:
            return "plausible partial foreground contribution"
        return "foreground contribution small in fiducial model"
    if coverage_limited:
        return "coverage-limited; no eligible foreground identified"
    return "no eligible foreground in covered census"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pm(block, digits=3):
    return (f"${block['median']:.{digits}f}^{{+{block['err_plus']:.{digits}f}}}"
            f"_{{-{block['err_minus']:.{digits}f}}}$")


def tex_escape(value):
    return str(value).replace("_", r"\_")


def load_foreground_inputs():
    budget = json.loads(BUDGET_PATH.read_text())["rows"]
    foreground = json.loads(FOREGROUND_PATH.read_text())["rows"]
    contributors = list(csv.DictReader(CONTRIBUTORS_PATH.open()))
    if len(budget) != 12:
        raise ValueError(f"expected 12 foreground budget rows, found {len(budget)}")

    by_burst = {}
    current = None
    for cells in foreground:
        current = cells[0] or current
        if current is None:
            raise ValueError("foreground table begins with an inherited burst")
        by_burst.setdefault(current, []).append(cells)
    return budget, by_burst, contributors


def consistency_tau_block(nick, catalog_row):
    """Load the policy-required alpha=4 consistency-tau posterior, if present."""
    value = catalog_row.get("tau_consistency_1ghz_ms", "")
    if not value:
        return None
    path = TAU_CONSISTENCY_DIR / f"{nick}_joint_alpha4_pbf-exp-exp.json"
    if not path.is_file():
        raise ValueError(f"catalog claims consistency tau but refit is missing: {path}")
    payload = json.loads(path.read_text())
    block = payload.get("tau_1ghz", payload.get("percentiles", {}).get("tau_1ghz"))
    if not isinstance(block, dict):
        raise ValueError(f"consistency refit lacks tau posterior: {path}")
    return block, path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    adj_path = JOINT / "fit_adjudication.csv"
    comp_path = SCINT / "dsa_lorentzian_components.csv"
    adj = list(csv.DictReader(adj_path.open()))
    comps = list(csv.DictReader(comp_path.open()))
    consistency_catalog = {
        row["nickname"].casefold(): row
        for row in csv.DictReader(TAU_CONSISTENCY_PATH.open())
    }
    budget, foreground_by_burst, contributors = load_foreground_inputs()
    if len(adj) != 12:
        raise ValueError(f"expected 12 adjudication rows, found {len(adj)}")
    if not comps or "quality_flags" not in comps[0]:
        raise ValueError("DSA component catalog schema changed")

    joint_rows, dsa_rows, screen_rows, screen_json = [], [], [], []
    fit_by_tns, adj_by_tns = {}, {}
    for row in adj:
        nick, tns = row["burst"], row["tns"]
        fit = None
        if row["fit_json"]:
            fit_path = JOINT / row["fit_json"]
            fit = json.loads(fit_path.read_text())
            fit_by_tns[tns] = fit
            joint_rows.append(
                f"{tns.replace('FRB ', '')} & {row['variant']} & {pm(fit['tau_1ghz'])} & "
                f"{pm(fit['alpha'], 2)} & {pm(fit['beta'], 2)} & "
                f"{row['chi2_chime']}/{row['chi2_dsa']} & "
                f"{tex_escape(row['adjudication'].replace('_', ' '))} \\\\"
            )
        else:
            joint_rows.append(
                f"{tns.replace('FRB ', '')} & {row['variant']} & \\nodata & \\nodata & "
                f"\\nodata & {row['chi2_chime']}/{row['chi2_dsa']} & rejected; no retained fit \\\\"
            )
        adj_by_tns[tns] = row

        clean = [c for c in comps if c["burst"] == nick and
                 c["component"] == "1" and not c["quality_flags"]]
        values = [float(c["dnu_mhz"]) for c in clean]
        if values:
            med = sorted(values)[len(values) // 2] if len(values) % 2 else (
                sorted(values)[len(values)//2 - 1] + sorted(values)[len(values)//2]) / 2
            span = f"{min(values):.3g}--{max(values):.3g}" if len(values) > 1 else f"{values[0]:.3g}"
            cert = ("provisional aggregate; certified point separate"
                    if nick == "oran" else "provisional")
            dsa_rows.append(f"{tns.replace('FRB ', '')} & {len(values)} & {med:.3g} & {span} & {cert} \\\\")
        else:
            dsa_rows.append(f"{tns.replace('FRB ', '')} & 0 & \\nodata & \\nodata & no clean narrow component \\\\")

        if row["adjudication"] != "accepted_physical" or fit is None:
            continue
        consistency = consistency_tau_block(nick, consistency_catalog[nick.casefold()])
        if consistency is None:
            verdict = "pending fixed-index consistency refit"
            screen_rows.append(
                f"{tns.replace('FRB ', '')} & {len(clean)} & \\nodata & \\nodata & "
                f"\\nodata & {verdict} \\\\"
            )
            screen_json.append({"burst": nick, "tns": tns, "products": [],
                                "verdict": verdict})
            continue
        tau, consistency_path = consistency
        pairs = []
        for c in clean:
            value, error = screen_product(
                tau["median"], 0.5 * (tau["err_minus"] + tau["err_plus"]),
                4.0, 0.0,
                float(c["center_freq_mhz"]), float(c["dnu_mhz"]),
                float(c["dnu_err_mhz"]),
            )
            pairs.append((value, error))
        verdict = classify_products(pairs)
        vals = [p[0] for p in pairs]
        median = sorted(vals)[len(vals)//2] if len(vals) % 2 else (
            sorted(vals)[len(vals)//2 - 1] + sorted(vals)[len(vals)//2]) / 2
        screen_rows.append(
            f"{tns.replace('FRB ', '')} & {len(vals)} & {median:.2g} & "
            f"{min(vals):.2g}--{max(vals):.2g} & "
            f"{min(v - e for v, e in pairs):.2g} & {verdict} \\\\"
        )
        screen_json.append({"burst": nick, "tns": tns,
                            "tau_consistency_source": str(consistency_path.relative_to(ROOT)),
                            "products": [{"value": v, "sigma_approx": e}
                                         for v, e in pairs], "verdict": verdict})

    screen_by_tns = {row["tns"]: row for row in screen_json}
    contributor_counts = {}
    for contributor in contributors:
        contributor_counts[contributor["tns"]] = contributor_counts.get(contributor["tns"], 0) + 1

    foreground_rows, foreground_json = [], []
    for budget_row in budget:
        tns = budget_row["burst"]
        if tns not in adj_by_tns:
            raise ValueError(f"foreground roster not present in fit adjudication: {tns}")
        adjudication = adj_by_tns[tns]["adjudication"]
        fit = fit_by_tns.get(tns)
        tau_fit = fit["tau_1ghz"]["median"] if fit else None
        tau_int = float(budget_row["tau_int"])
        coverage_limited = "u" in budget_row.get("burst_note", "")
        eligible_count = contributor_counts.get(tns, 0)
        tau_ratio = (tau_int / tau_fit if tau_fit and
                     not (coverage_limited and eligible_count == 0) else None)
        foreground_entries = foreground_by_burst.get(tns, [])
        inconclusive_b = [float(cells[3]) for cells in foreground_entries
                          if cells[8] == "inconclusive" and cells[3] != r"\nodata"]
        nearest_inconclusive = min(inconclusive_b) if inconclusive_b else None
        interpretation = classify_foreground_alignment(
            adjudication, eligible_count, coverage_limited, tau_ratio)
        propagation_status = screen_by_tns.get(tns, {}).get("verdict", "fit unusable")
        propagation_tex = ("pending fixed-index refit"
                           if propagation_status == "pending fixed-index consistency refit"
                           else tex_escape(propagation_status))
        foreground_json.append({
            "tns": tns,
            "adjudication": adjudication,
            "propagation_status": propagation_status,
            "coverage": "limited" if coverage_limited else "covered",
            "eligible_foreground_systems": eligible_count,
            "nearest_inconclusive_impact_kpc": nearest_inconclusive,
            "tau_int_ms": tau_int,
            "tau_fit_1ghz_ms": tau_fit,
            "tau_int_over_tau_fit": tau_ratio,
            "interpretation": interpretation,
        })
        tau_fit_tex = f"{tau_fit:.3g}" if tau_fit is not None else r"\nodata"
        ratio_tex = f"{tau_ratio:.3g}" if tau_ratio is not None else r"\nodata"
        nearest_tex = f"{nearest_inconclusive:.0f}" if nearest_inconclusive is not None else r"\nodata"
        foreground_rows.append(
            f"{tns.replace('FRB ', '')} & {propagation_tex} & "
            f"{'limited' if coverage_limited else 'covered'} & {eligible_count} & "
            f"{nearest_tex} & {tau_int:.3g} & {tau_fit_tex} & {ratio_tex} & "
            f"{tex_escape(interpretation)} \\\\"
        )

    def table(path, label, caption, columns, header, rows, comments=None):
        path.write_text("% Generated by scripts/build_provisional_propagation_tables.py; do not hand-edit.\n"
                        "\\begin{deluxetable*}{" + columns + "}\n"
                        "\\tablecaption{" + caption + "\\label{" + label + "}}\n"
                        "\\tablehead{" + header + "}\n\\startdata\n" +
                        "\n".join(rows) + "\n\\enddata\n"
                        "\\tablecomments{" + (comments or
                        "All values are best-so-far and provisional unless explicitly certified.") + "}\n"
                        "\\end{deluxetable*}\n")

    table(ROOT / "joint_fit_provisional_table.tex", "tab:joint-fit-provisional",
          "Best-so-far DM-locked two-dimensional joint fits (provisional).",
          "lcccccc", "\\colhead{FRB} & \\colhead{Model} & \\colhead{$\\tau_{1\\,GHz}$ (ms)} & \\colhead{$\\alpha$} & \\colhead{$\\beta$} & \\colhead{$\\chi^2_{\\nu,C}/\\chi^2_{\\nu,D}$} & \\colhead{Residual status}", joint_rows)
    table(ROOT / "dsa_scint_provisional_table.tex", "tab:dsa-scint-provisional",
          "Best-so-far clean narrow-component DSA-110 bandwidth fits (provisional).",
          "lcccl", "\\colhead{FRB} & \\colhead{$N$} & \\colhead{Median $\\Delta\\nu_d$ (MHz)} & \\colhead{Range (MHz)} & \\colhead{Status}", dsa_rows)
    table(ROOT / "twoscreen_provisional_table.tex", "tab:twoscreen-provisional",
          "Two-screen consistency evaluation readiness.",
          "lccccl", "\\colhead{FRB} & \\colhead{$N$} & \\colhead{Median $\\tau\\Delta\\nu_d$} & \\colhead{Range} & \\colhead{min$(P-\\sigma_P)$} & \\colhead{Inference}", screen_rows,
          "The accepted dual-$\\tau$ policy requires $\\alpha$ fixed to 4 in "
          "$\\tau_{\\rm consistency}$ refits. No products or verdicts are "
          "reported until those refits exist; free-$\\alpha$ joint $\\tau$ is "
          "not substituted.")
    table(ROOT / "foreground_propagation_provisional_table.tex",
          "tab:foreground-propagation-provisional",
          "Foreground-census alignment with provisional propagation constraints.",
          "llccccccc", "\\colhead{FRB} & \\colhead{Screen test} & \\colhead{Coverage} & "
          "\\colhead{$N_{\\rm fg}$} & \\colhead{$b_{\\rm inc,min}$ (kpc)} & "
          "\\colhead{$\\tau_{\\rm int}$ (ms)} & \\colhead{$\\tau_{\\rm joint}$ (ms)} & "
          "\\colhead{Fraction} & \\colhead{Reading}", foreground_rows,
          "$N_{\\rm fg}$ counts deduplicated budget-eligible systems; "
          "$b_{\\rm inc,min}$ is the nearest inconclusive projected candidate; "
          "Fraction is $\\tau_{\\rm int}/\\tau_{\\rm joint}$. The latter is the "
          "provisional free-$\\alpha$ morphology-track value and is used only for "
          "this foreground diagnostic, never for screen consistency. Ratios are suppressed "
          "for coverage-limited zero-foreground rows. Values and causal readings "
          "remain provisional.")

    consistency_refits = sorted(TAU_CONSISTENCY_DIR.glob("*_joint_alpha4_pbf-exp-exp.json"))
    inputs = [adj_path, comp_path, BUDGET_PATH, FOREGROUND_PATH,
              TAU_CONSISTENCY_PATH,
              CONTRIBUTORS_PATH] + [JOINT / r["fit_json"] for r in adj if r["fit_json"]]
    inputs += consistency_refits
    (OUT / "results.json").write_text(json.dumps({
        "status": "PROVISIONAL_UNVERIFIED", "single_screen_range": [0.1, 2.0],
        "uncertainty": "first-order independent marginal propagation; covariance unavailable",
        "screen_analysis_status": "PENDING_ALPHA4_CONSISTENCY_REFITS",
        "screen_tau_policy": "alpha-fixed tau_consistency only; free-alpha joint tau prohibited",
        "command": "python3 scripts/build_provisional_propagation_tables.py",
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in inputs},
        "screen_rows": screen_json,
        "foreground_alignment_rows": foreground_json,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
