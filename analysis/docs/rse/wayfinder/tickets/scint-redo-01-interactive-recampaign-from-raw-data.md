# Re-do the scintillation analysis interactively from the raw data

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: owner + agent (joint, interactive)
- Blocked by: repository integration and worktree cleanup
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner charter, 2026-07-26

## Owner decision card

```json
{
  "id": "resume-scintillation-redo",
  "kind": "scientific",
  "title": "Resume scintillation re-do",
  "decision": "Should the interactive raw-data scintillation campaign resume?",
  "recommended": {
    "choice": "paused",
    "reason": "Keep it paused until repository integration and worktree cleanup are complete."
  },
  "choices": [
    {
      "id": "resume",
      "label": "Resume with dispersion-measure reference and uncertainty decisions."
    },
    {
      "id": "paused",
      "label": "Keep the campaign paused."
    }
  ],
  "context": [
    "The 24-file raw-input set is frozen and accepted.",
    "All previous scintillation results remain first-pass rather than final manuscript measurements.",
    "The owner directed execution to wait for a fully reconciled workspace."
  ],
  "evidence": [
    {
      "label": "Raw-input freeze",
      "path": "docs/rse/specs/scint-redo-step1-raw-input-freeze-2026-07-26.md",
      "sha256": "1ee642130eaf626ef8cb321e6753d04455260aa6813019c9a366f07454c4b82f"
    }
  ],
  "effect": "The choice either starts the next interactive checkpoint or preserves the current pause.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/scint-redo-01-interactive-recampaign-from-raw-data.md",
    "action": "Record the choice and clear the blocker only after workspace reconciliation."
  },
  "priority": 50
}
```

## Charter

Owner direction (2026-07-26 session): treat the entire existing scintillation
campaign — the window-tuning work, the two-component (2L) ACF model runs, and
the `window_campaign_2L` results table — as a **first pass, not final**. The
manuscript scintillation numbers will come from a fresh campaign, rebuilt
step by step from the raw data, executed **interactively with the owner at
every step** inside a cleaner organizational framework.

Consequences:

- The 2L table (local first-pass evidence at
  `~/Data/Faber2026/scratch-outputs-20260726/window_campaign_2L/`) is not
  ratified and will not be ratified in its current form. It is preserved as
  first-pass evidence and as a comparison reference for the re-do.
- The prior ratification chain —
  [ticket 02](02-ratify-chime-scintillation-method.md) and
  [ticket 17](17-remediate-scintillation-inputs-and-rerun.md) — is
  **superseded by this charter**: their defect findings (RFI excision, DM
  consistency, dedispersion of upchan products) become checklist inputs to
  the re-do rather than gates on the old campaign.
- Injection-validated machinery from the first pass (the matched-window
  estimator, the two-component ACF model, physicality gates; FLITS PR #192)
  remains available code, but every methodological choice is re-decided with
  the owner during the re-do, not inherited silently.
- No step of the re-do runs unattended: the owner reviews inputs and
  diagnostics at each stage before the next stage begins.

## Working outline (each step is an owner checkpoint)

1. Raw-data inventory and provenance: enumerate the CHIME singlebeam and
   DSA-110 filterbank raw inputs on the h17 authority, with checksums.
   **Complete 2026-07-26** — owner accepted the 24-file frozen set
   (`../../specs/scint-redo-step1-raw-input-freeze-2026-07-26.md`).
2. Dedispersion-measure determination, re-done from scratch (owner
   direction 2026-07-26): the existing DM adjudication —
   `dispersion/results/joint-phase/manuscript_dm_catalog.csv` (adopted_dm, chime_primary)
   and everything downstream of it — is reclassified **first-pass, not
   final**, same standing as the first-pass scintillation campaign. The
   re-do re-derives per-burst DMs from the frozen raw inputs interactively
   (method, band roles, and uncertainty convention each an owner decision;
   the marker-independence rule from the drift-estimator refutation still
   governs). The first-pass catalog remains the manuscript's operative DM
   source until the re-derived values are ratified; consumers (DM budget
   tables, waterfall renders) are re-pointed only at ratification, as a
   separately scoped step.
3. Bad-channel policy: owner-reviewed manual maps (the resolved RFI route).
4. Product generation: spectra at explicitly chosen resolutions, with the
   scalloping-comb treatment recorded.
5. Window selection, ACF estimation, and model choice — re-decided together.
6. Per-burst review of fits and diagnostics; only then any sample-wide table.


## Step-2 decisions recorded so far

- **Estimator principle (owner, 2026-07-26): structure-maximizing** —
  the DM re-derivation uses structure-maximizing estimation (coherent
  power / phase sharpness), consistent with the marker-independence rule.
  S/N-maximizing and marker/template alignment are rejected as the primary
  principle.
- **Lane paused (owner, 2026-07-26):** execution starts only after the
  clean-slate closure of remaining worktrees and integrations, so the re-do
  begins from a fully reconciled workspace. Remaining sub-decisions when it
  resumes: DM reference data and band roles; uncertainty convention; then
  the one-burst pilot.

## Resolution

Open. This ticket closes when the owner ratifies the re-done campaign's
outputs as manuscript inputs.
