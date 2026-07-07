# Two-Telescope Model-Derived ToAs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-epoch roster surface with a two-telescope, model-derived ToA contract for CHIME/FRB and DSA-110.

**Architecture:** The manuscript roster remains a sample-identification table with no ToA columns. Precision timing moves to a future association/timing artifact that has one row per burst per telescope and records the model-selected arrival parameter, reference frequency, DM convention, uncertainty, method, and source artifact. Until that artifact exists and is pinned, timing residuals and chance-coincidence timing claims remain withheld.

**Tech Stack:** AASTeX manuscript files, `scripts/make_sample_table.py`, pinned `pipeline/` metadata, future FLITS pipeline tests.

---

### Task 1: Remove the Single-ToA Roster Surface

**Files:**
- Modify: `scripts/make_sample_table.py`
- Modify: `sample_table.tex`
- Modify: `sections/observations.tex`

- [ ] **Step 1: Update the roster generator**

Remove `mjd` and `utc` from the generated row payload, change the table shape from `llcccc` to `llcc`, and change the caption to say timing products are withheld until CHIME and DSA model-derived ToAs are available together.

Run:

```bash
python scripts/make_sample_table.py
```

Expected:

```text
wrote sample_table.tex (12 rows, pinned commit <sha>)
```

- [ ] **Step 2: Verify the generated table has no ToA columns**

Run:

```bash
rg -n "MJD|UTC|epoch|ToA|arrival" sample_table.tex
```

Expected: matches only in comments or withheld-product prose, not in `\tablehead` columns.

- [ ] **Step 3: Update observations prose**

Change `sections/observations.tex` so Table 1 lists only TNS designations, nicknames, and sky positions. The paragraph must state that CHIME and DSA ToAs are withheld together pending the timing provenance artifact.

- [ ] **Step 4: Build the manuscript**

Run:

```bash
make
```

Expected: exit 0 with no new warnings from the table change.

### Task 2: State the Two-Telescope ToA Contract

**Files:**
- Modify: `sections/toa.tex`

- [ ] **Step 1: Replace the generic V6 wording**

Change the residuals/systematics paragraph so restoring timing residuals requires:

```text
model-selected CHIME and DSA ToAs;
one shared reference frequency;
one declared DM convention;
per-telescope ToA uncertainty and provenance;
explicit flagging of any detection/peak ToA fallback.
```

- [ ] **Step 2: Keep the delay equations**

Do not change `eq:dmdelay` or `eq:geodelay`; they remain the residual calculation once valid per-telescope ToAs exist.

- [ ] **Step 3: Build the manuscript**

Run:

```bash
make
```

Expected: exit 0 with no new warnings from `sections/toa.tex`.

### Task 3: Future FLITS Timing Artifact

**Files:**
- Future create in FLITS: `crossmatching/model_toa_provenance.csv`
- Future create in FLITS: `scripts/build_model_toa_provenance.py`
- Future create in FLITS: `tests/test_model_toa_provenance.py`

- [ ] **Step 1: Add a schema test before implementation**

The future test should require two rows per burst, one for `chime` and one for `dsa`, with these columns:

```python
REQUIRED = {
    "nickname",
    "telescope",
    "toa_utc",
    "toa_mjd",
    "reference_frequency_mhz",
    "dm_used",
    "dm_convention",
    "model_family",
    "model_selection_status",
    "toa_uncertainty_ms",
    "source_artifact",
    "source_checksum",
}
```

Expected: 24 rows for the 12-burst sample; no empty provenance cells for rows with a citable ToA.

- [ ] **Step 2: Implement only accepted model-derived rows**

The builder should emit a citable ToA only when the per-burst, per-telescope model-selection state accepts the morphology model. Detection/peak ToAs may be emitted only with `model_selection_status=detection_fallback` and must be excluded from precision timing residuals.

- [ ] **Step 3: Gate residual restoration on this artifact**

The manuscript timing table and residual/P_cc columns may be restored only after `model_toa_provenance.csv` is committed or regenerated in CI, tested, and the Faber2026 `pipeline/` pin is bumped deliberately.

### Self-Review

- Spec coverage: Task 1 removes the misleading single-ToA roster surface; Task 2 states the CHIME+DSA model-derived ToA contract; Task 3 captures the future FLITS artifact needed before timing residuals return.
- Placeholder scan: no placeholder markers or unspecified implementation steps remain.
- Type consistency: `telescope`, `toa_utc`, `toa_mjd`, `reference_frequency_mhz`, `dm_used`, `dm_convention`, `model_family`, `model_selection_status`, `toa_uncertainty_ms`, `source_artifact`, and `source_checksum` are used consistently.
