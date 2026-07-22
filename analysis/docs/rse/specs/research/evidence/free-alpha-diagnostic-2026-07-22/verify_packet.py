#!/usr/bin/env python3
"""Verify the preserved scintillation-leakage evidence packet using stdlib only."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_PRODUCTS = {
    "scintleak_casey_C64_g0.0269_m1.0_dec_s0.json": 147,
    "scintleak_casey_C64_g0.302_m1.0_dec_s0.json": 148,
    "scintleak_wilhelm_C8_g0.13_m1.0_dec_s0.json": 149,
    "scintleak_wilhelm_C8_g2.236_m1.0_dec_s0.json": 150,
    "scintleak_casey_C64_g0.302_m1.0_sta_s0.json": 151,
    "scintleak_wilhelm_C8_g2.236_m1.0_sta_s0.json": 152,
}
EXPECTED_HASHED_PATHS = {
    "inputs/casey_campaign.json",
    "inputs/wilhelm_campaign.json",
    "jobs/fit_scintleak.sbatch",
    "source/PLPBF_FITTER_PROVENANCE.md",
    "source/scint_leakage_inject.py",
    *(f"logs/jtfsl_{job}.{suffix}" for job in range(147, 153) for suffix in ("err", "out")),
    *(f"products/{name}" for name in EXPECTED_PRODUCTS),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_hashes() -> None:
    lines = (ROOT / "SHA256SUMS").read_text().splitlines()
    entries = [line.split("  ", 1) for line in lines]
    paths = [relative for _, relative in entries]
    require(len(paths) == len(set(paths)), "duplicate SHA-256 manifest path")
    require(set(paths) == EXPECTED_HASHED_PATHS, "SHA-256 artifact roster changed")
    for expected, relative in entries:
        payload = (ROOT / relative).read_bytes()
        actual = hashlib.sha256(payload).hexdigest()
        require(actual == expected, f"hash mismatch: {relative}")


def verify_inputs() -> None:
    for burst in ("casey", "wilhelm"):
        record = json.loads((ROOT / "inputs" / f"{burst}_campaign.json").read_text())
        require(record["name"] == burst, f"wrong input name: {burst}")
        require(record["science_status"] == "non_detection", f"{burst} is not diagnostic")
        support = record["artifact_controls"]["subband_support"]
        require(not support["sufficient"], f"{burst} unexpectedly passes subband support")
        require(support["n_valid_subbands"] == 1, f"{burst} valid-subband count changed")


def verify_products_and_logs() -> tuple[float, float]:
    paths = sorted((ROOT / "products").glob("*.json"))
    require({path.name for path in paths} == set(EXPECTED_PRODUCTS), "product roster changed")

    all_biases: list[float] = []
    decorr_biases: list[float] = []
    for path in paths:
        record = json.loads(path.read_text())
        truth = record["truth"]
        low, median, high = record["alpha_apparent"]
        require(record["mode"] == "scint_leakage", f"wrong mode: {path.name}")
        require(truth["alpha"] == record["alpha_true"] == 4.0, f"wrong truth: {path.name}")
        require(truth["m"] == 1.0, f"non-maximal modulation: {path.name}")
        require(truth["seed"] == 0, f"seed changed: {path.name}")
        require(low <= median <= high, f"unordered interval: {path.name}")
        require(low < 4.0 < high, f"90% interval misses alpha=4: {path.name}")
        require(math.isclose(record["bias"], median - 4.0, abs_tol=1e-12), f"bias mismatch: {path.name}")
        # The driver builds an inclusive 400--800 MHz linspace, so its actual
        # spacing is 400/(nchan-1). The saved chan_width field instead records
        # the nominal 400/nchan width. Verify both semantics explicitly.
        nominal_width = 400.0 / truth["nchan_target"]
        actual_grid_spacing = 400.0 / (truth["nchan_target"] - 1)
        require(math.isclose(truth["chan_width_mhz_target"], nominal_width, abs_tol=1e-12), f"nominal width mismatch: {path.name}")
        expected_m_eff = min(1.0, math.sqrt(truth["gamma_mhz"] / actual_grid_spacing))
        require(math.isclose(truth["m_eff_target"], expected_m_eff, abs_tol=1e-12), f"m_eff mismatch: {path.name}")
        require(record["verdict"] == "no leakage (alpha recovers ~4)", f"verdict mismatch: {path.name}")

        job = EXPECTED_PRODUCTS[path.name]
        log = (ROOT / "logs" / f"jtfsl_{job}.out").read_text()
        require(f"JOB={job}" in log and "RC=0" in log, f"job failed or mismatched: {job}")
        require(path.name in log, f"log does not name product: {job}")
        require(re.search(r"VERDICT: no leakage \(alpha recovers ~4\)", log) is not None, f"log verdict mismatch: {job}")
        require((ROOT / "logs" / f"jtfsl_{job}.err").stat().st_size == 0, f"stderr not empty: {job}")

        all_biases.append(abs(record["bias"]))
        if truth["decorr"]:
            decorr_biases.append(abs(record["bias"]))

    require(len(decorr_biases) == 4, "expected four decorrelating injections")
    require(len(all_biases) - len(decorr_biases) == 2, "expected two static controls")
    max_all = max(all_biases)
    max_decorr = max(decorr_biases)
    require(max_all < 0.02, "six-run absolute-bias bound failed")
    require(max_decorr < 0.015, "decorrelating-injection bound failed")
    return max_all, max_decorr


def main() -> None:
    json.loads((ROOT / "manifest.json").read_text())
    verify_hashes()
    verify_inputs()
    max_all, max_decorr = verify_products_and_logs()
    print("PASS: 23 copied artifacts match SHA-256 manifest")
    print("PASS: 6/6 intervals contain alpha=4; logs report RC=0; stderr is empty")
    print(f"PASS: max |bias| all runs = {max_all:.12f} < 0.02")
    print(f"PASS: max |bias| decorrelating runs = {max_decorr:.12f} < 0.015")


if __name__ == "__main__":
    main()
