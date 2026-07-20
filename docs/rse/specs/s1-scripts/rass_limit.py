import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

POS = SkyCoord("11h51m20.4s", "+71d44m35s")
Z, R500_KPC = 0.200, 727.0   # R500 from b=603.6 kpc at b/R500=0.83

# --- 1RXS sources near position: detection check + local exposure ---
from astroquery.vizier import Vizier
v = Vizier(columns=["1RXS","RAJ2000","DEJ2000","Count","e_Count","ExpTime","_r"], row_limit=200)
near = v.query_region(POS, radius=2.0*u.deg, catalog="IX/10A/1rxs")  # RASS BSC
fsc  = v.query_region(POS, radius=2.0*u.deg, catalog="IX/29/rass_fsc")
rows = []
for tabs, name in ((near,"BSC"),(fsc,"FSC")):
    if tabs:
        t = tabs[0].to_pandas()
        t["cat"] = name
        rows.append(t)
import pandas as pd
src = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
if not src.empty:
    src = src.sort_values("_r")
    close = src[src._r < 6/60.0]  # within theta500-ish (6')
    print(f"1RXS sources <6' of cluster: {len(close)}")
    if len(close): print(close[["cat","_r","Count","ExpTime"]].to_string())
    exp_local = np.median(src.head(10).ExpTime.dropna())
    print(f"local RASS exposure (median of 10 nearest srcs within 2deg): {exp_local:.0f} s")
else:
    raise SystemExit("no 1RXS neighbours found; cannot estimate exposure")

# --- RASS broad-band counts cutout + aperture UL ---
from astroquery.skyview import SkyView
imgs = SkyView.get_images(position=POS, survey=["RASS-Cnt Broad"], radius=1.0*u.deg)
hdu = imgs[0][0]
from astropy.wcs import WCS
w = WCS(hdu.header)
data = hdu.data
ny, nx = data.shape
yy, xx = np.mgrid[:ny, :nx]
sc = w.pixel_to_world(xx, yy)
sep = POS.separation(sc).arcmin
pixscale_amin = abs(hdu.header["CDELT2"]) * 60.0
theta500 = np.degrees(R500_KPC / 700e3) * 60  # D_A(0.2)~700 Mpc -> arcmin
ap  = sep <= theta500
bkg = (sep > 2*theta500) & (sep < 4*theta500)
n_ap = ap.sum()
c_ap = float(data[ap].sum())
b_rate_pix = float(np.mean(data[bkg]))
b_in_ap = b_rate_pix * n_ap
excess = c_ap - b_in_ap
# 3-sigma UL on counts (Gaussian on background-subtracted aperture counts)
sigma = np.sqrt(max(c_ap, b_in_ap) + b_in_ap*(n_ap/ bkg.sum()))
ul_counts = max(excess, 0) + 3*sigma
rate_ul = ul_counts / exp_local
print(f"theta500={theta500:.2f}' pix={pixscale_amin:.2f}' n_ap={n_ap}")
print(f"aperture counts={c_ap:.1f} bkg-in-ap={b_in_ap:.1f} excess={excess:.1f}")
print(f"3sig count UL={ul_counts:.1f}  rate UL={rate_ul:.4f} ct/s")

# --- rate -> flux -> L_X ---
ECF = 1.0e-11  # (erg/cm2/s)/(ct/s), PSPC 0.1-2.4 keV, T~2keV, NH~1.3e20; +/-20%
flux_ul = rate_ul * ECF
from astropy.cosmology import FlatLambdaCDM
cosmo = FlatLambdaCDM(H0=70, Om0=0.3)
DL = cosmo.luminosity_distance(Z).to(u.cm).value
LX_ul = 4*np.pi*DL**2 * flux_ul
print(f"flux UL = {flux_ul:.3e} erg/cm2/s   L_X(<2.4keV) UL = {LX_ul:.3e} erg/s")

# --- MCXC L-M mapping recovered by regression (round-trip gate) ---
vm = Vizier(columns=["MCXC","z","L500","M500"], row_limit=-1)
mc = vm.query_constraints(catalog="J/A+A/534/A109/mcxc")[0].to_pandas().dropna(subset=["L500","M500","z"])
# MCXC computed M500 from L500 via REXCESS L-M; recover mapping incl. E(z):
Ez = cosmo.efunc(mc.z.values)
X = np.log10(mc.L500.values/Ez**(7/3))       # L in 1e37 W = 1e44 erg/s
Y = np.log10(mc.M500.values/Ez**(2/5)) if False else np.log10(mc.M500.values)
# fit: log10(M500/E^a) = A + B*log10(L500/E^7/3); standard MCXC: M ∝ E^-2/5 [L/E^7/3]^(1/1.64)
Ym = np.log10(mc.M500.values*Ez**(2/5))
B, A = np.polyfit(X, Ym, 1)
pred = 10**(A + B*X)/Ez**(2/5)
frac = np.abs(pred - mc.M500.values)/mc.M500.values
print(f"MCXC L-M regression: slope={B:.3f} intercept={A:.3f} round-trip median|err|={np.median(frac)*100:.1f}% p95={np.percentile(frac,95)*100:.1f}%")
LX_1e44 = LX_ul/1e44
Ez02 = cosmo.efunc(Z)
M_ul = 10**(A + B*np.log10(LX_1e44/Ez02**(7/3)))/Ez02**(2/5)   # in 1e14 Msun
print(f"M500_UL_Xray = {M_ul:.3f} x1e14 Msun  (log10 = {14+np.log10(M_ul):.3f})")
np.save("psz2_placeholder.npy", [0])
