import numpy as np, sys
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.vizier import Vizier
POS = SkyCoord("11h51m20.4s", "+71d44m35s")

# exposure spread + local detection floor from FSC/BSC neighbours
v = Vizier(columns=["RAJ2000","DEJ2000","Count","e_Count","ExpTime","_r"], row_limit=500)
out = {}
for cat,label in (("IX/10A/1rxs","BSC"),("IX/29/rass_fsc","FSC")):
    t = v.query_region(POS, radius=3.0*u.deg, catalog=cat)
    if t:
        d = t[0].to_pandas().dropna(subset=["Count","ExpTime"])
        d = d.sort_values("_r")
        out[label] = d
        print(f"{label}: n(<3deg)={len(d)}  ExpTime p10/p50/p90 = "
              f"{np.percentile(d.ExpTime,10):.0f}/{np.percentile(d.ExpTime,50):.0f}/{np.percentile(d.ExpTime,90):.0f} s  "
              f"min detected rate = {d.Count.min():.4f} ct/s")
fsc = out["FSC"]
floor_rate = float(np.percentile(fsc.Count, 5))
exp_p10 = float(np.percentile(fsc.ExpTime, 10))
print(f"adopted local detection-floor rate (FSC p5): {floor_rate:.4f} ct/s ; conservative exposure (p10): {exp_p10:.0f} s")

# conservative rate UL: max(aperture UL @ p10 exposure, FSC floor)
UL_COUNTS_3SIG = 45.5
rate_ul_cons = max(UL_COUNTS_3SIG/exp_p10, floor_rate)
print(f"conservative rate UL = {rate_ul_cons:.4f} ct/s")

from astropy.cosmology import FlatLambdaCDM
cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
Z = 0.200
DL = cosmo.luminosity_distance(Z).to(u.cm).value
for ecf in (0.8e-11, 1.0e-11, 1.2e-11):
    LX = 4*np.pi*DL**2 * rate_ul_cons*ecf
    Ez = cosmo.efunc(Z)
    A,B = 0.328, 0.619
    M = 10**(A + B*np.log10((LX/1e44)/Ez**(7/3)))/Ez**(2/5)
    print(f"ECF={ecf:.1e}: L_X UL={LX:.2e}  M500_UL={M:.3f}e14 (log={14+np.log10(M):.3f})")

# ---- Phase 3: DM propagation ----
sys.path.insert(0, "/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline")
from galaxies.foreground.scattering_predict import dm_cluster_mnfw_model
dm_central = dm_cluster_mnfw_model(m500_msun=10**14.1, z=Z, impact_kpc=603.6)
print(f"regression anchor: DM(logM=14.1) = {dm_central:.1f} pc/cm3 (carried: ~184)")
# worst-case (most permissive) M_UL across ECF band and conservative rate:
M_worst = 10**(0.328 + 0.619*np.log10((4*np.pi*DL**2*rate_ul_cons*1.2e-11/1e44)/cosmo.efunc(Z)**(7/3)))/cosmo.efunc(Z)**(2/5)
for label, m14 in (("M_UL(ECF=1.0)", 10**(0.328+0.619*np.log10((4*np.pi*DL**2*rate_ul_cons*1.0e-11/1e44)/cosmo.efunc(Z)**(7/3)))/cosmo.efunc(Z)**(2/5)),
                   ("M_UL worst-case(ECF=1.2)", M_worst)):
    dm_ul = dm_cluster_mnfw_model(m500_msun=m14*1e14, z=Z, impact_kpc=603.6)
    print(f"{label}: {m14:.3f}e14 -> DM_mNFW(M_UL) = {dm_ul:.1f} pc/cm3")
