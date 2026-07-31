# Decide TNG calibration authority

- Type: `wayfinder:grilling` (HITL)
- Status: open
- Assignee: manuscript owner
- Blocked by: none
- Map: [ApJ submission](../map-apj-submission.md)
- Triage: `ready-for-human`

## Owner decision card

```json
{
  "id": "tng-calibration-authority",
  "kind": "scientific",
  "title": "TNG calibration authority",
  "decision": "What evidence must govern the IllustrisTNG intergalactic dispersion calibration used by the host-dispersion calculation?",
  "recommended": {
    "choice": "published-binary",
    "reason": "Accept the immutable first-party artifact only as a fixed calibration input, while preserving explicit limits: its fit was not reproduced and no host-dispersion result is admitted without separate local and intervening receipts."
  },
  "choices": [
    {
      "id": "published-binary",
      "label": "Accept Connor repository revision c8ca7cccc22828270291b039963a316b5e35d04f and src/tng_params_new.npy SHA-256 e4e1aa68ae4367bb698df5ca1cc93d9eaaeba23f73bef2435f4aee0ef5674625 as the calibration authority. This permits a reviewed receipt to bind the fixed grid and a diagnostic rerun. It forbids claiming that the TNG fit was reproduced, that its producing environment is known, or that any host-dispersion result is admitted."
    },
    {
      "id": "original-fit",
      "label": "Require the original TNG fit inputs, producer command or code revision, and producing environment before accepting the calibration. Until those exist and reproduce the binary within an owner-defined tolerance, this forbids using the grid as an admitted calibration or rerunning it for an admissible result."
    },
    {
      "id": "replace",
      "label": "Reject this calibration and select a replacement. This forbids using the Connor binary beyond historical comparison; a replacement requires its own immutable source, fit inputs, producer, environment, scientific validation, and downstream rerun receipt."
    }
  ],
  "context": [
    "At immutable first-party revision c8ca7cccc22828270291b039963a316b5e35d04f, src/tng_params_new.npy has SHA-256 e4e1aa68ae4367bb698df5ca1cc93d9eaaeba23f73bef2435f4aee0ef5674625; all 12 redshifts match local ordering, mean and scatter columns agree within 5e-9, and the f_IGM baseline 0.797 matches.",
    "The first-party repository does not identify the original inputs, command, or producing environment for tng_params_new.npy; proc_TNG.py writes a differently named artifact. The semantic match therefore establishes transcription, not reproduction of the fit.",
    "The local host_dm_receipt.json remains fail_closed and independently requires an admitted calibration receipt, a rerun bound to producer and environment, cluster/intervening closure for FRB 20230307A, and owner admission review."
  ],
  "evidence": [
    {
      "label": "First-party Connor reproduction repository at the inspected immutable revision",
      "path": "https://github.com/liamconnor/frb_baryon_connor2024/tree/c8ca7cccc22828270291b039963a316b5e35d04f/src"
    },
    {
      "label": "Remaining-science research note",
      "path": "docs/rse/specs/research/research-remaining-science-questions-2026-07-31.md",
      "sha256": "0615403457950b538a5d641a16a229f063db9413ca3a54eab04381b72cf7c508"
    },
    {
      "label": "Current fail-closed host-dispersion receipt",
      "path": "foregrounds/results/propagation/host_dm_receipt.json",
      "sha256": "ea2791313da7599f9a286b34b42cc4d25aef0d04938f000d1aee98c38b3c2f96"
    }
  ],
  "effect": "The choice determines whether the immutable published binary may serve as a fixed calibration input, whether full fit-production provenance is mandatory, or whether the calibration must be replaced. No choice alone admits a host-dispersion result.",
  "recorder": {
    "path": "docs/rse/wayfinder/tickets/owner-decision-tng-calibration-authority.md",
    "action": "Record the owner choice, its permitted claim boundary, and any required follow-up receipts; then resolve this ticket without changing scientific trust."
  },
  "priority": 24
}
```

## Evidence boundary

**Fact.** The immutable Connor repository artifact and its local transcription
agree as stated in the card. The exact repository revision, artifact hash,
shape, column meanings, redshift ordering, value comparison, and baseline are
recorded in the cited research note.

**Non-result.** This comparison does not reproduce the IllustrisTNG fit, identify
its original simulation inputs or producing environment, validate the physical
calibration, or admit a host-dispersion result.

**Scientific falsifier.** Reject the transcription match if an independent
fetch at the named revision does not yield the stated SHA-256, shape, column
meanings, or redshift ordering; if the two local columns differ by more than
the declared `1e-8` rounding tolerance; or if the first-party code uses a
different $f_{\rm IGM}$ baseline. Under the stricter choice, reject the
calibration if an original-input reproduction differs beyond an owner-defined
materiality threshold; that threshold is not yet set.

**Admission blocker.** An owner choice is required because the published binary
has immutable source identity but lacks its original fit inputs, command, and
producing environment. Regardless of the choice, host-dispersion admission also
requires a reviewed calibration receipt, a local rerun receipt binding producer,
environment, inputs and outputs, resolution of the FRB 20230307A intervening
column, and owner review.

**Prerequisite check.** The immutable-source check is executable now because
the repository, revision, artifact path, expected hash, column meanings, local
arrays, and tolerance are identified in the cited note. No fit-reproduction
command is prescribed: its original inputs and producer are absent. No host
rerun is prescribed until the owner selects an authority standard and the
remaining admission prerequisites exist.
