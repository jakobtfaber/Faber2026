#!/usr/bin/env python3
"""Cross-reference all 52 registered candidates + open search against expanded catalog library.

Catalogs queried:
- GSC 2.4.2 (I/353/gsc242) -> Star/Galaxy morphological class (Class 3=extended/galaxy, 4=starlike/star)
- ALLWISE (II/328/allwise) -> W1, W2 IR photometry
- CatWISE2020 (II/365/catwise) -> IR proper motion & high-precision IR photometry
- unWISE (II/363/unwise) -> Deep unWISE co-add fluxes
"""

import os
import sys
import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u
from astroquery.vizier import Vizier

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, REPO_ROOT)

REGISTRY_PATH = os.path.join(REPO_ROOT, "pipeline/galaxies/foreground/data/intervening_census_registry.csv")
BURSTS_PATH = os.path.join(REPO_ROOT, "pipeline/galaxies/foreground/data/frozen_census/bursts.csv")

def parse_registry():
    df = pd.read_csv(REGISTRY_PATH)
    return df

def parse_bursts():
    df = pd.read_csv(BURSTS_PATH)
    return df

def query_expanded_catalogs_for_candidate(ra_deg, dec_deg, match_radius_arcsec=3.0):
    coord = SkyCoord(ra_deg * u.deg, dec_deg * u.deg, frame="icrs")
    v = Vizier(columns=["*", "_r"])
    v.ROW_LIMIT = 5
    
    catalogs = {
        "gsc242": "I/353/gsc242",
        "allwise": "II/328/allwise",
        "catwise": "II/365/catwise",
        "unwise": "II/363/unwise",
    }
    
    out = {
        "gsc_class": None,
        "gsc_name": None,
        "allwise_w1": None,
        "allwise_w2": None,
        "catwise_name": None,
        "unwise_id": None,
    }
    
    for cat_key, cat_id in catalogs.items():
        try:
            res = v.query_region(coord, radius=match_radius_arcsec * u.arcsec, catalog=cat_id)
            if res and len(res) > 0:
                tbl = res[0]
                if len(tbl) > 0:
                    row = tbl[0]
                    if cat_key == "gsc242":
                        out["gsc_class"] = str(row["Class"]) if "Class" in row.colnames else None
                        out["gsc_name"] = str(row["GSC2"]) if "GSC2" in row.colnames else None
                    elif cat_key == "allwise":
                        out["allwise_w1"] = float(row["W1mag"]) if "W1mag" in row.colnames and not np.isnan(row["W1mag"]) else None
                        out["allwise_w2"] = float(row["W2mag"]) if "W2mag" in row.colnames and not np.isnan(row["W2mag"]) else None
                    elif cat_key == "catwise":
                        out["catwise_name"] = str(row["Name"]) if "Name" in row.colnames else None
                    elif cat_key == "unwise":
                        out["unwise_id"] = str(row["objID"]) if "objID" in row.colnames else None
        except Exception:
            pass
            
    return out

def main():
    print("================================================================================")
    print("Expanded Catalog Cross-Reference Sweep (GSC 2.4.2, ALLWISE, CatWISE2020, unWISE)")
    print("================================================================================\n")
    
    reg_df = parse_registry()
    print(f"Loaded {len(reg_df)} candidates from master intervening census registry.\n")
    
    results = []
    
    for idx, row in reg_df.iterrows():
        ra = row.get("ra_deg")
        dec = row.get("dec_deg")
        nick = row.get("nickname")
        obj_id = row.get("obj")
        verdict = row.get("final_verdict")
        
        if pd.isna(ra) or pd.isna(dec):
            continue
            
        matches = query_expanded_catalogs_for_candidate(float(ra), float(dec), match_radius_arcsec=3.0)
        
        # Interpret GSC Class: Class 0=star, 3=galaxy/extended, 4=starlike, 5=blend
        gsc_desc = "unmatched"
        if matches["gsc_class"] is not None:
            c = matches["gsc_class"]
            if c == "3":
                gsc_desc = "GALAXY/EXTENDED (Class 3)"
            elif c == "4":
                gsc_desc = "STARLIKE (Class 4)"
            else:
                gsc_desc = f"Class {c}"
                
        w1_w2_color = None
        if matches["allwise_w1"] is not None and matches["allwise_w2"] is not None:
            w1_w2_color = round(matches["allwise_w1"] - matches["allwise_w2"], 3)
            
        results.append({
            "idx": idx + 1,
            "nickname": nick,
            "obj": obj_id,
            "ra": ra,
            "dec": dec,
            "verdict": verdict,
            "gsc_class": gsc_desc,
            "allwise_w1": matches["allwise_w1"],
            "w1_w2_color": w1_w2_color,
            "catwise": matches["catwise_name"] is not None,
            "unwise": matches["unwise_id"] is not None,
        })
        
        if (idx + 1) % 10 == 0 or idx == len(reg_df) - 1:
            print(f"Processed {idx + 1}/{len(reg_df)} candidates...")

    res_df = pd.DataFrame(results)
    
    print("\nSummary of GSC 2.4.2 Morphological Classifications Across Census:")
    print(res_df["gsc_class"].value_counts().to_string())
    
    print("\nDetailed Candidate Sample Cross-References:")
    print(res_df[["idx", "nickname", "obj", "verdict", "gsc_class", "allwise_w1", "w1_w2_color"]].head(15).to_string())
    
    # Save full expanded cross-reference report to CSV
    out_csv = os.path.join(REPO_ROOT, "pipeline/galaxies/foreground/data/expanded_catalog_cross_references.csv")
    res_df.to_csv(out_csv, index=False)
    print(f"\nSaved full expanded catalog cross-reference table to: {out_csv}")
    print("================================================================================")

if __name__ == "__main__":
    main()
