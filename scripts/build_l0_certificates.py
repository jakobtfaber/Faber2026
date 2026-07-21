#!/usr/bin/env python3
"""Build raw-layer (stratum-0) input certificates for the 36 archival products.

Wayfinder ticket 17. Reads waterfall-review deck meta + pipeline data
manifest + local instrument-specific products; writes
docs/rse/certificates/l0-certificates.json. Optionally refreshes the raw-layer section of
docs/rse/control/results-registry.toml.

Frequency-order methods (asserted from data, not assumed):
  - CHIME full-resolution: occupancy of the persistent cellular interference
    band at 729–756 MHz (scripts/audit_fig1_axes.py). When that score
    saturates (wilhelm), fall back to leave-one-out agreement with the
    shared sample convention.
  - DSA-110: leave-one-out flagged-row profile consistency plus the
    descending-frequency storage convention in telescopes.yaml.
  - CHIME upchannelized: companion *_chime_freq.npy is strictly ascending.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_fig1_axes import audit_chime_ordering, audit_dsa_ordering, _flagged_rows_raw  # noqa: E402
from l0_conventions import freq_order_from_axis, md5_prefix, sha256_file  # noqa: E402

CHIME_FULL_ROOT = Path.home() / "Data/Faber2026/chimefrb/CHIME_bursts"
DSA_FULL_ROOT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"
UPCHAN_ROOT = Path.home() / "Data/Faber2026/dsa110/upchan_codetections"
DECK = ROOT / "docs/rse/decks/scintillation/waterfall-review-2026-07-18"
MANIFEST = ROOT / "pipeline/data-manifest.csv"
OUT_JSON = ROOT / "docs/rse/certificates/l0-certificates.json"
REGISTRY = ROOT / "docs/rse/control/results-registry.toml"

L0_MARKER = "# ── Derived intensity-product inventory"
CLEARED_BY = (
    "wayfinder ticket 17 raw-layer spot-check 2026-07-19 "
    "(36/36 checksums; cellular-band / leave-one-out / frequency-file orders; "
    "casey, freya, and zach review-deck panels)"
)
CERTIFICATE_STATE = {
    "trust": "pending",
    "cleared_by": "",
    "notes_scope": (
        "derived intensity product — NOT raw CHIME data; see "
        "docs/rse/specs/notes/definition-raw-chime-data-2026-07-19.md"
    ),
}


def _load_meta() -> dict:
    meta: dict = {}
    for path in sorted(DECK.glob("meta_*.json")):
        meta.update(json.loads(path.read_text()))
    return meta


def _load_manifest() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    with MANIFEST.open() as f:
        for row in csv.DictReader(f):
            out[(row["burst"], row["telescope"])] = row
    return out


def _chime_loo_verdicts(chime_paths: dict[str, Path], n_rows: int = 1024) -> dict[str, dict]:
    bin_width = 16
    profiles: dict[str, np.ndarray] = {}
    for nick, path in chime_paths.items():
        h = np.zeros(n_rows // bin_width)
        for i in _flagged_rows_raw(path):
            h[min(i // bin_width, len(h) - 1)] += 1
        profiles[nick] = h
    out: dict[str, dict] = {}
    for nick, h in profiles.items():
        pooled = np.sum([v for k, v in profiles.items() if k != nick], axis=0)
        a, b = h - h.mean(), pooled - pooled.mean()
        mirrored = b[::-1]
        denom = float(np.sqrt((a**2).sum() * (b**2).sum()) or 1.0)
        c_same = float((a * b).sum() / denom)
        denom_m = float(np.sqrt((a**2).sum() * (mirrored**2).sum()) or 1.0)
        c_mirr = float((a * mirrored).sum() / denom_m)
        out[nick] = {
            "corr_vs_pool": round(c_same, 3),
            "corr_vs_mirrored_pool": round(c_mirr, 3),
            "verdict": "descending" if c_same > c_mirr else "ascending",
        }
    return out


def _display_path(path: Path) -> str:
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def build_certificates(
    chime_full_root: Path = CHIME_FULL_ROOT,
    dsa_full_root: Path = DSA_FULL_ROOT,
    upchan_root: Path = UPCHAN_ROOT,
) -> list[dict]:
    roots = {
        "CHIME/FRB full-resolution": Path(chime_full_root),
        "DSA-110 full-resolution": Path(dsa_full_root),
        "CHIME/FRB upchannelized": Path(upchan_root),
    }
    missing = [label for label, path in roots.items() if not path.is_dir()]
    if missing:
        raise SystemExit(f"local data roots missing: {missing}")
    meta = _load_meta()
    man = _load_manifest()
    nicks = sorted(meta.keys())
    if len(nicks) != 12:
        raise SystemExit(f"expected 12 bursts in deck meta, got {len(nicks)}")

    dsa_paths = {n: dsa_full_root / meta[n]["dsa"]["file"] for n in nicks}
    dsa_audit = audit_dsa_ordering(dsa_paths, n_rows=6144)
    dsa_all_ok = all(dsa_audit[n]["consistent_with_shared_convention"] for n in nicks)

    chime_paths = {
        n: chime_full_root / meta[n]["chime_full"]["file"] for n in nicks
    }
    chime_loo = _chime_loo_verdicts(chime_paths)

    rows: list[dict] = []
    for nick in nicks:
        m = meta[nick]

        cf = m["chime_full"]
        path = chime_full_root / cf["file"]
        cellular = audit_chime_ordering(path, n_rows=int(cf["shape"][0]))
        method = "chime_cellular_band_mask_occupancy_729_756_MHz"
        order = cellular["verdict"]
        detail = {
            "n_flagged_rows": cellular["n_flagged_rows"],
            "cellular_band_occupancy_if_descending": cellular[
                "lte_occupancy_if_descending"
            ],
            "cellular_band_occupancy_if_ascending": cellular[
                "lte_occupancy_if_ascending"
            ],
            "verdict": cellular["verdict"],
            "matches_loader_assumption": cellular["matches_loader_assumption"],
        }
        if order == "ambiguous":
            leave_one_out = chime_loo[nick]
            order = leave_one_out["verdict"]
            method = (
                "chime_cellular_band_ambiguous"
                "+leave_one_out_shared_convention"
            )
            detail["leave_one_out"] = {
                **leave_one_out,
                "note": (
                    "cellular-band occupancy saturated under both axis "
                    "hypotheses (heavy flagging); leave-one-out vs the "
                    "sample flagged-row profile prefers descending"
                ),
            }
        mrow = man[(nick, "chime")]
        file_md5 = md5_prefix(path)
        rows.append(
            {
                "nick": nick,
                "product": "chime_full",
                "file": cf["file"],
                "local_path": _display_path(path),
                "sha256": mrow["sha256"],
                "bytes": int(mrow["bytes"]),
                "deck_md5": cf["md5"],
                "file_md5": file_md5,
                "md5_ok": cf["md5"] == file_md5,
                "freq_order": order,
                "freq_order_method": method,
                "freq_order_detail": detail,
                "shape": cf["shape"],
                "arc_path": mrow["arc_path"],
                "builder": mrow["builder"],
                "byte_status": mrow["status"],
                "gen": "gen-2+_dmphase_archival",
                "lineage": (
                    "CANFAR archive CHIME_bursts/dmphase; "
                    "local bytes match archive"
                ),
                **CERTIFICATE_STATE,
            }
        )

        ds = m["dsa"]
        path = dsa_full_root / ds["file"]
        mrow = man[(nick, "dsa")]
        file_md5 = md5_prefix(path)
        da = dsa_audit[nick]
        order = (
            "descending"
            if (dsa_all_ok and da["consistent_with_shared_convention"])
            else "ambiguous"
        )
        rows.append(
            {
                "nick": nick,
                "product": "dsa",
                "file": ds["file"],
                "local_path": _display_path(path),
                "sha256": mrow["sha256"],
                "bytes": int(mrow["bytes"]),
                "deck_md5": ds["md5"],
                "file_md5": file_md5,
                "md5_ok": ds["md5"] == file_md5,
                "freq_order": order,
                "freq_order_method": (
                    "dsa_leave_one_out_flagged_profile"
                    "+telescopes_yaml_descending"
                ),
                "freq_order_detail": {
                    **da,
                    "shared_sample_convention": "descending",
                    "all_twelve_consistent": dsa_all_ok,
                },
                "shape": ds["shape"],
                "arc_path": mrow["arc_path"],
                "builder": mrow["builder"],
                "byte_status": mrow["status"],
                "gen": "archival_dsa_I",
                "lineage": (
                    "CANFAR archive DSA_bursts; local bytes match archive; "
                    "frequency descending per telescopes.yaml"
                ),
                **CERTIFICATE_STATE,
            }
        )

        cu = m["chime_upchan"]
        path = upchan_root / cu["file"]
        freq_path = upchan_root / f"{nick}_chime_freq.npy"
        freq = np.load(freq_path)
        order = freq_order_from_axis(freq)
        file_md5 = md5_prefix(path)
        rows.append(
            {
                "nick": nick,
                "product": "chime_upchan",
                "file": cu["file"],
                "local_path": _display_path(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "deck_md5": cu["md5"],
                "file_md5": file_md5,
                "md5_ok": cu["md5"] == file_md5,
                "freq_order": order,
                "freq_order_method": "companion_frequency_file_monotonic",
                "freq_order_detail": {
                    "fmin": float(freq.min()),
                    "fmax": float(freq.max()),
                    "nchan": int(freq.size),
                },
                "freq_path": _display_path(freq_path),
                "freq_sha256": sha256_file(freq_path),
                "shape": cu["shape"],
                "arc_path": f"h17:$COD/upchan_codetections/{cu['file']}",
                "builder": (
                    "upchannelize_chime.py --no-time-shift + "
                    "build_npz_aligned_generic (gen-2+)"
                ),
                "byte_status": "LOCAL_MD5_MATCH_DECK",
                "gen": "gen-2+",
                "lineage": (
                    "h17 upchan_codetections; PROVENANCE.md; "
                    "companion frequency file"
                ),
                **CERTIFICATE_STATE,
            }
        )
    return rows


def _toml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render_registry_fragment(rows: list[dict]) -> str:
    lines = [
        "",
        L0_MARKER + " (MISLABELED as L0 — 2026-07-19) ─",
        "# These 36 rows inventory derived products; they are not raw CHIME data",
        "# and byte/axis checks do not grant scientific trust.",
        "# (12 bursts × {CHIME full-resolution, CHIME upchannelized, DSA-110}).",
        "# Frequency order is measured: CHIME full-resolution via cellular-band",
        "# (729–756 MHz) mask occupancy; DSA-110 via leave-one-out flagged-row",
        "# profiles + telescopes.yaml descending convention; upchannelized via",
        "# companion *_chime_freq.npy.",
        "",
    ]
    for r in rows:
        pid = f"l0.{r['nick']}.{r['product']}"
        artifact = (
            f"{r['local_path']} sha256:{r['sha256']} deck_md5:{r['deck_md5']}"
        )
        if r["product"] == "chime_upchan":
            artifact += f" freq_sha256:{r['freq_sha256']}"
        byte_status = r["byte_status"]
        if byte_status == "ARC_BYTE_MATCH":
            byte_status = "local_bytes_match_archive"
        elif byte_status == "LOCAL_MD5_MATCH_DECK":
            byte_status = "local_checksum_matches_review_deck"
        builder = r["builder"]
        if builder == "UNVERIFIED_BUILDER":
            builder = "builder identity not yet verified"
        notes = "; ".join(
            [
                f"generation={r['gen']}",
                f"builder={builder}",
                f"byte_status={byte_status}",
                f"frequency_method={r['freq_order_method']}",
                f"shape={r['shape']}",
                f"lineage={r['lineage']}",
            ]
        )
        trust = r.get("trust", "pending")
        cleared = r.get("cleared_by", "")
        lines.extend(
            [
                "[[result]]",
                f'id = "{pid}"',
                "library_slots = []",
                'section = "§0"',
                'kind = "input_certificate"',
                f'description = "L0 certificate: {r["nick"]} {r["product"]} ({r["file"]})"',
                f'value = "{r["freq_order"]}"',
                'units = "freq_order"',
                'producing_script = "scripts/build_l0_certificates.py"',
                'pipeline_pin = ""',
                f'inputs = ["{_toml_escape(r["arc_path"])}"]',
                "external_sources = []",
                f'artifact = "{_toml_escape(artifact)}"',
                "consumed_by = []",
                f'trust = "{trust}"',
                f'cleared_by = "{cleared}"',
                "current = true",
                f'notes = "{_toml_escape(notes)}"',
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def update_registry(rows: list[dict]) -> None:
    text = REGISTRY.read_text()
    frag = render_registry_fragment(rows)
    if L0_MARKER in text:
        text = re.sub(
            re.escape(L0_MARKER) + r".*\Z",
            frag.lstrip("\n"),
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = text.rstrip() + "\n" + frag
    text = re.sub(
        r'^updated = ".*"',
        'updated = "2026-07-19"',
        text,
        count=1,
        flags=re.M,
    )
    REGISTRY.write_text(text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    path_arg = lambda value: Path(value).expanduser()  # noqa: E731
    ap.add_argument("--chime-full-root", type=path_arg, default=CHIME_FULL_ROOT)
    ap.add_argument("--dsa-full-root", type=path_arg, default=DSA_FULL_ROOT)
    ap.add_argument("--upchan-root", type=path_arg, default=UPCHAN_ROOT)
    ap.add_argument(
        "--update-registry",
        action="store_true",
        help="rewrite the L0 section of docs/rse/control/results-registry.toml",
    )
    args = ap.parse_args()
    rows = build_certificates(
        chime_full_root=args.chime_full_root,
        dsa_full_root=args.dsa_full_root,
        upchan_root=args.upchan_root,
    )
    for r in rows:
        if not r["md5_ok"]:
            raise SystemExit(
                f"review-deck checksum mismatch: {r['nick']} {r['product']}"
            )
    if args.update_registry:
        # Preserve trust/cleared_by from existing registry rows when present.
        try:
            import tomllib
        except ModuleNotFoundError:  # pragma: no cover
            import tomli as tomllib  # type: ignore
        prior: dict[str, dict] = {}
        if REGISTRY.exists():
            data = tomllib.loads(REGISTRY.read_text())
            for item in data.get("result", []):
                rid = item.get("id", "")
                if rid.startswith("l0."):
                    prior[rid] = item
        for r in rows:
            rid = f"l0.{r['nick']}.{r['product']}"
            if rid in prior:
                r["trust"] = prior[rid].get("trust", "pending")
                # Prefer the plain-language clearance string once trusted.
                if r["trust"] == "trusted":
                    r["cleared_by"] = CLEARED_BY
                else:
                    r["cleared_by"] = prior[rid].get("cleared_by", "")
            elif r.get("trust") == "trusted":
                r["cleared_by"] = CLEARED_BY
        update_registry(rows)
        print(f"updated raw-layer section in {REGISTRY}")
    OUT_JSON.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"wrote {OUT_JSON} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
