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
# Keep model files out of the OS temporary directory: FastEmbed's default
# cache can be partially evicted while its snapshot metadata survives.
EMBED_CACHE_DIR = ANALYSIS_ROOT / ".kb" / "fastembed_cache"

# ---------------------------------------------------------------------------
# docs: manuscript + operational documentation
# ---------------------------------------------------------------------------
DOCS_GLOBS = [
    (ANALYSIS_ROOT, "*.md"),
    (ANALYSIS_ROOT, "docs/**/*.md"),
    (MANUSCRIPT_ROOT, "*.md"),
    (MANUSCRIPT_ROOT, "sections/*.tex"),
    (MANUSCRIPT_ROOT, "main.tex"),
    (ANALYSIS_ROOT, "observations/**/*.md"),
    (ANALYSIS_ROOT, "associations/**/*.md"),
    (ANALYSIS_ROOT, "dispersion/**/*.md"),
    (ANALYSIS_ROOT, "scattering/**/*.md"),
    (ANALYSIS_ROOT, "scintillation/**/*.md"),
    (ANALYSIS_ROOT, "foregrounds/**/*.md"),
    (ANALYSIS_ROOT, "energetics/**/*.md"),
    (ANALYSIS_ROOT, "polarization/**/*.md"),
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
]
CODE_MAX_FILE_BYTES = 200_000
NOTEBOOK_MAX_FILE_BYTES = 2_000_000  # .ipynb carry base64 outputs; outputs are skipped

# ---------------------------------------------------------------------------
# config: pipeline YAML (telescopes, samplers, bursts, manifests, envs)
# ---------------------------------------------------------------------------
CONFIG_GLOBS = [
    (ANALYSIS_ROOT, "config/**/*.yaml"),
    (ANALYSIS_ROOT, "config/**/*.yml"),
    (ANALYSIS_ROOT, "observations/**/*.yaml"),
    (ANALYSIS_ROOT, "associations/**/*.yaml"),
    (ANALYSIS_ROOT, "dispersion/**/*.yaml"),
    (ANALYSIS_ROOT, "scattering/**/*.yaml"),
    (ANALYSIS_ROOT, "scintillation/**/*.yaml"),
    (ANALYSIS_ROOT, "foregrounds/**/*.yaml"),
    (ANALYSIS_ROOT, "energetics/**/*.yaml"),
    (ANALYSIS_ROOT, "polarization/**/*.yaml"),
]

# ---------------------------------------------------------------------------
# git: commit history (analysis + parent). FLITS is pinned by uv.lock.
# ---------------------------------------------------------------------------
GIT_MAX_COMMITS = 2000
GIT_REPOS = [
    (ANALYSIS_ROOT, "analysis@"),
    (MANUSCRIPT_ROOT, ""),
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
