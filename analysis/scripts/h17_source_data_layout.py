#!/usr/bin/env python3
"""Safely migrate the 12 paired preliminary source products on h17."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import sys
import tempfile
from typing import Callable, Iterable
import uuid


OLD_ROOT = "/data/research/astrophysics/frbs/chime-dsa-codetections"
NEW_ROOT = "/data/Faber2026/data"
REMOTE_PROVENANCE_ROOT = "/data/Faber2026/provenance"


@dataclass(frozen=True)
class BurstSource:
    project_id: str
    tns_name: str
    chime_event_id: str
    dsa_observation_id: str
    dsa_source_directory: str

    @property
    def dsa_filename(self) -> str:
        return f"{self.dsa_observation_id}_dev_polcal_I.fil"

    @property
    def chime_filename(self) -> str:
        return f"singlebeam_{self.chime_event_id}.h5"


BURSTS = (
    BurstSource("zach", "FRB 20220207C", "210456524", "220207aabh", "zach_240203aacl_210456524"),
    BurstSource("whitney", "FRB 20220310F", "215063905", "220310aaam", "whitney_220310aaam_215063905"),
    BurstSource("oran", "FRB 20220506D", "224263996", "220506aabd", "oran_220506aabd_224263996"),
    BurstSource("isha", "FRB 20221113A", "252069198", "221113aaao", "isha_221113aaao_252069198"),
    BurstSource("wilhelm", "FRB 20221203A", "253635173", "221203aaaa", "wilhelm_221203aaaa_253635173"),
    BurstSource("phineas", "FRB 20230307A", "274819243", "230307aaao", "phineas_230307aaao_274819243"),
    BurstSource("freya", "FRB 20230325A", "278720455", "230325aaag", "freya_230325aaag_278720455"),
    BurstSource("johndoeii", "FRB 20230814B", "311723353", "230814aaas", "johndoeII_230814aaas_311723353"),
    BurstSource("hamilton", "FRB 20230913A", "318353610", "230913aaao", "hamilton_230913aaao_318353610"),
    BurstSource("mahi", "FRB 20240122A", "354049284", "240122aaag", "mahi_240122aaag_354049284"),
    BurstSource("chromatica", "FRB 20240203A", "356959136", "240203aacl", "chromatica_240203aacl_356959136"),
    BurstSource("casey", "FRB 20240229A", "362593221", "240229aaad", "casey_240229aaad_362593221"),
)


EXCLUDED_PATHS = (
    f"{OLD_ROOT}/archive/arc_trash_2026-06/singlebeam_h5/singlebeam_175128652.h5",
    f"{OLD_ROOT}/dsa_filterbanks/Codetections_DSA_Filterbanks/"
    "FRB20220912A2_221025aanu_247683525?_247683548?_247683922?/221025aanu_dev_polcal_I.fil",
    f"{OLD_ROOT}/dsa_filterbanks/220207aabh/Level3/220207aabh_dev_polcal_I.fil",
)


def old_paths(burst: BurstSource) -> tuple[str, str]:
    return (
        f"{OLD_ROOT}/dsa_filterbanks/Codetections_DSA_Filterbanks/"
        f"{burst.dsa_source_directory}/{burst.dsa_filename}",
        f"{OLD_ROOT}/chime_singlebeam/{burst.chime_filename}",
    )


def new_paths(burst: BurstSource) -> tuple[str, str]:
    return (
        f"{NEW_ROOT}/dsa-110/{burst.project_id}/{burst.dsa_filename}",
        f"{NEW_ROOT}/chime-frb/{burst.project_id}/{burst.chime_filename}",
    )


def canonical_paths(path_builder: Callable[[BurstSource], tuple[str, str]]) -> list[str]:
    return [path for burst in BURSTS for path in path_builder(burst)]


def move_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for burst in BURSTS:
        old_dsa, old_chime = old_paths(burst)
        new_dsa, new_chime = new_paths(burst)
        common = asdict(burst)
        records.extend(
            (
                {**common, "instrument": "dsa-110", "old_path": old_dsa, "new_path": new_dsa},
                {**common, "instrument": "chime-frb", "old_path": old_chime, "new_path": new_chime},
            )
        )
    return records


REMOTE_PROBE = r'''
import glob, json, os, socket, sys

request = json.load(sys.stdin)
paths = request["paths"]
wanted = set(paths)
handles = {path: [] for path in paths}
for fd in glob.glob("/proc/[0-9]*/fd/*"):
    try:
        target = os.readlink(fd)
    except OSError:
        continue
    if target in wanted:
        handles[target].append(fd)

entries = {}
for path in paths:
    try:
        stat = os.stat(path)
    except FileNotFoundError:
        entries[path] = {"exists": False, "open_handles": handles[path]}
        continue
    entry = {
        "exists": True,
        "is_file": os.path.isfile(path),
        "size": stat.st_size,
        "device": stat.st_dev,
        "inode": stat.st_ino,
        "mode": oct(stat.st_mode & 0o7777),
        "uid": stat.st_uid,
        "gid": stat.st_gid,
        "mtime_ns": stat.st_mtime_ns,
        "open_handles": handles[path],
    }
    entries[path] = entry

print(json.dumps({
    "host": socket.gethostname(),
    "captured_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "data_device": os.stat("/data").st_dev,
    "entries": entries,
}, sort_keys=True))
'''


REMOTE_HASH = r'''
import hashlib, json, sys
path = json.load(sys.stdin)["path"]
value = hashlib.sha256()
with open(path, "rb") as stream:
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
        value.update(block)
print(json.dumps({"path": path, "sha256": value.hexdigest()}))
'''


REMOTE_PERSIST_PREFLIGHT = r'''
import hashlib, json, os, pathlib, sys, tempfile

request = json.load(sys.stdin)
target = pathlib.Path(request["path"])
content = request["content"].encode("utf-8")
expected = request["sha256"]
actual = hashlib.sha256(content).hexdigest()
if actual != expected:
    raise RuntimeError(f"preflight payload digest mismatch before write: {actual} != {expected}")
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists():
    raise FileExistsError(f"preflight evidence already exists: {target}")
fd, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
try:
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(temporary, 0o444)
    os.link(temporary, target)
    directory_fd = os.open(target.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
with target.open("rb") as stream:
    persisted = hashlib.sha256(stream.read()).hexdigest()
if persisted != expected:
    raise RuntimeError(f"persisted preflight digest mismatch: {persisted} != {expected}")
print(json.dumps({"path": str(target), "sha256": persisted}, sort_keys=True))
'''


REMOTE_MIGRATE = r'''
import hashlib, json, os, pathlib, socket, subprocess, sys, tempfile

request = json.load(sys.stdin)
moves = request["moves"]
receipt_path = request["remote_receipt"]
preflight_ref = request["preflight"]
completed = []

preflight_path = pathlib.Path(preflight_ref["remote_path"])
with preflight_path.open("rb") as stream:
    preflight_bytes = stream.read()
actual_digest = hashlib.sha256(preflight_bytes).hexdigest()
if actual_digest != preflight_ref["sha256"]:
    raise RuntimeError(
        f"persisted preflight digest mismatch before migration: "
        f"{actual_digest} != {preflight_ref['sha256']}"
    )
preflight = json.loads(preflight_bytes)
if preflight["attempt_id"] != preflight_ref["attempt_id"]:
    raise RuntimeError("preflight attempt identifier mismatch")
if preflight["moves"] != moves:
    raise RuntimeError("preflight move mapping mismatch")
entries = preflight["probe"]["entries"]
for item in moves:
    old = item["old_path"]
    new = item["new_path"]
    stat = os.stat(old)
    expected = entries[old]
    for key, actual in (
        ("size", stat.st_size),
        ("device", stat.st_dev),
        ("inode", stat.st_ino),
        ("mtime_ns", stat.st_mtime_ns),
    ):
        if actual != expected[key]:
            raise RuntimeError(f"source changed since preflight ({key}): {old}")
    if os.path.exists(new):
        raise RuntimeError(f"target appeared since preflight: {new}")

def write_state(state, error=None):
    target = pathlib.Path(receipt_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "faber2026-h17-source-migration-journal-v1",
        "host": socket.gethostname(),
        "state": state,
        "error": error,
        "preflight": preflight_ref,
        "moves": moves,
        "completed": completed,
    }
    fd, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.chmod(temporary, 0o444)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

write_state("in_progress")
try:
    for item in moves:
        old = item["old_path"]
        new = item["new_path"]
        if not os.path.isfile(old):
            raise RuntimeError(f"source missing or not a file: {old}")
        if os.path.exists(new):
            raise RuntimeError(f"target collision: {new}")
        pathlib.Path(new).parent.mkdir(parents=True, exist_ok=True, mode=0o2775)
        os.chmod(pathlib.Path(new).parent, 0o2775)
        if os.stat(old).st_dev != os.stat(pathlib.Path(new).parent).st_dev:
            raise RuntimeError(f"cross-device move refused: {old} -> {new}")
        subprocess.run(["mv", "--no-clobber", "--", old, new], check=True)
        if os.path.exists(old) or not os.path.isfile(new):
            raise RuntimeError(f"move did not complete: {old} -> {new}")
        completed.append({"old_path": old, "new_path": new})
        write_state("in_progress")
except Exception as exc:
    rollback_errors = []
    for item in reversed(completed):
        try:
            os.rename(item["new_path"], item["old_path"])
        except Exception as rollback_exc:
            rollback_errors.append(str(rollback_exc))
    message = str(exc)
    if rollback_errors:
        message += "; rollback errors: " + "; ".join(rollback_errors)
    write_state("rolled_back" if not rollback_errors else "rollback_incomplete", message)
    raise

write_state("moved_pending_hash_verification")
print(json.dumps({"moved": len(completed), "journal": receipt_path}, sort_keys=True))
'''


REMOTE_FINALIZE = r'''
import json, os, pathlib, sys, tempfile
request = json.load(sys.stdin)
target = pathlib.Path(request["path"])
target.parent.mkdir(parents=True, exist_ok=True)
fd, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
try:
    with os.fdopen(fd, "w") as stream:
        json.dump(request["receipt"], stream, indent=2, sort_keys=True)
        stream.write("\n")
    os.chmod(temporary, 0o444)
    os.replace(temporary, target)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
print(json.dumps({"receipt": str(target)}, sort_keys=True))
'''


def _remote_python(host: str, program: str, payload: dict, timeout: int = 900) -> dict:
    remote_command = shlex.join(["python3", "-c", program])
    completed = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", host, remote_command],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if completed.returncode:
        raise RuntimeError(
            f"remote command failed ({completed.returncode}): {completed.stderr.strip()}"
        )
    output = completed.stdout.strip().splitlines()
    if not output:
        raise RuntimeError("remote command returned no JSON")
    return json.loads(output[-1])


def _probe(host: str, paths: Iterable[str], *, hash_existing: bool) -> dict:
    path_list = list(paths)
    probe = _remote_python(
        host,
        REMOTE_PROBE,
        {"paths": path_list},
    )
    if not hash_existing:
        return probe
    existing = [path for path in path_list if probe["entries"][path].get("is_file")]
    for index, path in enumerate(existing, start=1):
        print(f"hashing {index}/{len(existing)}: {path}", file=sys.stderr, flush=True)
        result = _remote_python(host, REMOTE_HASH, {"path": path}, timeout=900)
        probe["entries"][path]["sha256"] = result["sha256"]
    return probe


def _validate_mapping() -> None:
    if len(BURSTS) != 12:
        raise RuntimeError(f"expected 12 bursts, found {len(BURSTS)}")
    old = canonical_paths(old_paths)
    new = canonical_paths(new_paths)
    if len(set(old)) != 24 or len(set(new)) != 24:
        raise RuntimeError("canonical paths are not unique")
    if set(old) & set(EXCLUDED_PATHS):
        raise RuntimeError("an excluded path entered the canonical allowlist")
    for path in old + new:
        if PurePosixPath(path).suffix not in {".fil", ".h5"}:
            raise RuntimeError(f"unexpected extension: {path}")


def preflight(host: str, *, hash_existing: bool = True) -> dict:
    _validate_mapping()
    old = canonical_paths(old_paths)
    new = canonical_paths(new_paths)
    paths = old + new + list(EXCLUDED_PATHS)
    probe = _probe(host, paths, hash_existing=hash_existing)
    entries = probe["entries"]
    errors: list[str] = []
    for path in old:
        entry = entries[path]
        if not entry.get("exists") or not entry.get("is_file"):
            errors.append(f"missing source: {path}")
        elif entry["device"] != probe["data_device"]:
            errors.append(f"source is not on /data device: {path}")
        if entry.get("open_handles"):
            errors.append(f"source has open handles: {path}: {entry['open_handles']}")
    for path in new:
        if entries[path].get("exists"):
            errors.append(f"target collision: {path}")
    for path in EXCLUDED_PATHS:
        if not entries[path].get("exists"):
            errors.append(f"excluded sentinel missing: {path}")
    if errors:
        raise RuntimeError("preflight failed:\n" + "\n".join(errors))
    return probe


def _entry_identity(entry: dict) -> dict:
    return {key: entry[key] for key in ("size", "sha256", "device", "inode", "mtime_ns")}


def _canonical_json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _atomic_write_new(path: Path, payload: bytes) -> None:
    """Durably publish bytes without ever replacing an existing artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"evidence already exists: {path}")
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o444)
        os.link(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_preflight_manifest(before: dict, records: list[dict], attempt_id: str) -> dict:
    """Bind the complete 51-path probe to one immutable migration attempt."""
    expected_paths = (
        canonical_paths(old_paths)
        + canonical_paths(new_paths)
        + list(EXCLUDED_PATHS)
    )
    if set(before["entries"]) != set(expected_paths):
        raise RuntimeError("preflight probe does not contain the exact 51-path allowlist")
    return {
        "schema": "faber2026-h17-source-data-preflight-v1",
        "attempt_id": attempt_id,
        "host": before["host"],
        "captured_at": before["captured_at"],
        "data_device": before["data_device"],
        "moves": records,
        "excluded_paths": list(EXCLUDED_PATHS),
        "probe": before,
    }


def _persist_preflight(
    host: str,
    receipt_path: Path,
    before: dict,
    records: list[dict],
    attempt_id: str,
) -> dict:
    manifest = build_preflight_manifest(before, records, attempt_id)
    payload = _canonical_json_bytes(manifest)
    digest = _sha256_bytes(payload)
    filename = f"h17-source-data-preflight-{attempt_id}.json"
    local_path = receipt_path.parent / filename
    remote_path = f"{REMOTE_PROVENANCE_ROOT}/{filename}"
    _atomic_write_new(local_path, payload)
    result = _remote_python(
        host,
        REMOTE_PERSIST_PREFLIGHT,
        {
            "path": remote_path,
            "content": payload.decode("utf-8"),
            "sha256": digest,
        },
    )
    if result != {"path": remote_path, "sha256": digest}:
        raise RuntimeError(f"remote preflight persistence mismatch: {result}")
    if _sha256_bytes(local_path.read_bytes()) != digest:
        raise RuntimeError("local preflight digest changed after persistence")
    return {
        "attempt_id": attempt_id,
        "local_path": str(local_path),
        "remote_path": remote_path,
        "sha256": digest,
    }


def migrate(host: str, receipt_path: Path) -> dict:
    records = move_records()
    before = preflight(host, hash_existing=True)
    attempt_id = uuid.uuid4().hex
    preflight_ref = _persist_preflight(
        host, receipt_path, before, records, attempt_id
    )
    remote_journal = (
        f"{REMOTE_PROVENANCE_ROOT}/h17-source-data-migration-{attempt_id}.journal.json"
    )
    remote_receipt = (
        f"{REMOTE_PROVENANCE_ROOT}/h17-source-data-migration-{attempt_id}.json"
    )
    _remote_python(
        host,
        REMOTE_MIGRATE,
        {
            "moves": records,
            "remote_receipt": remote_journal,
            "preflight": preflight_ref,
        },
    )

    old = canonical_paths(old_paths)
    new = canonical_paths(new_paths)
    after = _probe(host, old + new + list(EXCLUDED_PATHS), hash_existing=True)
    before_entries = before["entries"]
    after_entries = after["entries"]
    errors: list[str] = []
    verified_records: list[dict] = []
    for record in records:
        old_path = record["old_path"]
        new_path = record["new_path"]
        if after_entries[old_path].get("exists"):
            errors.append(f"old path still exists: {old_path}")
        if not after_entries[new_path].get("exists"):
            errors.append(f"new path missing: {new_path}")
            continue
        pre_identity = _entry_identity(before_entries[old_path])
        post_identity = _entry_identity(after_entries[new_path])
        for key in ("size", "sha256", "device", "inode", "mtime_ns"):
            if pre_identity[key] != post_identity[key]:
                errors.append(f"{key} mismatch: {old_path} -> {new_path}")
        verified_records.append(
            {**record, "before": pre_identity, "after": post_identity}
        )

    exclusions = []
    for path in EXCLUDED_PATHS:
        pre_identity = _entry_identity(before_entries[path])
        post_identity = _entry_identity(after_entries[path])
        if pre_identity != post_identity:
            errors.append(f"excluded file changed: {path}")
        exclusions.append({"path": path, "before": pre_identity, "after": post_identity})

    receipt = {
        "schema": "faber2026-h17-source-data-migration-v1",
        "attempt_id": attempt_id,
        "status": "verified" if not errors else "failed_verification",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "host_alias": host,
        "hostname": after["host"],
        "data_device": after["data_device"],
        "new_root": NEW_ROOT,
        "preflight": preflight_ref,
        "remote_journal": remote_journal,
        "remote_receipt": remote_receipt,
        "records": verified_records,
        "exclusions": exclusions,
        "errors": errors,
    }
    _atomic_write_new(receipt_path, _canonical_json_bytes(receipt))
    _remote_python(host, REMOTE_FINALIZE, {"path": remote_receipt, "receipt": receipt})
    if errors:
        raise RuntimeError("post-move verification failed:\n" + "\n".join(errors))
    return receipt


def verify(host: str, receipt_path: Path) -> dict:
    receipt = json.loads(receipt_path.read_text())
    records = receipt["records"]
    old = [record["old_path"] for record in records]
    new = [record["new_path"] for record in records]
    exclusions = [entry["path"] for entry in receipt["exclusions"]]
    probe = _probe(host, old + new + exclusions, hash_existing=True)
    entries = probe["entries"]
    errors: list[str] = []
    for record in records:
        if entries[record["old_path"]].get("exists"):
            errors.append(f"old path exists: {record['old_path']}")
        actual = entries[record["new_path"]]
        expected = record["after"]
        if not actual.get("exists"):
            errors.append(f"new path missing: {record['new_path']}")
            continue
        for key in ("size", "sha256", "device", "inode", "mtime_ns"):
            if actual[key] != expected[key]:
                errors.append(f"{key} changed: {record['new_path']}")
        if actual.get("open_handles"):
            errors.append(f"new path has open handles: {record['new_path']}")
    for excluded in receipt["exclusions"]:
        actual = entries[excluded["path"]]
        expected = excluded["after"]
        if not actual.get("exists"):
            errors.append(f"excluded file missing: {excluded['path']}")
            continue
        for key in ("size", "sha256", "device", "inode", "mtime_ns"):
            if actual[key] != expected[key]:
                errors.append(f"excluded file changed: {excluded['path']}")
    if errors:
        raise RuntimeError("verification failed:\n" + "\n".join(errors))
    return {
        "verified": len(records),
        "old_paths_present": 0,
        "exclusions_preserved": len(exclusions),
        "hostname": probe["host"],
    }


def build_source_manifest(receipt: dict) -> dict:
    """Build the paired custody manifest without claiming unverified science metadata."""
    indexed = {
        (record["project_id"], record["instrument"]): record
        for record in receipt["records"]
    }
    bursts = []
    for burst in BURSTS:
        dsa = indexed[(burst.project_id, "dsa-110")]
        chime = indexed[(burst.project_id, "chime-frb")]
        bursts.append(
            {
                "project_id": burst.project_id,
                "tns_name": burst.tns_name,
                "chime_event_id": burst.chime_event_id,
                "dsa_observation_id": burst.dsa_observation_id,
                "source_products": {
                    "dsa-110": {
                        "format": "SIGPROC_filterbank",
                        "path": dsa["new_path"],
                        "size": dsa["after"]["size"],
                        "sha256": dsa["after"]["sha256"],
                        "known_processing": "incoherently_dedispersed",
                        "processing_basis": "owner_statement_2026-07-21",
                        "coherent_dedispersion_possible": False,
                        "applied_dm": "unverified_pending_header_and_producer_audit",
                    },
                    "chime-frb": {
                        "format": "HDF5_voltage",
                        "path": chime["new_path"],
                        "size": chime["after"]["size"],
                        "sha256": chime["after"]["sha256"],
                        "dedispersion_state": "unverified_pending_header_and_producer_audit",
                        "applied_dm": "unverified_pending_header_and_producer_audit",
                    },
                },
            }
        )
    return {
        "schema": "faber2026-paired-preliminary-source-manifest-v1",
        "status": "custody_verified_science_metadata_unverified",
        "migration_receipt_created_at": receipt["created_at"],
        "host_alias": receipt["host_alias"],
        "bursts": bursts,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "migrate", "verify", "manifest"):
        command = subparsers.add_parser(name)
        if name != "manifest":
            command.add_argument("--host", default="h17")
        if name in {"migrate", "verify", "manifest"}:
            command.add_argument("--receipt", type=Path, required=True)
        if name == "manifest":
            command.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "preflight":
            result = preflight(args.host)
            print(
                f"preflight passed: 24 sources, 0 targets, 3 exclusions; "
                f"host={result['host']} device={result['data_device']}"
            )
        elif args.command == "migrate":
            result = migrate(args.host, args.receipt)
            print(
                f"migration verified: {len(result['records'])}/24 files; "
                f"receipt={args.receipt}"
            )
        elif args.command == "verify":
            result = verify(args.host, args.receipt)
            print(
                f"{result['verified']}/24 verified, "
                f"{result['old_paths_present']} old canonical paths, "
                f"{result['exclusions_preserved']}/3 exclusions preserved"
            )
        else:
            result = build_source_manifest(json.loads(args.receipt.read_text()))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(f"paired source manifest: {len(result['bursts'])} bursts; output={args.output}")
    except (RuntimeError, subprocess.SubprocessError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
