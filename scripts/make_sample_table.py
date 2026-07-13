#!/usr/bin/env python
"""Generate sample_table.tex (Table 1: the co-detection sample roster).

Reads trust-safe raw observational inputs plus V6-revalidated association
diagnostics from the pinned dsa110-FLITS submodule and emits an AASTeX
deluxetable.

Sources (pinned submodule pipeline/):
  - configs/bursts.yaml                       -> MJD, UTC, RA/Dec
  - scattering/scat_analysis/burst_metadata.py::_FALLBACK_TNS -> nickname -> TNS
  - crossmatching/toa_crossmatch_results.json -> shared-DM timing residuals
  - crossmatching/association_report.json     -> P_cc and association verdict inputs

Regenerate with: python scripts/make_sample_table.py
For an isolated FLITS worktree, set FABER2026_PIPELINE_SOURCE=/path/to/worktree.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import subprocess
from pathlib import Path

import yaml

from association_diagnostics import reported_chance_probability

REPO = Path(__file__).resolve().parent.parent
PIPELINE = REPO / "pipeline"
PIPELINE_SOURCE = Path(os.environ.get("FABER2026_PIPELINE_SOURCE", PIPELINE))
REGISTRY = PIPELINE_SOURCE / "configs" / "bursts.yaml"
META = PIPELINE_SOURCE / "scattering" / "scat_analysis" / "burst_metadata.py"
TOA_RESULTS = PIPELINE_SOURCE / "crossmatching" / "toa_crossmatch_results.json"
ASSOCIATION_REPORT = PIPELINE_SOURCE / "crossmatching" / "association_report.json"
OUT = REPO / "sample_table.tex"

# Inter-site clock/timestamp alignment term (ms), added in quadrature to the
# per-burst timing budget. Stated in Section~\ref{sec:toa}; matches the
# clock_ms term of the pipeline's timing_budget_ms (association.py).
CLOCK_MS = 1.0
# Acceptance criterion: a residual is consistent with the geometric delay when
# it lies within this many per-burst timing budgets of zero.
N_SIGMA_ACCEPT = 3.0


def _source_commit() -> str:
    try:
        if PIPELINE_SOURCE.resolve() == PIPELINE.resolve():
            return subprocess.check_output(
                ["git", "-C", str(REPO), "rev-parse", "--short", "HEAD:pipeline"],
                text=True,
            ).strip()
        return subprocess.check_output(
            ["git", "-C", str(PIPELINE_SOURCE), "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _load_tns_map() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("burst_metadata", META)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {k.lower(): v for k, v in mod._FALLBACK_TNS.items()}


def _tex_scientific(value: float) -> str:
    exponent = math.floor(math.log10(value))
    mantissa = value / 10**exponent
    return rf"${mantissa:.1f}\times10^{{{exponent}}}$"


def _association_verdict(row: dict) -> str:
    pcc_ok = row["chance_coincidence_P"] < 1e-3
    pos_ok = row["position"]["consistent"] is True
    dm_ok = row["dm_agreement"]["consistent"]
    if pcc_ok and pos_ok and dm_ok is True:
        return "assoc. (DM+pos.)"
    if pcc_ok and pos_ok and dm_ok is None:
        return "assoc. (pos.)"
    return "review"


def _load_association_diagnostics() -> dict[str, dict[str, str]]:
    toa = {k.lower(): v for k, v in json.loads(TOA_RESULTS.read_text()).items()}
    report = json.loads(ASSOCIATION_REPORT.read_text())
    assoc = {
        row["name"].lower(): row
        for row in report["bursts"]
    }
    diagnostics = {}
    for nick, assoc_row in assoc.items():
        toa_row = toa[nick]
        residual_ms = toa_row["measured_offset_ms"] - toa_row["geometric_delay_ms"]
        # Per-burst timing budget (1 sigma), in quadrature: DM-uncertainty term
        # (combined CHIME+DSA arrival error under the shared-DM reference),
        # intrinsic pulse width, and the inter-site clock term. This is the
        # timing_budget_ms of association.py with baseline/intrachannel folded
        # into the DM term already carried by combined_dm_uncertainty_ms.
        dm_unc_ms = toa_row.get("combined_dm_uncertainty_ms") or 0.0
        fwhm_ms = toa_row.get("fwhm_ms") or 0.0
        sigma_ms = math.sqrt(dm_unc_ms**2 + fwhm_ms**2 + CLOCK_MS**2)
        n_sigma = abs(residual_ms) / sigma_ms if sigma_ms > 0 else float("inf")
        diagnostics[nick] = {
            "toa_residual_ms": f"${residual_ms:+.2f} \\pm {sigma_ms:.2f}$",
            "toa_nsigma": n_sigma,
            "pcc": _tex_scientific(reported_chance_probability(assoc_row)),
            "verdict": _association_verdict(assoc_row),
        }
    return diagnostics


def main() -> None:
    registry = yaml.safe_load(REGISTRY.read_text())["bursts"]
    tns = _load_tns_map()
    diagnostics = _load_association_diagnostics()
    commit = _source_commit()

    rows = []
    for nick, rec in registry.items():
        diag = diagnostics[nick.lower()]
        rows.append(
            {
                "tns": tns.get(nick.lower(), nick.upper()),
                "nick": nick,
                "ra": rec["ra_deg"],
                "dec": rec["dec_deg"],
                "mjd": rec["mjd"],
                "utc": rec["utc"].replace("T", " "),
                **diag,
            }
        )
    rows.sort(key=lambda r: r["mjd"])

    nsig_max = max(r["toa_nsigma"] for r in rows)
    n_accept = N_SIGMA_ACCEPT

    body = []
    for r in rows:
        body.append(
            f"{r['tns']} & "
            f"${r['ra']:.4f}$ & ${r['dec']:+.4f}$ & "
            f"${r['mjd']:.3f}$ & {r['utc']} & "
            f"{r['toa_residual_ms']} & {r['pcc']} & {r['verdict']} \\\\"
        )

    tex = f"""% Rows generated by scripts/make_sample_table.py from dsa110-FLITS
