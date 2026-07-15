"""Per-sightline NE2025 vs NE2001 vs YMW16 disk-DM comparison (review S15).

Regenerates the summary statistics quoted in Section 2 (obs-mw): NE2001 and
YMW16 are evaluated with pygedm to 30 kpc at the twelve co-detection
positions and compared against the NE2025 disk columns adopted by the budget
(Table tab:budget DM_MW minus the 40 pc cm^-3 halo prior).

Run: conda run -n flits python scripts/mw_model_comparison.py
(pygedm's yt2020 module needs scipy<1.12's `simps`; a shim is applied.)
"""

from __future__ import annotations

import scipy.integrate as _si

if not hasattr(_si, "simps"):  # scipy >= 1.12 renamed simps -> simpson
    _si.simps = _si.simpson  # type: ignore[attr-defined]

import astropy.units as u
import pygedm
from astropy.coordinates import SkyCoord

# (TNS, RA, Dec, NE2025 disk column from tab:budget DM_MW - 40 halo prior)
SIGHTLINES = [
    ("FRB 20220207C", 310.1995, 72.8823, 71),
    ("FRB 20220310F", 134.7205, 73.4908, 41),
    ("FRB 20220506D", 318.0448, 72.8273, 78),
    ("FRB 20221113A", 71.4110, 70.3074, 83),
    ("FRB 20221203A", 315.1295, 72.0376, 77),
    ("FRB 20230307A", 177.7813, 71.6956, 34),
    ("FRB 20230325A", 88.1880, 74.2005, 60),
    ("FRB 20230814B", 335.9747, 73.0259, 97),
    ("FRB 20230913A", 305.0372, 70.7928, 70),
    ("FRB 20240122A", 39.7665, 71.0179, 93),
    ("FRB 20240203A", 312.6191, 73.9000, 71),
    ("FRB 20240229A", 169.9835, 70.6762, 34),
]

PLACEHOLDER_Z = {"FRB 20230325A", "FRB 20230814B", "FRB 20240122A"}


def main() -> None:
    print(f"{'burst':16s} {'NE2025':>7s} {'NE2001':>7s} {'YMW16':>7s} "
          f"{'dNE2001':>8s} {'dYMW16':>8s}")
    devs_ne, devs_yw = [], []
    for tns, ra, dec, ne2025 in SIGHTLINES:
        g = SkyCoord(ra * u.deg, dec * u.deg).galactic
        ne = pygedm.dist_to_dm(g.l.deg, g.b.deg, 30000, method="ne2001")[0].value
        yw = pygedm.dist_to_dm(g.l.deg, g.b.deg, 30000, method="ymw16")[0].value
        d_ne, d_yw = ne / ne2025 - 1, yw / ne2025 - 1
        if tns not in PLACEHOLDER_Z:
            devs_ne.append(abs(d_ne))
            devs_yw.append(abs(d_yw))
        print(f"{tns:16s} {ne2025:7.0f} {ne:7.1f} {yw:7.1f} "
              f"{d_ne:+8.0%} {d_yw:+8.0%}")
    print(f"\nz-constrained sightlines: max |NE2001-NE2025|/NE2025 = "
          f"{max(devs_ne):.0%}; max |YMW16-NE2025|/NE2025 = {max(devs_yw):.0%}")


if __name__ == "__main__":
    main()
