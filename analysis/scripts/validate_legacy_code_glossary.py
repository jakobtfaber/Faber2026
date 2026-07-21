#!/usr/bin/env python3
"""Validate the retired letter+number planning-code glossary."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GLOSSARY = ROOT / "docs/rse/specs/legacy-code-glossary.md"
CONTEXT = ROOT / "CONTEXT.md"

REQUIRED_CODES = {
    "V1": "fit re-trust validation contract",
    "V2": "CHIME scattering-input lineage check",
    "V3": "energies pipeline re-validation",
    "V4": "foreground-census re-validation",
    "V5": "dispersion-budget re-validation",
    "V6": "association and observed-DM re-validation",
    "A1": "scintillation-to-scattering constraint layer",
    "A2": "extended-medium PBF kernel",
    "A3": "per-sightline geometry model selection",
    "A4": "rail-taxonomy retirement ADR amendment",
    "A5": "profile-component-count statistic",
    "B1": "burst configs for whitney, phineas, mahi, and isha",
    "B2": "CHIME regeneration for six never-generated co-detections",
    "B3": "mahi 700-725 MHz RFI inspection",
    "B4": "sample-wide CHIME-band ACF measurements",
    "B5": "joint CHIME+DSA two-screen analysis",
    "B6": "scintillation provenance and h17 tooling housekeeping",
    "B7": "census-aperture wording",
    "C1": "from-scratch twelve-burst scattering re-fit",
    "C2": "per-band systematics pass",
    "C3": "pipeline pin bump and table/figure regeneration",
    "D": "sightline analysis and foreground comparison",
    "E": "synthesis",
    "F": "manuscript reconciliation and polish",
    "G": "release mechanics",
    "S1": "deterministic trial set",
    "S2": "chance-coincidence units",
    "S3": "TOA estimator and time standards",
    "S4": "positive residual bias",
    "S5": "declination-conditioned CHIME rate",
    "S6": "repeater and clustering robustness",
    "S7": "jackknife and masking specification",
    "S8": "coverage-calibrated DM uncertainties",
    "S9": "host-DM table conversion and budget provenance",
    "S10": "phantom intervening-DM provenance",
    "S11": "missing-halo completeness systematic",
    "S12": "borderline b/R_vir probability",
    "S13": "cluster-aperture sensitivity",
    "S14": "intervening-scattering mapping",
    "S15": "Milky Way cross-reference and disk-model comparison",
    "S16": "modulation-index gate",
    "S17": "CHIME scintillation positive control",
    "S18": "missing scattering results and diagnostics",
    "S19": "effective-index sensitivity and delta-DM prior",
    "S20": "energy definitions and calibration budget",
    "P1": "windowed fine-channelization regeneration",
    "P2": "Route B ratio statistic",
    "P3": "delay-domain optimal estimator",
    "P4": "intrinsic-envelope modeling",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not GLOSSARY.exists():
        fail(f"missing glossary: {GLOSSARY.relative_to(ROOT)}")

    text = GLOSSARY.read_text(encoding="utf-8")
    missing = []
    for code, phrase in REQUIRED_CODES.items():
        row = re.compile(rf"^\|\s*`?{re.escape(code)}`?\s*\|.*{re.escape(phrase)}", re.M)
        if not row.search(text):
            missing.append(f"{code}: {phrase}")
    if missing:
        fail("glossary missing required mappings:\n" + "\n".join(missing))

    context = CONTEXT.read_text(encoding="utf-8")
    pending = context.split("**Explicit pending**:", 1)[1].split("**Pass 2 closeout", 1)[0]
    code_first = re.findall(
        r"\((\d+)\)\s+(?:[A-Z][A-Z0-9-]*\s+)?(?:§V|plan [A-Z]\d|V\d|A\d|B\d|C\d|P\d)",
        pending,
    )
    if code_first:
        fail("CONTEXT explicit pending still starts items with legacy code names")

    glossary_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    for target in glossary_links:
        if "://" in target or target.startswith("#"):
            continue
        path = (GLOSSARY.parent / target.split("#", 1)[0]).resolve()
        if not path.exists():
            fail(f"broken glossary link: {target}")

    print("legacy-code glossary validation passed")


if __name__ == "__main__":
    main()
