# Handoff: Freya (FRB 20230325A) DSA-110 localization uncertainty

---
**Date:** 2026-10-30 01:09
**Author:** AI Assistant (Claude Fable 5.1)
**Status:** Handoff
**Branch:** `method-reassessment-2026-09-11` (tracks `github/method-reassessment-2026-09-11`)
**Commit:** 1394e189

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Recover the DSA-110 localization uncertainty for Freya from the 2023-04-21 imaging on h23 | ✅ Complete | Executed notebook committed in 1394e189 and pushed |
| Write the analysis as an executed Jupyter notebook with figures, ASD-STE100 descriptive prose | ✅ Complete | 9 code cells, 0 errors, 4 figures; STE checker left 6 heuristic false positives |
| Assess whether the systematic term hitting the fit prior floor is a defect | ✅ Complete (advisory) | Profile likelihood shows the data do not constrain σ_sys; see Learnings |
| Add a profile-likelihood cell and correct the Dec systematic term in the notebook | 📋 Planned | Jakob has not yet asked for it; recommendation D1 below |
| Commit Jakob's markdown edits to the notebook | 📋 Planned | Working copy differs from HEAD in markdown only |
| Extend the same recipe to the other 11 co-detected bursts | 📋 Planned | Not started; manuscript gives no DSA uncertainty for any burst |

**Current Workflow Phase:** Validate (analysis done; one statistical defect identified and awaiting a decision)

## Workflow Artifacts

No `research-*`, `plan-*`, `experiment-*`, or `implement-*` documents were produced. The notebook is the artifact.

- `docs/rse/ops/freya_localization_uncertainty.ipynb` — the executed analysis (committed copy sha256 `66d1bfeb…`, working copy `98ad10d0…`).
- `docs/rse/ops/raw-data-provenance.md` — h17 is the raw-data authority for the project; the localization images used here live on h23 and are not covered by that document.

Previous handoffs in this directory (worktree disposition 2026-07-24, live-analysis batch 2026-08-05) are not about this task.

## Critical References

- `docs/rse/ops/freya_localization_uncertainty.ipynb` — read the Result, Limits, and section III markdown first, then the fit cell (search for `StraightLineIntrinsicScatterModel`).
- `h23:/home/ubuntu/vikram/notebooks/localize.ipynb` — the recipe this notebook copies; copy at `h23:/media/ubuntu/ssd/jfaber/freya_localization/recipe/`. The `lnV` bounds come from here.
- `h23:/media/ubuntu/ssd/jfaber/freya_localization/build_nb.py` — generator script that writes the notebook; edit this, regenerate, then execute with nbconvert (command below).

## Recent Changes

- `docs/rse/ops/freya_localization_uncertainty.ipynb` — new file in 1394e189. Working copy modified after the commit (file mtime 2026-10-30 00:55, not by this session): markdown only. Code cells and outputs are byte-identical to HEAD. Changes: Date/Author/Status line removed; "in the CHIME/DSA codetection sample" added to the result sentence; result line bolded; headings renamed to `## I.`, `## II.`, `## III.` (the temporary `# III.` heading level typo was restored to `## III.` before committing). A draft `docs/rse/ops/freya-dsa-localization-uncertainty.md` was created and removed before the commit.
- Same notebook also copied, untracked, to the Overleaf checkout `~/Developer/repos/git.overleaf.com/jakobtfaber/faber2026-codetections/docs/rse/ops/`. That copy is the committed version, not the edited one.

## Reproducibility & Data State

- **Seeds:** none. The analysis is deterministic (spline peak fit, BFGS from fixed `x0=[0.01, 0, 0]`).
- **Environment:** h23 conda env `casa38`: `/home/ubuntu/anaconda3/envs/casa38/bin/{python3,jupyter}` (CASA 6 tools, astropy, scipy). No lockfile exists for this env; it is a shared machine environment, provenance unverified beyond the package list printed in the notebook.
- **Data (all on h23, read-only source):** `/media/ubuntu/data/localization_processing/230325aaag/`, working copy `/media/ubuntu/ssd/jfaber/freya_localization/230325aaag/`. Inputs: `img2/imgx.image` (1000×1000, 0.3″ cells), `images/frb-image.fits` (10000×10000, 2″ cells), `icrs_image/<name>-dirty.fits` for 8 RFC calibrators, `rfc_idict.npz`. No checksums recorded; the notebook prints shapes and headers. T3 Level3 json `/dataz/dsa110/candidates/230325aaag/Level3/230325aaag.json` has null error fields and a T2 position 1.9° off.
- **Partial results:** none outstanding. Figures are embedded in the notebook; PNG copies in the session scratchpad are transient.
- **In-flight jobs:** none.
- **Re-execute:** `ssh h23 'cd /media/ubuntu/ssd/jfaber/freya_localization && /home/ubuntu/anaconda3/envs/casa38/bin/python3 build_nb.py && /home/ubuntu/anaconda3/envs/casa38/bin/jupyter nbconvert --execute --inplace freya_localization_uncertainty.ipynb'`, then scp to `docs/rse/ops/`.

## Verification State / Known-Broken

