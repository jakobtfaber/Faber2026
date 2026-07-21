#!/usr/bin/env python3
"""Render the expanded foreground catalog description from pinned artifacts.

This parent-side renderer never performs network queries and never writes into
the pipeline submodule.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "pipeline/galaxies/foreground/data/expanded_catalog_cross_references.csv"
BUILD = ROOT / "pipeline/galaxies/foreground/data/expanded_catalog_build.json"
OUTPUT = ROOT / "docs/rse/specs/expanded_foreground_photometry_and_morphology_catalog.md"


def _counts(frame: pd.DataFrame, column: str) -> str:
    return ", ".join(f"`{key}` {value}" for key, value in frame[column].value_counts().items())


def render() -> str:
    frame = pd.read_csv(CATALOG, dtype={"object_id": str})
    build = json.loads(BUILD.read_text())
    lines = [
        "# Expanded foreground photometry, morphology, and halo catalog",
        "",
        "**Status:** versioned audit product; scientific release remains governed by the independent validation and Figure 3 owner-review gates.",
        "",
        f"**Rows:** {len(frame)}",
        f"**Catalog SHA-256:** `{build['output_sha256']}`",
        "**Catalogs:** GSC 2.4.2 (`I/353/gsc242`), ALLWISE (`II/328/allwise`), CatWISE2020 (`II/365/catwise`), and unWISE (`II/363/unwise`).",
        "",
        "## Matching and quality contract",
        "",
        "Each 3-arcsecond cone response is stored in a normalized committed snapshot. Rows are sorted by exact spherical separation and then catalog identifier. The nearest row is selected only when the second-nearest separation is more than 0.3 arcsecond farther away. States are `matched`, `unmatched`, `ambiguous`, and `query_error`; a query error is never reported as an unmatched source.",
        "",
        f"- GSC 2.4.2: {_counts(frame, 'gsc242_status')}.",
        f"- ALLWISE: {_counts(frame, 'allwise_status')}.",
        f"- CatWISE2020: {_counts(frame, 'catwise2020_status')}.",
        f"- unWISE: {_counts(frame, 'unwise_status')}.",
        "",
        "The table retains selected separation, candidate count, second-nearest separation, release, retrieval time, response hash, identifiers, photometric errors, and native quality/artifact/extension flags. CatWISE2020 has no `ccf` field in its VizieR table; the catalog records this explicitly as `not_published_in_vizier_table`.",
        "",
        "GSC `Class 3` means non-star, not a secure galaxy classification. Crossmatches are audit evidence and never change the adjudicated census verdict.",
        "",
        "## Physical quantities",
        "",
        "- **Cluver et al. (2014):** diagnostic Equation 2, `log10(M*/Msun) = log10(L_W1/Lsun) - 2.54(W1-W2) - 0.17`, requires rest-frame color, valid W1/W2 photometry, and uncertainties. The current observed-frame catalog therefore leaves this diagnostic null with status `not_rest_frame`; no colorless fallback is used.",
        "- **Moster et al. (2013):** adopted galaxy stellar masses come only from the adjudicated census mass table and override ledger. Linear stellar mass in solar masses is inverted through the redshift-dependent Table 1 relation to obtain `M200c`.",
        "- **Radius:** `R200c = [3 M200c / (4 pi 200 rho_crit(z))]^(1/3)` in proper kpc. Concentration is not used to compute the radius.",
        "- **Dutton and Maccio (2014):** `log10(c200c)=a+b log10(M200c h / 10^12 Msun)`, with the calibration's published `h=0.671`, `b=-0.101+0.026z`, and `a=0.520+(0.905-0.520) exp[-0.617 z^1.21]`. It is used only for the scale radius `R200c/c200c`.",
        "- **Clusters:** retain catalog `M500` and `R500`. No galaxy stellar-mass relation or unvalidated cluster conversion is applied.",
        "- **Uncertainty:** native photometric errors and propagated W1-W2 errors are retained. Unknown adopted-mass, halo-mass, and radius uncertainties remain null with `pass_uncertainty_unavailable`; no numerical uncertainty is invented.",
        "",
        "## Stern et al. (2012) active-galaxy check",
        "",
        "The W1-W2 >= 0.8 selection is evaluated only for valid color and W2 <= 15.05 Vega. Outcomes are `selected_by_stern12`, `not_selected_within_depth`, `outside_validated_depth`, and `insufficient_color`. A blue color is not interpreted as proof of starlight dominance.",
        "",
        f"Observed outcomes: {_counts(frame, 'stern12_status')}.",
        "",
        "## Candidate inventory",
        "",
        "| FRB | Object | Type | Verdict | GSC state/class | ALLWISE state | Adopted log M* | M200c (Msun) | R200c (kpc) |",
        "|---|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in frame.itertuples(index=False):
        def fmt(value: object, pattern: str) -> str:
            return "--" if pd.isna(value) else format(float(value), pattern)

        lines.append(
            f"| {row.tns} | {row.object_id} | {row.type} | {row.final_verdict} | "
            f"{row.gsc242_status}/{fmt(row.gsc242_class, '.0f')} | {row.allwise_status} | "
            f"{fmt(row.adopted_log_mstar, '.3f')} | {fmt(row.m200c_msun, '.6e')} | "
            f"{fmt(row.r200c_kpc, '.3f')} |"
        )
    lines.extend(
        [
            "",
            "## Reproduction",
            "",
            "```bash",
            "uv run --project pipeline --frozen python -m galaxies.foreground.build_expanded_catalog --offline",
            "uv run --project pipeline --frozen python -m galaxies.foreground.build_sightline_halo_grid_input",
            "python3 scripts/build_expanded_foreground_provenance.py",
            "```",
            "",
            "The census verdict, duplicate, and budget fields are copied unchanged from the frozen registry. Redshift or budget re-adjudication requires a separate evidence record.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.write_text(render())
    print(args.output)


if __name__ == "__main__":
    main()
