#!/usr/bin/env python3
"""Verify the preserved free-alpha mechanism evidence packet."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCINT_PRODUCTS = {
    "scintleak_casey_C64_g0.0269_m1.0_dec_s0.json": 147,
    "scintleak_casey_C64_g0.302_m1.0_dec_s0.json": 148,
    "scintleak_wilhelm_C8_g0.13_m1.0_dec_s0.json": 149,
    "scintleak_wilhelm_C8_g2.236_m1.0_dec_s0.json": 150,
    "scintleak_casey_C64_g0.302_m1.0_sta_s0.json": 151,
    "scintleak_wilhelm_C8_g2.236_m1.0_sta_s0.json": 152,
}
COMPONENT_PRODUCTS = {
    "plpbf_leakage_b3.99_tau0.019_W1.0_a0.1_dt0.1_s0.json": 121,
    "plpbf_leakage_b3.99_tau0.019_W1.0_a0.1_dt0.3_s0.json": 122,
    "plpbf_leakage_b3.99_tau0.019_W1.0_a0.1_dt0.6_s0.json": 123,
    "plpbf_leakage_b3.99_tau0.019_W1.0_a0.15_dt0.5_s0.json": None,
    "plpbf_leakage_b3.99_tau0.019_W1.0_a0.2_dt0.1_s0.json": 124,
    "plpbf_leakage_b3.99_tau0.019_W1.0_a0.2_dt0.3_s0.json": 125,
    "plpbf_leakage_b3.99_tau0.019_W1.0_a0.2_dt0.6_s0.json": 126,
}
BOTH_PRODUCTS = {
    "plpbf_both_b3.5_si10.0_W1.0_a0.2_dt0.1_s0.json": None,
    "plpbf_both_b3.5_si10.0_W1.0_a0.4_dt0.1_s0.json": 137,
    "plpbf_both_b3.5_si3.0_W0.3_a0.2_dt0.1_s0.json": 138,
    "plpbf_both_b3.5_si3.0_W1.0_a0.2_dt0.1_s0.json": 135,
    "plpbf_both_b3.5_si3.0_W1.0_a0.4_dt0.1_s0.json": 136,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_hashes() -> None:
    lines = (ROOT / "SHA256SUMS").read_text().splitlines()
    require(len(lines) == 60, "expected hashes for 60 copied artifacts")
    manifested = set()
    for line in lines:
        expected, relative = line.split("  ", 1)
        manifested.add(relative)
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        require(actual == expected, f"hash mismatch: {relative}")
    require(len(manifested) == len(lines), "duplicate SHA-256 manifest path")
    copied = {
        str(path.relative_to(ROOT))
        for directory in ("inputs", "jobs", "logs", "products", "source")
        for path in (ROOT / directory).rglob("*")
        if path.is_file()
    }
    require(manifested == copied, "SHA-256 roster differs from copied artifacts")


def verify_inputs() -> None:
    for burst in ("casey", "wilhelm"):
        record = json.loads((ROOT / "inputs" / f"{burst}_campaign.json").read_text())
        require(record["name"] == burst, f"wrong input name: {burst}")
        require(record["science_status"] == "non_detection", f"{burst} is not diagnostic")
        support = record["artifact_controls"]["subband_support"]
        require(not support["sufficient"], f"{burst} unexpectedly passes subband support")
        require(support["n_valid_subbands"] == 1, f"{burst} valid-subband count changed")


def verify_roster(roster: dict) -> None:
    for key, directory, expected in (
        ("component_leakage", "component-leakage", COMPONENT_PRODUCTS),
        ("tail_plus_component", "tail-plus-component", BOTH_PRODUCTS),
    ):
        rows = {row["product"]: row for row in roster[key]}
        require(set(rows) == set(expected), f"{key} manifest roster changed")
        for product, job in expected.items():
            require(rows[product]["job"] == job, f"{key} job mapping changed: {product}")
            record = json.loads((ROOT / "products" / directory / product).read_text())
            require(math.isclose(rows[product]["bias"], record["bias"], abs_tol=1e-15), f"{key} roster bias changed: {product}")


def verify_scintillation() -> tuple[float, float]:
    paths = sorted((ROOT / "products").glob("*.json"))
    require({path.name for path in paths} == set(SCINT_PRODUCTS), "scintillation roster changed")
    all_biases: list[float] = []
    decorr_biases: list[float] = []
    for path in paths:
        record = json.loads(path.read_text())
        truth = record["truth"]
        low, median, high = record["alpha_apparent"]
        require(record["mode"] == "scint_leakage", f"wrong mode: {path.name}")
        require(truth["alpha"] == record["alpha_true"] == 4.0, f"wrong truth: {path.name}")
        require(truth["m"] == 1.0 and truth["seed"] == 0, f"injection changed: {path.name}")
        require(low <= median <= high and low < 4.0 < high, f"interval misses alpha=4: {path.name}")
        require(math.isclose(record["bias"], median - 4.0, abs_tol=1e-12), f"bias mismatch: {path.name}")
        nominal_width = 400.0 / truth["nchan_target"]
        actual_grid_spacing = 400.0 / (truth["nchan_target"] - 1)
        require(math.isclose(truth["chan_width_mhz_target"], nominal_width, abs_tol=1e-12), f"nominal width mismatch: {path.name}")
        expected_m_eff = min(1.0, math.sqrt(truth["gamma_mhz"] / actual_grid_spacing))
        require(math.isclose(truth["m_eff_target"], expected_m_eff, abs_tol=1e-12), f"m_eff mismatch: {path.name}")
        require(record["verdict"] == "no leakage (alpha recovers ~4)", f"verdict mismatch: {path.name}")
        job = SCINT_PRODUCTS[path.name]
        log = (ROOT / "logs" / f"jtfsl_{job}.out").read_text()
        require(f"JOB={job}" in log and "RC=0" in log and path.name in log, f"log mismatch: {job}")
        require(re.search(r"VERDICT: no leakage \(alpha recovers ~4\)", log) is not None, f"log verdict mismatch: {job}")
        require((ROOT / "logs" / f"jtfsl_{job}.err").stat().st_size == 0, f"stderr not empty: {job}")
        all_biases.append(abs(record["bias"]))
        if truth["decorr"]:
            decorr_biases.append(abs(record["bias"]))
    require(len(decorr_biases) == 4, "expected four decorrelating injections")
    require(max(all_biases) < 0.02 and max(decorr_biases) < 0.015, "scintillation bias bound failed")
    return max(all_biases), max(decorr_biases)


def verify_grid(directory: str, expected: dict[str, int | None], mode: str, log_prefix: str, marker: str) -> tuple[float, str]:
    paths = sorted((ROOT / "products" / directory).glob("*.json"))
    require({path.name for path in paths} == set(expected), f"{directory} roster changed")
    biases: list[tuple[float, str]] = []
    for path in paths:
        record = json.loads(path.read_text())
        truth = record["truth"]
        low, median, high = record["alpha_apparent"]
        require(record["mode"] == mode, f"wrong mode: {path.name}")
        require(low <= median <= high, f"unordered interval: {path.name}")
        require(math.isclose(record["bias"], median - record["alpha_true"], abs_tol=1e-12), f"bias mismatch: {path.name}")
        require(truth["alpha"] == record["alpha_true"] and truth["snr"] == 40.0, f"truth mismatch: {path.name}")
        job = expected[path.name]
        if job is not None:
            log = (ROOT / "logs" / f"{log_prefix}_{job}.out").read_text()
            require(f"JOB={job}" in log and "RC=0" in log, f"job failed or mismatched: {job}")
            match = re.search(rf"{marker} ([+-]?\d+\.\d+)", log)
            require(match is not None and math.isclose(float(match.group(1)), record["bias"], abs_tol=5e-4), f"rounded log bias mismatch: {job}")
            require((ROOT / "logs" / f"{log_prefix}_{job}.err").stat().st_size == 0, f"stderr not empty: {job}")
        biases.append((record["bias"], path.name))
    return min(biases)


def main() -> None:
    json.loads((ROOT / "manifest.json").read_text())
    roster = json.loads((ROOT / "grid_roster.json").read_text())
    verify_hashes()
    verify_inputs()
    verify_roster(roster)
    max_all, max_decorr = verify_scintillation()
    component_min = verify_grid("component-leakage", COMPONENT_PRODUCTS, "leakage", "plik", "LEAKAGE-BIAS")
    both_min = verify_grid("tail-plus-component", BOTH_PRODUCTS, "both", "plbo", "BOTH-BIAS")
    require(component_min == (-0.43040582429955254, "plpbf_leakage_b3.99_tau0.019_W1.0_a0.2_dt0.1_s0.json"), "component minimum changed")
    require(both_min == (-0.8561575297363464, "plpbf_both_b3.5_si10.0_W1.0_a0.4_dt0.1_s0.json"), "combined minimum changed")
    print("PASS: 60 copied artifacts match SHA-256 manifest and filesystem roster")
    print("PASS: scintillation 6/6 intervals contain alpha=4; scheduled logs report RC=0; stderr is empty")
    print(f"PASS: max |bias| all scintillation runs = {max_all:.12f} < 0.02")
    print(f"PASS: max |bias| decorrelating runs = {max_decorr:.12f} < 0.015")
    print(f"PASS: component grid 7 products (6 logged); minimum bias = {component_min[0]:.15f}")
    print(f"PASS: combined grid 5 products (4 logged); minimum bias = {both_min[0]:.15f}")


if __name__ == "__main__":
    main()