- **Tests:** none exist for this notebook. Execution check: 9/9 cells executed, 0 error outputs (verified with `jq` on the committed file this session).
- **Uncommitted / unpushed:** the markdown-only edits to the notebook described above. Untracked and separate from this task: `.archive/codex-2026-07-27-realtime-voice-chat-2/`, `.hydradb-plugin-data/`, `docs/rse/ops/.ipynb_checkpoints/`. Do not sweep these into a commit.
- **Unverified / disputed result:** the Dec systematic term. The notebook reports σ_sys(Dec) = 0.43″ from lnV = −1.71, but the raw standard deviation of the six Dec offsets is 0.35″. An intrinsic scatter above the total scatter is not a converged maximum. A profile likelihood recomputed off the printed calibrator table (RA from J-names, approximate to ~0.05 in lnV; script at scratchpad `profile_lnv.py`, not in the repo) puts the Dec maximum near lnV ≈ −3.2 (σ ≈ 0.20″) and the RA maximum near −2.4 (σ ≈ 0.30″), with ΔlnL between the −2 wall and the maximum of 0.1 (RA) and 1.1 (Dec). The committed numbers are therefore the recipe's convention, not measurements of σ_sys.
- **Scientific status:** exploratory. No project-owned acceptance criterion exists for a DSA localization uncertainty. The combined values 0.41″/0.44″ must not be quoted in the manuscript until D1 below is decided.

## Learnings

- The recipe's `ln_likelihood` has hard walls `lnV ∈ [−2, 2]`, i.e. σ_sys ≥ 0.37″. With six calibrators and per-point errors of 0.05–0.14″ (`mmyerr = 0.45*25/(1000*flux)`), the likelihood in lnV is nearly flat, so BFGS stops wherever the wall or a flat patch catches it. Hitting the floor is expected at this sample size, not evidence of a wrong prior.
- Two calibrators are rejected (offset > 10 pixels) and two have no dirty image, leaving 6 of 10. The scatter estimate has roughly 35 percent fractional uncertainty at best.
- Statistical term uses projected beam FWHM/(2·SNR) with MAD-based rms (SNR 77.5). Using the plain standard deviation gives SNR 64 and changes the combined values by under 0.02″.
- The corrected position (05h52m45.107s +74d12m00.67s) applies the fitted line offset at the FRB RA (−0.97″ RA, +0.90″ Dec). The recipe does not state the beam-projection convention; the notebook projects the beam on each axis.
- Local Mac python3 lacks `nbformat`; generate and execute on h23 only.
- Commit with `git add <file> && git commit --only <file>` in this repo to avoid sweeping the untracked separate-lane directories. Omit `Co-Authored-By` lines (Jakob's rule).

## Action Items & Next Steps

1. [ ] **D1 (Jakob decides):** choose the systematic-term convention for the paper: (a) empirical residual scatter from refitting a linear trend to the 6 calibrators with $N-2=4$ degrees of freedom ($\sqrt{\mathrm{RSS}/4} \approx 0.41''$ RA, $0.31''$ Dec, combined $\approx 0.45''/0.33''$; note plain residual std about the notebook's existing BFGS line gives $\approx 0.35''$ RA, $0.36''$ Dec, and final values must be recomputed from full-precision h23 inputs), (b) raw offset standard deviation (0.47″/0.35″), or (c) keep the recipe's BFGS output (floor-limited 0.37″ RA / unconverged 0.43″ Dec) and state explicitly that it is an unconverged recipe convention, not a converged MLE. Recommended: (a).
2. [ ] Edit `build_nb.py` on h23: add a profile-likelihood cell over lnV for both axes, report the chosen convention, and rewrite the Limits section to name the Dec non-convergence. Regenerate and re-execute (command above). Keep prose in STE descriptive mode and run `~/.claude/skills/asd-ste100/scripts/ste_check.py --mode descriptive` on the extracted markdown.
3. [ ] Reconcile Jakob's markdown edits: fold them into `build_nb.py` so regeneration does not discard them (`## III.` heading level already restored in the committed notebook).
4. [ ] Commit the notebook only (`git commit --only docs/rse/ops/freya_localization_uncertainty.ipynb`), push to `github/method-reassessment-2026-09-11`, and refresh the untracked Overleaf copy.
5. [ ] Decide whether to run the recipe for the other 11 bursts; check which have `localization_processing/<id>/` directories on h23 first.

**Recommended Next Skill:** `ai-research-workflows:validating-implementations` for items 1–4 (the analysis exists and needs its statistical claim corrected and verified). Use `ai-research-workflows:planning-implementations` if item 5 is taken up.

## Other Notes

- Side task completed this session, outside this repo: dotfiles PR #1130 (merged fc4838d3) pins git's pager to `/opt/homebrew/bin/delta` because Delta.app's CLI shadows git-delta on PATH; `~/.claude/settings.json` was relinked into dotfiles with `model: claude-opus-5-5`. The local dotfiles `make test` has 10 pre-existing bats failures (node-cli 4,6,7,8,9,10,12,13,14; forge-agent-lens-codex-hook 132) that are a separate lane.
- Scientific-rigor policy applies: treat the numbers here as exploratory until the convention in D1 is recorded with a dated rationale.

---

**Handoff created by AI Assistant on 2026-10-30**
