# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific and visual decisions. Silence leaves every item blocked._

## 1. Figure 3 installed-bytes approval

**Decision:** Approve the installed Figure 3 bytes (figures/sightline_halo_grid.pdf), or return needs_revision with the presentation changes required?

**Recommended:** `approve` — The analysis-only validation recomputes every census input behind the figure and passes with mutation coverage; the remaining judgment is presentation only, and the nine-panel layout follows the fail-closed rule for the three sightlines without an established host redshift.

**Choose:**

- `approve` — Approve the installed bytes and record the exact-hash decision.
- `needs-revision` — Return needs_revision, naming the presentation changes required.

**Context:**

- Nine of twelve sightlines are drawn; three are omitted because no established host redshift exists, and each omission is checked against the data rather than trusted.
- The candidate is byte-identical to the installed figures/sightline_halo_grid.pdf and to the owner-review.json review binding (SHA-256 281e4bf4…).
- Correctness is established by six recomputing checks with mutation tests; this call judges only whether the figure reads well for the paper.

**Evidence:**

- [Candidate bytes (installed Figure 3)](figure_review/artifacts/batches/2026-07-31-fig3-installed-approval/candidates/fig3-halo-grid.pdf) — `281e4bf4…`
- [Analysis-only validation receipt](docs/rse/specs/receipt-foreground-census-analysis-only-2026-07-29.md) — `c13404f8…`
- [Owner-review byte binding](docs/rse/specs/evidence/foreground-census-analysis-only-2026-07-29/owner-review.json) — `32887fda…`

**Effect:** Closes the last owner call on the Figure 3 independent-validation-gate ticket and unblocks exact-byte promotion of the installed figure.

**Record:** `figure_review/artifacts/batches/2026-07-31-fig3-installed-approval/manifest.json` — python3 scripts/figure_review.py decide 2026-07-31-fig3-installed-approval fig3-halo-grid approved|needs_revision --reviewer <owner> --note <note>

## 2. Predicted-delay trigger operating point

**Decision:** Accept the 1 per cent false-escalation envelope (windowed residual statistic threshold 4.65) as the second-screen escalation operating point, restricted to the regimes where the calibration shows power, or reject the trigger?

**Recommended:** `accept-restricted` — At the 1 per cent envelope the rule reliably detects comparable-or-larger second screens while the false-escalation rate is measured, and the calibration proves the rule has no power for tau2 <= 0.3 tau1 — so acceptance must carry that restriction explicitly rather than implying general sensitivity; a resolved scintillation bandwidth implying a much smaller near-screen tau cannot be adjudicated by this trigger.

**Choose:**

- `accept-restricted` — Accept the 1 per cent envelope, valid only for r >= 1 second screens on matching CHIME-like geometry.
- `reject` — Reject the trigger; second-screen escalation remains unavailable.
- `recalibrate` — Request a modified campaign (different grids, geometry, or statistic) before deciding.

**Context:**

- False-escalation envelopes (max over 15 null cells, 200 injections each): statistic 4.70 / 4.65 / 3.94 at 0.5 / 1 / 5 per cent.
- Detection at the 1 per cent envelope: 97.5-100 per cent for r >= 1 at S/N 30, 65 per cent for r = 3 at S/N 15, and exactly zero for r <= 0.3 at every S/N.
- The 30-injection nested-sampling anchor shows the ML surrogate is faithful (mean |delta p| = 0.0003); validity is restricted to single-component morphology and CHIME-like geometry.

**Evidence:**

- [Calibration report](simulation/experiments/predicted-delay-trigger/calibration.md) — `a3fc6eb4…`
- [Machine-readable rate table](simulation/experiments/predicted-delay-trigger/calibration.json) — `440ffb1b…`
- [Nested-sampling anchor pairs](simulation/experiments/predicted-delay-trigger/anchor.json) — `f18438bc…`

**Effect:** Sets whether and when a second scattering screen may be fitted, closing the reopened escalation-trigger element of the D4 coupling design.

**Record:** `docs/rse/wayfinder/tickets/04-close-scint-scattering-coupling-design.md` — Record the operating-point decision in this ticket and resolve it.
