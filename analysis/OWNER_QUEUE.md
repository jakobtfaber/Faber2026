# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`

_Only scientific and visual decisions. Silence leaves every item blocked._

## 1. Predicted-delay trigger operating point

**Decision:** Accept the 1 per cent false-escalation envelope (windowed residual statistic threshold 4.65) as the second-screen escalation operating point, restricted to the regimes where the calibration shows power, or reject the trigger?

**Recommended:** `accept-restricted` — At the 1 per cent envelope the rule reliably detects comparable-or-larger second screens while the false-escalation rate is measured, and the calibration proves the rule has no power for tau2 <= 0.3 tau1 — so acceptance must carry that restriction explicitly rather than implying general sensitivity; a resolved scintillation bandwidth implying a much smaller near-screen tau cannot be adjudicated by this trigger.

**Choose:**

- `accept-restricted` — Accept the 1 per cent envelope, valid only for r >= 1 second screens on matching CHIME-like geometry.
- `reject` — Reject the trigger; second-screen escalation remains unavailable.
- `recalibrate` — Request a modified campaign (different grids, geometry, or statistic) before deciding.

**Context:**

- False-escalation envelopes (max over 15 null cells, 200 injections each): statistic 4.70 / 4.65 / 3.94 at 0.5 / 1 / 5 per cent.
- Detection at the 1 per cent envelope: 97.5-100 per cent for r >= 1 at S/N 30, 65 per cent for r = 3 at S/N 15, and exactly zero for r <= 0.3 at every S/N.
- The 30-injection nested-sampling anchor shows the ML surrogate is faithful (mean |delta p| = 0.0003); validity is restricted to single-component morphology and CHIME-like geometry.

**Evidence:**

- [Calibration report](simulation/experiments/predicted-delay-trigger/calibration.md) — `a3fc6eb4…`
- [Machine-readable rate table](simulation/experiments/predicted-delay-trigger/calibration.json) — `440ffb1b…`
- [Nested-sampling anchor pairs](simulation/experiments/predicted-delay-trigger/anchor.json) — `f18438bc…`

**Effect:** Sets whether and when a second scattering screen may be fitted, closing the reopened escalation-trigger element of the D4 coupling design.

**Record:** `docs/rse/wayfinder/tickets/04-close-scint-scattering-coupling-design.md` — Record the operating-point decision in this ticket and resolve it.
