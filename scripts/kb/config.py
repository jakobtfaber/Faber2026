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
    "analysis/*.md",
    "analysis/docs/**/*.md",
    "analysis/campaigns/**/*.md",
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
    "analysis/scripts",
    "analysis/tests",
    "analysis/campaigns",
]
CODE_MAX_FILE_BYTES = 200_000
NOTEBOOK_MAX_FILE_BYTES = 2_000_000  # .ipynb carry base64 outputs; outputs are skipped

# ---------------------------------------------------------------------------
# config: project YAML
# ---------------------------------------------------------------------------
CONFIG_GLOBS = [
    "analysis/config/**/*.yaml",
    "analysis/config/**/*.yml",
    "analysis/campaigns/**/*.yaml",
    "analysis/campaigns/**/*.yml",
]

# ---------------------------------------------------------------------------
# git: commit history (parent repo + analysis submodule). PRs via `gh`.
# ---------------------------------------------------------------------------
GIT_MAX_COMMITS = 2000
GIT_SUBMODULES = ["analysis"]

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
