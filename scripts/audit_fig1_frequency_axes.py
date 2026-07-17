#!/usr/bin/env python3
"""Audit Figure 1 inputs and raw-header frequency ordering for both instruments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_DEFAULT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"
CHIME_METADATA_DEFAULT = Path.home() / "Data/Faber2026/dsa110/upchan_codetections"
FIXTURE_DEFAULT = ROOT / "pipeline/crossmatching/notebook_reproduction_fixture.json"
MANIFEST_DEFAULT = ROOT / "pipeline/data-manifest.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def order(first: float, last: float) -> str:
    if first > last:
        return "descending"
    if first < last:
        return "ascending"
    return "constant"


def audit(data_root: Path, metadata_root: Path, fixture_path: Path, manifest_path: Path) -> dict:
    fixture = json.loads(fixture_path.read_text())
    with manifest_path.open(newline="") as stream:
        manifest = list(csv.DictReader(stream))
    manifest_by_key = {(row["burst"].casefold(), row["telescope"]): row for row in manifest}
    records = []
    for burst in fixture["bursts"]:
        nick = burst["name"].casefold()
        file_nick = "johndoeII" if nick == "johndoeii" else nick
        dsa = burst["dsa"]
        dsa_last = dsa["fch1_mhz"] + dsa["foff_mhz"] * (dsa["nchans"] - 1)
        metadata_path = metadata_root / f"{file_nick}_time0_metadata.json"
        chime = json.loads(metadata_path.read_text())
        frequencies = np.asarray(chime["freq_mhz"], float)
        if not np.all(np.diff(frequencies) < 0):
            raise ValueError(f"{nick}: CHIME raw frequency metadata are not descending")
        if str(burst["chime_id"]) not in chime["h5"]:
            raise ValueError(f"{nick}: CHIME event id does not match tracked fixture")
        instruments = {}
        for telescope in ("chime", "dsa"):
            row = manifest_by_key[(file_nick.casefold(), telescope)]
            product = data_root / row["filename"]
            actual_hash = sha256(product)
            if actual_hash != row["sha256"] or product.stat().st_size != int(row["bytes"]):
                raise ValueError(f"{nick}/{telescope}: local product differs from manifest")
            instruments[telescope] = {
                "product_path": str(product),
                "product_shape": list(np.load(product, mmap_mode="r").shape),
                "product_sha256": actual_hash,
                "manifest_status": row["status"],
                "builder_status": row["builder"],
            }
        instruments["dsa"].update(
            {
                "raw_header_source": dsa["filterbank_path"],
                "nchans": dsa["nchans"],
                "tsamp_s": dsa["tsamp_s"],
                "first_channel_mhz": dsa["fch1_mhz"],
                "last_channel_mhz": dsa_last,
                "raw_channel_order": order(dsa["fch1_mhz"], dsa_last),
                "display_channel_order": "ascending",
            }
        )
        instruments["chime"].update(
            {
                "raw_header_source": chime["h5"],
                "extracted_metadata_path": str(metadata_path),
                "extracted_metadata_sha256": sha256(metadata_path),
                "nchans_present": int(frequencies.size),
                "delta_time_s": chime["delta_time"],
                "first_channel_mhz": float(frequencies[0]),
                "last_channel_mhz": float(frequencies[-1]),
                "min_channel_mhz": float(frequencies.min()),
                "max_channel_mhz": float(frequencies.max()),
                "raw_channel_order": order(frequencies[0], frequencies[-1]),
                "display_channel_order": "ascending",
            }
        )
        records.append({"nick": nick, "instruments": instruments})
    return {
        "schema_version": 1,
        "pipeline_revision": subprocess.check_output(
            ["git", "-C", str(ROOT / "pipeline"), "rev-parse", "HEAD"], text=True
        ).strip(),
        "audit_passed": len(records) == 12,
        "display_transform": "plot_codetection_gallery.load_band flips stored descending rows",
        "lineage_limit": "final _cntr_bpc builder is unverified; raw headers, byte-pinned products, and loader behavior are audited",
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DATA_DEFAULT)
    parser.add_argument("--metadata-root", type=Path, default=CHIME_METADATA_DEFAULT)
    parser.add_argument("--fixture", type=Path, default=FIXTURE_DEFAULT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(
        audit(args.data_root, args.metadata_root, args.fixture, args.manifest),
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
