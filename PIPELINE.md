# Pipeline pin

This manuscript's numbers and figures are produced by the **dsa110-FLITS**
analysis pipeline (Jakob Faber's fork), pinned as a git submodule at `pipeline/`
for reproducibility. Overleaf's GitHub bridge ignores submodules, so `pipeline/`
is empty in the Overleaf project — it matters only for the GitHub repo and local
builds.

- **Remote:** `https://github.com/jakobtfaber/dsa110-FLITS.git` (personal fork —
  manuscript source of truth; 300+ commits ahead of the `dsa110/dsa110-FLITS`
  org upstream)
- **Org upstream:** `https://github.com/dsa110/dsa110-FLITS.git` — not used for
  this pin. Sync from org upstream into the fork when needed; do not retarget
  this submodule back to the org remote.
- **Pin:** see the submodule's checked-out commit (`git -C pipeline rev-parse HEAD`)
  / the gitlink recorded in this repo.

## Notes

- A submodule pins to a commit on the **remote**, so the pinned commit must be
  pushed to the remote before the pin will resolve. If `pipeline/` is absent, add
  it from the repo root:
  ```sh
  git submodule add https://github.com/jakobtfaber/dsa110-FLITS.git pipeline
  git add pipeline .gitmodules && git commit -m "build: pin dsa110-FLITS pipeline"
  ```
- If you cloned this repo when `pipeline/` still pointed at the org upstream, sync
  the new URL into your existing checkout:
  ```sh
  git submodule sync --recursive
  git submodule update --init --recursive
  ```
- To refresh the pin after pipeline work lands on the fork:
  ```sh
  git -C pipeline fetch && git -C pipeline checkout <sha>
  git add pipeline && git commit -m "build: bump pipeline pin to <sha>"
  ```
