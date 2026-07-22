#!/usr/bin/env python3
"""Fail-closed author review and promotion for manuscript figures.

Candidates are immutable, hash-pinned files under figure_review/batches/.  A
candidate can reach a manuscript target only after an explicit manuscript-owner
decision.  The resulting receipt binds the decision, candidate bytes, and
promoted bytes together; ``verify`` rejects protected TeX inclusions without a
matching receipt.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = ROOT / "figure_review"
SLOTS_PATH = REVIEW_ROOT / "slots.json"
RECEIPTS = REVIEW_ROOT / "approval_receipts"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slots() -> list[dict]:
    data = load_json(SLOTS_PATH)
    expanded: list[dict] = []
    for group in data["groups"]:
        if "items" not in group:
            expanded.append(group)
            continue
        for item in group["items"]:
            nick = item["nick"]
            expanded.append(
                {
                    "id": group["id_pattern"].format(**item),
                    "title": group["title_pattern"].format(**item),
                    "family": group["family"],
                    "target": group["target_pattern"].format(**item),
                    "generator": group["generator"],
                    "subject": item,
                    "required_provenance": group["required_provenance"],
                }
            )
    return expanded


def batch_dir(batch_id: str) -> Path:
    return REVIEW_ROOT / "batches" / batch_id


def manifest_path(batch_id: str) -> Path:
    return batch_dir(batch_id) / "manifest.json"


def render_preview(pdf: Path, preview: Path) -> None:
    preview.parent.mkdir(parents=True, exist_ok=True)
    if pdf.suffix.lower() == ".png":
        shutil.copy2(pdf, preview)
        return
    prefix = preview.with_suffix("")
    subprocess.run(
        ["pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-png", "-r", "120", str(pdf), str(prefix)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def command_new_batch(args: argparse.Namespace) -> None:
    available_slots = slots()
    requested = set(args.candidate or [])
    known = {slot["id"] for slot in available_slots}
    unknown = requested - known
    if unknown:
        raise SystemExit(f"unknown candidate ids: {sorted(unknown)}")
    requested_families = set(args.only_family or [])
    known_families = {slot["family"] for slot in available_slots}
    unknown_families = requested_families - known_families
    if unknown_families:
        raise SystemExit(f"unknown candidate families: {sorted(unknown_families)}")
    selected_slots = [
        slot
        for slot in available_slots
        if (
            not requested
            and not requested_families
            or slot["id"] in requested
            or slot["family"] in requested_families
        )
    ]
    destination = batch_dir(args.batch_id)
    if destination.exists():
        raise SystemExit(f"batch already exists: {destination.relative_to(ROOT)}")
    candidates_dir = destination / "candidates"
    previews_dir = destination / "previews"
    candidates_dir.mkdir(parents=True)
    source_revision = subprocess.check_output(
        ["git", "rev-parse", args.source_revision], cwd=ROOT, text=True
    ).strip()
    dm_catalog = ROOT / "analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv"
    with dm_catalog.open(newline="", encoding="utf-8") as stream:
        dm_rows = list(csv.DictReader(stream))
    dm_by_nick = {row["nick"].casefold(): row for row in dm_rows}

    family_evidence = {
        "gallery": ["dm-catalog", "joint-render-manifest"],
        "association": ["dm-catalog"],
        "joint-model": ["dm-catalog", "joint-render-manifest", "joint-fit-roster", "joint-fit-adjudication"],
        "codetection-triptych": ["dm-catalog", "joint-render-manifest", "joint-fit-roster", "joint-fit-adjudication"],
        "scintillation-summary": [
            "oran-qualification",
            "chime-campaign-validation",
            "chromatica-hi-campaign",
            "chime-campaign-figure-review",
            "joint-scint-figure-provenance",
        ],
        "scintillation-acf": ["scint-component-catalog", "scint-fit-catalog"],
        "chime-scintillation-acf": [
            "chime-campaign-validation",
            "chime-campaign-records",
            "chime-campaign-figure-review",
            "joint-scint-figure-provenance",
        ],
        "scintillation-qualification": ["oran-qualification"],
    }
    required_evidence = {
        evidence_id
        for slot in selected_slots
        for evidence_id in family_evidence[slot["family"]]
    }

    provenance_dir = destination / "provenance"
    provenance_dir.mkdir()
    evidence_specs = [
        ("dm-catalog", "parent", "analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv"),
        ("joint-render-manifest", "parent", "scripts/jointmodel_triptych_manifest.yaml"),
        ("joint-fit-roster", "pipeline", "analysis/scattering-dm-locked-2026-07-14/fit_roster.csv"),
        ("joint-fit-adjudication", "pipeline", "analysis/scattering-dm-locked-2026-07-14/results/fit_adjudication.csv"),
        ("scint-component-catalog", "pipeline", "analysis/scintillation-dsa-lorentzian-2026-07-07/results/dsa_lorentzian_components.csv"),
        ("scint-fit-catalog", "pipeline", "analysis/scintillation-dsa-lorentzian-2026-07-07/results/dsa_lorentzian_fits.json"),
        ("oran-qualification", "pipeline", "analysis/scintillation-dsa-lorentzian-2026-07-07/results/oran_qualified/validation.json"),
        ("chime-campaign-validation", "pipeline", "analysis/window-tuning-campaign-2026-07-17/results/validation.json"),
        ("chime-campaign-records", "pipeline", "analysis/window-tuning-campaign-2026-07-17/results/campaign_results.jsonl"),
        ("chromatica-hi-campaign", "pipeline", "analysis/window-tuning-campaign-2026-07-17/results/chromatica_hi_campaign.json"),
        ("chime-campaign-figure-review", "pipeline", "analysis/window-tuning-campaign-2026-07-17/results/figures.review.json"),
        ("joint-scint-figure-provenance", "parent", "analysis/scintillation-summary/joint_figure_provenance.json"),
    ]
    evidence: list[dict] = []
    for evidence_id, repository, source_path in evidence_specs:
        if evidence_id not in required_evidence:
            continue
        if repository == "parent":
            command = ["git", "show", f"{source_revision}:{source_path}"]
            revision = source_revision
        else:
            command = ["git", "-C", str(args.pipeline_repo), "show", f"{args.pipeline_revision}:{source_path}"]
            revision = args.pipeline_revision
        suffix = Path(source_path).suffix
        stored = provenance_dir / f"{evidence_id}{suffix}"
        stored.write_bytes(subprocess.check_output(command, cwd=ROOT))
        evidence.append(
            {
                "id": evidence_id,
                "repository": repository,
                "source_path": source_path,
                "source_revision": revision,
                "stored_path": str(stored.relative_to(destination)),
                "sha256": sha256(stored),
            }
        )
    records: list[dict] = []
    for slot in selected_slots:
        source = args.candidate_root / slot["target"]
        if not source.exists() and not args.read_from_revision:
            raise SystemExit(f"missing candidate source for {slot['id']}: {slot['target']}")
        artifact_rel = Path("candidates") / f"{slot['id']}{Path(slot['target']).suffix.lower()}"
        preview_rel = Path("previews") / f"{slot['id']}.png"
        artifact = destination / artifact_rel
        if args.read_from_revision:
            if slot["target"].startswith("pipeline/"):
                relative = slot["target"].removeprefix("pipeline/")
                command = [
                    "git",
                    "-C",
                    str(args.pipeline_repo),
                    "show",
                    f"{args.pipeline_revision}:{relative}",
                ]
            else:
                command = ["git", "show", f"{source_revision}:{slot['target']}"]
            artifact.write_bytes(subprocess.check_output(command, cwd=ROOT))
        else:
            shutil.copy2(source, artifact)
        render_preview(artifact, destination / preview_rel)
        record = {
                **slot,
                "artifact": str(artifact_rel),
                "artifact_sha256": sha256(artifact),
                "preview": str(preview_rel),
                "decision": {
                    "status": args.initial_status,
                    "reviewer": args.reviewer,
                    "reviewer_role": "manuscript_owner" if args.reviewer else None,
                    "reviewed_at": utc_now() if args.reviewer else None,
                    "notes": args.note,
                },
                "evidence_ids": family_evidence[slot["family"]],
            }
        subject_nick = slot.get("subject", {}).get("nick")
        if subject_nick:
            record["dm_measurement"] = dm_by_nick.get(subject_nick.casefold())
        elif slot["family"] in {"gallery", "association"}:
            record["dm_measurements"] = dm_rows
        records.append(record)
    manifest = {
        "schema_version": 1,
        "batch_id": args.batch_id,
        "title": args.title,
        "created_at": utc_now(),
        "source_revision": source_revision,
        "pipeline_revision": args.pipeline_revision,
        "dm_catalog": {
            "path": str(dm_catalog.relative_to(ROOT)),
            "sha256": sha256(dm_catalog),
        },
        "evidence": evidence,
        "policy": {
            "approval_is_per_candidate": True,
            "agent_visual_review_is_not_author_approval": True,
            "promotion_requires_exact_hash_match": True,
        },
        "candidates": records,
    }
    write_json(manifest_path(args.batch_id), manifest)
    render_packet(args.batch_id)
    print(f"created {manifest_path(args.batch_id).relative_to(ROOT)}")


def validate_candidate(batch: Path, candidate: dict) -> list[str]:
    errors: list[str] = []
    artifact = batch / candidate["artifact"]
    preview = batch / candidate["preview"]
    if not artifact.is_file():
        errors.append(f"{candidate['id']}: missing artifact {candidate['artifact']}")
    elif sha256(artifact) != candidate["artifact_sha256"]:
        errors.append(f"{candidate['id']}: artifact SHA-256 mismatch")
    if not preview.is_file():
        errors.append(f"{candidate['id']}: missing preview {candidate['preview']}")
    for key in ("target", "generator", "required_provenance"):
        if not candidate.get(key):
            errors.append(f"{candidate['id']}: missing {key}")
    return errors


def validate_batch(batch_id: str) -> tuple[dict, list[str]]:
    manifest = load_json(manifest_path(batch_id))
    batch = batch_dir(batch_id)
    errors: list[str] = []
    catalog = ROOT / manifest["dm_catalog"]["path"]
    if not catalog.is_file() or sha256(catalog) != manifest["dm_catalog"]["sha256"]:
        errors.append("batch DM catalog is missing or has changed")
    evidence_ids: set[str] = set()
    for item in manifest.get("evidence", []):
        evidence_ids.add(item["id"])
        stored = batch / item["stored_path"]
        if not stored.is_file() or sha256(stored) != item["sha256"]:
            errors.append(f"evidence is missing or changed: {item['id']}")
    seen: set[str] = set()
    for candidate in manifest["candidates"]:
        if candidate["id"] in seen:
            errors.append(f"duplicate candidate id: {candidate['id']}")
        seen.add(candidate["id"])
        errors.extend(validate_candidate(batch, candidate))
        missing = set(candidate.get("evidence_ids", [])) - evidence_ids
        if missing:
            errors.append(f"{candidate['id']}: unknown evidence ids {sorted(missing)}")
    return manifest, errors


def render_packet(batch_id: str) -> None:
    manifest, errors = validate_batch(batch_id)
    batch = batch_dir(batch_id)
    cards: list[str] = []
    evidence = {item["id"]: item for item in manifest.get("evidence", [])}
    for candidate in manifest["candidates"]:
        decision = candidate["decision"]
        subject = candidate.get("subject", {})
        subject_text = " &middot; ".join(
            html.escape(str(value)) for value in subject.values() if value
        )
        evidence_links = ", ".join(
            f'<a href="{html.escape(evidence[item]["stored_path"])}">{html.escape(item)}</a>'
            for item in candidate.get("evidence_ids", [])
        )
        dm_payload = candidate.get("dm_measurement") or candidate.get("dm_measurements")
        dm_html = (
            f"<pre>{html.escape(json.dumps(dm_payload, indent=2))}</pre>" if dm_payload else "None"
        )
        cards.append(
            f"""
