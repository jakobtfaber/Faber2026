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
