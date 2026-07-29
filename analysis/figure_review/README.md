# Figure review

The directory follows the review workflow:

- `definitions/`: stable slots, reviewer metadata, and receipt templates;
- `artifacts/`: candidate batches, previews, provenance, audits, and staging renders;
- `decisions/`: owner decisions, batch dispositions, and approval receipts.

Approved manuscript figures are promoted to the parent repository's `figures/`
directory. They are final outputs, not review artifacts.

Scientific figures use a fail-closed reproduction and approval workflow. A
figure is withheld from the manuscript owner until an agent has traced and
verified its exact inputs, processing, fit configuration, code revisions,
command, environment, and regenerated output. Automated checks and an agent's
visual inspection still do **not** constitute manuscript-owner approval.

## 0. Reproduce before presenting

Create the candidate batch as below, but do not send its preview to the owner.
Re-run the producer from a clean checkout. Record the run using
[`reproduction-receipt.example.json`](definitions/reproduction-receipt.example.json):

```bash
python scripts/figure_review.py certify-reproduction <batch> <candidate> \
  --receipt /path/to/completed-reproduction-receipt.json
```

The receipt must bind the candidate to:

- complete SHA-256 input inventory;
- the exact revisions recorded in the manifest as `source_revision` and
  `pipeline_revision` (see [Recorded revisions](#recorded-revisions));
- argument-vector command and working directory;
- environment identity, such as a lockfile or container digest;
- a clean-worktree run; and
- regenerated output SHA-256 matching the candidate bytes.

Until this passes, the review page hides the image, owner decisions are
rejected, and promotion is impossible. Find the single next eligible figure
with:

```bash
python scripts/figure_review.py next
```

Audit every current manuscript figure across the regeneration catalog, review
batches, approval receipts, promoted bytes, and results-registry trust state:

```bash
python scripts/figure_review.py status
```

## 1. Candidate batch

Generate figures outside their manuscript targets, then stage an immutable
review batch:

```bash
python scripts/figure_review.py new-batch 2026-07-14-example \
  --title "Example candidate batch" \
  --candidate-root /path/to/isolated/render-output \
  --pipeline-revision "<exact analysis commit that produced the candidate>"
```

The candidate root mirrors manuscript-relative output paths (for example,
`/path/to/isolated/render-output/figures/codetection_data_grid.pdf`) so staging
never writes into live manuscript targets. The command copies those PDFs into
`figure_review/artifacts/batches/<batch>/`, records
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

## 2. Owner decision and promotion

Only an owner-approved candidate can be promoted:

```bash
python scripts/figure_review.py promote <batch> joint-oran
```

Promotion copies the exact approved bytes into the configured manuscript path
and writes a receipt under `figure_review/decisions/approval_receipts/`. The receipt pins
the reviewer decision, candidate hash, promoted hash, DM-catalog hash, source
revision, and pipeline revision.

## Recorded revisions

Every manifest and receipt carries two revision fields. Both have shifted
meaning over the project's history, so read them against the batch's date rather
than assuming a single repository:

- `source_revision` — the revision of the repository that held the generator
  when the batch was staged. Pre-migration batches (through 2026-07-17) record a
  parent `Faber2026` commit; current batches record a `Faber2026-analysis`
  commit.
- `pipeline_revision` — historically the `dsa110-FLITS` commit supplying the
  fitting library. That project is retired, so the values stored in existing
  manifests (for example `17d9d266`, `f3c8d22a`, `99e60c3a`) resolve in no
  current repository and cannot be checked out. For a new batch, record the
  `Faber2026-analysis` commit that produced the candidate.

`figure_review.py new-batch` retains the historical field name
`--pipeline-revision` because it is part of every existing hash-pinned receipt.
For new batches, its value is the exact `Faber2026-analysis` producer commit.
The field name does not imply a runtime dependency.

## Canonical paths

Anything reading the review tree must use these locations. The pre-2026-07-29
flat layout (`figure_review/batches/`, `figure_review/approval_receipts/`,
`figure_review/slots.json`) is retired; a reference to it is a defect, not an
alias.

| Content | Canonical path |
| --- | --- |
| Stable slot definitions | `figure_review/definitions/slots.json` |
| Reviewer morphology metadata | `figure_review/definitions/owner-morphology.yaml` |
| Reproduction-receipt template | `figure_review/definitions/reproduction-receipt.example.json` |
| Candidate batches and manifests | `figure_review/artifacts/batches/<batch>/` |
| Standalone audits | `figure_review/artifacts/audits/<audit>/` |
| Approval and promotion receipts | `figure_review/decisions/approval_receipts/<candidate>.json` |
| Batch dispositions | `figure_review/decisions/batch_dispositions.json` |
| Standalone owner decisions | `figure_review/decisions/owner_decisions/<decision>.json` |

## Owner decision cards

A batch manifest may attach an `owner_decision_card` to any candidate. A pending
candidate without an approved receipt **must** carry one: `scripts/owner_queue.py`
raises `QueueValidationError` otherwise, so the owner queue fails closed rather
than silently dropping the decision.

Required fields:

- `id` — stable slug matching `[a-z0-9][a-z0-9-]*`, unique across every queue
  source (tickets included);
- `kind` — either `scientific` or `visual`;
- `title` — 1 to 8 words;
- `decision` — the question the owner is being asked, non-empty;
- `recommended` — exactly `{"choice", "reason"}`, both text, reason non-empty;
- `choices` — list of `{"id", "label"}` entries, both text;
- `context` — list of plain-text facts the decision rests on;
- `evidence` — list of entries with text `label` and `path`, no key outside
  `{label, path, sha256}`;
- `effect` — what the decision settles, non-empty;
- `recorder` — exactly `{"path", "action"}`, both text, action non-empty,
  naming where the decision gets recorded at its source. The path must exist
  inside this repository.

Optional fields — there is exactly one, plus one conditional:

- `priority` — integer, default `100`; lower sorts earlier in the queue. Must be
  a real integer; a quoted number is rejected.
- `evidence[].sha256` — omissible **only** when `path` is an `http://` or
  `https://` URL, which is skipped entirely. For any repository-local path the
  hash is mandatory: the queue rejects the card if it is absent, if the file is
  missing, if the path escapes the repository, or if the recorded hash does not
  match the file's current bytes. Treat it as required in practice.

A card states the decision and its evidence. It does not record the outcome —
that goes to the authoritative source named in `recorder`, via
`figure_review.py decide` for exact-byte approval.

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

The review queue is derived from immutable batch manifests. Do not maintain a
second status spreadsheet or duplicate figure inventory.
