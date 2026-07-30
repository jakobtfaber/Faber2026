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

## 2. Second-screen fitting rule

**Decision:** If the observed burst profile has a mismatch at the delay expected for a second screen, and one-screen simulations do not reproduce it, may that result alone justify fitting a second scattering screen?

**Recommended:** `calibrate` — First test the rule on known one-screen and two-screen examples, so we know how often it requests a second screen incorrectly and how often it detects one when present.

**Choose:**

- `accept` — Allow this predicted-delay mismatch test alone to start a second-screen fit.
- `calibrate` — Validate the predicted-delay mismatch rule on known one-screen and two-screen examples before use.

**Context:**

- The autocorrelation-based rule was retired: its conservative threshold rejected all eight simulated two-screen cases.
- The remaining proposal compares the observed burst profile with profiles simulated from the fitted one-screen model, specifically at the delay predicted for a second screen.
- No measured error rate currently shows how often that predicted-delay test invents or misses a second screen.

**Evidence:**

- [Trigger calibration](docs/rse/specs/plan-a1-trigger-calibration.md) — `974ec606…`
- [Current circulation design](docs/rse/specs/plan-circulation-readiness.md) — `d2ae8ecc…`

**Effect:** The choice determines whether and when the analysis may fit a second scattering screen.

**Record:** `docs/rse/wayfinder/tickets/04a-close-residual-trigger.md` — Record the trigger decision and resolve this ticket.
