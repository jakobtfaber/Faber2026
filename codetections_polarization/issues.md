# Issues — spectropolarimetry manuscript (`main.tex`)

Source: `codetections_polarization/main.tex` (Ayush Pandhi et al., *Unique spectropolarimetric properties of FRBs codetected by CHIME/FRB and DSA-110*).

Each item maps to one `\fixme{...}` in the draft. Resolve by editing `main.tex` and removing the `\fixme{}` wrapper.

---

## ISSUE-001 — Codetection search section (§3)

- **Assignee:** Jakob Faber
- **Location:** `\section{Search for codetected FRBs}` (`\label{sec:obs_codetections}`), line 57
- **Status:** closed (2026-06-27)
- **Text in draft:**
  > [To do: Jakob] Include a summary covering all the necessary points but include a more detailed description in your paper. I imagine this would include: (i) ensuring the TOAs and sky positions at both telescopes agree to within uncertainties, (ii) what those uncertainties are/how they were derived, (iii) how the DMs for both data sets were derived and whether they agree with each other, and (iv) visual inspection of matching burst morphology (particularly for multi-component bursts). End with a few sentences summarizing the sample (e.g., number of FRBs, the fact that they're all non-repeaters, broadband, typically single or multi-component, typically scattered or not scattered, redshift distribution of hosts, etc.).

**Acceptance criteria**

- [x] New prose replaces the entire `\fixme{...}` block in §3.
- [x] TOA and sky-position agreement stated with uncertainties and derivation.
- [x] DM derivation and cross-telescope agreement described.
- [x] Burst-morphology visual matching noted (multi-component cases).
- [x] Sample summary: N=12, non-repeaters, broadband, component/scattering/host-redshift character.
- [x] Long-form detail deferred to paper I with a pointer, per Ayush's note.

**Notes:** Primary Jakob deliverable. Content likely overlaps Faber2026 / paper I codetection material.

---

## ISSUE-002 — DSA-110 FRB position refinement

- **Assignee:** Jakob Faber
- **Location:** `\subsection{DSA-110}` (`\label{sec:obs_dsa}`), line 49
- **Status:** closed (2026-06-27)
- **Text in draft:**
  > A sentence summarizing how the FRB position is refined?

**Acceptance criteria**

- [x] One sentence added after the localization paragraph describing position refinement (beamforming / imaging pipeline).
- [x] `\fixme{...}` removed.

**Notes:** Expanded 2026-06-27 with pipeline detail from Ravi et al. 2023 ApJL 949, L3 (DOI 10.3847/2041-8213/acc4b6): visibility formation, NVSS-based calibration, imaging, Gaussian fit to deconvolved image.

---

## ISSUE-003 — DSA-110 baseband S/N threshold

- **Assignee:** Jakob Faber
- **Location:** `\subsection{DSA-110}`, criterion (i)
- **Status:** closed
- **Resolution:** Real-time search trigger $\mathrm{S/N} > 8.5$ in any coherent fan beam (Law et al. 2024, ApJ 967, 29, \S2.1; `2024ApJ...967...29L`). Voltage dumps from all 63 antennas follow automatically on trigger.
- **Text in draft:**
  > `$\mathrm{S/N} > 8.5$` (was `\fixme{X}`)

**Acceptance criteria**

- [x] Numeric S/N cutoff inserted for saving full-polarization voltage data.
- [x] Nested `\fixme{X}` removed.

---

## ISSUE-004 — DSA-110 baseband selection criteria (iii)

- **Assignee:** Jakob Faber
- **Location:** `\subsection{DSA-110}`, voltage-save trigger list
- **Status:** closed
- **Resolution:** Not manual verification. Law et al. 2024 \S2.1 real-time trigger: (i) $\mathrm{S/N}>8.5$, (ii) not strong terrestrial RFI, (iii) $\mathrm{DM}>50$~pc~cm$^{-3}$ and $\mathrm{DM}>0.75\,\mathrm{DM}_\mathrm{MW}$ (\citet{2002astro.ph..7156C}). Post-trigger confirmation is interferometric localization (same \S), already described above in prose.
- **Text in draft:**
  > Three-item list per Law 2024 (was manual-verification `\fixme{}`)

**Acceptance criteria**

- [x] Confirm whether criterion (iii) is manual verification; reword list item (i)–(iii) accordingly.
- [x] `\fixme{...}` removed from the criterion list.

---

## ISSUE-005 — DSA-110 system / commissioning citation

- **Assignee:** Jakob Faber
- **Location:** `\subsection{DSA-110}`, end of commissioning paragraph
- **Status:** closed
- **Resolution:** Ravi et al. 2023 (ApJL 949, L3, \S2.1 + Table 1) and Law et al. 2024 (ApJ 967, 29, \S2.1) — commissioning array, real-time search, voltage triggers (`2023ApJ...949L...3R`, `2024ApJ...967...29L`). Sherman 2024 is polarization-only; full instrument paper still Ravi in prep.
- **Text in draft:**
  > `\citep{2023ApJ...949L...3R, 2024ApJ...967...29L}` (was commissioning `\fixme{}`)

**Acceptance criteria**

- [x] Appropriate `\citep{...}` added (Law et al. 2024 ApJ).
- [x] `\fixme{...}` removed.

---

## ISSUE-006 — DSA-110 polarization catalog citation

- **Assignee:** Jakob Faber
- **Location:** `\subsection{FRB magnetoionic environments}` (`\label{sec:results_host_env}`), line 118
- **Status:** closed
- **Resolution:** CHIME future catalog: `M.~Ng et al.~in prep.`; DSA published sample: `\citet{2024ApJ...964..131S}` (ApJ 964, 131). Sentence split so DSA side is not “future catalog.”
- **Text in draft:**
  > `\citet{2024ApJ...964..131S}`

**Acceptance criteria**

- [x] Citation paired with “M. Ng et al. in prep.” for future CHIME/FRB and DSA-110 polarization catalogs.
- [x] `\fixme{DSA-110 citation?}` removed.

---

## ISSUE-007 — DSA acknowledgements

- **Assignee:** Jakob Faber
- **Location:** `\section*{Acknowledgements}`, line 325
- **Status:** closed
- **Resolution:** DSA-110 ack paragraph added (OVRO staff + Caltech radio group; Big Pine Paiute land acknowledgement; NSF MSIP grant AST-1836018) — verified against Sherman et al. 2024 (ApJ 964, 131) and the DSA-110 FRB/host catalog (Law/Ravi 2024, ApJ 967, 29) acknowledgements.
- **Text in draft:**
  > OVRO/Caltech + Big Pine Paiute + NSF MSIP AST-1836018

**Acceptance criteria**

- [x] DSA-110 funding / facility acknowledgement paragraph added (mirror CHIME block style).
- [x] `\fixme{DSA acknowledgements.}` removed.

---

## ISSUE-008 — "Twelve apparently non-repeating FRBs" is false for FRB 20230814B

- **Assignee:** Jakob Faber (raise with Ayush)
- **Location:** abstract + `\section{Search for codetected FRBs}` sample summary
- **Status:** open (2026-07-17)
- **Problem:** FRB 20230814B (johndoeII) is a repeater: the DSA-110 catalog carries a
  prior DSA-only detection of the same source (row `johndoe`, S/N 72.6, DM 696.4,
  47 days earlier, identical z=0.5535; raw data not saved). The Verdi et al.
  DSA full-sample draft marks 20230814B with a repeater asterisk. Both this draft
  and paper I currently describe the sample as "twelve apparently non-repeating
  FRBs"; paper I's `toa.tex` no-repeat-detection claim is flagged on Faber2026
  PR #106.

**Acceptance criteria**

- [ ] Abstract/sample prose amended (e.g. "one of which has a single earlier
  DSA-110-only detection") or the non-repeating qualifier dropped.
- [ ] Consistent wording agreed with paper I.

---

## ISSUE-009 — Redshift provenance: "adopted from paper I" is not the actual source

- **Assignee:** Jakob Faber (raise with Ayush)
- **Location:** `\section{...}` RM/budget methods ("The observed DM ... and host
  galaxy redshift, z, of these FRBs are reported in paper I and adopted for this work")
- **Status:** open (2026-07-17)
- **Problem:** paper I currently has no z for 20230814B and carries a provisional
  z=0.510 for 20221203A — this draft (correctly, per the Verdi et al. DSA
  full-sample table, now the agreed standard) uses z=0.5535 for 20230814B and no
  z for 20221203A. The provenance sentence should cite the actual source
  (Verdi et al. in prep. / DSA-110 host program), and paper I is being updated to
  match the same standard.

**Acceptance criteria**

- [ ] Provenance sentence corrected.
- [ ] Both drafts agree on the z-set: nine z-constrained bursts including
  20230814B (0.5535), excluding 20221203A/20230325A/20240122A.

---

## ISSUE-010 — RM budget for FRB 20230307A omits the intervening cluster (material)

- **Assignee:** Jakob Faber (raise with Ayush)
- **Location:** RM/budget methods (eqs. `eq:dm_comps`/`eq:rm_comps`) + Table
  `tb:host_props` row FRB 20230307A
- **Status:** open (2026-07-17)
- **Problem:** the MC budget carries no intervening term, but paper I's census
  crosses the cluster J115120.4+714435 at b/R500=0.83 with DM_cl ≈ 184
  pc cm⁻³ (obs; 84–328 bracket, X-ray-capped mass). Neglecting its RM is
  equivalent to asserting |⟨B∥,ICM⟩| < 0.04–0.16 μG — an order of magnitude
  below measured outskirt fields (classification MATERIAL under the
  predeclared record; ±0.5 μG shifts RM_host by ~7σ of its quoted error, and
  the DM-side correction alone moves ⟨B∥,host⟩ from −2.0 to ≈ −4.5 μG).
  Full memo with two language options:
  `docs/rse/specs/memo-thread1-rm-repartition-2026-07-17.md` (paper I repo).
- **Amendment (2026-07-17, post literature sweep):** a systematic Undermind
  sweep expanded the record's literature set to six studies / five systems
  (Fornax counted once, adjudicated). Classification remains **MATERIAL**
  but at the boundary — outskirt σ_RM median 18.9 vs threshold 18.6
  observed-frame (1.7% margin). The ~7σ field sensitivity and the DM-side
  correction are independent of that margin; see memo (v1.3 table).

**Acceptance criteria**

- [ ] Both-owner decision recorded (Option A: add intervening term for this
  burst; Option B: keep host-only + state the implied ICM-field ceiling; or C).
- [ ] `tb:host_props` 20230307A row and its prose adjusted per the decision.
- [ ] Paper I adds at most one forward-reference sentence (its side of the
  both-owners gate).

---

## Summary

| ID | Assignee | Section |
|----|----------|---------|
| ISSUE-001 | **Jakob Faber** | Search for codetected FRBs |
| ISSUE-002 | **Jakob Faber** | DSA-110 observations |
| ISSUE-003 | **Jakob Faber** | DSA-110 observations |
| ISSUE-004 | **Jakob Faber** | DSA-110 observations |
| ISSUE-005 | **Jakob Faber** | DSA-110 observations |
| ISSUE-006 | **Jakob Faber** | FRB magnetoionic environments |
| ISSUE-007 | **Jakob Faber** | Acknowledgements |
| ISSUE-008 | **Jakob Faber** | Sample framing (non-repeating claim) |
| ISSUE-009 | **Jakob Faber** | Redshift provenance |
| ISSUE-010 | **Jakob Faber** | RM budget (intervening cluster) |

**Jakob:** 10 issues (ISSUE-001–010); 001–007 closed, 008–010 open.
