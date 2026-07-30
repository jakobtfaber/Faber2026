# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific and visual decisions. Silence leaves every item blocked._

## 1. Zach component-count sampling

**Decision:** When testing whether Zach has three, four, or five DSA-110 pulse components, should adjacent native time samples be averaged together?

**Recommended:** `native` — Keep every 32.768-microsecond sample because averaging can blend nearby pulse components and change the inferred count.

**Choose:**

- `native` — Keep every native 32.768-microsecond DSA-110 sample.
- `coarse` — Average adjacent samples to 65.536 microseconds.
- `stop` — Do not run the three-versus-four-versus-five component comparison.

**Context:**

- This comparison determines how many distinct pulse components are fitted in Zach's DSA-110 burst.
- The current shared-window limit averages adjacent DSA-110 samples, changing 32.768 microseconds to 65.536 microseconds.
- Keeping native samples doubles the fitted bins and computing cost but preserves closely spaced structure.

**Evidence:**

- [Readiness audit](docs/rse/verify/joint-scattering-controlled-rerun-07-zach-count-readiness-20260729/readiness-audit.json) — `c1894081…`
- [Readiness explanation](docs/rse/verify/joint-scattering-controlled-rerun-07-zach-count-readiness-20260729/README.md) — `974aac68…`

**Effect:** The choice fixes the time sampling for the 27 controlled component-count fits.

**Record:** `docs/rse/wayfinder/tickets/joint-scattering-controlled-rerun-07-adjudicate-zach-component-count.md` — Record the selected resolution and update the controlled-run contract.
