# Visual scientific review

Goal: reserve manuscript-owner attention for scientific judgment. Agents do
the provenance trace and exact regeneration first.

Formatting is defined by
[`../ops/manuscript-figure-style.md`](../ops/manuscript-figure-style.md).

## Hard gate

Do not show a figure to the owner until all are recorded and verified:

1. exact input paths and SHA-256 values;
2. processing and fit configuration;
3. analysis and pipeline revisions;
4. argument-vector command and working directory;
5. environment or container identity;
6. clean-worktree regeneration; and
7. regenerated output SHA-256 matching the immutable candidate.

Failure at any step leaves the figure in `preparation`. The review page hides
the image. Owner decision and manuscript promotion are disabled.

## One authoritative flow

- `../results-registry.toml`: manuscript result and trust authority.
- parent `figures/catalog.yaml`: regeneration graph.
- `figure_review/definitions/slots.json`: stable review definitions.
- batch `manifest.json`: immutable candidate, evidence, reproduction, and
  owner decision.
- `approval_receipts/`: exact promoted-byte approvals.

Generated status is a join of those authorities. Do not maintain a parallel
spreadsheet.

```bash
make figure-review-status  # every manuscript figure
make figure-review-next    # one eligible owner-review item
```

## Responsibilities

Agent: trace, reproduce, inspect diagnostics, recommend a disposition, and
withhold incomplete work.

Owner: judge the physical and statistical credibility of the review-ready
figure. Short responses are sufficient: accept, flag a panel, reject a value,
or request a competing model.

Any flag immediately blocks downstream values, claims, captions, and derived
figures until resolved.
