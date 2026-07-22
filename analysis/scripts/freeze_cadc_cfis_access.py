#!/usr/bin/env python3
"""Freeze an authenticated CADC/CFIS access result without exposing credentials."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


ENDPOINT = "https://ws-uv.canfar.net/youcat/sync"
QUERY = "SELECT TOP 1 ID, u_ALPHA_J2000, u_DELTA_J2000 FROM cfht.cfiscat"
DENIAL = (
    "Table [ cfht.cfiscat ] is not found in TapSchema. "
    "Possible reasons: table does not exist or permission is denied."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_response(response: bytes) -> str:
    text = response.decode("utf-8", errors="replace").strip()
    if text == DENIAL:
        return "access_denied"
    if "cfht.cfiscat" in text and "not found in TapSchema" in text:
        return "access_denied"
    return "query_response_unclassified"


def certificate_metadata(certfile: Path) -> dict[str, str]:
    result = subprocess.run(
        [
            "openssl",
            "x509",
            "-in",
            str(certfile),
            "-noout",
            "-subject",
            "-issuer",
            "-enddate",
            "-fingerprint",
            "-sha256",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    values = {}
    for line in result.stdout.splitlines():
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def authenticated_query(certfile: Path) -> tuple[str, int, bytes]:
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "table": "cfht.cfiscat",
        "method": "sync",
        "format": "tsv",
        "query": QUERY,
    }
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    marker = b"\n__HTTP_STATUS__:"
    command = [
        "curl",
        "-sS",
        "--cert",
        str(certfile),
        "--get",
        ENDPOINT,
        "--write-out",
        "\n__HTTP_STATUS__:%{http_code}",
    ]
    for key, value in params.items():
        command.extend(["--data-urlencode", f"{key}={value}"])
    result = subprocess.run(command, check=True, capture_output=True)
    response, encoded_status = result.stdout.rsplit(marker, 1)
    return url, int(encoded_status), response


def vospace_handshake(certfile: Path) -> str:
    result = subprocess.run(
        [
            "vls",
            "--certfile",
            str(certfile),
            "arc:home/jfaber/baseband_morphologies/chime_dsa_codetections/",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def freeze(certfile: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=False)
    url, http_status, response = authenticated_query(certfile)
    status = classify_response(response)
    if status != "access_denied":
        raise RuntimeError(f"unexpected CFIS response: {status}")
    handshake = vospace_handshake(certfile)
    retrieved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    response_path = output_dir / "cfis-query-response.txt"
    response_path.write_bytes(response)
    handshake_path = output_dir / "vospace-read-handshake.txt"
    handshake_path.write_text(handshake, encoding="utf-8")
    query_path = output_dir / "cfis-query.adql"
    query_path.write_text(QUERY + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "status": status,
        "service": "CADC YouCat TAP",
        "table": "cfht.cfiscat",
        "release": "UNIONS CFIS DR3",
        "endpoint": ENDPOINT,
        "request_url": url,
        "http_status": http_status,
        "query_file": query_path.name,
        "query_sha256": sha256(query_path.read_bytes()),
        "response_file": response_path.name,
        "response_bytes": len(response),
        "response_sha256": sha256(response),
        "retrieved_at": retrieved_at,
        "authenticated": True,
        "certificate": certificate_metadata(certfile),
        "vospace_handshake_file": handshake_path.name,
        "vospace_handshake_sha256": sha256(handshake_path.read_bytes()),
        "interpretation": (
            "The authenticated CADC identity works but cannot see cfht.cfiscat; "
            "under official CFIS documentation this is access_denied, not unmatched."
        ),
        "scientific_changes_authorized": False,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    sums = [
        f"{sha256(path.read_bytes())}  {path.name}"
        for path in sorted(output_dir.iterdir())
        if path.name != "SHA256SUMS"
    ]
    (output_dir / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certfile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(freeze(args.certfile, args.output_dir))


if __name__ == "__main__":
    main()
