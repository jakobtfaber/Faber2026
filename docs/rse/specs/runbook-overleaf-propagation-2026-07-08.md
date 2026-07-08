# Runbook: Overleaf propagation — mirror / pull / merge ordering

**Date:** 2026-07-08
**Purpose:** Land the three 2026-07-08 lanes (nside=32 skymaps, referee impl, DSA subband figures) + CM-serif association cards into the compiled Overleaf manuscript, in an order that does **not** let Overleaf's prose-sync revert git-only edits.

## Verified git state (source of truth for this runbook)

| Ref | Tip | Contains |
|-----|-----|----------|
| `origin/main` | `eeed373` | skymaps `1e01334` + referee `c330d77`; **missing** `f139c7b` |
| `origin/docs/clarify-chance-coincidence` | `f139c7b` | all three lanes |
| local `docs/clarify-chance-coincidence` | `b81d8c5` | +1 unpushed: the two session handoffs |

- `main` ↔ feature delta = **exactly one commit** (`f139c7b`, subband figs).
- `main` tip is a merge commit → main→f139c7b is **not** a fast-forward; needs a merge/PR, not `--ff-only`.

## GATE 0 — confirm before running anything

1. **Which branch does Overleaf sync?** Overleaf ▸ Menu ▸ GitHub → shows the linked branch. Assumed `main`; **unconfirmed**. If it's `docs/clarify-chance-coincidence` instead, Phase B is a no-op (branch already has everything).
2. **Association-card count.** Handoff reports drift 12 → 11 in `~/Developer/overleaf/Faber2026/figures/association_cards/`. All 12 must be CM-serif regenerations. Confirm in Phase C before committing — this is a one-way door.

---

## Step 0 — clear the sandbox-left git locks (REQUIRED FIRST)

A prior agent commit left two 0-byte locks that will block your next git write. On your machine (you own them there, so this works):

```bash
cd ~/Developer/repos/github.com/jakobtfaber/Faber2026
rm -f .git/HEAD.lock .git/index.lock
git status -sb            # sanity; expect "ahead 1" on docs/clarify-chance-coincidence
```

## Phase A — push the handoffs commit (optional but recommended)

```bash
git fetch origin
git status -sb                                   # expect: ahead 1 (b81d8c5)
git push origin docs/clarify-chance-coincidence  # fast-forward; branch has live writers, so fetch first
```

If `git push` is rejected (someone advanced origin): `git pull --rebase origin docs/clarify-chance-coincidence` then push. **Never force-push** — the branch has concurrent writers (per referee handoff).

## Phase B — get subband figures (`f139c7b`) onto the Overleaf-synced branch

**If GATE 0 = `main`:**
```bash
git fetch origin
git checkout main && git pull --ff-only origin main
git merge --no-ff origin/docs/clarify-chance-coincidence \
  -m "Merge scintillation subband figures + session docs to main"
latexmk -pdf main.tex          # sanity: expect 32 pp, 0 undefined refs (2 pre-existing overfull hboxes OK)
git push origin main
```
This carries only the missing delta (`f139c7b`, plus `b81d8c5` if pushed in Phase A) — everything else is already on `main`.

**If GATE 0 = `docs/clarify-chance-coincidence`:** skip Phase B — the branch already holds all three lanes.

## Phase C — association cards (ONE-WAY DOOR — do in the Overleaf checkout)

The Overleaf checkout at `~/Developer/overleaf/Faber2026` is a **separate working copy** of the same repo. The fixed `plot_association_cards.py` (dsa110-FLITS) hardcodes `MANUSCRIPT_OUTDIR` to write PDFs straight into it.

```bash
cd ~/Developer/overleaf/Faber2026
git fetch origin
git status                                    # GATE 1: 11 or 12 cards modified?
git diff --stat figures/association_cards/
```

Reconcile the count — regenerate any stale card so all 12 are CM-serif:
```bash
conda activate flits
# run from the dsa110-FLITS clone that has the use_flits_style() fix on sys.path
python crossmatching/plot_association_cards.py     # writes into this Overleaf checkout
```

Commit + push **on the synced branch** (`<SYNC>` = GATE 0 answer):
```bash
git checkout <SYNC>
git add figures/association_cards/*.pdf
git -c user.name="Jakob Faber" -c user.email="jfaber@caltech.edu" \
    commit -m "figures: association cards in CM serif (use_flits_style)"
git push origin <SYNC>
```

## Phase D — pull into Overleaf, recompile

Overleaf ▸ **Menu ▸ GitHub ▸ Pull GitHub changes** → **Recompile**.

Brings in: nside=32 skymaps, referee `main.tex`/section edits, subband figures (if merged in Phase B), CM-serif cards.

**Ordering rule (the load-bearing part):** do this **Pull before making any further edits directly in Overleaf**. `main.tex` + `sections/*.tex` are co-mastered by Overleaf. Pulling first folds the git-only referee additions — keyword `Radio bursts (1339)`, abstract `≈100–560`, the astropy/pygedm `\software` cites — into Overleaf's copy. If you edit in Overleaf and push *first*, those git-only lines get clobbered.

## Phase E — verify + cleanup

- Recompiled PDF: skymaps hi-res, cards CM-serif, referee prose present, 0 undefined refs.
- Delete backups once confident:
  ```bash
  git tag -d backup/local-20260708-070029 backup/worktree-20260708-070029
  ```
  plus the session scratch clones + 257 MB tarball.

## Still open (not in this runbook — author calls)

Fiducial priors / `DM_host` headline shift acceptance; B3 trial count; B7 aperture; spot-check 11 `refs.bib` entries vs ADS; decide whether `docs/referee_report_2026-07-07.md` stays private (currently untracked — do not push blind). See `handoff-2026-07-08-07-29-*.md` Action Items 1–7.
