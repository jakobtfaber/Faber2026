<!-- wayfinder:map -->
# Map: Establish a manuscript-only Overleaf bridge

Tickets live in [`tickets/`](tickets/). This is a planning-only map. It does
not authorize an Overleaf push, deletion, repository cleanup, credential
change, workflow activation, or manuscript-content change.

## Destination

Every decision required to implement and operate a two-way, manuscript-only
native Git bridge between Faber2026 GitHub `main` and the existing Overleaf
project is recorded. The resulting contract preserves GitHub authority,
collaborator edits, compile fidelity, provenance, and rollback while remaining
within Overleaf's file limits.

## Notes

- Use `/wayfinder`, `/grilling`, and `/domain-modeling`; use `/research` for
  facts that require primary sources outside this repository.
- Owner decisions from charting, 2026-07-20 through 2026-07-21:
  - preserve the existing Overleaf project; its history and comments need not
    constrain the bridge;
  - retire GitHub Sync for this project and use its native Overleaf Git remote;
  - keep GitHub `main` authoritative and reconcile Overleaf-originated edits
    through a reviewed staging branch before returning them to `main`;
  - keep the bridge manifest and tooling in Faber2026, with no second
    authoritative manuscript repository;
  - select the projection from the `main.tex` compile dependency closure plus
    explicit exceptions, never whole research directories; and
  - snapshot and classify every Overleaf-only path before the first bridge
    operation may delete or replace anything.
- The authority contract remains
  [Choose the code and manuscript authority policy](tickets/authority-08-choose-code-manuscript-authority.md):
  freeze edits, snapshot both identities, compare paths and bytes, merge a
  focused GitHub pull request, return the merged projection to Overleaf, then
  compile and compare the PDF.
- Prior art exists at commits `37343933` and `9cd0d3ce`: an automatic native
  Git mirror was created, then disabled because GitHub Sync and the bridge
  would have been concurrent writers. Reuse evidence, not its unrestricted
  `rsync --delete` design.
- Current diagnosis at charting: tracked editable-looking files total about
  49 MiB; Overleaf documents a 7 MB editable-material limit and recommends no
  editable text file exceed 2 MB. The bridge must measure the projected tree,
  not the full repository.
- Never place an Overleaf token, session cookie, or credential-bearing URL in
  the repository, logs, tickets, or chat.

## Decisions so far

<!-- one linked gist per resolved ticket; decision detail stays in the ticket -->

## Not yet specified

- The exact explicit exceptions to the compile-derived projection; these
  depend on the live manuscript and Overleaf inventory.
- The disposition of Overleaf-only paths and the maintenance window for the
  first reconciliation; these depend on the read-only snapshot.
- The exact receipts, alerting surface, and recovery procedure for routine
  operation; these sharpen after the state machine and execution surface are
  chosen.

## Out of scope

- Creating a replacement Overleaf project or preserving the current project's
  history and comments as migration requirements.
- Continuing or repairing Overleaf GitHub Sync.
- Moving analysis code, operational documentation, review transcripts, or
  provenance evidence merely to make the full repository fit Overleaf.
- Changing manuscript prose, scientific claims, figures, tables, or the
  `pipeline/` submodule pin.
- Implementing, activating, or running the bridge; that begins only after this
  map clears and an implementation plan is approved.
