# Faber2026 readiness board (markdown)

> Static markdown conversion of the retired HTML board (`readiness.html`, archived alongside).
> Converted 2026-07-27 with `pandoc -f html -t gfm-raw_html`; the GitHub Pages site is down.
> Task-state data source remains `owner-view.json`; the journal remains `docs/rse/journal.jsonl`.


# Faber2026 — circulation readiness

CHIME/FRB × DSA-110 co-detection paper · 12 bursts · trust reset 07-06,
climbing back via the §V ladder · branch state lives in the journal

**Owner view**updated 2026-07-15T12:35-0700 · data:
docs/rse/control/board/owner-view.json (agents keep this current)

#### Needs you

#### In flight

- **P4 resolved: envelope not separable — ratify CHIME closure wording**
  ownerP4 hit its predeclared E2 fail branch: models stiff enough to
  keep a scintle leave 5–72 sigma of un-attributable envelope-mismatch
  structure, the one control-clean model (GP 0.5 MHz) absorbs the
  injected scintles; all three families dropped, the real residual was
  never scanned (0/3 looks). The intrinsic envelope is not removable
  in-house, so the CHIME constraint stays envelope-confusion-limited
  with no post-subtraction upper limit either. OWNER: ratify the
  manuscript closure wording with P3' + P4 in hand (FLITS PR \#182;
  record §Outcome)

#### Up next — your pick

- **A5: N-component profile-fit statistic**calibrated N-vs-1 profile
  model comparison (owner charter at A1 closure); design after control
  system lands
- **Figure 1 data-only gallery**per the 2026-07-14 decision route;
  independent of the CHIME question

**Sample & association**V6validatedPR 17 merged — done

**Budget & census**V4·V5validatedDM adopted; scattering after D

**Scattering**V1·A·CA1 trigger closed (no operating point)A5 chartered ·
V1/V2 startable

