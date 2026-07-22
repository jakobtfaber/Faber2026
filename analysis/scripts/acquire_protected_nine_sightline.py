#!/usr/bin/env python3
"""Freeze authenticated WISE--PS1--STRM evidence for nine FRB sightlines.

Credentials stay in macOS Keychain.  The script records the exact SQL, CasJobs
job metadata, downloaded response bytes, and hashes.  The server query uses a
one-arcsecond guard rectangle around the approved inclusive 15-arcminute cone;
independent replay applies the exact spherical boundary to these preserved
native rows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTEXT = "HLSP_WISE_PS1_STRM"
SOURCE_TABLE = "catalogRecordRowStore"
RELEASE = "WISE-PS1-STRM v1 (2022-09-14)"
DOI = "10.17909/wf64-kq10"
RADIUS_ARCMIN = 15.0
GUARD_ARCSEC = 1.0
FINAL_JOB_CODES = {3: "cancelled", 4: "failed", 5: "finished"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_sightlines(path: Path) -> list[dict[str, Any]]:
    """Select the nine rows with finite positive input z_spec values."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    selected = []
    for row in rows:
        try:
            input_z = float(row["z_spec"])
        except (TypeError, ValueError):
            continue
        if not math.isfinite(input_z) or input_z <= 0:
            continue
        selected.append(
            {
                "nickname": row["nickname"],
                "tns": row["tns"],
                "ra_deg": float(row["ra_deg"]),
                "dec_deg": float(row["dec_deg"]),
            }
        )
    if len(selected) != 9:
        raise ValueError(f"expected nine eligible sightlines, found {len(selected)}")
    return selected


def bounding_box(ra_deg: float, dec_deg: float) -> dict[str, float]:
    """Return a spherical-cap-containing rectangle with a one-arcsec guard."""
    radius_deg = RADIUS_ARCMIN / 60.0 + GUARD_ARCSEC / 3600.0
    dec_min = dec_deg - radius_deg
    dec_max = dec_deg + radius_deg
    radius_rad = math.radians(radius_deg)
    cos_dec = math.cos(math.radians(dec_deg))
    if cos_dec <= 0 or math.sin(radius_rad) >= cos_dec:
        ra_half_width = 180.0
    else:
        ra_half_width = math.degrees(math.asin(math.sin(radius_rad) / cos_dec))
    if ra_deg - ra_half_width < 0 or ra_deg + ra_half_width >= 360:
        raise ValueError("right-ascension wrap is unsupported for this frozen sample")
    return {
        "ra_min": ra_deg - ra_half_width,
        "ra_max": ra_deg + ra_half_width,
        "dec_min": dec_min,
        "dec_max": dec_max,
    }


def spherical_separation_arcsec(
    ra1_deg: float, dec1_deg: float, ra2_deg: float, dec2_deg: float
) -> float:
    ra1, dec1, ra2, dec2 = map(
        math.radians, (ra1_deg, dec1_deg, ra2_deg, dec2_deg)
    )
    delta_ra = ra2 - ra1
    delta_dec = dec2 - dec1
    haversine = (
        math.sin(delta_dec / 2) ** 2
        + math.cos(dec1) * math.cos(dec2) * math.sin(delta_ra / 2) ** 2
    )
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(haversine)))) * 3600


def audit_response(response: bytes, sightline: dict[str, Any]) -> dict[str, Any]:
    """Summarize raw rows without merging shared WISE identities."""
    text = response.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    exact_rows = []
    for row in rows:
        separation = spherical_separation_arcsec(
            sightline["ra_deg"],
            sightline["dec_deg"],
            float(row["raMean"]),
            float(row["decMean"]),
        )
        if separation <= RADIUS_ARCMIN * 60:
            exact_rows.append(row)
    wise_groups: dict[str, set[str]] = {}
    for row in exact_rows:
        wise_id = row.get("cntr", "").strip()
        optical_id = row.get("objID", "").strip()
        if wise_id:
            wise_groups.setdefault(wise_id, set()).add(optical_id)
    ambiguous = [
        {"cntr": wise_id, "objIDs": sorted(optical_ids)}
        for wise_id, optical_ids in wise_groups.items()
        if len(optical_ids) > 1
    ]
    ambiguous.sort(key=lambda item: item["cntr"])
    return {
        "raw_row_count": len(rows),
        "native_column_count": len(reader.fieldnames or []) - 3,
        "exact_cone_row_count": len(exact_rows),
        "guard_only_row_count": len(rows) - len(exact_rows),
        "shared_wise_identity_state": "ambiguous",
        "shared_wise_identifier_groups": ambiguous,
    }


