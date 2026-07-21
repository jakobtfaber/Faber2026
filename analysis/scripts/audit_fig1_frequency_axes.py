#!/usr/bin/env python3
"""Audit Figure 1 inputs and raw-header frequency ordering for both instruments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shlex
import struct
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHIME_FULL_ROOT_DEFAULT = Path.home() / "Data/Faber2026/chimefrb/CHIME_bursts"
DSA_FULL_ROOT_DEFAULT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"
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


def root_for_telescope(
    telescope: str,
    chime_full_root: Path,
    dsa_full_root: Path,
) -> Path:
    roots = {"chime": Path(chime_full_root), "dsa": Path(dsa_full_root)}
    try:
        return roots[telescope]
    except KeyError as exc:
        raise ValueError(f"unknown telescope: {telescope!r}") from exc


def parse_sigproc_header(blob: bytes) -> dict:
    """Parse a SIGPROC filterbank header from its leading bytes.

    The format is a sequence of length-prefixed keyword strings, each followed
    by a binary value whose type the keyword implies, bracketed by
    HEADER_START/HEADER_END.
    """
    doubles = {"fch1", "foff", "tsamp", "tstart", "src_raj", "src_dej", "az_start", "za_start", "refdm", "period"}
    ints = {"nchans", "nbits", "nifs", "telescope_id", "machine_id", "data_type", "barycentric", "pulsarcentric", "nbeams", "ibeam", "nsamples"}
    strings = {"source_name", "rawdatafile"}

    def read_string(offset: int) -> tuple[str, int]:
        (length,) = struct.unpack_from("<i", blob, offset)
        if not 0 < length < 128:
            raise ValueError(f"implausible header string length {length} at offset {offset}")
        value = blob[offset + 4 : offset + 4 + length].decode("ascii")
        return value, offset + 4 + length

    keyword, cursor = read_string(0)
    if keyword != "HEADER_START":
        raise ValueError("blob does not begin with HEADER_START")
    header: dict = {}
    while True:
        keyword, cursor = read_string(cursor)
        if keyword == "HEADER_END":
            return header
        if keyword in doubles:
            (header[keyword],) = struct.unpack_from("<d", blob, cursor)
            cursor += 8
        elif keyword in ints:
            (header[keyword],) = struct.unpack_from("<i", blob, cursor)
            cursor += 4
        elif keyword in strings:
            header[keyword], cursor = read_string(cursor)
        else:
            raise ValueError(f"unhandled SIGPROC header keyword {keyword!r}")


def read_remote_sigproc_header(host: str, path: str, *, n_bytes: int = 4096) -> dict:
    """Fetch and parse the header of a filterbank living on a remote host."""
    blob = subprocess.check_output(
        ["ssh", "-o", "BatchMode=yes", host, f"head -c {n_bytes} {shlex.quote(path)}"]
    )
    return parse_sigproc_header(blob)


def mask_summary(product: Path) -> dict:
    """Per-channel validity of a stored product: non-finite or zero-variance
    rows are the channels the display renders as masked."""
    data = np.load(product, mmap_mode="r")
    finite = np.isfinite(data).all(axis=1)
    variance = np.zeros(data.shape[0])
    variance[finite] = np.nanvar(np.asarray(data[finite], dtype=np.float64), axis=1)
    valid = finite & (variance > 0)
    return {
        "n_channels": int(data.shape[0]),
        "n_time_samples": int(data.shape[1]),
        "n_valid_channels": int(valid.sum()),
        "n_masked_channels": int((~valid).sum()),
        "masked_fraction": round(float((~valid).mean()), 6),
    }


def audit(
    chime_full_root: Path,
    dsa_full_root: Path,
    metadata_root: Path,
    fixture_path: Path,
    manifest_path: Path,
    raw_header_host: str | None = None,
) -> dict:
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
            product = root_for_telescope(
                telescope, chime_full_root, dsa_full_root
            ) / row["filename"]
            actual_hash = sha256(product)
            if actual_hash != row["sha256"] or product.stat().st_size != int(row["bytes"]):
                raise ValueError(f"{nick}/{telescope}: local product differs from manifest")
            instruments[telescope] = {
                "product_path": str(product),
                "product_shape": list(np.load(product, mmap_mode="r").shape),
                "product_sha256": actual_hash,
                "product_mask_summary": mask_summary(product),
                "manifest_status": row["status"],
                "builder_status": row["builder"],
            }
        instruments["dsa"].update(
            {
                "raw_header_source": dsa["filterbank_path"],
                "header_validation": "tracked reproduction fixture",
                "raw_header_read": False,
                "nchans": dsa["nchans"],
                "tsamp_s": dsa["tsamp_s"],
                "channel_width_mhz": abs(dsa["foff_mhz"]),
                "first_channel_mhz": dsa["fch1_mhz"],
                "last_channel_mhz": dsa_last,
                "raw_channel_order": order(dsa["fch1_mhz"], dsa_last),
                "display_channel_order": "ascending",
            }
        )
        if raw_header_host:
            host, _, remote_path = dsa["filterbank_path"].rpartition(":")
            if host and host != raw_header_host:
                raise ValueError(f"{nick}: filterbank lives on {host!r}, not {raw_header_host!r}")
            header = read_remote_sigproc_header(raw_header_host, remote_path)
            mismatches = {
                key: (header[raw_key], dsa[fixture_key])
                for key, raw_key, fixture_key in (
                    ("fch1_mhz", "fch1", "fch1_mhz"),
                    ("foff_mhz", "foff", "foff_mhz"),
                    ("tsamp_s", "tsamp", "tsamp_s"),
                    ("nchans", "nchans", "nchans"),
                )
                if not np.isclose(header[raw_key], dsa[fixture_key], rtol=0, atol=1e-9)
            }
            if mismatches:
                raise ValueError(f"{nick}: raw filterbank header disagrees with fixture: {mismatches}")
            instruments["dsa"].update(
                {
                    "header_validation": f"raw SIGPROC header read over ssh from {raw_header_host}",
                    "raw_header_read": True,
                    "raw_header_fch1_mhz": header["fch1"],
                    "raw_header_foff_mhz": header["foff"],
                    "raw_header_tsamp_s": header["tsamp"],
                    "raw_header_nchans": header["nchans"],
                }
            )
        instruments["chime"].update(
            {
                "raw_header_source": chime["h5"],
                "header_validation": "hash-pinned metadata extracted from the raw h5",
                "raw_header_read": False,
                "extracted_metadata_path": str(metadata_path),
                "extracted_metadata_sha256": sha256(metadata_path),
                "nchans_present": int(frequencies.size),
                "delta_time_s": chime["delta_time"],
                "channel_width_mhz": round(float(np.median(np.abs(np.diff(frequencies)))), 9),
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
        "lineage_limit": (
            "final _cntr_bpc builder is unverified; byte-pinned products and loader "
            "behavior are audited. DSA header lineage: "
            + (
                "raw SIGPROC headers read remotely and matched to the tracked fixture"
                if raw_header_host
                else "tracked fixture values only (raw filterbanks not read in this run)"
            )
            + ". CHIME header lineage: hash-pinned metadata extracted from the raw h5."
        ),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    path_arg = lambda value: Path(value).expanduser()  # noqa: E731
    parser.add_argument(
        "--chime-full-root", type=path_arg, default=CHIME_FULL_ROOT_DEFAULT
    )
    parser.add_argument("--dsa-full-root", type=path_arg, default=DSA_FULL_ROOT_DEFAULT)
    parser.add_argument("--metadata-root", type=Path, default=CHIME_METADATA_DEFAULT)
    parser.add_argument("--fixture", type=Path, default=FIXTURE_DEFAULT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument(
        "--raw-header-host",
        help="ssh host holding the raw DSA filterbanks; when given, each header is "
        "read remotely and must match the tracked fixture (fail-closed)",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(
        audit(
            args.chime_full_root,
            args.dsa_full_root,
            args.metadata_root,
            args.fixture,
            args.manifest,
            raw_header_host=args.raw_header_host,
        ),
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
