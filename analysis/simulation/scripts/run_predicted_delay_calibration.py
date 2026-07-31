#!/usr/bin/env python3
"""Predicted-delay trigger calibration campaign driver (plan Phases 4-5).

Per-cell checkpointing mirrors run_a1_trigger_calibration.py: each finished
cell is written to <out>.cells/<cell>.json immediately; rerunning skips
finished cells.  The report states the trigger remains unavailable for
model selection until the owner accepts an operating point.

Full campaign:
  python simulation/scripts/run_predicted_delay_calibration.py \
      --out simulation/experiments/predicted-delay-trigger/calibration.json
Anchor set (Phase 5, nested-sampling surrogate-fidelity check):
  ... --anchor
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from simulation.predicted_delay_trigger import (  # noqa: E402
    ANCHOR_CELLS,
    ANCHOR_INJECTIONS,
    DT_MS,
    N_INJECTIONS,
    POWER_RS,
    RATES,
    SEED0,
    TRUTH_TAU1_1GHZ_MS,
    anchor_pair,
    declared_cells,
    rate_table,
    run_cell,
)

MIN_TAU2_SAMPLES = 2.0


def _assert_resolvable():
    """Plan Risk Assessment: no declared power cell may inject a
    sub-resolution second screen."""
    band_center = 0.6
    tau1_band = TRUTH_TAU1_1GHZ_MS * band_center ** -4.0
    smallest = min(POWER_RS) * tau1_band
    if smallest < MIN_TAU2_SAMPLES * DT_MS:
        raise SystemExit(
            f"declared power grid injects tau2={smallest:.6f} ms < "
            f"{MIN_TAU2_SAMPLES} samples at dt={DT_MS} ms")


def _run_and_checkpoint(kind, key, snr, value, idx, n, cells_dir):
    ck = Path(cells_dir) / f"{key.replace(':', '_')}.json"
    if ck.exists():
        return kind, key, json.loads(ck.read_text())["records"]
    records = run_cell(kind, snr, value, n, idx, seed0=SEED0)
    ck.write_text(json.dumps(
        {"records": records, "kind": kind, "snr": snr, "value": value,
         "cell_index": idx, "seed0": SEED0}))
    finite = sum(1 for r in records if np.isfinite(r["statistic"]))
    print(f"[cell {idx}] {key}: n={len(records)} finite={finite}",
          flush=True)
    return kind, key, records


def _write_report(out_path, table, nulls, powers, anchor, complete):
    git_sha = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    report = {
        "schema": 1,
        "source_revision": git_sha,
        "seed0": SEED0,
        "rates": list(RATES),
        "table": table,
        "n_null_cells": len(nulls),
        "n_power_cells": len(powers),
        "anchor": anchor,
        "complete": complete,
        "status": (("" if complete else "PARTIAL CELL SELECTION - not the "
                    "declared campaign. ")
                   + "PRELIMINARY: trigger remains unavailable for model "
                   "selection until the owner accepts an operating point"),
    }
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    md = out_path.with_suffix(".md")
    lines = [
        "# Predicted-delay trigger calibration report"
        + ("" if complete else " (PARTIAL cell selection)"), "",
        f"Source revision: `{git_sha}`; seed0 {SEED0}.", "",
        "The trigger remains **unavailable for model selection** until the",
        "owner accepts an operating point from this table (ticket 04a).", "",
        "## Conservative false-escalation envelopes (max over null cells)", "",
        "| rate | statistic threshold |", "|---|---|",
    ]
    for rate, thr in table["thresholds"].items():
        lines.append(f"| {rate} | {thr:.3f} |")
    lines += ["", "## Detection rate per power cell at each envelope", "",
              "| cell | " + " | ".join(str(r) for r in RATES) + " |",
              "|---|" + "---|" * len(RATES)]
    for cell in sorted(powers):
        row = " | ".join(
            f"{table['detection'][rate][cell]:.3f}" for rate in RATES)
        lines.append(f"| {cell} | {row} |")
    if anchor:
        shifts = [abs(a["ml_pvalue"] - a["nested_pvalue"])
                  for a in anchor if np.isfinite(a.get("ml_pvalue", np.nan))
                  and np.isfinite(a.get("nested_pvalue", np.nan))]
        mean_shift = float(np.mean(shifts)) if shifts else float("nan")
        verdict = ("USABLE" if np.isfinite(mean_shift) and mean_shift <= 0.05
                   else "UNUSABLE - report stays PRELIMINARY")
        lines += ["", "## Nested-sampling anchor (surrogate fidelity)", "",
                  f"{len(anchor)} paired injections; mean |Delta p| = "
                  f"{mean_shift:.4f}; ML surrogate {verdict}."]
    else:
        lines += ["", "## Nested-sampling anchor", "",
                  "Not yet run (`--anchor`); report stays PRELIMINARY."]
    md.write_text("\n".join(lines) + "\n")
    print(f"wrote {out_path} and {md}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(
        "simulation/experiments/predicted-delay-trigger/calibration.json"))
    ap.add_argument("--injections", type=int, default=N_INJECTIONS)
    ap.add_argument("--cells", action="append",
                    help="restrict to these cell keys; repeatable")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--workers", type=int, default=4,
                    help="process-parallel cells (hard cap 4: the "
                         "workstation must not saturate)")
    ap.add_argument("--anchor", action="store_true",
                    help="run the Phase 5 nested-sampling anchor set")
    ap.add_argument("--anchor-nlive", type=int, default=500)
    args = ap.parse_args()

    _assert_resolvable()
    cells = declared_cells()
    if args.cells:
        cells = [c for c in cells if c[1] in set(args.cells)]
        if not cells:
            raise SystemExit(f"no declared cell matches {args.cells}")
    if args.plan_only:
        for _kind, key, _snr, _value, _idx in cells:
            print(key)
        print(f"{len(cells)} cells; out root {args.out}")
        return

    workers = min(args.workers, 4)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cells_dir = args.out.parent / (args.out.stem + ".cells")
    cells_dir.mkdir(parents=True, exist_ok=True)

    nulls, powers = {}, {}
    work = [(kind, key, snr, value, idx, args.injections, str(cells_dir))
            for kind, key, snr, value, idx in cells]
    if workers > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_run_and_checkpoint, *w) for w in work]
            for fut in as_completed(futures):
                kind, key, records = fut.result()
                (nulls if kind == "null" else powers)[key] = [
                    r["statistic"] for r in records]
    else:
        for w in work:
            kind, key, records = _run_and_checkpoint(*w)
            (nulls if kind == "null" else powers)[key] = [
                r["statistic"] for r in records]

    anchor = None
    anchor_path = args.out.parent / "anchor.json"
    if args.anchor:
        anchor = []
        for kind, snr, value in ANCHOR_CELLS:
            for injection in range(ANCHOR_INJECTIONS):
                anchor.append(anchor_pair(
                    kind, snr, value, SEED0 + 900_000 + injection,
                    nlive=args.anchor_nlive))
        anchor_path.write_text(json.dumps(anchor, indent=2) + "\n")
    elif anchor_path.exists():
        anchor = json.loads(anchor_path.read_text())

    declared_keys = {c[1] for c in declared_cells()}
    present_keys = set(nulls) | set(powers)
    if not args.cells and present_keys != declared_keys:
        missing = sorted(declared_keys - present_keys)
        raise SystemExit(
            f"full campaign incomplete: {len(missing)} declared cells "
            f"missing (first: {missing[:3]}); no report written")
    if nulls and powers:
        table = rate_table(nulls, powers, rates=RATES)
        _write_report(args.out, table, nulls, powers, anchor,
                      complete=(present_keys == declared_keys))
    else:
        print("partial cell selection: no report written "
              f"({len(nulls)} null, {len(powers)} power cells present)")


if __name__ == "__main__":
    main()
