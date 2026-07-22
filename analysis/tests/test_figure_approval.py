import json
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_review_module():
    path = ROOT / "scripts/figure_review.py"
    spec = importlib.util.spec_from_file_location("figure_review_tool", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_figure_approval_gate() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/figure_review.py", "verify"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_review_slots_are_unique_and_cover_requested_families() -> None:
    config = json.loads((ROOT / "figure_review/slots.json").read_text())
    families = {group["family"] for group in config["groups"]}
    assert families == {
        "gallery",
        "association",
        "scintillation-summary",
        "scintillation-acf",
        "chime-scintillation-acf",
        "joint-model",
        "codetection-triptych",
        "scintillation-qualification",
        "foreground-halo-grid",
    }


def test_new_batch_can_select_one_stable_candidate() -> None:
    module = load_review_module()
    parsed = module.parser().parse_args(
        [
            "new-batch",
            "example",
            "--title",
            "example",
            "--pipeline-revision",
            "deadbeef",
            "--only",
            "fig6-scint-summary",
            "--only-family",
            "chime-scintillation-acf",
        ]
    )
    assert parsed.candidate == ["fig6-scint-summary"]
    assert parsed.only_family == ["chime-scintillation-acf"]


def test_figure3_review_slot_does_not_retroactively_protect_old_bytes() -> None:
    module = load_review_module()
    slot = next(item for item in module.slots() if item["id"] == "fig3-halo-grid")
    assert slot["protect_in_manuscript"] is False


def test_figure3_source_replay_batch_is_exactly_pinned() -> None:
    batch = ROOT / "figure_review/batches/2026-07-22-fig3-source-replay"
    manifest = json.loads((batch / "manifest.json").read_text())
    candidate = manifest["candidates"][0]
    assert manifest["source_revision"] == "afa9cc7d59f3f64b5098acd6cf8dca842ca86661"
    assert manifest["pipeline_revision"] == "f3c8d22a9088914e0179cfecf1ee4086777dc927"
    assert candidate["id"] == "fig3-halo-grid"
    assert candidate["artifact_sha256"] == (
        "45017274a7e3d60cf6918d72c3e89558c0e9d50e27427d39a216547c4999fa6c"
    )
    assert candidate["decision"]["status"] == "pending"
    assert candidate["protect_in_manuscript"] is False
    assert candidate["evidence_ids"] == [item["id"] for item in manifest["evidence"]]
    assert {item["id"]: item["sha256"] for item in manifest["evidence"]} == {
        "expanded-catalog-build": "6d7881c243613149b436de53e69b02d575041b84918f801a9c03a6d927329aef",
        "figure3-input": "ce0179a27fd2d4f18b7599cea9f8d56f98874d9c4c6a7a654e84395ff163acc3",
        "verdi-host-redshifts": "2d38d171ca065ccf9f65e88045c7a695cb7d36240b84e6d76061445be6d5b3aa",
        "law-host-redshifts": "fe8441914e81ddc519404a80652926cded9509053888e6455c5e94014876faaf",
        "candidate-redshift-ledger": "7235219a0dee7e2dd0be2f10fd524f2739fcce51eed6f0fe0af484d6c79026cf",
        "candidate-redshift-replay": "4f9a78864b8bc824dd5f81c588f9e8c704f0d589de2535c061951a72fe1df3f3",
        "candidate-redshift-payloads": "f1c21a95f174bd1ec0bbbf4bb4e82e15a0cac2442d3a529000eeb26787e75dd7",
    }


def test_gate_rejects_unapproved_protected_inclusion() -> None:
    module = load_review_module()
    target = "figures/codetection_data_grid.pdf"
    errors = module.approval_errors(
        rf"\includegraphics{{{target}}}",
        {target: "fig1-gallery"},
        {},
    )
    assert errors == [
        "protected figure is included without approval: fig1-gallery "
        "(figures/codetection_data_grid.pdf)"
    ]


def test_approval_receipts_are_hash_pinned() -> None:
    receipts = ROOT / "figure_review/approval_receipts"
    if not receipts.exists():
        return
    for path in receipts.glob("*.json"):
        receipt = json.loads(path.read_text())
        assert receipt["decision"]["status"] == "approved"
        assert receipt["decision"]["reviewer_role"] == "manuscript_owner"
        assert receipt["candidate_sha256"] == receipt["promoted_sha256"]
