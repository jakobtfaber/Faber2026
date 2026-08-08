#!/usr/bin/env python3
"""Fail-closed validation for profile-component injection campaigns.

This validates campaign evidence only. It never selects manuscript component
counts and deliberately rejects autocorrelation-function screen-count results.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "faber2026-profile-component-calibration/v1"
REQUIRED_ARMS = {"gain_s2_1", "gain_s2_10", "gain_s2_100"}


def validate_campaign(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    if payload.get("domain") != "time_frequency_profile":
        errors.append("domain must be time_frequency_profile; ACF screen counts are inadmissible")
    if payload.get("status") not in {"calibration_only", "scientific_gate_pending"}:
        errors.append("status must remain calibration_only or scientific_gate_pending")
    if payload.get("manuscript_count_setting_enabled") is not False:
        errors.append("manuscript_count_setting_enabled must be false before owner ratification")

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        for field in ("pipeline_git_sha", "config_sha256", "input_manifest_sha256", "command", "seed_rule"):
            if not provenance.get(field):
                errors.append(f"provenance.{field} is required")

    contract = payload.get("comparison_contract")
    if not isinstance(contract, dict):
        errors.append("comparison_contract must be an object")
    else:
        if contract.get("same_likelihood") is not True:
            errors.append("comparison_contract.same_likelihood must be true")
        if contract.get("same_time_frequency_support") is not True:
            errors.append("comparison_contract.same_time_frequency_support must be true")
        if contract.get("ordered_arrivals") is not True:
            errors.append("comparison_contract.ordered_arrivals must be true")
        arms = set(contract.get("gain_prior_arms", []))
        if not REQUIRED_ARMS.issubset(arms):
            errors.append("comparison_contract.gain_prior_arms must include 1, 10, and 100")

    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        errors.append("cells must be a non-empty array")
        return errors

    seen: set[tuple[Any, ...]] = set()
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            errors.append(f"cells[{index}] must be an object")
            continue
        key = tuple(cell.get(name) for name in ("instrument", "true_count", "snr", "separation_bins", "width_bins"))
        if key in seen:
            errors.append(f"cells[{index}] duplicates a calibration cell")
        seen.add(key)
        if cell.get("instrument") not in {"CHIME/FRB", "DSA-110"}:
            errors.append(f"cells[{index}].instrument is unsupported")
        true_count = cell.get("true_count")
        if type(true_count) is not int or true_count < 1:
            errors.append(f"cells[{index}].true_count must be a positive integer")
        n = cell.get("n_injections")
        confusion = cell.get("selected_count_histogram")
        if type(n) is not int or n < 1:
            errors.append(f"cells[{index}].n_injections must be positive")
        if not isinstance(confusion, dict):
            errors.append(f"cells[{index}].selected_count_histogram must be an object")
        elif type(n) is int:
            try:
                total = sum(int(value) for value in confusion.values())
            except (TypeError, ValueError):
                errors.append(f"cells[{index}].selected_count_histogram values must be integers")
            else:
                if total != n:
                    errors.append(f"cells[{index}] histogram total {total} != n_injections {n}")
        for metric in ("overcount_rate", "undercount_rate", "exact_recovery_rate"):
            value = cell.get(metric)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                errors.append(f"cells[{index}].{metric} must be finite and in [0, 1]")
        if all(isinstance(cell.get(metric), (int, float)) for metric in
               ("overcount_rate", "undercount_rate", "exact_recovery_rate")):
            total_rate = sum(float(cell[metric]) for metric in
                             ("overcount_rate", "undercount_rate", "exact_recovery_rate"))
            if not math.isclose(total_rate, 1.0, abs_tol=1e-8):
                errors.append(f"cells[{index}] recovery rates must sum to 1")
        if cell.get("all_gain_prior_arms_agree") is not True:
            errors.append(f"cells[{index}] gain-prior arms do not agree")
        if cell.get("mode_matched") is not True:
            errors.append(f"cells[{index}] is not mode matched")

    gate = payload.get("scientific_gate")
    if not isinstance(gate, dict):
        errors.append("scientific_gate must be an object")
    else:
        if gate.get("owner_ratified") is not False:
            errors.append("scientific_gate.owner_ratified must remain false in this evidence packet")
        for field in ("maximum_overcount_rate", "maximum_undercount_rate", "supported_domain"):
            if gate.get(field) is not None:
                errors.append(f"scientific_gate.{field} must remain null until owner ratification")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.campaign.read_text(encoding="utf-8"))
    errors = validate_campaign(payload)
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
