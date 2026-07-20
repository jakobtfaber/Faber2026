# DRAFT — message to Ayush Pandhi (Thread 1 both-owners gate)

**Status: DRAFT ONLY — not sent. Owner reviews, edits, and sends by hand.**
Attachments to include when sending:
`docs/rse/specs/notes/memo-thread1-rm-repartition-2026-07-17.md` (the full memo),
`docs/rse/decks/budget/thread1-2026-07-17/rm_repartition_sensitivity.pdf` (one-page
sensitivity figure), and optionally `scripts/rm_cluster_repartition.json`
(seeded, reproducible backing numbers).

---

**Subject:** FRB 20230307A RM budget — the intervening cluster from paper I's
census (proposal + two options)

Hi Ayush,

While cross-checking the two drafts I hit a seam between your RM budget and
our foreground census that I think we should settle together before either
paper freezes. Short version below; the attached memo has the full numbers,
and nothing in either draft changes until we agree.

**The seam.** For FRB 20230307A your budget attributes the entire
non-Galactic residual to the host (RM_host = −756 ± 15 rad m⁻²,
⟨B∥,host⟩ = −2.0 μG). Our census finds that sightline crosses the cluster
J115120.4+714435 (z = 0.200, DESI spec) at b = 0.83 R500, with an
intracluster electron column of ≈184 pc cm⁻³ (bracket 84–328, now
X-ray-capped from above). At that column, every μG of coherent intracluster
field is worth ≈125 rad m⁻² of observed RM — so leaving the term out is
algebraically the same as asserting |⟨B∥,ICM⟩| < 0.04–0.16 μG at 0.83 R500,
an order of magnitude below the ~1 μG-scale outskirt fields these
statistical RM studies infer (Böhringer+ 2016; Osinga+ 2025; Alonso-López+
2025; Khadir+ 2025; Anderson+ 2021 / Loi+ 2025 for Fornax). The median
outskirt σ_RM across that set (six studies, five systems — Fornax counted
once), diluted to our z = 0.2 screen, is ~19 rad m⁻² — 2× your quoted
RM_host error, though I'll flag honestly that this sits right at our
predeclared materiality threshold rather than comfortably above it. The
stronger statement is model-side and doesn't depend on that median: a
perfectly ordinary ±0.5 μG field would move your RM_host by ~7σ of its
quoted error.
The DM side has the same issue independent of B: subtracting the census
column from your DM_host = 464 roughly doubles the implied host field
(⟨B∥,host⟩ ≈ −4.5 μG), and in ~9% of joint draws the published DM_host can't
absorb the column at all.

We reproduced your MC (your priors, 10⁴ trials; the zero-cluster corner
reproduces your published row exactly) before adding the one term, so the
numbers above are apples-to-apples — table in the memo.

**Two language options** (either is fine for paper I; we'd add at most one
forward-reference sentence):

- **A (our recommendation):** add DM_int/RM_int terms for this burst only,
  with the column from our census and ⟨B∥,cl⟩ marginalized over a stated
  prior; RM_host then carries an honest intervening systematic.
- **B:** keep host-only and add one sentence stating the implied ICM-field
  ceiling, with RM_host/B∥,host for this burst read as magnitude upper
  limits on the host contribution.

One genuinely positive framing for your draft either way: if the cluster
term is ever pinned externally (e.g. a background-RM grid), this sightline
becomes a direct ⟨B∥⟩ measurement of a ~1.5×10¹⁴ M☉ cluster at 0.83 R500 —
an FRB-as-ICM-magnetometer result that lives in your paper.

**Asks:**
1. Option A or B (or propose C) — tracked as ISSUE-010 in the shared
   `issues.md`.
2. Confirm the z-bookkeeping fix (ISSUE-009: 20230814B z = 0.5535 from the
   Verdi table; 20221203A's provisional z dropped) lands in the same
   revision, since your MC's z inputs move with it for those bursts.

Happy to jump on a call, and to share the runnable script if useful — it's
seeded and reproduces everything in the memo byte-for-byte.

Best,
Jakob
