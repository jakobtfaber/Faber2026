# Faber2026 — language / field-register audit

Scan for text that does not align with standard ApJ / FRB-field prose.
Locations are file:line. Comment-only (`%`) content noted separately.

## 1. Draft-scaffolding leaking into rendered prose (highest priority)
- main.tex:46-60 — five un-commented `[SLOT: ...]` placeholders inside the abstract; these TYPESET into the PDF.
- observations.tex:41 ("citable"), results.tex:153 ("restored as citable measurements") — "citable" is internal trust-ladder vocabulary.
- "deferred pending completion of the scattering analysis" (verbatim): observations.tex:43, budget.tex:189, results.tex:71, appendix.tex:145, methods.tex:56.
- "current" as draft-state flag: results.tex:152-154 (also "already informative", "remain diagnostic only until"), budget.tex:255.
- methods.tex:14 — "a trusted per-band amplitude fit" ("trusted" = trust-reset vocabulary).
- Section bodies are largely `% TODO(...)` comment blocks (discussion.tex nearly all TODO; also results/conclusions/budget/observations). Non-rendering, but Discussion & Conclusions are effectively unwritten.

## 2. Terminology inconsistencies (one thing, multiple names)
- Photo-z classifier named 3 ways: "WISE--PanSTARRS--STRM" (observations.tex:108), "PanSTARRS-STRM" (observations.tex:139), "PS1-STRM" (foreground_table.tex, throughout). Published name = PS1-STRM (Beck+2021).
- Survey release: prose "DESI Legacy ... DR9" (observations.tex:126,160,163) vs budget_table.tex:57 note u "DESI Legacy DR8-North". DR8 vs DR9.
- Zhou2021 estimator described as "deep-learning estimator" (observations.tex:106) AND "random-forest estimator" (observations.tex:127) for the same catalog — contradictory (it is random-forest).
- Cluster catalogs: PSZ2/MCXC/MCXC-II X-ray/SZ machinery described (observations.tex) but all clusters actually from Wen & Han 2024 (tables, CONTEXT.md). X-ray/SZ text sources nothing.

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
