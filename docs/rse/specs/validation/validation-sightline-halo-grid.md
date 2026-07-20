# Validation — sightline foreground-halo grid (Figure 2)

> Validated against **no formal plan file** (figure built ad-hoc this session);
> success criteria were synthesized from the implementation intent and the
> manuscript's foreground-census claims. Updated on 2026-07-07 against the
> parent working tree and generator commit `b1be242` on the `pipeline` submodule
> branch `agent/sightline-halo-grid-figure`.

## Scope

Target: the per-sightline foreground-halo grid figure
(`figures/sightline_halo_grid.pdf`, `\label{fig:sightline_halo_grid}`,
Figure 2), its generator
(`pipeline/galaxies/v2_0/sightline_halo_grid.py`), and its manuscript
integration in `sections/observations.tex`. Styled after Khrykin et al. 2024
(FLIMFLAM DR1, arXiv:2402.00505) Fig. 4.

## Synthesized success criteria

Since no `plan-*.md` exists, these are the implicit criteria the work was built
against:

1. Generator runs cleanly and emits pdf/svg/png.
2. Every panel and halo traces to the source catalog; counts are correct.
3. Exactly one cluster crossing is emphasized (matches the paper's "single
   cluster within R500" claim).
4. Manuscript compiles with the figure placed and numbered, no float/dead-cycle
   errors.
5. The figure is cited in the prose (an in-text `\ref`).
6. The result is reproducible: the committed figure can be regenerated from
   tracked code + a pinned data source.
7. Rendered figure is correct and legible (ticks, labels, colorbar, legend).

## Implementation status

| # | Criterion | Status |
|---|---|---|
| 1 | Generator runs, emits 3 formats | ✅ Verified |
| 2 | Data provenance / counts | ✅ Verified |
| 3 | Single cluster crossing emphasized | ✅ Verified |
| 4 | Manuscript compiles, figure placed | ✅ Verified |
| 5 | In-text `\ref` to the figure | ✅ Verified |
| 6 | Reproducible from tracked code + pinned data | ⚠️ Partial: code-side defects fixed; input catalog provenance remains external |
| 7 | Rendered figure correct/legible | ✅ Verified (with one caveat) |

## Automated verification results (fresh output, this session)

- ✅ **Generator run** (`sightline_halo_grid.py --out-dir …`) — exit 0, wrote
  pdf + svg + png.
- ✅ **Data provenance** — 9 z-known panels, 257 foreground halos, per-sightline
  counts: 20220207C 0, 20240203A 7, 20221113A 37, 20230307A 98, 20240229A 61,
  20220506D 5, 20230913A 3, 20220310F 44, 20221203A 2. All trace to
  `chime_dsa_gladep_candidates_ranked.csv` (`is_foreground`, z<z_frb).
- ✅ **Cluster crossing** — exactly 1 halo passes (strict R200 intersection AND
  M200 > 1e14): FRB 20230307A. Consistent with the manuscript's
  "single cluster whose sightline passes within R500" (observations.tex,
  budget.tex).
- ✅ **Manuscript compile** — `latexmk -pdf main.tex` exit 0, no
  "Output loop / dead cycles", no "Float too large for page". Figure resolves as
  `{2}{5}` (Figure 2, page 5), section "Foreground-galaxy search".
- ✅ **In-text reference** — `sections/observations.tex` now cites
  `Figure~\ref{fig:sightline_halo_grid}` before the figure block.
- ⚠️ **Reproducibility** — the code-side failures below were fixed by the
  `pipeline` generator branch; the remaining limitation is the external,
  unversioned halo-catalog input.

## Code review findings

### Critical

- **Resolved: generator was not committed.** The figure was first committed
  before `pipeline/galaxies/v2_0/sightline_halo_grid.py` existed in the
  submodule history. The generator now lives on
  `agent/sightline-halo-grid-figure` at `b1be242`, and the parent repo pins the
  submodule to that commit.

- **Output size depends on the working directory.** `main()` calls
  `fig.savefig(path)` with a comment stating it deliberately avoids
  `bbox_inches='tight'` (tight re-lays-out the axes after the display-space
  circle radii are computed, distorting the circles). But
  `pipeline/matplotlibrc` sets `savefig.bbox: tight` globally, and matplotlib
  auto-loads that rc **only when the process starts inside `pipeline/`**. Result:
  run from `pipeline/` → 1138×934 (tight, the layout the code says to avoid);
  run from repo root → 1200×975 (standard). Same code, same data, different
  output. The committed figure is the *tight* variant (aspect 1.218 vs 1.231),
  i.e. produced under the exact condition the code comment warns against. The
  visible distortion is small (~1% aspect; circles still read as round), so the
  rendered figure is acceptable, but the non-determinism must be closed.

### Important

- **Data source is external and unversioned.** `DEFAULT_HALO_CSV` points at
  `~/Data/frb-foreground-halos/results/chime_dsa_gladep_candidates_ranked.csv`,
  which is not inside any git repo (the source repo was archived 2026-07-05).
  Nothing pins the catalog version the committed figure was made from.

### Matches to intent (verified, not defects)

- Signed impact parameter (sign from Dec offset), display-space R200 circles,
  magma palette matching the burst waterfalls, single-cluster ring, empty
  panels for clean sightlines, redshift-ordered panels, shared axis labels — all
  present and rendered correctly.

## Rendered-figure check (criterion 7)

Read `figures/sightline_halo_grid.png` directly: ticks (major+minor) and tick
labels present on left column (impact parameter, ±500 kpc) and bottom panels
(redshift, 0.0–0.5); colorbar labeled; legend key legible; single cluster ring
in the FRB 20230307A panel. Legible and correct.

## Manual testing required

- **Visual sign-off on the final PDF placement** — confirm Figure 2 on page 5
  reads well at print size (caption length, panel density in the 20230307A
  field). Not machine-checkable.

## Recommendations

**Critical**
1. Commit the generator `pipeline/galaxies/v2_0/sightline_halo_grid.py` to the
   `pipeline` submodule (on a feature branch — the submodule blocks commits on
   `main`), then bump the submodule pointer in the top repo. Without this the
   committed figure is unreproducible. **Done 2026-07-07 at `b1be242`.**
2. Make the output deterministic regardless of run location: either set
   `bbox_inches` explicitly in `main()` (and re-verify the circles are
   undistorted with whatever value is chosen), or load the intended rc
   explicitly in the script rather than relying on cwd-based auto-load.

**Important**
3. Pin the halo-catalog provenance: record the CSV's checksum/date in the figure
   manifest or the generator docstring, and/or copy the exact input alongside
   the committed figure so the version is recoverable.

**Nice to have**
4. Add an in-text `\ref{fig:sightline_halo_grid}` in the "Foreground-galaxy
   search" prose (observations.tex) so the figure is cited, not orphaned.
   **Done 2026-07-07.**

**Follow-up (separate lane, not this figure)**
5. Empty `tmp1.tmp`, `tmp2.tmp`, `tmp3.tmp` are untracked in the top repo — stray
   0-byte artifacts, not produced by this figure work. Left untouched; dispose
   separately.

## Verdict

**Figure content and manuscript integration: PASS.** The figure is correct,
data-faithful, compiles, and renders legibly as Figure 2.

**Reproducibility and provenance: PASS (both Critical items resolved
2026-07-07).**

- Critical #1 (uncommitted generator) — **FIXED.** Generator committed on
  submodule branch `agent/sightline-halo-grid-figure` at `b1be242`. Verified:
  the committed blob regenerates the installed figure pixel-identically
  (1200×975).
- Critical #2 (cwd-dependent output) — **FIXED.** `savefig.bbox='standard'` is
  now pinned at import, overriding the repo matplotlibrc. Verified: output is
  identical (1200×975) run from `pipeline/` and from the repo root; the previous
  1138×934-vs-1200×975 split is gone. The installed figure was regenerated with
  the deterministic (undistorted-circle) layout and the manuscript recompiles
  clean.

### Remaining (not Critical)

- **Important** — data source still external/unversioned (`~/Data/…`). Recommend
  pinning its checksum/date. Not a blocker.
- **Nice to have** — the in-text `\ref{fig:sightline_halo_grid}` is now present.
- **Follow-up / one-way door** — the top-repo submodule pointer for `pipeline`
  is bumped to include `b1be242`; pushing the parent commit remains subject to
  the repo push gate.

## References

- Generator: `pipeline/galaxies/v2_0/sightline_halo_grid.py`
- Manuscript: `sections/observations.tex` (Figure 2 block, `fig:sightline_halo_grid`)
- Source catalog: `~/Data/frb-foreground-halos/results/chime_dsa_gladep_candidates_ranked.csv`
- Reference figure: Khrykin et al. 2024, arXiv:2402.00505, Fig. 4
