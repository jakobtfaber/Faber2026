# Figure review, scientific revalidation, and controlled replacement

**Established:** 2026-07-14  
**Last reconciled:** 2026-07-14  
**Repository:** `jakobtfaber/Faber2026`  
**Status:** approval gate active; replacement science and owner review pending

This document records the durable review contract for disputed manuscript
figures. It is not an approval record and it does not make any candidate ready
for promotion.

The command-level operating guide lives in
[`figure_review/README.md`](../../../figure_review/README.md). The slot registry,
candidate decisions, approval receipts, and exact promoted hashes remain the
machine-readable authority.

## Authoritative anchors

At the last reconciliation:

- Faber2026 `main` was `fbea8460b364c62a1b4411684f9105920617224e`,
  including the merged CHIME inventory in PR #41.
- The `pipeline/` gitlink was
  `91a5120ed702d04530b9c3aae32d53a3861e87bd`, the FLITS PR #174 merge.
- PR #35, merged as `ee14f329c0093fa2aeca600aa7d9b045a3984787`,
  installed the fail-closed figure approval gate.
- PR #36 was closed without merge. Its rejected review packet is preserved by
  the annotated tag `archive/rejected-figure-candidates-20260714`, which peels
  to `ba63448d8ed5f3561f2cc52ed9484ab7a1bd85bc`.

Commit hashes above are provenance anchors, not permanently current branch
tips. Before doing new figure work, verify `origin/main`, the recorded
`pipeline/` gitlink, and the candidate batch hashes live.

## Current scientific boundary

The consolidated CHIME inventory reports **zero qualified CHIME
scintillation-bandwidth measurements**. It also reports no qualified Oran CHIME
detection. See
[`report-chime-scintillation-inventory-2026-07-14.md`](../notes/report-chime-scintillation-inventory-2026-07-14.md)
for the evidence table and failure diagnostics.

Oran's DSA qualification is a separate instrument-specific result. It must not
be used to imply a CHIME detection, and its numerical qualification does not
constitute owner approval of a manuscript visualization.

The rejected July figure packet remains comparison evidence only:

- all 39 candidates are `needs_revision`;
- no candidate in the packet has an approval receipt;
- passing tests, reproducible generation, a clean PR, or agent visual review
  does not change those decisions;
- the packet must never be merged or relabeled as approved.

Its immutable batch-scoped provenance is:

| Evidence | Revision or SHA-256 |
|---|---|
| rejected manuscript source | `fcc67fba6ce28830ab65677b6ccba91c77c0426a` |
| rejected packet pipeline | `67bdd01418f5c4181902b499992746b965c83367` |
| adopted-DM catalog | `86f631aaedefc6a37571360b718589e864d80c05c7864ac1e4c21661367a11c8` |
| joint render manifest | `0ab236d30ec0c3db450516a86f2147aaa803c49d844e00da9041e6ea5b7e7d19` |
| joint-fit roster | `101fa5389692beadd9cf5ce06f0593dea0c43889a0ae0784eadbd7008ad20e40` |
| joint-fit adjudication | `7ed91f3eab8f09f9f414254b138ae2baceecb7d92c0f89437760a366eb97877d` |
| scintillation component catalog | `cb1686c76250e97d881fa4b9dcad8ace012004e5abdbc31abd444697ea74c16f` |
| scintillation fit catalog | `15ac6736485b5baaa787c605a62bc2372fabf450caf0b8f3d9ef4febdf915346` |
| Oran DSA qualification JSON | `e0c455e1c73e1a9bd24bbc833029cd5506d1d710fe18585251094b48d11e89f9` |

These values identify the rejected batch; they do not endorse its science or
presentation.

## Three independent gates

Every promoted figure must pass all three gates in order:

1. **Reproducibility:** the bytes can be regenerated from pinned inputs and the
   exact pipeline revision.
2. **Scientific validity:** the data selection, DM treatment, fit, components,
   residuals, uncertainties, flags, and interpretation are accepted.
3. **Owner approval:** the exact candidate bytes and presentation are approved
   under a stable candidate ID.

Passing an earlier gate is not evidence for a later one. In particular, a
matching catalog hash proves identity of an input, not scientific validity, and
green CI proves neither scientific validity nor author approval.

## Protected inventory

The protected review surface contains 39 candidates:

- `fig1-gallery`;
- `fig5-association`;
- `fig6-scint-summary`;
- `oran-qualified-scintillation`;
- 12 `dsa-acf-{nick}` candidates;
- 11 `joint-{nick}` candidates;
- 12 `triptych-{nick}` candidates.

The `joint-*` family is the DM-locked joint-model audit family. The
`triptych-*` family is the data/model/residual presentation family. Shared
upstream artifacts do not make these interchangeable manuscript products.

Use stable candidate IDs in decisions, commits, and receipts. Figure numbers
are not stable review identifiers.

## Required revalidation

