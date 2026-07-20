# Owner data-review findings — scintillation input products (2026-07-18)

---
**Reviewer:** Jakob Faber (owner), from the 36-panel input-waterfall review
(`docs/rse/decks/scintillation/waterfall-review-2026-07-18/`) — full-res CHIME, upchannelized
CHIME, and DSA dynamic spectra for all twelve co-detections, rendered directly
from the byte-level products (md5s on each panel).
**Status:** ADJUDICATED — three defect classes; scintillation-campaign
ratification (wayfinder ticket 02) BLOCKED pending remediation.
---

## Defect 1 — RFI not excised

- **CHIME upchannelized (nearly all twelve):** RFI is present in the dynamic
  spectra, not flagged/excised to standard. RFI contaminates the per-channel
  de-scalloping statistics and the frequency ACF directly.
- **DSA (several bursts):** a central channel carries unremoved RFI.

## Defect 2 — over-dedispersion in the upchannelized CHIME products

Owner visual verdict: the burst is clearly over-dedispersed (residual sweep
drags the burst in time) in at least: **chromatica, zach, phineas, wilhelm,
isha, johndoeII, mahi, oran, whitney**. Consequence for the scintillation
method specifically: the ACF window bounds isolate the burst in time — a
dragged sweep puts part of the burst outside the window, so the windowed
refit computes ACFs on a truncated, chromatically-biased slice.

## Defect 3 — DM inconsistency between CHIME products (quantified)

The upchan builder (`build_npz_aligned_generic_20260706.py` TARGETS, from
h17 `upchannelize_chime.py`) applied per-burst DMs that do not match the
full-resolution product DMs (filename-encoded, `DSA_bursts/*_chime_I_*`):

| burst | upchan DM | full-res DM | ΔDM (pc cm⁻³) | residual sweep 400–800 MHz |
|---|---|---|---|---|
| isha | 411.568 | 411.4359 | **+0.132** | ≈ 2.6 ms |
| oran | 396.882 | 397.0153 | **−0.133** | ≈ 2.6 ms |
| wilhelm | 602.346 | 602.3809 | −0.035 | ≈ 0.68 ms |
| chromatica | 272.664 | 272.6382 | +0.026 | ≈ 0.50 ms |
| phineas | 610.274 | 610.2894 | −0.015 | ≈ 0.30 ms |
| whitney | 462.174 | 462.1891 | −0.015 | ≈ 0.29 ms |
| johndoeII | 696.506 | 696.5184 | −0.012 | ≈ 0.24 ms |
| freya | 912.400 | 912.4067 | −0.007 | ≈ 0.13 ms |
| zach | 262.368 | 262.3621 | +0.006 | ≈ 0.11 ms |
| mahi | 960.128 | 960.1316 | −0.004 | ≈ 0.07 ms |
| hamilton | 518.799 | 518.8007 | −0.002 | ≈ 0.03 ms |
| casey | 491.207 | 491.2085 | −0.002 | ≈ 0.03 ms |

(Sweep scale: 19.45 ms per pc cm⁻³ across 400–800 MHz, K_DM = 1/2.41e-4.)
Residuals of 0.3–2.6 ms are comparable to or larger than several burst widths
(e.g. chromatica FWHM 0.82 ms, zach 0.96 ms) — consistent with the visual
over-dedispersion verdict. Sign varies by burst, so this is not one global
convention offset. Neither product set has yet been reconciled against the
adopted manuscript DM catalog (`manuscript_dm_catalog.csv`) — that
reconciliation is part of remediation, and the marker-dependence rule
(scattering lags markers; a real DM error is marker-independent) governs any
re-measurement.

## Consequences

1. **wf-02 ratification BLOCKED.** The R5/R6 campaign consumed these inputs;
   contract term (i) — verified input lineage — FAILS. The chromatica/zach
   detections, all subband γ values, and the two-band scalings are suspect
   until re-derived on remediated inputs. The method design itself is not
   refuted; it was fed defective data.
2. **PR #140 must not merge** (pin bump + figures built on these inputs).
3. The stale-closure and α-error-convention issues found earlier are now
   subsumed by the larger remediation.

## Remediation (execution — scint lane)

1. RFI excision pass on all CHIME upchannelized products (flag + excise to
   standard; document mask per burst) and the DSA central-channel RFI.
2. One authoritative DM per burst across all products: reconcile upchan
   TARGETS, full-res products, and the adopted manuscript DM catalog;
   rebuild the aligned upchan npz set at the adopted DMs.
3. Byte-provenance: regenerate PROVENANCE.md + checksums for the remediated
   set; registry inputs updated.
4. Re-run the windowed-refit campaign end-to-end on remediated inputs
   (same predeclared gates), rerun closure/finalization, regenerate
   validation.json and figures, then return to ratification with a fresh
   36-panel + ACF review.