% source commit {commit}: configs/bursts.yaml (MJD/UTC/RA/Dec), burst_metadata.py
% (nickname -> TNS), crossmatching/toa_crossmatch_results.json (shared-DSA-DM
% TOA residuals), and crossmatching/association_report.json (P_cc/verdict).
% V6 restored the association diagnostics under the shared DSA-DM reference.
% Do not hand-edit; regenerate with: python scripts/make_sample_table.py
\\begin{{deluxetable*}}{{lccccccc}}
\\tablecaption{{The CHIME/FRB--DSA-110 co-detection sample: twelve fast radio
bursts detected by both facilities between 2022 February and 2024 February.
Columns list the TNS designation, J2000 sky position (decimal degrees), burst
detection epoch (MJD and UTC, referenced to 400\\,MHz), and the
Section~\\ref{{sec:toa}} association diagnostics restored by V6: the shared-DSA-DM
timing residual $\\Delta t$ with its per-burst $1\\sigma$ timing budget,
chance-coincidence probability $P_{{\\rm cc}}$, and
association verdict. The quoted uncertainty is the quadrature sum of the
combined CHIME+DSA arrival error under the shared-DM reference, the intrinsic
pulse width, and a $\\sim\\!1$\\,ms inter-site clock term
(Section~\\ref{{sec:toa}}); it is dominated by the pulse width for the two
broadest bursts. A pair is accepted when $|\\Delta t| \\le {n_accept:.0f}\\sigma$;
all twelve satisfy this (maximum $|\\Delta t|/\\sigma = {nsig_max:.1f}$), and the
sign convention is defined in Section~\\ref{{sec:toa}}. \\label{{tab:sample}}}}
\\tabletypesize{{\\scriptsize}}
\\tablehead{{\\colhead{{TNS}} & \\colhead{{R.A.}} &
  \\colhead{{Decl.}} & \\colhead{{MJD}} & \\colhead{{UTC}} &
  \\colhead{{$\\Delta t \\pm \\sigma$ (ms)}} & \\colhead{{$P_{{\\rm cc}}$}} &
  \\colhead{{Verdict}}}}
\\startdata
{chr(10).join(body)}
\\enddata
\\end{{deluxetable*}}
"""
    OUT.write_text(tex)
    print(f"wrote {OUT.relative_to(REPO)} ({len(rows)} rows, source commit {commit})")


if __name__ == "__main__":
    main()
