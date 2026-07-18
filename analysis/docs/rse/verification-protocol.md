# Verification & rigor protocol

**Adopted 2026-07-18 (owner).** Companion to [`BOARD.md`](BOARD.md)'s
Verification & rigor lane. Five tiers, keyed to claim class; every manuscript
unit inherits the tiers its claims touch. Tool exclusions per owner:
no scite.ai, Elicit, or Consensus.

## Tier 1 — Derivations & equations

Every displayed equation and every derivation step the text relies on is
checked by **two independent CAS engines**: WolframScript (hpcc; precedent
`specs/emg_alpha4_verify.wls`) and SymPy (pinned pipeline env). MATLAB (hpcc)
serves as the numerical tiebreaker where symbolic forms diverge. A
disagreement between engines is a **blocker** until resolved. All budget and
delay arithmetic additionally passes an `astropy.units` dimensional audit —
computations carried in quantities end-to-end, not floats.

**Fires:** on any PR touching an equation or the scripts implementing it.
Check scripts live under `scripts/verify/` and run in CI where inputs permit;
hpcc-only checks record their output hash in the evidence ledger.

## Tier 2 — Numbers in prose and tables (BLOCKING CI gate)

Extends the existing table-parity gate to **all numeric claims in the tex**:
every number in prose maps to a pinned pipeline artifact through the
**results registry** (`docs/rse/results-registry.toml` — the canonical
manuscript-facing inventory, BOARD.md §0), and CI recomputes/compares at PR
time. An unmatched or
drifted number **fails CI** (owner decision 2026-07-18: blocking, not
advisory). Drafting escape hatch: numbers wrapped in a `\draftnum{}` macro
are exempt but render visibly flagged; the exemption list must be **empty at
circulation freeze** — the gate enforces zero `\draftnum` occurrences on the
circulation branch.

**Fires:** every PR touching `sections/*.tex`, `*_table.tex`, or the
manifest.

## Tier 3 — Fits & posteriors

The re-trust validation contract governs (verified input lineage,
synthetic-injection recovery, rail-as-rejection, posterior-predictive check,
independently re-derived cross-check). Added on top: **simulation-based
calibration** (Talts et al. 2018, arXiv:1804.06788) for the dynesty
pipelines — rank-statistic uniformity across the prior, catching posterior
miscalibration that PPC misses. Coverage tests for reported uncertainties
(the DM-uncertainty injection campaign pattern generalizes).

**Fires:** at each fit-campaign closeout, before its products are quotable.

## Tier 4 — Literature claims & citations

Pre-circulation sweep, plus incremental checks at section fill:

- **ADS metadata verification** of every `refs.bib` entry (title/author/venue
  against ADS; the 2026-07-08 spot-check becomes a full sweep, scripted).
- **Retraction check** via the Retraction Watch database (free through
  Crossref's REST API: `/works/{doi}` update/retraction fields).
- **Semantic Scholar API** cross-check for citation existence and versioning
  (preprint vs published; flag superseded arXiv versions).
- **Prior-work coverage:** for each headline results claim, an Undermind deep
  search for missed prior art; Perplexity for quick point-fact checks.
  Findings recorded per claim in the evidence ledger.

**Fires:** section fill (incremental) + one full sweep at circulation freeze
+ re-sweep at submission.

## Tier 5 — Whole-document adversarial review

Iterative multi-model referee passes: at least two independent frontier
models review the compiled PDF cold (no shared context), findings triaged
into a dispositions doc exactly as the 2026-07-15 technical review was
(valid/invalid/deferred, with per-item evidence). **Convergence criterion:**
a pass yields no new valid P0/P1 findings. Human owner referee-mode read is
the final pass and is not delegable.

**Fires:** pre-circulation and pre-submission (minimum two rounds).

## Enforcement summary

CI-blocking: tier 2 (prose+table parity), existing `check-state`, figure
approval gate, science tests. Ledger-recorded manual gates: tiers 1
(hpcc-side), 3, 4, 5. A manuscript unit on `BOARD.md` is not **done** until
its inherited tiers are green.
