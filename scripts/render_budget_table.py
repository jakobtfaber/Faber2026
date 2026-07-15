"""Render ``budget_table.tex`` with the verified DM and host-DM products.

The foreground/cosmological columns remain owned by the pinned FLITS table
data.  This super-repository layer replaces only ``DM_obs`` from the adopted
phase-coherence catalog and ``DM_host`` from the forward Monte Carlo, keeping
the manuscript table reproducible without changing the pipeline submodule pin.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "pipeline"
CATALOG = ROOT / "analysis" / "dm-joint-phase-v2" / "manuscript_dm_catalog.csv"
HOST_CSV = ROOT / "scripts" / "dm_budget_uncertainty.csv"
BASE_DATA = PIPELINE / "galaxies" / "foreground" / "budget_table_data.json"
OUT = ROOT / "budget_table.tex"

EMITTER = PIPELINE / "galaxies" / "foreground" / "budget_table_emitter.py"


def _load_base_emitter():
    """Load the stdlib-only emitter without executing the package ``__init__``.

    Importing ``galaxies.foreground`` eagerly imports Astropy, which is
    irrelevant to table rendering and unavailable in the workflow's initial
    plain-Python parity step.
    """
    spec = importlib.util.spec_from_file_location("_budget_table_emitter", EMITTER)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load budget table emitter: {EMITTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_base_emitter()


def _csv_by(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="") as fh:
        return {row[key]: row for row in csv.DictReader(fh) if row.get(key)}


def render() -> str:
    dm = _csv_by(CATALOG, "tns")
    host = _csv_by(HOST_CSV, "burst")
    rows = json.loads(BASE_DATA.read_text())["rows"]
    if {row["burst"] for row in rows} != set(dm):
        raise ValueError("budget and adopted-DM rosters differ")
    for row in rows:
        burst = row["burst"]
        row["dm_obs"] = f'{float(dm[burst]["adopted_dm"]):.4f}'
        if row["z"] is not None:
            h = host[burst]
            p16, p50, p84 = (int(h[k]) for k in ("dm_host_p16", "dm_host_p50", "dm_host_p84"))
            row["dm_host"] = [p50, p84 - p50, p50 - p16]

    head = base._HEAD.replace(  # noqa: SLF001 - pinned internal formatting contract
        "% !! GENERATED FILE -- do not edit by hand. Values live in\n"
        "%    galaxies/foreground/budget_table_data.json; markup in budget_table_emitter.py.\n"
        "%    Regenerate: python -m galaxies.foreground.budget_table_emitter --out <this file>\n",
        "% !! GENERATED FILE -- do not edit by hand.\n"
        "%    Regenerate: python scripts/render_budget_table.py\n"
        "% Foreground columns come from pipeline/galaxies/foreground/budget_table_data.json;\n"
        "% DM_obs and DM_host come from the verified super-repository products.\n",
    ).replace(
        "DSA-110 catalog dispersion measure under the shared DSA-DM reference\n"
        "convention of Section~\\ref{sec:toa}.",
        "adopted CHIME phase-coherence measurement from Table~\\ref{tab:dm-measurements}.",
    )
    body = "\n".join(base.render_row(row) for row in rows)
    # Super-repo overlay on the emitter footnotes/comments: (i) the f_IGM
    # sensitivity statement tracks the manuscript forward model (median -5
    # after the 2026-07-15 census remediation -> 0.2 sigma, conservative);
    # (ii) note u needs the lower-bound clause for the one sightline with
    # both a shallow-layer confirmed system and no deep coverage.
    tail = base._TAIL.replace(  # noqa: SLF001
        "within $0.3\\sigma$",
        "within $0.2\\sigma$",
    ).replace(
        # (iii) The upward move of the host medians relative to the old
        # mean-subtracted residuals is driven mainly by the f_IGM 0.84 -> 0.76
        # recalibration (~26 of a ~30 pc/cm^3 shift at z~0.3), not by the
        # log-normal skew; attribute it correctly.
        "\\tablecomments{Because the diffuse cosmic term is drawn from a skewed log-normal,\n"
        "the host posteriors are asymmetric and their medians exceed the naive\n"
        "mean-subtracted residuals. One high-redshift sightline",
        "\\tablecomments{The host posteriors are asymmetric because the diffuse cosmic\n"
        "term is drawn from a skewed log-normal. Their medians sit above the naive\n"
        "mean-subtracted residuals, but that offset is driven mainly by the lower IGM\n"
        "normalization adopted here ($f_{\\rm IGM}=0.76$ versus $0.84$), not by the\n"
        "skew; the forward model's value is the asymmetric interval and the\n"
        "per-sightline $P(\\mathrm{DM_{host}}<0)$, not the shift in central value.\n"
        "One high-redshift sightline",
    ).replace(
        "not\nexcluded---absence of coverage is not absence of foreground\n"
        "(Section~\\ref{sec:obs-fg}).}",
        "not\nexcluded---absence of coverage is not absence of foreground\n"
        "(Section~\\ref{sec:obs-fg}). On the one such sightline with a\n"
        "shallow-layer confirmed system (FRB~20240203A), the tabulated column\n"
        "is a lower bound rather than a complete census.}",
    )
    return head + body + "\n" + tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not args.out.exists() or args.out.read_text() != expected:
            print(f"DRIFT: {args.out}", file=sys.stderr)
            return 1
        print(f"OK: {args.out}")
        return 0
    args.out.write_text(expected)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