### DM-dependent figures

For Figure 1, Figure 5, joint fits, and triptychs, verify for every burst:

- adopted DM, uncertainty, and adoption rule;
- CHIME and DSA measurements without conflating their qualification states;
- the DM encoded in each input product;
- any physical re-dedispersion offset;
- the DM coordinate used by the generator and fit;
- time and frequency windows after re-dedispersion;
- agreement among catalogs, fit artifacts, labels, captions, and plotted data.

Figure 5 requires end-to-end recalculation of every DM-dependent difference,
uncertainty, and category annotation. Editing displayed values alone is not
sufficient.

### Joint-fit candidates

For each retained `joint-*` candidate:

- pin the CHIME and DSA inputs and hashes;
- verify the adopted-DM lock and both input-product DMs;
- inspect configuration, priors, bounds, initialization, convergence, and
  component count;
- inspect residuals separately by band;
- distinguish a physically accepted scattering result from a morphology-only
  audit product;
- reconcile the panel, roster, adjudication, caption, and proposed claim.

If correctness cannot be demonstrated, the candidate remains
`needs_revision`, regardless of presentation quality.

### Scintillation candidates

For each scintillation candidate, verify:

- sub-band edges and center frequencies;
- lag convention, ACF values, uncertainty construction, masks, and zero-lag or
  first-lag exclusions;
- all fitted components, flags, and narrow-track membership;
- whether each displayed result is diagnostic, qualified, excluded, or an
  upper limit;
- width and interval conventions;
- any scattering or PBF overlay and its provenance.

CHIME candidates must satisfy the qualification contract recorded in the
merged CHIME inventory before any bandwidth claim is proposed. A diagnostic
scale or successful injection cell is not a real-data measurement.

## Controlled replacement workflow

### 1. Revalidate before rendering

Resolve the scientific inputs and intended product family first. Do not render
multiple competing families and treat the most attractive result as the design
decision.

### 2. Create an isolated candidate batch

Render outside protected manuscript targets, then create a batch:

```bash
python3 scripts/figure_review.py new-batch <batch-id> \
  --title "Corrected figure candidates" \
  --candidate-root /absolute/path/to/isolated/render-output \
  --pipeline-revision "<exact-FLITS-commit>" \
  --pipeline-repo /absolute/path/to/verified/FLITS-checkout
```

A candidate PR may carry the immutable batch plus necessary generator or
provenance changes. It must not promote candidate bytes or change protected TeX
inclusions.

### 3. Record explicit decisions

Record one owner decision per stable candidate ID:

```bash
python3 scripts/figure_review.py decide <batch-id> <candidate-id> approved \
  --reviewer "Jakob Faber" \
  --note "Scientific inputs, fit, labels, and presentation accepted"
```

Use `needs_revision` with a concrete note when a candidate is rejected.
Silence, automated checks, and PR state never imply approval.

### 4. Promote exact approved bytes separately

Promotion belongs in a focused PR:

```bash
python3 scripts/figure_review.py promote <batch-id> <candidate-id>
python3 scripts/figure_review.py verify
make test-science
```

The receipt must bind the reviewer decision, candidate hash, promoted hash,
input catalog hash, manuscript revision, and pipeline revision. Editing the
promoted bytes afterward invalidates the receipt.

### 5. Compile and inspect the manuscript

After promotion, force a clean manuscript build and inspect the rendered PDF.
Confirm the actual TeX inclusion chain, float placement, captions, labels,
legibility, page breaks, and consistency with the accepted claim.

## Recommended order

1. Decide the intended Figure 1 product and layout.
2. Freeze and revalidate the adopted-DM catalog.
3. Recompute and review Figure 5's DM-dependent content.
4. Audit joint fits one burst at a time.
5. Approve a joint/triptych visual contract without conflating the families.
6. Revalidate scintillation components and qualification status.
7. Approve a representative visual contract, then render the family
   consistently.
8. Review outliers and exclusions individually.
9. Promote only approved candidates in small, family-scoped PRs.

## Closure conditions

The replacement effort is complete only when all applicable candidates have:

- scientifically accepted inputs and interpretation;
- isolated, hash-pinned candidate bytes;
- an explicit owner decision;
- a valid approval receipt for the exact promoted bytes;
- passing `figure_review.py verify` and scientific tests;
- a clean manuscript build whose rendered pages were inspected;
- a focused merged PR with no incidental `pipeline/` gitlink change.

Until then, placeholders and omitted protected figure families are the correct
fail-closed state. Do not restore rejected `\includegraphics` lines merely to
make the manuscript look complete.

## Archived rejected evidence

The July rejected packet is retained under:

```text
archive/rejected-figure-candidates-20260714
  figure_review/batches/2026-07-14-replacement-review/
```

The archive is immutable comparison history. New candidates require a new
batch ID and new hashes; never overwrite the archived packet or change its
decisions to `approved`.