def sql_for_sightline(sightline: dict[str, Any], table_name: str) -> str:
    box = bounding_box(sightline["ra_deg"], sightline["dec_deg"])
    nickname = sightline["nickname"]
    return (
        f"SELECT '{nickname}' AS sightline, "
        f"CAST({sightline['ra_deg']:.12f} AS FLOAT) AS center_ra_deg, "
        f"CAST({sightline['dec_deg']:.12f} AS FLOAT) AS center_dec_deg, r.*\n"
        f"INTO MyDB.{table_name}\n"
        f"FROM {SOURCE_TABLE} AS r\n"
        f"WHERE r.raMean >= {box['ra_min']:.12f}\n"
        f"  AND r.raMean <= {box['ra_max']:.12f}\n"
        f"  AND r.decMean >= {box['dec_min']:.12f}\n"
        f"  AND r.decMean <= {box['dec_max']:.12f};"
    )


class CasJobsClient:
    """Small MAST CasJobs SOAP client with no credential environment variables."""

    root = "https://mastweb.stsci.edu/ps1casjobs"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        response = self._post(
            f"{self.root}/casusers.asmx/GetWebServiceId",
            {"userid": username, "password": password},
        )
        self.wsid = (ET.fromstring(response).text or "").strip()
        if not self.wsid or self.wsid == "-1":
            raise RuntimeError("MAST CasJobs authentication failed")

    def _post(self, url: str, fields: dict[str, Any], timeout: int = 120) -> bytes:
        data = urllib.parse.urlencode(fields).encode()
        request = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()

    def _jobs(self, operation: str, fields: dict[str, Any]) -> ET.Element:
        payload = {"wsid": self.wsid, "pw": self.password, **fields}
        response = self._post(f"{self.root}/services/jobs.asmx/{operation}", payload)
        return ET.fromstring(response)

    def submit(self, sql: str, task_name: str) -> int:
        root = self._jobs(
            "SubmitJob",
            {
                "qry": sql,
                "context": CONTEXT,
                "taskname": task_name,
                "estimate": 30,
            },
        )
        return int((root.text or "").strip())

    def status(self, job_id: int) -> int:
        root = self._jobs("GetJobStatus", {"jobid": job_id})
        return int((root.text or "").strip())

    def monitor(self, job_id: int, poll_seconds: float = 5.0) -> str:
        while True:
            code = self.status(job_id)
            if code in FINAL_JOB_CODES:
                state = FINAL_JOB_CODES[code]
                if state != "finished":
                    raise RuntimeError(f"CasJobs job {job_id} ended as {state}")
                return state
            time.sleep(poll_seconds)

    def job_info(self, job_id: int) -> dict[str, str]:
        root = self._jobs(
            "GetJobs",
            {
                "owner_wsid": self.wsid,
                "owner_pw": self.password,
                "conditions": f"jobid : {job_id}",
                "includeSystem": "false",
            },
        )
        job = next(
            (
                node
                for node in root.iter()
                if node.tag.split("}")[-1] == "CJJob"
            ),
            None,
        )
        if job is None:
            raise RuntimeError(f"no metadata returned for CasJobs job {job_id}")
        return {child.tag.split("}")[-1]: child.text or "" for child in job}

    def jobs(self) -> list[dict[str, str]]:
        root = self._jobs(
            "GetJobs",
            {
                "owner_wsid": self.wsid,
                "owner_pw": self.password,
                "conditions": "",
                "includeSystem": "false",
            },
        )
        return [
            {child.tag.split("}")[-1]: child.text or "" for child in job}
            for job in root
        ]

    def wait_for_output_info(
        self, job_id: int, attempts: int = 12, poll_seconds: float = 2.0
    ) -> dict[str, str]:
        """Wait for CasJobs' eventually consistent extraction URL."""
        for _ in range(attempts):
            info = self.job_info(job_id)
            if info.get("OutputLoc"):
                return info
            time.sleep(poll_seconds)
        raise RuntimeError(f"output job {job_id} has no download URL")

    def request_csv(self, table_name: str) -> int:
        root = self._jobs(
            "SubmitExtractJob", {"tableName": table_name, "type": "CSV"}
        )
        return int((root.text or "").strip())

    @staticmethod
    def download(url: str) -> bytes:
        with urllib.request.urlopen(url, timeout=600) as response:
            return response.read()


