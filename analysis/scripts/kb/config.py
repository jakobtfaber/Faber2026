"""Knowledge-base configuration: source locations and allowlists.

Everything is relative to the repo root unless absolute. Edit here to add or
remove sources; adapters read these constants.
"""

from __future__ import annotations

from pathlib import Path

from workspace import ANALYSIS_ROOT, manuscript_root

MANUSCRIPT_ROOT = manuscript_root()

# SQLite database (gitignored).
DB_PATH = ANALYSIS_ROOT / ".kb" / "kb.sqlite3"

# ---------------------------------------------------------------------------
# docs: manuscript + operational documentation
# ---------------------------------------------------------------------------
DOCS_GLOBS = [
    (ANALYSIS_ROOT, "*.md"),
    (ANALYSIS_ROOT, "docs/**/*.md"),
    (MANUSCRIPT_ROOT, "*.md"),
    (MANUSCRIPT_ROOT, "sections/*.tex"),
    (MANUSCRIPT_ROOT, "main.tex"),
    (MANUSCRIPT_ROOT, "pipeline/*.md"),
    (MANUSCRIPT_ROOT, "pipeline/docs/**/*.md"),
    (MANUSCRIPT_ROOT, "pipeline/external/**/*.md"),
    (MANUSCRIPT_ROOT, "pipeline/exports/*.tex"),
]
# Paths never indexed by the docs adapter (tickets have their own adapter).
DOCS_EXCLUDE_PARTS = {
    ".venv", "node_modules", "__pycache__", ".archive", "quarantine", "graphify-out",
}
TICKETS_DIR = ANALYSIS_ROOT / "docs" / "rse" / "wayfinder" / "tickets"

# ---------------------------------------------------------------------------
# code: python source, path-allowlisted (mirrors Cerebras per-repo allowlists)
# ---------------------------------------------------------------------------
CODE_DIRS = [
    ANALYSIS_ROOT / "scripts",
    ANALYSIS_ROOT / "tests",
    MANUSCRIPT_ROOT / "figures" / "ax",
    MANUSCRIPT_ROOT / "pipeline" / "analysis",
    MANUSCRIPT_ROOT / "pipeline" / "galaxies",
    MANUSCRIPT_ROOT / "pipeline" / "scintillation",
    MANUSCRIPT_ROOT / "pipeline" / "scattering",
    MANUSCRIPT_ROOT / "pipeline" / "flits",
    MANUSCRIPT_ROOT / "pipeline" / "simulation",
    MANUSCRIPT_ROOT / "pipeline" / "dispersion",
    MANUSCRIPT_ROOT / "pipeline" / "crossmatching",
    MANUSCRIPT_ROOT / "pipeline" / "scripts",
    MANUSCRIPT_ROOT / "pipeline" / "tests",
    MANUSCRIPT_ROOT / "pipeline" / "notebooks",
    MANUSCRIPT_ROOT / "pipeline" / "external",
]
CODE_MAX_FILE_BYTES = 200_000
NOTEBOOK_MAX_FILE_BYTES = 2_000_000  # .ipynb carry base64 outputs; outputs are skipped

# ---------------------------------------------------------------------------
# config: pipeline YAML (telescopes, samplers, bursts, manifests, envs)
# ---------------------------------------------------------------------------
CONFIG_GLOBS = [
    (MANUSCRIPT_ROOT, "pipeline/**/*.yaml"),
    (MANUSCRIPT_ROOT, "pipeline/**/*.yml"),
]

# ---------------------------------------------------------------------------
# git: commit history (parent repo + pipeline/ submodule). PRs via `gh`.
# ---------------------------------------------------------------------------
GIT_MAX_COMMITS = 2000
GIT_REPOS = [
    (ANALYSIS_ROOT, "analysis@"),
    (MANUSCRIPT_ROOT, ""),
    (MANUSCRIPT_ROOT / "pipeline", "pipeline@"),
]

# ---------------------------------------------------------------------------
# refs: cited-references library
# ---------------------------------------------------------------------------
BIB_FILES = [MANUSCRIPT_ROOT / "bib" / "refs.bib"]
# Optional Zotero-enriched export (CSL JSON, keyed by DOI/citekey); created by
# the references-library workflow. Merged into bib entries when present.
REFS_CSL_JSON = MANUSCRIPT_ROOT / "bib" / "references_library.json"

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