**Scintillation**BP4 DOCUMENTED-FAIL (envelope not separable): CHIME
constraint is envelope-confusion-limited, foreground not removable
in-houseowner ratifies manuscript closure wording (P3' + P4); separate
decision: sample-wide P3'/P4 across the other eleven co-detections

**Energies**V3contract authored; rail + selection-rule resolved;
estimator re-based data-driven (owner 2026-07-15)CHIME-side data-driven
fluence run + independent verifier + regenerated-table review (runbook:
validation-v3-energetics-2026-07-15.md §6), then owner V3 sign-off

**Synthesis**D·E·F1blockedfrozen until CHIME route resolves or owner
closes campaign

**Mechanics**P0·F·Gactivepin 479d2c8 current (P4 landed) · control
system LANDED (PR 59) · views generated

## The paper, strand by strand — inputs → method → measured → validated → written

**Sample & association** §2 observations · toa — which 12 bursts, and
why we believe the pairings V6 ✓

**inputs**DM/TOA provenance per telescope

**method**shared DSA-DM convention

**measured**residuals · P_cc

**validated**V6 cleared 07-07

**written**verified DM table + methods + Figure 1 in final validation

**DM budget & foreground census** §3 budget — where the dispersion comes
from V4 ✓ · V5 ✓ · D2

**inputs**DR9/DESI/NED/PS1 re-audit

**method**models verified vs refs

**measured**35 systems ✓ · D2 comparison ← scattering

**validated**V4+V5 cleared 07-07

**written**adopted DM propagated; scattering comparison after D

**Scattering** co-model methods · results · tab:beta — τ, β, geometry
per sightline V1 · V2 · A1–A4 · C1–C3 · F2

**inputs**V2 cube forensics startable

**method**A1 with you · V1 contract ← scint prior odds

**measured**C1 re-fit ×12

**validated**under V1 contract

**written**tab:beta rework F2

**Scintillation** two-screen appendix — Δν_d both bands; sets scattering
geometry · hard circulation gate B1–B6

**inputs**CHIME regen startable; freya ACF correction stuck →
upper-limit fallback

**method**recipe-parity Phase 1 landed

**measured**both bands, under V1

**validated**B5 two-screen rebuild

**written**fig:scint_screens re-made

**Energies & intrinsic** tab:burst-energies — what the bursts themselves
are V3 · E2

**inputs**rides scattering inputs

**method**γ_D pile-up + selection rule to resolve

**measured**c₀,γ re-export

**validated**after P0 + V1 rails

**written**table re-admitted then

**Synthesis & interpretation** discussion · conclusions — propagation vs
intrinsic, per sightline D1 · E1 · F1

**inputs**← scattering + budget

**method**adjudicated geometries

**measured**D1 measured-vs-predicted

**validated**

**written**F1 the big rewrite

**Paper mechanics** cross-cutting — foundations, audits, authorship,
release P0 · F3–F7 · G1–G3

P0 provenance freeze — recommended next F3 consistency audit — runnable
now F6 co-author draft — runnable now F4 referee pass — partial now F5
line polish — after F3/F4 G1–G3 release — gated, last

done partial active now needs you startable waiting upstream · ← feed =
cross-strand dependency

Agent detail — recovery map, trust ladder, lanes & tasks (V·P0 … G3)

## Recovery pipeline — the dependency graph agents schedule against

![](data:image/svg+xml;base64,PHN2ZyB2aWV3Ym94PSIwIDAgMTE1MCAyNjgiIHJvbGU9ImltZyIgYXJpYS1sYWJlbD0iRGVwZW5kZW5jeSBtYXA6IGxhbmVzIFYsIEEsIEIgZmVlZCBDLCB0aGVuIEQsIEUsIEYsIEciPgogIDxkZWZzPgogICAgPG1hcmtlciBpZD0iYXJyIiB2aWV3Ym94PSIwIDAgOCA4IiByZWZ4PSI3IiByZWZ5PSI0IiBtYXJrZXJ3aWR0aD0iNyIgbWFya2VyaGVpZ2h0PSI3IiBvcmllbnQ9ImF1dG8iPgogICAgICA8cGF0aCBkPSJNMCwwIEw4LDQgTDAsOCB6IiBmaWxsPSJ2YXIoLS1ibG9ja2VkKSIgLz4KICAgIDwvbWFya2VyPgogIDwvZGVmcz4KCiAgPHBhdGggY2xhc3M9ImVkZ2UiIGQ9Ik0xNzgsNDcgIEMyMTUsNDcgMjE1LDEyMCAyNDQsMTIwIiBtYXJrZXItZW5kPSJ1cmwoI2FycikiIC8+CiAgPHBhdGggY2xhc3M9ImVkZ2UiIGQ9Ik0xNzgsMTM0IEwyNDQsMTM0IiBtYXJrZXItZW5kPSJ1cmwoI2FycikiIC8+CiAgPHBhdGggY2xhc3M9ImVkZ2UiIGQ9Ik0xNzgsMjIxIEMyMTUsMjIxIDIxNSwxNDggMjQ0LDE0OCIgbWFya2VyLWVuZD0idXJsKCNhcnIpIiAvPgogIDxwYXRoIGNsYXNzPSJlZGdlIiBkPSJNNDAyLDEzNCBMNDY4LDEzNCIgbWFya2VyLWVuZD0idXJsKCNhcnIpIiAvPgogIDxwYXRoIGNsYXNzPSJlZGdlIiBkPSJNNjE4LDEzNCBMNjc2LDEzNCIgbWFya2VyLWVuZD0idXJsKCNhcnIpIiAvPgogIDxwYXRoIGNsYXNzPSJlZGdlIiBkPSJNODE2LDEzNCBMODY2LDEzNCIgbWFya2VyLWVuZD0idXJsKCNhcnIpIiAvPgogIDxwYXRoIGNsYXNzPSJlZGdlIiBkPSJNMTAwNiwxMzQgTDEwNDAsMTM0IiBtYXJrZXItZW5kPSJ1cmwoI2FycikiIC8+CgogIDxnPjx0aXRsZT5WIOKAlCB0cnVzdCBsYWRkZXI6IDMgb2YgNyBydW5ncyBjbGVhcmVkIChWNCBjZW5zdXMsIFY1IGJ1ZGdldCwgVjYgYXNzb2NpYXRpb24pOyBQMC9QMS9QMiBzdGFydGFibGU8L3RpdGxlPgogIDxyZWN0IHg9IjgiIHk9IjEwIiB3aWR0aD0iMTcwIiBoZWlnaHQ9Ijc0IiByeD0iOSIgY2xhc3M9Im5vZGUtcmVhZHkiIHN0cm9rZS13aWR0aD0iMS41IiAvPgogIDx0ZXh0IHg9IjIyIiB5PSIzNiIgY2xhc3M9Im5pZCB0LXJlYWR5Ij5WPC90ZXh0PgogIDx0ZXh0IHg9IjQ0IiB5PSIzNCIgY2xhc3M9Im5ubSI+VHJ1c3QgbGFkZGVyPC90ZXh0PgogIDx0ZXh0IHg9IjIyIiB5PSI1MiIgY2xhc3M9Im5zdCI+My83IGNsZWFyZWQgwrcgcGljayBuZXh0IHJ1bmc8L3RleHQ+CiAgPHJlY3QgeD0iMjIiIHk9IjYwIiB3aWR0aD0iMTQyIiBoZWlnaHQ9IjYiIHJ4PSIzIiBjbGFzcz0idHJhY2siIC8+CiAgPHJlY3QgeD0iMjIiIHk9IjYwIiB3aWR0aD0iNTkiIGhlaWdodD0iNiIgcng9IjMiIGNsYXNzPSJzZWctZ29vZCIgLz4KICA8cmVjdCB4PSI4MyIgeT0iNjAiIHdpZHRoPSI1OSIgaGVpZ2h0PSI2IiByeD0iMyIgY2xhc3M9InNlZy1yZWFkeSIgLz4KICA8L2c+CgogIDxnPjx0aXRsZT5BIOKAlCBtZXRob2RvbG9neSByZXNldDogQTEgdHdvLXNjcmVlbiBkZXNpZ24gb3BlbiB3aXRoIHRoZSBvd25lcjsgQTLigJNBNCBzdGFydGFibGU8L3RpdGxlPgogIDxyZWN0IHg9IjgiIHk9Ijk3IiB3aWR0aD0iMTcwIiBoZWlnaHQ9Ijc0IiByeD0iOSIgY2xhc3M9Im5vZGUtcGVuZCIgc3Ryb2tlLXdpZHRoPSIxLjUiIC8+CiAgPHRleHQgeD0iMjIiIHk9IjEyMyIgY2xhc3M9Im5pZCB0LXBlbmQiPkE8L3RleHQ+CiAgPHRleHQgeD0iNDQiIHk9IjEyMSIgY2xhc3M9Im5ubSI+TWV0aG9kb2xvZ3k8L3RleHQ+CiAgPHRleHQgeD0iMjIiIHk9IjEzOSIgY2xhc3M9Im5zdCI+QTEgZGVzaWduIOKAlCB3aXRoIHlvdTwvdGV4dD4KICA8cmVjdCB4PSIyMiIgeT0iMTQ3IiB3aWR0aD0iMTQyIiBoZWlnaHQ9IjYiIHJ4PSIzIiBjbGFzcz0idHJhY2siIC8+CiAgPHJlY3QgeD0iMjIiIHk9IjE0NyIgd2lkdGg9IjM0IiBoZWlnaHQ9IjYiIHJ4PSIzIiBjbGFzcz0ic2VnLXBlbmQiIC8+CiAgPHJlY3QgeD0iNTgiIHk9IjE0NyIgd2lkdGg9IjEwNiIgaGVpZ2h0PSI2IiByeD0iMyIgY2xhc3M9InNlZy1yZWFkeSIgLz4KICA8L2c+CgogIDxnPjx0aXRsZT5CIOKAlCBzY2ludGlsbGF0aW9uIGNhbXBhaWduLCBib3RoIGJhbmRzOiBhY3RpdmU7IENISU1FIHJlY2lwZSBwYXJpdHkgaW4gZmxpZ2h0OyBCNC9CNSBibG9ja2VkIG9uIHByZXAgKyBWMTwvdGl0bGU+CiAgPHJlY3QgeD0iOCIgeT0iMTg0IiB3aWR0aD0iMTcwIiBoZWlnaHQ9Ijc0IiByeD0iOSIgY2xhc3M9Im5vZGUtbm93IiBzdHJva2Utd2lkdGg9IjEuNSIgLz4KICA8dGV4dCB4PSIyMiIgeT0iMjEwIiBjbGFzcz0ibmlkIHQtbm93Ij5CPC90ZXh0PgogIDx0ZXh0IHg9IjQ0IiB5PSIyMDgiIGNsYXNzPSJubm0iPlNjaW50aWxsYXRpb248L3RleHQ+CiAgPHRleHQgeD0iMjIiIHk9IjIyNiIgY2xhc3M9Im5zdCI+YWN0aXZlIMK3IENISU1FIHJlY2lwZSBwYXJpdHk8L3RleHQ+CiAgPHJlY3QgeD0iMjIiIHk9IjIzNCIgd2lkdGg9IjE0MiIgaGVpZ2h0PSI2IiByeD0iMyIgY2xhc3M9InRyYWNrIiAvPgogIDxyZWN0IHg9IjIyIiB5PSIyMzQiIHdpZHRoPSI5MyIgaGVpZ2h0PSI2IiByeD0iMyIgY2xhc3M9InNlZy1yZWFkeSIgLz4KICA8L2c+CgogIDxnPjx0aXRsZT5DIOKAlCBzY2F0dGVyaW5nIHJlLWZpdCBmcm9tIHNjcmF0Y2gsIGFsbCAxMjogYmxvY2tlZCB1bnRpbCBWMSArIEEgKyBCNTwvdGl0bGU+CiAgPHJlY3QgeD0iMjUyIiB5PSI5NyIgd2lkdGg9IjE1MCIgaGVpZ2h0PSI3NCIgcng9IjkiIGNsYXNzPSJub2RlLWJsb2NrZWQiIHN0cm9rZS13aWR0aD0iMS41IiAvPgogIDx0ZXh0IHg9IjI2NiIgeT0iMTIzIiBjbGFzcz0ibmlkIHQtYmxvY2tlZCI+QzwvdGV4dD4KICA8dGV4dCB4PSIyODgiIHk9IjEyMSIgY2xhc3M9Im5ubSI+UmUtZml0IMOXMTI8L3RleHQ+CiAgPHRleHQgeD0iMjY2IiB5PSIxMzkiIGNsYXNzPSJuc3QiPm5lZWRzIFYxICsgQSArIEI1PC90ZXh0PgogIDxyZWN0IHg9IjI2NiIgeT0iMTQ3IiB3aWR0aD0iMTIyIiBoZWlnaHQ9IjYiIHJ4PSIzIiBjbGFzcz0idHJhY2siIC8+CiAgPC9nPgoKICA8Zz48dGl0bGU+RCDigJQgc2lnaHRsaW5lIGFuZCBmb3JlZ3JvdW5kIGNvbXBhcmlzb246IGJsb2NrZWQgb24gQyAoVjQvVjUgYWxyZWFkeSBjbGVhcmVkKTwvdGl0bGU+CiAgPHJlY3QgeD0iNDc2IiB5PSI5NyIgd2lkdGg9IjE0MiIgaGVpZ2h0PSI3NCIgcng9IjkiIGNsYXNzPSJub2RlLWJsb2NrZWQiIHN0cm9rZS13aWR0aD0iMS41IiAvPgogIDx0ZXh0IHg9IjQ5MCIgeT0iMTIzIiBjbGFzcz0ibmlkIHQtYmxvY2tlZCI+RDwvdGV4dD4KICA8dGV4dCB4PSI1MTIiIHk9IjEyMSIgY2xhc3M9Im5ubSI+U2lnaHRsaW5lczwvdGV4dD4KICA8dGV4dCB4PSI0OTAiIHk9IjEzOSIgY2xhc3M9Im5zdCI+bmVlZHMgQyDCtyBWNC9WNSDinJM8L3RleHQ+CiAgPHJlY3QgeD0iNDkwIiB5PSIxNDciIHdpZHRoPSIxMTQiIGhlaWdodD0iNiIgcng9IjMiIGNsYXNzPSJ0cmFjayIgLz4KICA8L2c+CgogIDxnPjx0aXRsZT5FIOKAlCBzeW50aGVzaXM6IGJsb2NrZWQgb24gRDwvdGl0bGU+CiAgPHJlY3QgeD0iNjc2IiB5PSI5NyIgd2lkdGg9IjE0MCIgaGVpZ2h0PSI3NCIgcng9IjkiIGNsYXNzPSJub2RlLWJsb2NrZWQiIHN0cm9rZS13aWR0aD0iMS41IiAvPgogIDx0ZXh0IHg9IjY5MCIgeT0iMTIzIiBjbGFzcz0ibmlkIHQtYmxvY2tlZCI+RTwvdGV4dD4KICA8dGV4dCB4PSI3MTIiIHk9IjEyMSIgY2xhc3M9Im5ubSI+U3ludGhlc2lzPC90ZXh0PgogIDx0ZXh0IHg9IjY5MCIgeT0iMTM5IiBjbGFzcz0ibnN0Ij5uZWVkcyBEPC90ZXh0PgogIDxyZWN0IHg9IjY5MCIgeT0iMTQ3IiB3aWR0aD0iMTEyIiBoZWlnaHQ9IjYiIHJ4PSIzIiBjbGFzcz0idHJhY2siIC8+CiAgPC9nPgoKICA8Zz48dGl0bGU+RiDigJQgbWFudXNjcmlwdDogYWN0aXZlIG5vdyBvbiBydW5uYWJsZSBwYXJ0cyAoRjMvRjQvRjYpOyB0aGUgYmlnIHJld3JpdGUgRjEgd2FpdHMgb24gRC9FPC90aXRsZT4KICA8cmVjdCB4PSI4NjYiIHk9Ijk3IiB3aWR0aD0iMTQwIiBoZWlnaHQ9Ijc0IiByeD0iOSIgY2xhc3M9Im5vZGUtbm93IiBzdHJva2Utd2lkdGg9IjEuNSIgLz4KICA8dGV4dCB4PSI4ODAiIHk9IjEyMyIgY2xhc3M9Im5pZCB0LW5vdyI+RjwvdGV4dD4KICA8dGV4dCB4PSI5MDIiIHk9IjEyMSIgY2xhc3M9Im5ubSI+TWFudXNjcmlwdDwvdGV4dD4KICA8dGV4dCB4PSI4ODAiIHk9IjEzOSIgY2xhc3M9Im5zdCI+cGFydGlhbCBub3cgwrcgRjEgYWZ0ZXIgRTwvdGV4dD4KICA8cmVjdCB4PSI4ODAiIHk9IjE0NyIgd2lkdGg9IjExMiIgaGVpZ2h0PSI2IiByeD0iMyIgY2xhc3M9InRyYWNrIiAvPgogIDxyZWN0IHg9Ijg4MCIgeT0iMTQ3IiB3aWR0aD0iMTQiIGhlaWdodD0iNiIgcng9IjMiIGNsYXNzPSJzZWctZ29vZCIgLz4KICA8cmVjdCB4PSI4OTYiIHk9IjE0NyIgd2lkdGg9IjQ2IiBoZWlnaHQ9IjYiIHJ4PSIzIiBjbGFzcz0ic2VnLXJlYWR5IiAvPgogIDwvZz4KCiAgPGc+PHRpdGxlPkcg4oCUIHJlbGVhc2UgbWVjaGFuaWNzOiBnYXRlZCwgbGFzdDwvdGl0bGU+CiAgPHJlY3QgeD0iMTA0MCIgeT0iOTciIHdpZHRoPSIxMDIiIGhlaWdodD0iNzQiIHJ4PSI5IiBjbGFzcz0ibm9kZS1ibG9ja2VkIiBzdHJva2Utd2lkdGg9IjEuNSIgLz4KICA8dGV4dCB4PSIxMDU0IiB5PSIxMjMiIGNsYXNzPSJuaWQgdC1ibG9ja2VkIj5HPC90ZXh0PgogIDx0ZXh0IHg9IjEwNzYiIHk9IjEyMSIgY2xhc3M9Im5ubSI+UmVsZWFzZTwvdGV4dD4KICA8dGV4dCB4PSIxMDU0IiB5PSIxMzkiIGNsYXNzPSJuc3QiPmdhdGVkIMK3IGxhc3Q8L3RleHQ+CiAgPHJlY3QgeD0iMTA1NCIgeT0iMTQ3IiB3aWR0aD0iNzQiIGhlaWdodD0iNiIgcng9IjMiIGNsYXNzPSJ0cmFjayIgLz4KICA8L2c+Cjwvc3ZnPg==)

active now needs your decision startable blocked upstream bar = lane
progress: done · startable · rest blocked

## Trust ladder — earning back the revoked products (§V)

P0

P0 Provenance freezerecommended next

P1

P1 · V1 Fit re-trust contractstartable

P2

P2 · V2 Input forensicsstartable

✓

P3 · V4 Censuscleared 07-07

✓

P4 · V5 DM budgetcleared 07-07

P5

P5 · V3 Energiesafter P0 + P1

✓

P6 · V6 Association + DM_obscleared 07-07

## Lanes & tasks — what every ID means

VTrust re-validation — earn back every revoked product
(plan-trust-reset-revalidation.md)blocks: everything downstream

- P0Provenance freeze pin SHA-256 of every data input; restore the
  removed census scripts + frozen CSVs into the tracked tree; label the
  two fit generations; make budget/foreground tables emitter-generated
  instead of hand-typedstartable
- P1·V1The re-trust contract ADR-0008: 5 rungs a fit must pass to be
  citable. Builds: one shared rail detector (today there are 3
  conflicting ones), absolute injection-recovery requirement (current:
  only linear, ~2.5× off), a real posterior-predictive check (current
  "PPC" is just a χ² stat), fixed verification coveragestartable
- P2·V2Scattering-input forensics find the off-repo cube builder on h17,
  checksum all 24 CHIME cubes, test each for the gen-1 de-chirp/wrap
  defect, close the open DATA_SOURCES reconciliation mysterystartable
- P3·V4Census re-validation owner-cleared 2026-07-07 on the
  DR9/DESI-DR1/NED/PS1-STRM re-validation (incl. the phineas DESI-STAR
  contaminant fix; all census clusters traced to Wen & Han 2024).
  tab:foreground, verdicts, impact parameters, two-phase mNFW DM_int,
  fig:clusters_icm restored (CONTEXT.md status)cleared 07-07
- P4·V5DM-budget re-validation owner-cleared 2026-07-07 with V4 — census
  now presents 35 systems; budget table + fig:budget left panel
  restored. Measured-scattering side of fig:budget stays revoked (wave-1
  τ fits, plan D1)cleared 07-07
- P5·V3Energies audit explain the γ_D ≈ −5 pile-up (prior rail study at
  floor −10), make the table's selection rule explicit + enforced,
  resolve chromatica's contradictory gate verdictsafter P0+P1 rails
- P6·V6Association + DM_obs re-validation (wave 3) complete 2026-07-07 —
  per-burst per-telescope DM_obs provenance + CHIME–DSA agreement
  documented; association residuals, P_cc, verdicts quotable from the
  pinned V6 artifacts under the shared DSA-DM convention (report:
  v6-association-dm-report-2026-07-07.md)cleared 07-07

AMethodology reset — geometry selection replaces the rail taxonomyA1
draft → A2/A3 → C

- A1Two-screen treatment — working draft, design open draft
  (2026-07-06): scint products enter as a modular constraint layer
  (frozen posteriors/limits, never point estimates); τ·Δν_d counts
  screens probabilistically; no fitted 2nd broadening component unless
  the escalation trigger fires (Pr(τ_near/τ_dom\>0.1)\>0.1,
  median\>0.03, same-screen ambiguity, or PPC residual at the predicted
  scale); scint sets prior odds on the kernel family, evidence decides.
  All elements revisable — discussion liveopen — discussing
- A2Extended-medium PBF kernel code the Williamson uniform-LOS
  pulse-broadening function in FLITS as the alternative to thin-screen,
  β-coupled per ADR-0007 — needed because 10/12 posteriors railed at β=4
  (thin-screen closure rejected)design open
- A3Per-sightline geometry selection thin screen vs extended medium
  chosen per burst by evidence/model comparison, with A1's scint prior
  odds; interior rows (freya, phineas) re-adjudicated under the same
  machinerydesign open
- A4ADR amendment write the FLITS ADR recording: rail classes are
  campaign QA only, α=4-limit quoting retired, A1 decision textstartable

BScintillation campaign, both bands — hard circulation gate ·
**active**: CHIME recipe-parity loop in flight (journal lane B); CHIME
instrumental-ACF correction blocked at freya off-pulse null (FLITS PR
\#160)B1–B4 → B5 → C

- B1Burst configs for whitney / phineas / mahi / isha casey pattern;
  burst bins ~1020 / ~1079 / ~29 / ~55; first run doubles as loader
  teststartable
- B2U sizing + CHIME regeneration, six never-generated co-detections
  zach, oran, wilhelm, johndoeii, hamilton, chromatica (NE2025 MW-floor
  rule)startable
- B3mahi 700–725 MHz RFI inspection before any measurement uses that
  sub-bandstartable
- B4CHIME-band ACF / Δν_d measurements across the sample run under the
  V1 contract; recipe-parity plan (plan-chime-scint-recipe-parity.md) is
  the active prepafter B1/B2 + V1
- B5Two-screen analysis rebuilt on joint CHIME+DSA scint includes
  re-running the revoked DSA-band ACF fits under the contractafter B1–B4
- B6Provenance housekeeping refresh DATA_PROVENANCE (gen-2 md5s), commit
  the h17-side tooling into FLITSstartable

CScattering re-fit from scratch, all 12, geometry-adjudicatedneeds V +
A + B5

- C1Fresh fit campaign on verified inputs under the V1 contract not a
  patch of the nine railed rowsblocked
- C2Per-band systematics pass on whatever C1 flags with elevated
  per-band χ² (old trio wilhelm/hamilton/zach = starting
  hypothesis)blocked
- C3Pin bump + regenerate all tables/figures in the manuscript the one
  build: commit hereblocked

DSightline analysis & foreground comparisonneeds C (V4/V5 cleared)

- D1Measured-vs-predicted foreground scattering per sightline under the
  adjudicated geometries (old version was
  thin-screen-conditioned)blocked
- D2Galaxy / galaxy-cluster foreground comparison as first-class results
  per-sightline attribution verdictsblocked

ESynthesisneeds D

- E1What each foreground medium class does to the signal propagation vs
  intrinsic, per sightlineblocked
- E2Intrinsic emission properties where separable energies table is the
  seedblocked

FManuscript reconciliation & polishF1 needs D/E; F3/F4/F6 anytime

- F1The big rewrite abstract, §2, co-model methods, results, discussion,
  conclusions restructured around geometry selection; purge rail
  vocabulary + α=4 limits; rewrite census/budget prose on re-verified
  productsafter C (β) / V4·V5+D (budget)
- F2tab:beta rework geometry-adjudicated quoting; descriptive
  exponential-consistency for ex-railed rowsafter C3
- F3Mechanical consistency audit per-section sample counts,
  retired-language sweep, table/figure provenance, cross-refs — non-β
  sections nowstartable
- F4Referee-mode full read-through structural pass on
  intro/observations/toa/budget can run now; full pass after F1partial
  now
- F5Line-level prose polish after F3/F4 triageafter F3/F4
- F6Co-author list draft from Law2024 (DSA-110) + CHIME/FRB 2018 author
  overlap, for your pruning; then typeset auth.texstartable
- F7codetections_polarization/ working choice: companion-paper
  materials, intentionally parked, no action — revisableworking choice

GRelease mechanics — lastneeds everything

- G1Push accumulated main commits outward gate: Overleaf pulls maingated
- G2Clean make from a fresh clone at the final pinlast
- G3Overleaf UI pull + visual check of the compiled PDFlast

done / cleared active now startable now needs owner decision blocked
upstream

Journal — agent activity log (newest first)

- 07-27 00:17claudepin-bumpParent \#262 rerun in flight after registry
  orphan repair; watcher merges on green
- 07-27 00:17claudeh17-consolidationh17 lane opened: per-snapshot
  verification of all worktrees; 3 dirty worktrees frozen as
  archive/h17-\*-snapshot-20260727 (hash-verified exact), t0audit branch
  pushed; dispositions pending owner (pre-rewrite main, worktree
  retirement, run trees, /data)
- 07-27 00:17claudebranch-consolidationRemote+local sweep complete
  across all three repos; registry orphan repair (FLITS 9175b925, parent
  8d492fea restored as archive/ refs); receipts merged
  (#137/#138/#141/#142)
- 07-26 19:02claudefig3-regenowner needs_revision recorded (drop
  diamonds); no-diamond candidate rendered at FLITS 99e60c3a,
  deterministic double render certified (3dece7e3); batch
  2026-07-26-fig3-no-diamonds staged; gate rebound; analysis PR next
- 07-26 18:08claudefig3-regencorrected-name candidate staged (batch
  2026-07-26-fig3-name-repair, sha a56d43cc); release gate rebound to
  pipeline 2463289; blocker figure3-registry-snapshot-stale discharged;
  PR \#132 in CI; parent pin PR next; owner approval decision remains
- 07-19 22:11grokjointtf-v2-harvestjobs 169-182 harvested: oran→C1D1
  johndoeII→C1D2 zach C2D3@s2=100; s2=10 D4 MODE-JUMP invalid; report
  validation-jointtf-v2-rerun-harvest-2026-07-19.md; rung-2 still owner
- 07-19 16:35claudejoint-tf-fitsHandoff written:
  docs/rse/specs/handoff-2026-07-19-16-33-jointtf-audit-twoscreen-stage0.md
  (session arc: closure merge -\> charter -\> Stage-0 16/16 wrong-sign
  FAIL -\> t0-prior bug -\> 2 production ghosts -\> v2 re-runs 169-179
  DONE unharvested, 180-182 running). Separate stratified/L0 lane in
  tree preserved untouched.
- 07-19 14:30claudejoint-tf-fitsNeighbor sweep landed (PR \#206 verified
  merged: full off-window audit table in
  COMPONENT_COUNT_LADDER_AUDIT.md; 29 higher-count diagnostics
  untestable without npz regen). GO given for all v2 re-runs: oran
  C1D1vC2D1 (4 jobs), johndoeII C1D2vC2D2 (4), zach C2D{3,4,5} x
  s2{10,100} (6); production-audit re-runs outrank zach if staged; both
  arms under v2, never v1-vs-v2 lnZ. Envelope sweep 159-168 still
  running.
- 07-19 14:20claudejoint-tf-fitsPR \#205 (t0 clamp) verified merged
  0c8c4f5. PRODUCTION OFF-WINDOW AUDIT: 2 ghosts CONFIRMED by my own vet
  (oran C2D1 t0_C1=-5.23 CI\[-11,+3.5\], ghost fluence 3.0 vs real 2.5;
  johndoeII C2D2 t0_C1=-6.16 CI\[-11.6,+0.2\], ghost fluence 26.2 vs
  real 8.4 = SEVERE) — no visible pre-window structure either burst;
  real components tight in-window. 6 production fits CLEAN, isha
  edge-watch, phineas npz-unresolved (independently suspect: beta-rail +
  8.3ms t0_D1 CI). TOA rows oran+johndoeII CHIME structure SUSPECT
  pending v2 re-runs (approved: oran C1D1vC2D1, johndoeII C1D2vC2D2).
  All lanes proceeding parallel: neighbor sweep, zach D3/D4/D5 v2,
  Stage-0 envelope sweep.
- 07-19 14:06claudejoint-tf-fitsFULL WAVE HARVESTED (queue empty;
  teammate idle; my direct reads). TWO-SCREEN STAGE-0: all 6 points
  NO-WEDGE, WRONG SIGN — casey +0.17/+0.42/+0.56, wilhelm
  +0.90/+1.45/+1.68, monotonic in r. Same-alpha two-screen mixing biases
  free-alpha UPWARD, opposite the observed sub-4 wedges =\> rung-1 fails
  the pre-registered falsifier (envelope sweep = remaining formality);
  rung-2 (independent beta2, different scaling laws) gate condition MET,
  owner decision next. COUNT WAVE: hamilton C5D1 -41 vs C4D1 (same floor
  mode; C5 rejected pending vet); C4D2 flips hamilton to HEALTHY corner
  (beta 3.978, tau 25.6us, 19x) but cross-mode dLnZ -1600 INVALID per
  protocol =\> profiled-gain fallback; phineas C4D4 MODE-TRAPPED to
  floor (beta 3.018 vs production 4.043 healthy) =\> invalid, phineas
  neighbor story suspect. All downstream of off-window audit + t0-prior
  fix.
- 07-18 17:42claudejoint-tf-fitszach rejection ACKED by teammate (audit
  doc updated 77-\>129 lines, +3550 consumed nowhere, invalid pair
  snapshotted — all verified on disk). ROOT CAUSE: burstfit.build_priors
  t0 = init +/- 2\*max(tau,10) =\> +/-20ms prior untethered from window,
  inherited by ALL joint fits. Approved re-run grid C2D3/C2D4/C2D5
  (bounded t0, in-window seeds, D5=ceiling test). ORDERED campaign-wide
  off-window audit (crude sweep: 26/51 JSONs flagged, most CHIME
  false-positives, but whitney_fine D1 -9.8/-10.8, isha C1 -13.7,
  johndoeII D1 -9.2 likely real; production 12/12 priority; off-window
  in production =\> escalate). Prior-fix PR lands before re-run;
  production evidences stay as-fitted pending audit.
- 07-18 17:32claudejoint-tf-fitsFLITS PR \#204 MERGED+verified (6a1d206,
  joint_tf_prep RFI/binning via proper 3-way rebase; main's 2
  intervening commits preserved; RFI_FIX_FLIP_RECORD gap closed).
  Two-screen Stage-0 kernel VALIDATED (nesting exact, r=1 derivative
  6e-10, FFT xcheck 1e-5) + grid RUNNING (jobs 153-158 confirmed in
  squeue: casey/wilhelm x r={0.1,0.3,1.0}, nlive=400, free-alpha refit).
  Smoke hint: casey r=0.3 bias +0.42 WRONG SIGN (no wedge) at nlive=60 —
  Stage-0 FAIL is live possibility per charter's pre-registered concern;
  envelope sweep before any FAIL call. Count wave 120/127-129/132 still
  R.
- 07-18 17:09claudejoint-tf-fitszach fine pair ADJUDICATED INVALID
  (team-lead direct read + visual vet on h17): both healthy-mode, dLnZ
  +3549.6 for C2D4, BUT added component is an OFF-WINDOW ghost (t0
  -1.36ms, window \[0,5.9\]; both fits also park D1 at -8/-9ms
  off-window) and the owner cluster (window-rel ~3.6/4.0/4.5) stays ONE
  broad component with identical 4-6sigma residuals in BOTH fits. +3550
  = gain-marginal exploiting off-window kernels, NOT the 4th member. New
  guardrail: t0 priors bounded to fitted window. Remediation delegated:
  bound t0 + rerun pair with in-window seeded D4. Verdict-hold
  discipline worked.
- 07-18 16:21claudejoint-tf-fitsFLITS PR \#203 MERGED+verified (f2ab4e9,
  20 files: provenance x4, PL-PBF fitters, dipole-mask, scint-leakage,
  relaxalpha, FFT fix, sbatch mem fix; pipeline pin untouched). Rulings:
  joint_tf_prep.py RFI/binning code -\> land via rebase-PR
  (reproducibility gap, phineas flip depends on it);
  build_toa_table+residual_check deferred to task-6 TOA deliverable;
  figures stay deck-side. zach 133 done healthy (beta 3.980) — verdict
  HELD for 134 pair mode-check. Two-screen Stage 0 now the priority
  teammate item.
- 07-18 16:14claudejoint-tf-fitsOWNER DECISION: Option A — two-screen
  forward model CHARTERED (non-gating parallel lane). Charter written:
  charter-two-screen-forward-model-2026-07-18.md (rung-1 double-exp PBF
  shared-beta, r=tau2/tau1 nested; Stage 0 wedge-reproduction falsifier
  BEFORE real data; Stage 1 recovery+null injections; Stage 2
  casey+wilhelm three-way; Stage 3 owner review). Decision brief marked
  DECIDED. Dispatching kernel build to teammate.
- 07-18 16:09claudejoint-tf-fitsPR \#142 MERGED to main
  (2026-07-18T23:09Z): closure report + two-screen decision brief +
  07-17/18 lane specs + journal/board. All CI green. Next: FLITS-side
  artifact landing delegated to teammate; decision framing to owner.
- 07-18 16:04claudejoint-tf-fitsSCINT-LEAKAGE CLOSED (6/6 recover
  alpha~4, bias\<=0.003 at m=1 + real 2L Dnu_d + real channelization;
  static controls clean) =\> elimination COMPLETE, two-screen sole
  survivor. Closure docs written:
  report-jointtf-mechanism-closure-2026-07-18.md +
  decision-two-screen-charter-2026-07-18.md (recommend charter as
  non-gating parallel lane). Deck updated (leakage closed + decision
  queue) + deployed. Memory: plpbf-rejected-emg-stands saved. Committing
  docs via handoff-sync branch -\> PR -\> merge per owner instruction.
- 07-18 15:24claudejoint-tf-fitsDIPOLE-MASK DISCRIMINANT COMPLETE +
  published: DISTRIBUTED on both bursts (casey wedge +3540/+3795 of
  +5537 survives, alpha 2.27; wilhelm +634/+586 of +731, alpha 2.75;
  hard/soft agree; verified on disk) =\> both peak dipoles exonerated,
  TWO-SCREEN CHROMATICITY primary for both wedges. Secondary finding:
  rails have different origins — casey ceiling PEAK-ASSOCIATED
  (masked-tied beta 3.44 CI±0.01 excludes 3.99; diagnostic only,
  production limit stands), wilhelm ceiling intrinsic (rail robust to
  excision). Montage + wedge figure vetted + deployed with table (deck
  slide 6). Remaining: scint-leakage bound 147-152 (pre-figured
  negligible), zach-fine, hamilton, phineas.
- 07-18 14:52claudejoint-tf-fitsHandoff written:
  docs/rse/specs/handoff-2026-07-18-14-51-jointtf-plpbf-campaign.md —
  PL-PBF three-way verdict IN (casey +3.3 / wilhelm -3.3 vs production,
  s_i upper-railed both =\> physical heavy tail NOT the mechanism;
  free-alpha still +5533/+734), 12/12 landscape, zach binning-drop
  pending, neighbor counts unadopted (mode-trap caveat), leakage
  injection = the discriminant for the -1.6.
- 07-18 14:08claudejoint-tf-fitsScheduler stall found+fixed:
  fit_pool.sbatch has NO --mem directive =\> job 120 defaulted to
  whole-node 95000M ledger claim, serializing 14 pending jobs against 38
  idle CPUs (ledger is bookkeeping-only). Surgery: MinMemoryNode=2048 on
  pending 127-134; requeued 120 (33min lost, no artifacts) + 2G +
  cleared BeginTime hold-off. All 15 jobs now RUNNING concurrently
  (hamilton probes, zach fine pair, 8 dipole-mask, phineas restarted).
  Durable fix flagged to teammate: add --mem-per-cpu=1G to
  fit_pool.sbatch. Backstop watcher re-armed (b2uxexu5i; prior one
  killed).

Reference — trust state & decisions ledger

## Trust state after the 2026-07-06 reset — where it stands now

### Restored via the §V ladder

[TABLE]

### Still revoked / unsupported

|  |  |
|----|----|
| Joint scattering fits wave 1 — every β, τ₁GHz, multiplicity, PPC; interior rows (freya, phineas) included · awaits V1 + C | revoked |
| Sub-band EMG fits · scint ACF fits (Δν_d) wave 1 — gen-1 data-defect lineage unresolved; CHIME-band campaign re-establishes both bands | revoked |
| c₀, γ amplitudes → all energies wave 1 — γ_D ≈ −5 pile-up unexplained · awaits V3 | revoked |
| Downstream claims still unsupported measured side of fig:budget + measured-vs-predicted overlay · τ·Δν_d two-screen test · scint excess · 20230913A attribution · multiplicity demo (fig:whitney_mult, abstract close, conclusions 7) · tab:beta · tab:burst-energies · fig:jointmodel_montage · fig:scint_screens | unsupported |

## Decisions ledger — working choices, all open (owner: nothing stays locked)

### A1 — two-screen treatment discussing

Draft: modular constraint layer; prior-odds kernel selection; posterior
escalation trigger for any fitted 2nd component. Full text:
plan-circulation-readiness.md A1. Every element revisable.

### Rail tallies · F7 · F6 working choices

Tallies dropped from manuscript · polarization dir = companion paper,
keep as-is · co-authors drafted from Law2024 + CHIME/FRB 2018 overlap.
All revisable on your word.

### Trust reset (three waves)

All fits revoked (w1); census + DM budget revoked (w2); TOA arithmetic +
DM_obs revoked (w3). V4/V5/V6 since cleared (07-07); wave-1 fits +
energies remain out pending V1/V3 + C. Re-entry only via the §V ladder.

Sources: CONTEXT.md (domain contract; trust-state statuses) ·
docs/rse/specs/plan/plan-circulation-readiness.md ·
docs/rse/specs/plan/plan-trust-reset-revalidation.md (§V expansion) ·
docs/rse/protocols/journal.jsonl (protocol:
docs/rse/protocols/journal-protocol.md) ·
docs/rse/control/board/owner-view.json (owner view data). Structure: the
owner-facing view groups work by **science strand** (association ·
budget/census · scattering · scintillation · energies · synthesis ·
mechanics), each on an inputs→method→measured→validated→written
lifecycle; the canonical task IDs (P0, A1, B4, …) from the plans are
unchanged and the agent-facing recovery map/lanes live in the fold.
Board source: docs/rse/control/board/readiness.html — any agent edits it
(keep strands, map, ladder, and lane detail in sync), rebakes
(scripts/render_journal_panel.py), deploys (scripts/deploy-board.sh) to
https://jakobtfaber.github.io/Faber2026/board/. This board is the
standing "where are we" reference.
