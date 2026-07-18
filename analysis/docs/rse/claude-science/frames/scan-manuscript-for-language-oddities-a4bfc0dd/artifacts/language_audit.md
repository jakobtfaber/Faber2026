# Faber2026 — language / field-register audit

Scan for text that does not align with standard ApJ / FRB-field prose.
Locations are file:line. Comment-only (`%`) content noted separately.

## 1. Draft-scaffolding leaking into rendered prose (highest priority)
- main.tex:46-60 — five un-commented `[SLOT: ...]` placeholders inside the abstract; these TYPESET into the PDF.
- observations.tex:41 ("citable"), results.tex:153 ("restored as citable measurements") — "citable" is internal trust-ladder vocabulary.
- Draft-deferral language recurs across sections. Exact phrase "deferred pending completion of the scattering analysis" appears verbatim at observations.tex:43 and budget.tex:189 only. Related-but-different deferral wordings: results.tex:71 ("deferred to the scattering analysis"), appendix.tex:145 ("deferred to the completed scattering analysis"), methods.tex:56 ("Energy rows are deferred until the spectral amplitudes...").
- "current" as draft-state flag: results.tex:152-154 (also "already informative", "remain diagnostic only until"), budget.tex:255.
- methods.tex:14 — "a trusted per-band amplitude fit" ("trusted" = trust-reset vocabulary).
- Section bodies are largely `% TODO(...)` comment blocks (discussion.tex nearly all TODO; also results/conclusions/budget/observations). Non-rendering, but Discussion & Conclusions are effectively unwritten.

## 2. Terminology inconsistencies (one thing, multiple names)
- Photo-z classifier named 3 ways: "WISE--PanSTARRS--STRM" (observations.tex:108), "PanSTARRS-STRM" (observations.tex:139), "PS1-STRM" (foreground_table.tex, throughout). Published name = PS1-STRM (Beck+2021).
- Survey release: RESOLVED (not a conflict). Discovery stage uses DESI Legacy DR8 North (VizieR VII/292/north); validation independently queries DR9 photo-z. Two deliberate pipeline stages. Fix applied: discovery paragraph (observations.tex:105) now names "DR8 North" explicitly so it no longer reads as disagreeing with budget_table note u. DR9 in validation prose (126,160,163) is correct.
- Zhou2021 estimator: FIXED. Was "deep-learning" (observations.tex:106) vs "random-forest" (127); it is random-forest — corrected to random-forest.
- Cluster catalogs: RETRACTED (over-read, no change needed). Discovery ClusterEngine genuinely queries PSZ2/MCXC/MCXC-II (config.py:81-83); "every matched cluster comes from the optical catalog" correctly reports that only Wen & Han 2024 systems survived at this declination (V4-cleared, CONTEXT.md). Reporting searched space + yield is correct practice.

## 3. Coined / non-standard terms used as if standard
- "chance-maximizing windows": toa.tex:72, results.tex:15, conclusions.tex:12. (Field: "conservative"/"worst-case".)
- "co-model / co-models" (verb): main.tex:41, observations.tex:57, budget.tex:122. (Field: "jointly model".)
- "sub-floor offset": toa.tex:159. (Means "below the uncertainty floor".)
- "soft disk": observations.tex:183 — plotting-marker language in a physics caption.

## 4. Informal register in captions / appendix
- "at-a-glance cross-check", "qualitative sanity check": appendix.tex:5,16.
- "backlights": intro.tex:5 — borderline; does appear in FRB literature.

## Checked and OK
- Counts consistent: 15 confirmed + 13 inconclusive = 28 rows; 35 = 28 + 7 refuted; 8 "DM+pos." + 4 "pos." = 12; tau_int "<= 0.024 ms" = table max; "eleven" panels = 12 - chromatica (gate-FAIL).
- Uniform American spelling (-ize, "modeling"); no British/American mix.
- No burst-nickname leaks in rendered prose (only in figure filenames/labels).
