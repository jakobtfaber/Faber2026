# Re-do the scintillation analysis interactively from the raw data

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: owner + agent (joint, interactive)
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner charter, 2026-07-26

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
2. Dedispersion and DM policy per burst (one recorded convention).
3. Bad-channel policy: owner-reviewed manual maps (the resolved RFI route).
4. Product generation: spectra at explicitly chosen resolutions, with the
   scalloping-comb treatment recorded.
5. Window selection, ACF estimation, and model choice — re-decided together.
6. Per-burst review of fits and diagnostics; only then any sample-wide table.

## Resolution

Open. This ticket closes when the owner ratifies the re-done campaign's
outputs as manuscript inputs.
