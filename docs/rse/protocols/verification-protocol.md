# Verification & rigor protocol

**Amended 2026-07-20 (owner): plain-language names.** Opaque “Tier #” / “L#”
codes are retired in new prose. Work climbs the **data chain**; manuscript
claims clear the **checks**. (Old Tier/L labels may still appear in git
history, certificate filenames, and stubs — treat them as synonyms below.)

Root cause of repeated backtracking: issues were structured by analysis topic
while trust flows along the data DAG; work opened on inputs never certified.

## Glossary (use these names)

### Data chain (must clear bottom-up)

| Name | Meaning |
|------|---------|
| **Raw Data** | True raw products only. CHIME: the twelve singlebeam voltage `.h5` files on h17 — see [`specs/notes/definition-raw-chime-data-2026-07-19.md`](../specs/notes/definition-raw-chime-data-2026-07-19.md). Intensity `.npy` / upchan products are **not** Raw Data. |
| **Input Data Products** | Dedispersed / upchannelized arrays, RFI masks, applied DM (chosen at build time). Certified with per-(burst, product) **data cards** (waterfall + timeseries + spectrum + DM strip + mask, DM authority + sign-test receipt, axis conventions, owner hash-bound approval). |
| **Measurements and Fits** | DM, TOA, τ, ACF / joint-TF fits, etc. — predeclared gates + injections; run only on certified Input Data Products. |
| **Analyses and Interpretations** | Budget overlays, τ·Δν_d, screen attributions, composites — only from certified Measurements and Fits. |
| **In-Manuscript Claims** | What the tex asserts — must pass the Calculation Check (registry parity). |

**Rule:** work on a later link may not open until the certificates it consumes
exist. One authority per physical quantity per purpose (input-authority table
in `results-registry.toml`). Conventions are executable tests. Superseding a
Raw Data / Input Data Product certificate flips consuming registry rows to
`pending`.

### Checks (chores on claims — not a substitute for the data chain)

| Name | What it is |
|------|------------|
| *(data chain first)* | Not a numbered check — do not skip Raw Data → … → In-Manuscript Claims. |
| **Equation Check** | Dual CAS (WolframScript + SymPy; MATLAB tiebreak) + `astropy.units` on budget/delay arithmetic. |
| **Calculation Check** | Every number in prose/tables ↔ results registry; blocking CI; `\draftnum{}` empty at circulation freeze. |
| **Model/Fit Check** | Re-trust contract + injections/PPC + simulation-based calibration before fits are quotable. |
| **Reference Check** | ADS / Retraction Watch / Semantic Scholar + prior-art sweep per headline claim. |
| **No-Context Review** | ≥2 independent cold reads of the PDF; triage dispositions; owner final pass. |

House style: “casey still open on **Input Data Products**” / “association
needs a **Calculation Check**” — not “blocked on L1” / “Tier 2.”

**Adopted 2026-07-18 (owner)** for the check suite; companion to
[`BOARD.md`](../control/BOARD.md) Verification & rigor lane. Tool exclusions:
no scite.ai, Elicit, or Consensus.

---

## Equation Check

Every displayed equation and every derivation step the text relies on is
checked by **two independent CAS engines**: WolframScript (hpcc; precedent
`scripts/verify/emg_alpha4_verify.wls`) and SymPy (pinned pipeline env). MATLAB
(hpcc) serves as the numerical tiebreaker where symbolic forms diverge. A
disagreement between engines is a **blocker** until resolved. All budget and
delay arithmetic additionally passes an `astropy.units` dimensional audit —
computations carried in quantities end-to-end, not floats.

**Fires:** on any PR touching an equation or the scripts implementing it.
Check scripts live under `scripts/verify/` and run in CI where inputs permit;
hpcc-only checks record their output hash in the evidence ledger.

## Calculation Check (BLOCKING CI)

Extends the existing table-parity gate to **all numeric claims in the tex**:
every number in prose maps to a pinned pipeline artifact through the
**results registry** (`docs/rse/control/results-registry.toml` — the canonical
manuscript-facing inventory, BOARD.md §0), and CI recomputes/compares at PR
time. An unmatched or drifted number **fails CI** (owner decision 2026-07-18:
blocking, not advisory). Drafting escape hatch: numbers wrapped in a
`\draftnum{}` macro are exempt but render visibly flagged; the exemption list
must be **empty at circulation freeze**.

**Fires:** every PR touching `sections/*.tex`, `*_table.tex`, or the manifest.

## Model/Fit Check

The re-trust validation contract governs (verified input lineage,
synthetic-injection recovery, rail-as-rejection, posterior-predictive check,
independently re-derived cross-check). Added on top: **simulation-based
calibration** (Talts et al. 2018, arXiv:1804.06788) for the dynesty
pipelines — rank-statistic uniformity across the prior, catching posterior
miscalibration that PPC misses. Coverage tests for reported uncertainties
(the DM-uncertainty injection campaign pattern generalizes).

**Fires:** at each fit-campaign closeout, before its products are quotable.

## Reference Check

Pre-circulation sweep, plus incremental checks at section fill:

- **ADS metadata verification** of every `refs.bib` entry.
- **Retraction check** via Retraction Watch / Crossref.
- **Semantic Scholar** cross-check for citation existence and versioning.
- **Prior-work coverage:** Undermind deep search per headline results claim;
  Perplexity for point facts. Findings in the evidence ledger.

**Fires:** section fill (incremental) + full sweep at circulation freeze +
re-sweep at submission.

## No-Context Review

Iterative multi-model referee passes: at least two independent frontier
models review the compiled PDF cold (no shared context), findings triaged
into a dispositions doc. **Convergence:** a pass yields no new valid P0/P1
findings. Human owner referee-mode read is the final pass and is not
delegable.

**Fires:** pre-circulation and pre-submission (minimum two rounds).

## Enforcement summary

CI-blocking: **Calculation Check**, existing `check-state`, figure approval
gate, science tests. Ledger-recorded manual gates: Equation Check (hpcc-side),
Model/Fit Check, Reference Check, No-Context Review. A manuscript unit on
`BOARD.md` is not **done** until its inherited checks are green — and nothing
is quotable until the **data chain** under it is certified.