def keychain_password(service: str, account: str) -> str:
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-w",
            "-s",
            service,
            "-a",
            account,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip("\n")


def _matching_job(
    jobs: list[dict[str, str]], *, task_name: str, query_contains: str | None = None
) -> dict[str, str] | None:
    matches = [job for job in jobs if job.get("TaskName") == task_name]
    if query_contains is not None:
        matches = [job for job in matches if query_contains in job.get("Query", "")]
    if not matches:
        return None
    return max(matches, key=lambda item: int(item["JobID"]))


def acquire(args: argparse.Namespace) -> Path:
    sightlines = load_sightlines(args.bursts_csv)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=args.resume_run_id is not None)
    password = keychain_password(args.keychain_service, args.username)
    client = CasJobsClient(args.username, password)
    run_id = args.resume_run_id or datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    records = []
    existing_jobs = client.jobs() if args.resume_run_id else []

    for sightline in sightlines:
        nickname = sightline["nickname"]
        table_name = f"f26_ps1strm_{nickname}_{run_id.lower()}"
        sql = sql_for_sightline(sightline, table_name)
        sql_path = output_dir / f"{nickname}.sql"
        expected_sql = sql + "\n"
        if sql_path.exists() and sql_path.read_text(encoding="utf-8") != expected_sql:
            raise RuntimeError(f"resume SQL mismatch: {sql_path}")
        sql_path.write_text(expected_sql, encoding="utf-8")
        task_name = f"Faber2026 protected corpus {nickname}"
        existing = _matching_job(
            existing_jobs, task_name=task_name, query_contains=table_name
        )
        query_job_id = (
            int(existing["JobID"])
            if existing is not None
            else client.submit(sql, task_name)
        )
        records.append(
            {
                **sightline,
                "table_name": table_name,
                "query_job_id": query_job_id,
                "sql_file": sql_path.name,
                "sql_sha256": sha256_bytes(sql_path.read_bytes()),
                "bounding_box": bounding_box(
                    sightline["ra_deg"], sightline["dec_deg"]
                ),
            }
        )

    for record in records:
        client.monitor(record["query_job_id"])
        record["query_job"] = client.job_info(record["query_job_id"])
        existing_output = _matching_job(
            existing_jobs, task_name=record["table_name"]
        )
        output_job_id = (
            int(existing_output["JobID"])
            if existing_output is not None
            else client.request_csv(record["table_name"])
        )
        client.monitor(output_job_id)
        output_job = client.wait_for_output_info(output_job_id)
        output_url = output_job.get("OutputLoc", "")
        raw = client.download(output_url)
        raw_path = output_dir / f"{record['nickname']}.csv"
        raw_path.write_bytes(raw)
        record.update(
            {
                "output_job_id": output_job_id,
                "output_job": output_job,
                "response_file": raw_path.name,
                "response_bytes": len(raw),
                "response_sha256": sha256_bytes(raw),
                "retrieved_at": utc_now(),
                "response_audit": audit_response(raw, record),
            }
        )

    manifest = {
        "schema_version": 1,
        "status": "protected_source_responses_frozen",
        "service": "MAST CasJobs",
        "authenticated_account": args.username,
        "credentials_recorded": False,
        "context": CONTEXT,
        "source_table": SOURCE_TABLE,
        "release": RELEASE,
        "doi": DOI,
        "approved_region": {
            "shape": "inclusive cone",
            "radius_arcmin": RADIUS_ARCMIN,
            "raw_query": "guard rectangle containing cone",
            "guard_arcsec": GUARD_ARCSEC,
            "exact_spherical_filter_stage": "independent replay",
        },
        "pagination": {
            "method": "CasJobs batch MyDB materialization and extract job",
            "row_limit": None,
            "truncation_allowed": False,
        },
        "sightlines": records,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    sums = [
        f"{sha256_bytes(path.read_bytes())}  {path.name}"
        for path in sorted(output_dir.iterdir())
        if path.name != "SHA256SUMS"
    ]
    (output_dir / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return manifest_path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--bursts-csv", type=Path, required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--username", required=True)
    result.add_argument(
        "--resume-run-id",
        help="resume an existing UTC run id such as 20260722T172102Z",
    )
    result.add_argument(
        "--keychain-service", default="Agents/mast-casjobs-password"
    )
    return result


if __name__ == "__main__":
    print(acquire(parser().parse_args()))
