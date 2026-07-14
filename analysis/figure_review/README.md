# Figure candidate review and approval

Scientific figures use a two-PR, fail-closed workflow. Automated tests and an
agent's visual inspection can establish that a figure is reproducible and
legible; they do **not** constitute manuscript-owner approval.

## 1. Candidate PR

Generate figures outside their manuscript targets, then stage an immutable
review batch:

```bash
python scripts/figure_review.py new-batch 2026-07-14-example \
  --title "Example candidate batch" \
  --candidate-root /path/to/isolated/render-output \
  --pipeline-revision "<exact FLITS commit>"
```

The candidate root mirrors manuscript-relative output paths (for example,
`/path/to/isolated/render-output/figures/codetection_data_grid.pdf`) so staging
never writes into live manuscript targets. The command copies those PDFs into
`figure_review/batches/<batch>/`, records
their SHA-256 values and the adopted-DM catalog SHA-256, renders first-page PNG
previews, and builds `index.html`. A candidate PR contains only this review
packet and any generator/provenance changes. It does not edit TeX inclusions or
promote files into `figures/`.

Review by stable candidate ID. Record each owner decision separately:

```bash
python scripts/figure_review.py decide <batch> joint-oran approved \
  --reviewer "Jakob Faber" --note "DM, residuals, labels, and fit accepted"

python scripts/figure_review.py decide <batch> dsa-acf-zach needs_revision \
  --reviewer "Jakob Faber" --note "Broader component is assigned incorrectly"
```

Silence, automated checks, PR creation, and agent review never imply approval.

## 2. Promotion PR

Only an owner-approved candidate can be promoted:

```bash
python scripts/figure_review.py promote <batch> joint-oran
```

Promotion copies the exact approved bytes into the configured manuscript path
and writes a receipt under `figure_review/approval_receipts/`. The receipt pins
the reviewer decision, candidate hash, promoted hash, DM-catalog hash, source
revision, and pipeline revision.

`python scripts/figure_review.py verify` scans all TeX sections. It fails when a
protected figure path is included without an approved receipt or when promoted
bytes differ from the approved candidate. `make test-science` runs this gate in
CI.

## Review checklist

Every approval should explicitly cover:

- correct event and telescope inputs;
- adopted DM, input-product DM, and re-dedispersion offset;
- axes, units, masks, and displayed resolution;
- fit configuration, component count, and residual structure;
- diagnostic versus physically accepted status;
- caption claims and any PBF/scintillation overlays;
- whether the figure layout is the intended manuscript design.

If any item cannot be established from the packet, mark the candidate
`needs_revision`. Corrected figures belong in a new batch with new hashes.
