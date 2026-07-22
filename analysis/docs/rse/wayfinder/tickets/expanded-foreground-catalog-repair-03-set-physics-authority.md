# Set the stellar-mass, halo-mass, and radius authority

- Type: `wayfinder:task` (AFK)
- Status: resolved
- Assignee: —
- Blocked by: none
- Map: [Expanded foreground catalog repair](../map-expanded-foreground-catalog-repair.md)
- Delegation: [Standing delegated decision authority](../standing-delegation-2026-07-20.md)
- Triage: `resolved`

## Question

Which measurements govern each object type, and when must a derived mass or
radius remain null rather than be produced from an inapplicable relation?

## Acceptance decision

The adjudicated census table and overrides govern adopted galaxy stellar mass.
Recompute halo `M200c` with the redshift-dependent Moster relation and `R200c`
from `M200c` and critical density; do not reuse its known-bad legacy radius
columns. A fresh Cluver value is diagnostic only and remains null unless
rest-frame W1-W2, valid photometric flags, and uncertainties are available.
Cluster rows retain their catalog `M500` and `R500`; any `M200c` conversion must
name and test a separate cluster model. Unknown uncertainty stays null with an
explicit status. No numerical fallback is allowed.

## Resolution

Resolved 2026-07-22 under the
[standing delegated decision authority](../standing-delegation-2026-07-20.md),
strictly after the prerequisite
[crossmatch contract](expanded-foreground-catalog-repair-02-set-crossmatch-contract.md)
was reverified and resolved. This resolution accepts the physics authority
already implemented by
[dsa110-FLITS PR #213](https://github.com/jakobtfaber/dsa110-FLITS/pull/213).
It does not recalculate or change any scientific value.

Acceptance evidence:

- This away-from-keyboard ticket was open at the delegation scope anchor,
  parent commit `33e9e1ce357073c78f6a4aaf7138b3e03e9c87da`; the 2026-07-22
  amendment permits resolution after its blocker and acceptance checks pass.
- PR #213 merged as `3e466c1a180fb169ad09845312348cf539b82632` on
  2026-07-21. Current pipeline `origin/main`,
  `f3c8d22a9088914e0179cfecf1ee4086777dc927`, contains that merge. The
  physics implementation and focused tests are unchanged since the merge.
- The builder takes the adopted census mass and overrides, converts logarithmic
  stellar mass to linear solar mass at the named interface, applies the
  redshift-dependent Moster relation, and derives `R200c` from Planck18 critical
  density. Tests independently check the published Moster reference case and
  the enclosed-mass identity.
- Fresh Cluver mass remains diagnostic and null without rest-frame color,
  valid photometry, and uncertainties. Unknown adopted-mass uncertainty stays
  null with an explicit `pass_uncertainty_unavailable` status. There is no
  numerical fallback.
- Cluster rows retain catalog `M500` and `R500`; galaxy `M200c` and `R200c`
  fields stay null for clusters unless a separately named conversion model is
  introduced and tested.
- In the same clean isolated checkout, `conda run -n flits python -m pytest
  galaxies/foreground/test_expanded_catalog.py -q` passed: 13 tests. The
  offline catalog rebuild reproduced the tracked catalog and manifest bytes
  with no diff.