<article id="{html.escape(candidate['id'])}" class="card status-{html.escape(decision['status'])}">
  <h2>{html.escape(candidate['id'])}: {html.escape(candidate['title'])}</h2>
  <p><strong>Status:</strong> {html.escape(decision['status'])}</p>
  <p>{subject_text}</p>
  <a href="{html.escape(candidate['artifact'])}"><img src="{html.escape(candidate['preview'])}" alt="{html.escape(candidate['title'])}"></a>
  <dl>
    <dt>Manuscript target</dt><dd><code>{html.escape(candidate['target'])}</code></dd>
    <dt>Candidate SHA-256</dt><dd><code>{html.escape(candidate['artifact_sha256'])}</code></dd>
    <dt>Generator</dt><dd><code>{html.escape(candidate['generator'])}</code></dd>
    <dt>Required provenance</dt><dd>{html.escape('; '.join(candidate['required_provenance']))}</dd>
    <dt>Frozen evidence</dt><dd>{evidence_links}</dd>
    <dt>DM record</dt><dd>{dm_html}</dd>
    <dt>Reviewer notes</dt><dd>{html.escape(decision.get('notes') or 'None yet')}</dd>
  </dl>
</article>"""
        )
    error_html = "".join(f"<li>{html.escape(error)}</li>" for error in errors) or "<li>None</li>"
    contact_sheet = batch / "contact-sheet.png"
    preview_paths = [batch / candidate["preview"] for candidate in manifest["candidates"]]
    try:
        from PIL import Image
    except ImportError:
        contact_sheet.unlink(missing_ok=True)
    else:
        cell_width, cell_height, columns = 720, 220, 2
        rows = (len(preview_paths) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
        for index, path in enumerate(preview_paths):
            with Image.open(path) as opened:
                tile = opened.convert("RGB")
                tile.thumbnail((cell_width - 12, cell_height - 12))
                x = (index % columns) * cell_width + (cell_width - tile.width) // 2
                y = (index // columns) * cell_height + (cell_height - tile.height) // 2
                sheet.paste(tile, (x, y))
        sheet.save(contact_sheet)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(manifest['title'])}</title>
<style>
body{{font:16px system-ui,sans-serif;max-width:1500px;margin:auto;padding:2rem;background:#f5f6f8;color:#17202a}}
.summary,.card{{background:white;border:1px solid #ccd2d8;border-radius:10px;padding:1rem;margin:1rem 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:1rem}}
.card{{margin:0;border-left:8px solid #c17d00}} .status-approved{{border-left-color:#16803c}} .status-needs_revision{{border-left-color:#b42318}}
img{{width:100%;max-height:680px;object-fit:contain;background:white}} code{{word-break:break-all}} dt{{font-weight:700;margin-top:.5rem}}
</style></head><body>
<h1>{html.escape(manifest['title'])}</h1>
<section class="summary"><p><strong>Batch:</strong> <code>{html.escape(batch_id)}</code><br>
<strong>Source revision:</strong> <code>{html.escape(manifest['source_revision'])}</code><br>
<strong>Pipeline revision:</strong> <code>{html.escape(manifest['pipeline_revision'])}</code><br>
<strong>DM catalog:</strong> <code>{html.escape(manifest['dm_catalog']['sha256'])}</code></p>
<p>Approval is per candidate. Reply with the stable candidate ID and either <em>approve</em> or <em>needs revision</em>, plus notes. Promotion is impossible unless the approved candidate bytes still match this packet.</p>
<p><a href="contact-sheet.png">Open the full contact sheet</a> before reviewing individual evidence cards.</p>
<h3>Packet validation</h3><ul>{error_html}</ul></section>
<main class="grid">{''.join(cards)}</main></body></html>"""
    (batch / "index.html").write_text(page, encoding="utf-8")


