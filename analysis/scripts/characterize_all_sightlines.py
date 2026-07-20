import sys
import yaml
import pandas as pd
from pathlib import Path
from astropy.coordinates import SkyCoord
import astropy.units as u

# Add pipeline to python path so we can import packages if needed
sys.path.append(str(Path(__file__).resolve().parent.parent / "pipeline"))

from mwprop.nemod.NE2025 import ne2025

# Band centers (same as pipeline/scintillation/ne2025/query_ne2025_scint.py)
BAND_CENTERS_MHZ = {"CHIME": 600.19, "DSA": 1405.0}
FREQ_EXP = 4.4

def mw_scattering(l_deg, b_deg, dmax_kpc=30.0):
    Dk, Dv, Du, Dd = ne2025(
        ldeg=l_deg, bdeg=b_deg, dmd=dmax_kpc, ndir=-1, classic=False, dmd_only=False
    )
    return {
        "dm_mw": Dv["DM"],  # pc/cm^3, integrated to dmax
        "sm": Dv["SM"],  # kpc m^-20/3
        "tau_1ghz_ms": Dv["TAU"],  # ms @ 1 GHz
        "sbw_1ghz_mhz": Dv["SBW"],  # MHz @ 1 GHz
        "scintime_1ghz_s": Dv["SCINTIME"],  # s @ 1 GHz @ 100 km/s
        "theta_g_mas": Dv["THETA_G"],  # mas @ 1 GHz
        "d_eff_kpc": Dv["DEFFSM2"],  # effective MW screen distance
        "nu_t_ghz": Dv["NU_T"],  # transition frequency
    }

def scale_val(val_1ghz, freq_mhz, kind):
    freq_ghz = freq_mhz / 1000.0
    e = -FREQ_EXP if kind == "tau" else FREQ_EXP
    return val_1ghz * freq_ghz**e

# Load bursts catalog
cat_path = Path(__file__).resolve().parent.parent / "pipeline/configs/bursts.yaml"
bursts = yaml.safe_load(cat_path.read_text())["bursts"]

rows = []
for name, b in bursts.items():
    coord = SkyCoord(ra=b["ra_deg"] * u.deg, dec=b["dec_deg"] * u.deg, frame="icrs")
    gl = coord.galactic.l.value
    gb = coord.galactic.b.value
    p = mw_scattering(gl, gb)
    
    # Scale tau and sbw to CHIME and DSA
    tau_chime_us = scale_val(p["tau_1ghz_ms"], BAND_CENTERS_MHZ["CHIME"], "tau") * 1000.0
    sbw_chime_khz = scale_val(p["sbw_1ghz_mhz"], BAND_CENTERS_MHZ["CHIME"], "sbw") * 1000.0
    tau_dsa_us = scale_val(p["tau_1ghz_ms"], BAND_CENTERS_MHZ["DSA"], "tau") * 1000.0
    sbw_dsa_khz = scale_val(p["sbw_1ghz_mhz"], BAND_CENTERS_MHZ["DSA"], "sbw") * 1000.0
    
    row = {
        "burst": name,
        "ra_deg": b["ra_deg"],
        "dec_deg": b["dec_deg"],
        "l_deg": gl,
        "b_deg": gb,
        "dm_mw_pc_cm3": p["dm_mw"],
        "sm_kpc_m203": p["sm"],
        "d_eff_kpc": p["d_eff_kpc"],
        "theta_g_1ghz_mas": p["theta_g_mas"],
        "scintime_1ghz_s": p["scintime_1ghz_s"],
        "nu_t_ghz": p["nu_t_ghz"],
        "tau_1ghz_us": p["tau_1ghz_ms"] * 1000.0,
        "sbw_1ghz_mhz": p["sbw_1ghz_mhz"],
        "tau_chime_us": tau_chime_us,
        "sbw_chime_khz": sbw_chime_khz,
        "tau_dsa_us": tau_dsa_us,
        "sbw_dsa_khz": sbw_dsa_khz
    }
    rows.append(row)

df = pd.DataFrame(rows)
csv_out = Path(__file__).resolve().parent.parent / "data/ne2025_mw_properties.csv"
df.to_csv(csv_out, index=False)
print(f"Saved {len(df)} rows to {csv_out}")
