# Referee-response status matrix — Faber et al. (2026)

**Compiled:** 2026-07-09 &nbsp;·&nbsp; **Referee report:** `docs/referee_report_2026-07-07.md` &nbsp;·&nbsp; **origin/main:** `75630c4`

Every item from the referee report, its current status, and the PR / commit / file:line that resolves it. Compiled by tracing the merged PR history (#26–#44) and the current working tree against each referee point.

**Legend:** ✓ done &nbsp; △ partial (minimum ask met; remainder blocked or submission-time) &nbsp; ✗ blocked

**Summary:** of 27 referee items, **16 are fully resolved and merged**, **4 are partial** (the minimum ask is met but a numeric/archival/design piece remains), and **7 are blocked** on either (a) the pending scattering/scintillation sections the referee itself flagged as to-be-added, (b) author-only design decisions (D2–D5), or (c) submission-time actions (Zenodo DOI mint, abstract-slot fill).

> **Note on B4:** the sign convention and geometric |τ_geo| range are in the text, but the referee's core B4 ask — a *per-burst residual uncertainty* in Table `tab:sample` and a *numeric acceptance threshold* ('what residual would have failed?') — is not yet addressed. B4 is therefore **partial**, not done.

## Blocking items (B1–B5)

| | Ref | Item | Status | Evidence |
|---|---|---|---|---|
| ✓ | **B1** | Uncertainties in the dispersion budget (DM_host as posterior) | DONE | PR #40 (re-base cosmic DM on TNG IGM log-normal) + #41 (appendix/table sync) + #42 (low-z spline guard); forward model in scripts/dm_budget_uncertainty.py |
| ✓ | **B2** | Cluster (FRB 20230307A) intracluster column with uncertainty | DONE | c330d77 + budget_table.tex: beta-model p50=252, [p16,p84]=[159,383], 95% CI [96,561] |
| ✓ | **B3** | P_cc trials-factor denominator (searched-vs-matched) | DONE | PR #44: 64 DSA-110 FRBs in window; toa.tex:73 Sigma mu_j ~ 3e-7 |
| △ | **B4** | Timing residuals: errors, acceptance criterion, sign convention, geometric range | PARTIAL / BLOCKED | Sign convention + geometric range DONE (toa.tex:19-31 |tau_geo|<=4.5 ms; Residuals & systematics L94). NOT DONE: per-burst residual uncertainty column in tab:sample and a numeric acceptance threshold ('what residual would have failed?') are still absent. |
| △ | **B5** | Non-citable internal materials -> archival release | PARTIAL / BLOCKED | All internal-materials refs now point to Sec Data Availability (obs.tex:14,25; toa.tex:155; main.tex:82). Actual Zenodo DOI mint is a submission-time author action. |

## Design decisions for the incoming scattering sections (D1–D5)

| | Ref | Item | Status | Evidence |
|---|---|---|---|---|
| △ | **D1** | Galactic-vs-extragalactic alpha inconsistency | DONE (min. ask) / BLOCKED (full) | 'At minimum acknowledge in Obs-MW': DONE, observations.tex:53-62 states the deliberate asymmetry. Full resolution (fixed-alpha vs beta-posterior in screen attribution) is a % TODO in discussion.tex:29, blocked on the scattering sections. |
| ✗ | **D2** | beta=4 / inner-scale degeneracy -> closure-regime column | BLOCKED | Design decision for the pending results table; scattering campaign is board phase C (blocked on V/A/B5). |
| ✗ | **D3** | Sub-band EMG validation labeled as diagnostic, not turbulence constraint | BLOCKED | Belongs to the pending Sub-band section (results.tex TODO). |
| ✗ | **D4** | Scintillation double-use (gain marginalization vs observable) | BLOCKED | Belongs to the pending Methods/Results-scintillation sections. |
| ✗ | **D5** | Energetics comparability (fixed rest-frame band variant) | BLOCKED | Belongs to the pending Energetics section (results.tex:207 TODO). |

## Association (§ToA) — non-blocking

| | Ref | Item | Status | Evidence |
|---|---|---|---|---|
| ✓ | **A1** | 'Fewer than one in ten million' understates P_cc<1e-8 | DONE | results.tex:17 & toa.tex:134 now read 'one in a hundred million'. |
| ✓ | **A2** | DM window / f_DM=1 for position-only class | DONE | toa.tex:147-150: position-only class carries f_DM=1, stated conservative. |
| ✓ | **A3** | Monte-Carlo cross-check (0.3%) — keep | DONE | No action needed (referee endorsed). |

## Milky Way foreground (§Obs-MW) — non-blocking

| | Ref | Item | Status | Evidence |
|---|---|---|---|---|
| ✓ | **MW4** | NE2025 (Ocker 2026) published/on arXiv by submission | DONE / WATCH | bib/refs.bib:314 Ocker2026 present; publication status is a submission-time watch. |
| ✓ | **MW5** | Text-table DM_MW inconsistency (disk-only vs +halo) | DONE | PR #32 (95->97) + observations.tex:82-84 reconcile the +40 halo offset explicitly. |

## Foreground census (§Obs-FG) — non-blocking

| | Ref | Item | Status | Evidence |
|---|---|---|---|---|
| ✓ | **FG6** | Photo-z misclassification budget (~16%/object, outlier rate) | DONE | observations.tex:194-196 states the ~16% per-object tolerance + Legacy DR9 catastrophic-outlier rate. |
| ✓ | **FG7** | Aperture values stated numerically (galaxies + clusters) | DONE | PR #36 (virial criteria) + 02e4ebb (b<=R_vir census) + 765a40a (pierced-halo 102-237 kpc). |
| ✓ | **FG8** | Fallback-mass prescription (note m) | DONE | budget_table.tex:67-68: fiducial stellar mass, b/R_vir~1.3-1.8, conservative zero. |

## Minor (9–16)

| | Ref | Item | Status | Evidence |
|---|---|---|---|---|
| ✓ | **M9** | Remove draft-status/re-validation language from reader-facing text | DONE | PR #26 / 7ea0260. Remaining re-validation language is inside %-commented TODO scaffolds only. |
| ✓ | **M10** | Remove internal nicknames from tab:sample; fix methods.tex comment | DONE | 7ea0260; no nicknames remain in observations.tex sample table. |
| △ | **M11** | \software{}: add pygedm, pipeline Zenodo DOI, cite astropy | PARTIAL / BLOCKED | main.tex:97-99 has astropy + pygedm. Pipeline Zenodo DOI awaits the B5 archival mint. |
| ✓ | **M12** | Keywords: add 'Radio bursts (1339)' | DONE | main.tex:64 keywords include 'Radio bursts (1339)'. |
| ✓ | **M13** | Parked EMG appendix: no dangling \ref | DONE | main.tex:109 the \input is %-commented out; appendix not compiled, no dangling ref. |
| ✓ | **M14** | tab:budget: FRB 20230814B chronological order | DONE | budget_table.tex: 20230307A -> 20230814B -> 20230913A is correct chronological order. |
| ✗ | **M15** | Fig sightline_halo_grid caption: state panel count / omissions | BLOCKED | Tied to the sightline-halo-grid figure finalization (census figure set). |
| ✗ | **M16** | Abstract slot: cluster column carries B2 uncertainty when filled | BLOCKED | Abstract SLOT fill is a submission-time step once B2 numbers are frozen. |

## Core pending science

| | Ref | Item | Status | Evidence |
|---|---|---|---|---|
| ✗ | **SCI** | Scattering / scintillation / turbulence / energetics sections | BLOCKED (core science) | Board phases V/A/B/C/D: fit re-validation ladder, geometry-selection campaign, two-screen analysis. Not autonomously completable — new data analysis + author design. |

## What is genuinely still open, and why it is not autonomously completable

- **B4 (partial).** Adding a per-burst timing-residual uncertainty and a numeric pass/fail threshold to `tab:sample` — a small but real author/coding task, not yet done.
- **D2–D5 (design decisions).** Lock choices the per-sightline attribution ledger inherits (closure-regime column, sub-band diagnostic labeling, scintillation double-use, energetics comparability). Author judgement, not code.
- **Scattering / scintillation / turbulence / energetics sections.** Board phases V/A/B/C/D: the fit re-validation ladder, geometry-selection campaign, and two-screen analysis on joint CHIME+DSA scintillation. New data analysis on real burst products — the paper's central contribution — and cannot be written without running that campaign.
- **Submission-time actions.** B5/M11 Zenodo DOI mint, M16 abstract-slot fill from frozen B2 numbers, MW4 NE2025 publication-status watch. Each is a one-step author action at submission.

*This matrix is a tracking artifact; it makes no science claims of its own.*