def command_render(args: argparse.Namespace) -> None:
    render_packet(args.batch_id)
    _, errors = validate_batch(args.batch_id)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"rendered {batch_dir(args.batch_id).relative_to(ROOT) / 'index.html'}")


def command_decide(args: argparse.Namespace) -> None:
    manifest, errors = validate_batch(args.batch_id)
    if errors:
        raise SystemExit("\n".join(errors))
    candidate = next((item for item in manifest["candidates"] if item["id"] == args.candidate), None)
    if candidate is None:
        raise SystemExit(f"unknown candidate: {args.candidate}")
    candidate["decision"] = {
        "status": args.status,
        "reviewer": args.reviewer,
        "reviewer_role": "manuscript_owner",
        "reviewed_at": utc_now(),
        "notes": args.note,
    }
    write_json(manifest_path(args.batch_id), manifest)
    render_packet(args.batch_id)
    print(f"recorded {args.status} for {args.candidate}")


def command_promote(args: argparse.Namespace) -> None:
    manifest, errors = validate_batch(args.batch_id)
    if errors:
        raise SystemExit("\n".join(errors))
    candidate = next((item for item in manifest["candidates"] if item["id"] == args.candidate), None)
    if candidate is None:
        raise SystemExit(f"unknown candidate: {args.candidate}")
    decision = candidate["decision"]
    if decision.get("status") != "approved" or decision.get("reviewer_role") != "manuscript_owner":
        raise SystemExit(f"{args.candidate} is not approved by the manuscript owner")
    source = batch_dir(args.batch_id) / candidate["artifact"]
    if sha256(source) != candidate["artifact_sha256"]:
        raise SystemExit(f"{args.candidate} candidate bytes changed after approval")
    target = ROOT / candidate["target"]
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    receipt = {
        "schema_version": 1,
        "candidate_id": candidate["id"],
        "batch_id": args.batch_id,
        "candidate_sha256": candidate["artifact_sha256"],
        "promoted_target": candidate["target"],
        "promoted_sha256": sha256(target),
        "decision": decision,
        "dm_catalog": manifest["dm_catalog"],
        "source_revision": manifest["source_revision"],
        "pipeline_revision": manifest["pipeline_revision"],
        "promoted_at": utc_now(),
    }
    write_json(RECEIPTS / f"{candidate['id']}.json", receipt)
    print(f"promoted {candidate['id']} -> {candidate['target']}")


