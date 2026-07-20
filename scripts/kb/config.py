"""Knowledge-base configuration: source locations and allowlists.

Everything is relative to the repo root unless absolute. Edit here to add or
remove sources; adapters read these constants.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# SQLite database (gitignored).
DB_PATH = REPO_ROOT / ".kb" / "kb.sqlite3"

# ---------------------------------------------------------------------------
# docs: manuscript + operational documentation
# ---------------------------------------------------------------------------
DOCS_GLOBS = [
    "*.md",                # CONTEXT.md, PIPELINE.md, REPRODUCE.md, ...
    "docs/**/*.md",        # rse specs, board, protocols, referee docs
    "sections/*.tex",
    "main.tex",
    "pipeline/*.md",       # submodule top-level docs
    "pipeline/docs/**/*.md",
    "pipeline/external/**/*.md",   # vendored-tool READMEs
    "pipeline/exports/*.tex",      # generated manuscript tables
]
# Paths never indexed by the docs adapter (tickets have their own adapter).
DOCS_EXCLUDE_PARTS = {
    ".venv", "node_modules", "__pycache__", "quarantine", "graphify-out",
}
TICKETS_DIR = REPO_ROOT / "docs" / "rse" / "wayfinder" / "tickets"

# ---------------------------------------------------------------------------
# code: python source, path-allowlisted (mirrors Cerebras per-repo allowlists)
# ---------------------------------------------------------------------------
CODE_DIRS = [
    "scripts",
    "tests",
    "pipeline/analysis",
    "pipeline/galaxies",
    "pipeline/scintillation",
    "pipeline/scattering",
    "pipeline/flits",
    "pipeline/simulation",
    "pipeline/dispersion",
    "pipeline/crossmatching",
    "pipeline/scripts",
    "pipeline/tests",
    "pipeline/notebooks",   # .py and .ipynb (cell-level chunks)
    "pipeline/external",    # vendored DM-power / DM_phase
]
CODE_MAX_FILE_BYTES = 200_000
NOTEBOOK_MAX_FILE_BYTES = 2_000_000  # .ipynb carry base64 outputs; outputs are skipped

# ---------------------------------------------------------------------------
# config: pipeline YAML (telescopes, samplers, bursts, manifests, envs)
# ---------------------------------------------------------------------------
CONFIG_GLOBS = [
    "pipeline/**/*.yaml",
    "pipeline/**/*.yml",
]

# ---------------------------------------------------------------------------
# git: commit history (parent repo + pipeline/ submodule). PRs via `gh`.
# ---------------------------------------------------------------------------
GIT_MAX_COMMITS = 2000
GIT_SUBMODULES = ["pipeline"]   # refs become "pipeline@<sha>"

# ---------------------------------------------------------------------------
# refs: cited-references library
# ---------------------------------------------------------------------------
BIB_FILES = ["bib/refs.bib"]
# Optional Zotero-enriched export (CSL JSON, keyed by DOI/citekey); created by
# the references-library workflow. Merged into bib entries when present.
REFS_CSL_JSON = REPO_ROOT / "bib" / "references_library.json"

# ---------------------------------------------------------------------------
# obsidian: personal vault (optional). Set to an absolute Path to enable, e.g.
# OBSIDIAN_VAULT = Path("/Users/jakobfaber/Obsidian/Research")
# ---------------------------------------------------------------------------
OBSIDIAN_VAULT: Path | None = None

# ---------------------------------------------------------------------------
# retrieval
# ---------------------------------------------------------------------------
EMBED_MODEL = "BAAI/bge-small-en-v1.5"   # via fastembed (ONNX, local, 384-d)
EMBED_DIM = 384
RRF_K = 60          # reciprocal-rank-fusion constant (Cerebras uses 60)
CANDIDATES = 50     # per-signal candidate depth before fusion
CHUNK_TARGET = 1200  # chars; headings-aware chunkers aim for <= this
CHUNK_MIN = 200      # merge chunks smaller than this into neighbours
