#!/usr/bin/env python3
"""Build raw-layer (stratum-0) certificates for the twelve CHIME singlebeam voltage files.

Wayfinder ticket 17 (Stratum 0 / L0 raw data certification).
Binding definition: docs/rse/specs/notes/definition-raw-chime-data-2026-07-19.md
Writes docs/rse/certificates/l0-raw-voltage-certificates.json.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "docs/rse/certificates/l0-raw-voltage-certificates.json"

VOLTAGE_FILES = [
    ("zach", "210456524"),
    ("whitney", "215063905"),
    ("oran", "224263996"),
    ("isha", "252069198"),
    ("wilhelm", "253635173"),
    ("phineas", "274819243"),
    ("freya", "278720455"),
    ("johndoeII", "311723353"),
    ("hamilton", "318353610"),
    ("mahi", "354049284"),
    ("chromatica", "356959136"),
    ("casey", "362593221"),
]

H17_BASE = "/data/Faber2026/data/chime-frb"
CANFAR_BASE = "arc:projects/chime_frb/data/chime/baseband/processed"

def build_voltage_certificates() -> list[dict]:
    certs = []
    for nick, event_id in VOLTAGE_FILES:
        filename = f"singlebeam_{event_id}.h5"
        certs.append({
            "nick": nick,
            "event_id": event_id,
            "product": "chime_voltage_singlebeam",
            "format": "HDF5_voltage",
            "file": filename,
            "host": "h17",
            "host_path": f"{H17_BASE}/{nick.lower()}/{filename}",
            "upstream_archive": f"{CANFAR_BASE}/<date>/astro_{event_id}/{filename}",
            "stratum": "L0",
            "is_raw": True,
            "frozen_dm": None,
            "notes": "True raw CHIME baseband voltage file (~1 GB); DM applied at dynamic spectrum build time."
        })
    return certs

def main() -> None:
    certs = build_voltage_certificates()
    OUT_JSON.write_text(json.dumps(certs, indent=2) + "\n")
    print(f"wrote {OUT_JSON} ({len(certs)} raw CHIME voltage certificates)")

if __name__ == "__main__":
    main()