def included_tex() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "sections").glob("*.tex")))


def approval_errors(tex: str, protected: dict[str, str], receipts: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    for target, candidate_id in protected.items():
        if target not in tex and target.removeprefix("figures/") not in tex:
            continue
        artifact = ROOT / target
        receipt = receipts.get(target)
        if receipt is None:
            errors.append(f"protected figure is included without approval: {candidate_id} ({target})")
            continue
        if receipt["decision"].get("status") != "approved":
            errors.append(f"receipt is not approved: {candidate_id}")
        if not artifact.is_file() or sha256(artifact) != receipt["promoted_sha256"]:
            errors.append(f"promoted bytes do not match receipt: {candidate_id}")
        if receipt["candidate_sha256"] != receipt["promoted_sha256"]:
            errors.append(f"candidate/promoted hash mismatch: {candidate_id}")
    return errors


def command_verify(_: argparse.Namespace) -> None:
    protected = {slot["target"]: slot["id"] for slot in slots()}
    receipts: dict[str, dict] = {}
    for path in RECEIPTS.glob("*.json") if RECEIPTS.exists() else []:
        receipt = load_json(path)
        receipts[receipt["promoted_target"]] = receipt
    errors = approval_errors(included_tex(), protected, receipts)
    if errors:
        raise SystemExit("\n".join(errors))
    print("figure approval gate: ok")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    sub = result.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new-batch")
    new.add_argument("batch_id")
    new.add_argument("--title", required=True)
    new.add_argument("--source-revision", default="HEAD")
    new.add_argument(
        "--candidate-root",
        type=Path,
        default=ROOT,
        help="root containing candidate outputs in manuscript-relative paths",
    )
    new.add_argument(
        "--read-from-revision",
        action="store_true",
        help="stage target bytes from --source-revision instead of the worktree",
    )
    new.add_argument("--pipeline-revision", required=True)
    new.add_argument(
        "--candidate",
        "--only",
        dest="candidate",
        action="append",
        help="stage only this candidate id; repeat for multiple candidates",
    )
    new.add_argument(
        "--pipeline-repo",
        type=Path,
        default=ROOT / "pipeline",
        help="FLITS checkout used to read submodule artifacts",
    )
    new.add_argument("--initial-status", choices=("pending", "needs_revision"), default="pending")
    new.add_argument("--reviewer")
    new.add_argument("--note")
    new.add_argument(
        "--only-family",
        action="append",
        help="stage every candidate in this configured family; repeat as needed",
    )
    new.set_defaults(func=command_new_batch)
    render = sub.add_parser("render")
    render.add_argument("batch_id")
    render.set_defaults(func=command_render)
    decide = sub.add_parser("decide")
    decide.add_argument("batch_id")
    decide.add_argument("candidate")
    decide.add_argument("status", choices=("approved", "needs_revision"))
    decide.add_argument("--reviewer", required=True)
    decide.add_argument("--note", required=True)
    decide.set_defaults(func=command_decide)
    promote = sub.add_parser("promote")
    promote.add_argument("batch_id")
    promote.add_argument("candidate")
    promote.set_defaults(func=command_promote)
    verify = sub.add_parser("verify")
    verify.set_defaults(func=command_verify)
    return result


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
