"""Render the manuscript DM table from the reviewed adopted-DM catalog."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "analysis" / "dm-joint-phase-v2" / "manuscript_dm_catalog.csv"
OUT = ROOT / "dm_measurements_table.tex"

HEAD = r"""% Adopted values: analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv
% Do not hand-edit without updating the catalog and the DM decision record.
\begin{deluxetable*}{lrrrr}
\tabletypesize{\scriptsize}
\tablecaption{Verified structure-optimizing dispersion measures. CHIME/FRB and
DSA-110 were fitted independently with the phase-coherence method described in
Section~\ref{sec:dm-measurement}. The adopted value is the CHIME/FRB result for
every burst because its broader fractional bandwidth gives substantially greater
DM leverage and the measured coherence curves are narrower and more stable.
DSA-110 is retained as an independent cross-check; $\Delta\mathrm{DM}$ is
CHIME minus DSA. Uncertainties include channel-block jackknife, resolution,
fluctuation-frequency-cutoff, and numerical-floor terms. DM in
$\mathrm{pc\,cm^{-3}}$. \label{tab:dm-measurements}}
\tablehead{\colhead{Burst} & \colhead{$\mathrm{DM_{CHIME}}$} &
\colhead{$\mathrm{DM_{DSA}}$} & \colhead{$\Delta\mathrm{DM}$} &
\colhead{$\mathrm{DM_{adopted}}$}}
\startdata
"""

TAIL = "\\enddata\n\\end{deluxetable*}\n"


def render() -> str:
    with CATALOG.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 12:
        raise ValueError(f"DM catalog must contain 12 rows, got {len(rows)}")
    body = []
    for row in rows:
        if row["adoption"] != "chime_primary":
            raise ValueError(f"{row['nick']}: expected chime_primary adoption")
        body.append(
            f'{row["tns"]} & '
            f'${float(row["chime_dm"]):.4f}\\pm{float(row["chime_sigma"]):.4f}$ & '
            f'${float(row["dsa_dm"]):.4f}\\pm{float(row["dsa_sigma"]):.4f}$ & '
            f'${float(row["chime_minus_dsa"]):+.4f}$ & '
            f'${float(row["adopted_dm"]):.4f}\\pm{float(row["adopted_sigma"]):.4f}$ \\\\'
        )
    return HEAD + "\n".join(body) + "\n" + TAIL


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
