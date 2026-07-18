# Plan: post-PL-PBF joint-fit figure reconciliation

**Status:** approved by owner ruling and executed fail-closed
**Research:** `research-post-pl-pbf-figure-reconciliation-2026-07-17.md`

1. Pin the audit to manuscript `a9b881a3` and pipeline `17d9d266`; inspect the
   reviewed tree and live artifact stores without modifying the active fit lane.
2. Promote replacements only if a complete post-PL-PBF production roster,
   matching dumps, provenance metadata, and review-bound panels exist.
3. Because that gate fails, remove the representative triptych input/reference
   and the appendix joint-grid input while preserving all historical files.
4. Mark both manifest families unembedded and record the exact blocker in the
   manuscript, checklist, and reproducibility documentation.
5. Add regression coverage for the compiled TeX graph and manifest state; run
   focused tests, the consistency audit, and a clean LaTeX build.
