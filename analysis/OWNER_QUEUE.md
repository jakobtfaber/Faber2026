# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific and visual decisions. Silence leaves every item blocked._

## 1. Figure 3 approval

**Decision:** Approve the exact installed Figure 3 bytes for the manuscript?

**Recommended:** `approve` — The independent census validation passes and the staged bytes match the manuscript exactly.

**Choose:**

- `approve` — Approve the exact figure bytes.
- `revise` — Request a revision and state the required visual change.

**Context:**

- All six independent census, source, matching, coverage, radius, and figure-content checks pass.
- The staged review artifact and installed manuscript figure are byte-identical.
- This approval is visual; it does not replace the recorded scientific validation.

**Evidence:**

- [Exact Figure 3 PDF](figure_review/artifacts/staging/fig3_halo_grid/figures/sightline_halo_grid.pdf) — `281e4bf4…`
- [Independent validation](docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/validation.json) — `577ccb27…`
- [Reproduction receipt](docs/rse/specs/receipt-foreground-census-analysis-only-2026-07-29.md) — `c13404f8…`

**Effect:** Approval closes the Figure 3 visual gate and permits issue #206 closeout.

**Record:** `docs/rse/wayfinder/tickets/figure3-installed-owner-approval.md` — Record the owner choice and bind any approval receipt to the exact PDF hash.

## 2. Figure 1 disposition

**Decision:** How should the data-only Figure 1 candidate handle the unmet residual-drift gate?

**Recommended:** `revise-gate` — Keep promotion blocked until the scientific gate is explicitly accepted or replaced.

**Choose:**

- `accept-limitation` — Accept the observed-peak candidate with its stated residual-drift limitation.
- `revise-gate` — Define and validate a replacement scientific gate before promotion.
- `defer` — Omit or defer Figure 1.

**Context:**

- The installed figure uses fitted arrival-time shifts and is not a data-only product.
- The proposed dispersion correction was refuted because it depends on the pulse marker.
- The surviving candidate has 8 zero-consistent, 7 nonzero, and 9 unconstrained residual-drift measurements.

**Evidence:**

- [Observed-peak candidate](figure_review/artifacts/batches/2026-07-17-fig1-observed-peak-audit/candidates/fig1-gallery.pdf) — `979e616b…`
- [Scientific validation](docs/rse/specs/validation-fig1-observed-peak-audit.md) — `d9181691…`
- [Correction refutation](figure_review/artifacts/batches/2026-07-17-fig1-observed-peak-dmcorr/provenance/marker-dependence-refutation.json) — `87a4eff2…`

**Effect:** Selects the final Figure 1 path without admitting an unsupported dispersion correction.

**Record:** `figure_review/artifacts/batches/2026-07-17-fig1-observed-peak-audit/manifest.json` — Record the scientific disposition, then use figure_review.py for exact-byte approval.

## 3. Zach time resolution

**Decision:** Which DSA-110 time resolution should govern the Zach component-count comparison?

**Recommended:** `native` — Retain 32.768 microseconds because the issue requires native resolution and the earlier failed comparison used coarse binning.

**Choose:**

- `native` — Retain 32.768 microseconds and raise the reconciled-bin cap.
- `coarse` — Permit 65.536 microseconds and amend the scientific contract.
- `stop` — Stop the component-count comparison.

**Context:**

- The per-band preparation selects native DSA-110 resolution, but the later shared-window cap doubles the time bin.
- Raising the cap to 1024 restores native resolution and increases sampler cost.

**Evidence:**

- [Readiness audit](docs/rse/verify/joint-scattering-controlled-rerun-07-zach-count-readiness-20260729/readiness-audit.json) — `c1894081…`
- [Readiness explanation](docs/rse/verify/joint-scattering-controlled-rerun-07-zach-count-readiness-20260729/README.md) — `974aac68…`

**Effect:** The choice freezes the processing contract so the 27 controlled fits can run.

**Record:** `docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md` — Record the selected resolution and update the controlled-run contract.

## 4. Scattering escalation trigger

**Decision:** May posterior-predictive residuals alone trigger a second broadening component?

**Recommended:** `calibrate` — Require a false-escalation calibration before residuals become the sole trigger.

**Choose:**

- `accept` — Accept posterior-predictive residuals as the sole trigger.
- `calibrate` — Require false-escalation calibration before accepting the trigger.

**Context:**

- The autocorrelation model-comparison trigger was retired because it had no usable operating point.
- Posterior-predictive residuals are the only remaining proposed escalation trigger.

**Evidence:**

- [Trigger calibration](docs/rse/specs/plan-a1-trigger-calibration.md) — `974ec606…`
- [Current circulation design](docs/rse/specs/plan-circulation-readiness.md) — `d2ae8ecc…`

**Effect:** The choice fixes the trigger used by later scattering model selection.

**Record:** `docs/rse/wayfinder/tickets/04a-close-residual-trigger.md` — Record the trigger decision and resolve this ticket.
