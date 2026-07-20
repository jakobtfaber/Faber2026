# Documented Expanded Foreground Photometry, Morphology & Virial Radius Catalog

**Manuscript:** Faber2026
**Generated:** July 20, 2026
**Primary Catalogs Queried:** Guide Star Catalog 2.4.2 (`I/353/gsc242`), ALLWISE (`II/328/allwise`), CatWISE2020 (`II/365/catwise`), unWISE (`II/363/unwise`)

--- 

## 1. Methodology & Estimator Formulas

1. **GSC 2.4.2 Morphological Classification (`gsc242_morphology_class`):**
   - Official ReadMe definitions: `Class 0` (Star), `Class 1` (Galaxy), `Class 2` (Blend), `Class 3` (Non-star), `Class 4` (Unclassified), `Class 5` (Defect).
2. **Mid-IR Stellar Mass (\log_{10} M_*/\mathrm{M}_\odot):**
   - Derived using Cluver et al. (2014) Eq. 2 color-dependent $W1\text{--}W2$ mass-to-light relation:
     $$\log_{10}(M_*/\mathrm{M}_\odot) = \log_{10}(L_{W1}/\mathrm{L}_\odot) - 2.54 \times (W1 - W2) - 0.17$$
3. **Halo Mass & Virial Radius ($R_{\mathrm{vir}}$):**
   - Moster et al. (2013) SHMR inverted via `generate_galaxy_plots.estimate_halo_mass` + Dutton & Macciò (2014) $c\text{--}M$ relation via `generate_galaxy_plots.get_rvir_and_rs`.
4. **AGN Contamination Check:**
   - Stern et al. (2012) mid-IR color threshold ($W1 - W2 \ge 0.8\,\mathrm{mag}$ alert vs $W1 - W2 < 0.8\,\mathrm{mag}$ starlight-dominated pass; missing color labeled `NO COLOR DATA`).

--- 

## 2. Complete Candidate Master Inventory

| # | FRB | Object ID | Type | Verdict | GSC Morphology | $W1$ (mag) | $W1-W2$ | AGN Check | $\log M_*$ | $R_{\mathrm{vir}}$ (kpc) | $b/R_{\mathrm{vir}}$ | Catalog Provenance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | zach | 195373100910393540 | halo | inconclusive | Class 4 (Unclassified) | 18.04 | 0.27 | PASS (Starlight-dominated) | 10.08 | 2607.3 | 0.03 | GSC2.4.2 ID=N1IB037588; ALLWISE II/328/allwise; CatWISE2020 J204022.10+724838.1; unWISE 3113p726o0025112 |
| 2 | whitney | 1472 | halo | refuted | Class 3 (Non-star) | 16.73 | -0.10 | PASS (Starlight-dominated) | 11.73 | 2518.8 | 0.04 | GSC2.4.2 ID=N7UO023653; ALLWISE II/328/allwise; CatWISE2020 J085856.60+732928.0; unWISE 1323p742o0001571 |
| 3 | whitney | 1473 | halo | confirmed | unmatched | \nodata | \nodata | NO COLOR DATA | \nodata | \nodata | \nodata | Catalog Matched |
| 4 | whitney | 1582 | halo | inconclusive | unmatched | 17.65 | 0.27 | PASS (Starlight-dominated) | 10.24 | 2605.4 | 0.07 | ALLWISE II/328/allwise; CatWISE2020 J085854.81+732954.4; unWISE 1323p742o0040961 |
| 5 | whitney | 196191347354360083 | halo | refuted | Class 3 (Non-star) | 16.73 | -0.10 | PASS (Starlight-dominated) | 11.73 | 2518.8 | 0.04 | GSC2.4.2 ID=N7UO023653; ALLWISE II/328/allwise; CatWISE2020 J085856.60+732928.0; unWISE 1323p742o0001571 |
| 6 | whitney | J085546.0+732230, 1160094 | cluster | confirmed | Class 0 (Star) | 13.71 | 0.22 | PASS (Starlight-dominated) | 10.66 | 2969.1 | 0.69 | GSC2.4.2 ID=N7TS005319; ALLWISE II/328/allwise; CatWISE2020 J085546.14+732227.9; unWISE 1313p726o0027983 |
| 7 | whitney | J085531.9+732432, 1159975 | cluster | confirmed | Class 3 (Non-star) | 14.86 | 0.25 | PASS (Starlight-dominated) | 11.24 | 2678.0 | 1.95 | GSC2.4.2 ID=N7TS009034; ALLWISE II/328/allwise; CatWISE2020 J085531.74+732431.8; unWISE 1313p726o0028699 |
| 8 | whitney | J085808.2+731234, 1161367 | cluster | confirmed | Class 3 (Non-star) | 15.20 | 0.09 | PASS (Starlight-dominated) | 11.08 | 2832.6 | 2.01 | GSC2.4.2 ID=N7UO006290; ALLWISE II/328/allwise; CatWISE2020 J085807.94+731232.2; unWISE 1362p726o0024398 |
| 9 | oran | 195393180643665627 | halo | inconclusive | Class 4 (Unclassified) | 16.20 | 0.34 | PASS (Starlight-dominated) | 10.19 | 2786.4 | 0.03 | GSC2.4.2 ID=N1G0052835; ALLWISE II/328/allwise; CatWISE2020 J211215.65+724943.8; unWISE 3162p726o0026810 |
| 10 | wilhelm | 194453151328186646 | halo | inconclusive | Class 3 (Non-star) | 16.80 | 0.17 | PASS (Starlight-dominated) | 10.93 | 2565.1 | 0.09 | GSC2.4.2 ID=N1J7038830; ALLWISE II/328/allwise; CatWISE2020 J210031.90+720247.7; unWISE 3162p726o0004000 |
| 11 | phineas | 832 | halo | confirmed | Class 3 (Non-star) | 16.80 | 0.39 | PASS (Starlight-dominated) | 9.39 | 2901.3 | 0.05 | GSC2.4.2 ID=N77R002453; ALLWISE II/328/allwise; CatWISE2020 J115103.25+714105.2; unWISE 1755p711o0027955 |
| 12 | phineas | 953 | halo | confirmed | Class 3 (Non-star) | 16.23 | 0.48 | PASS (Starlight-dominated) | 9.43 | 2894.3 | 0.08 | GSC2.4.2 ID=N77R002501; ALLWISE II/328/allwise; CatWISE2020 J115119.51+714136.0; unWISE 1755p711o0028153 |
| 13 | phineas | 983 | halo | confirmed | Class 3 (Non-star) | 17.97 | 0.22 | PASS (Starlight-dominated) | 9.21 | 2930.3 | 0.04 | GSC2.4.2 ID=N77R018963; ALLWISE II/328/allwise; CatWISE2020 J115115.99+714142.1; unWISE 1755p711o0082843 |
| 14 | phineas | 986 | halo | inconclusive | Class 3 (Non-star) | 17.89 | 0.79 | PASS (Starlight-dominated) | 8.00 | 2884.7 | 0.07 | GSC2.4.2 ID=N77R002535; ALLWISE II/328/allwise; CatWISE2020 J115055.43+714143.0; unWISE 1755p711o0028162 |
| 15 | phineas | 1072 | halo | inconclusive | Class 3 (Non-star) | \nodata | \nodata | NO COLOR DATA | \nodata | \nodata | \nodata | GSC2.4.2 ID=N77R028742; CatWISE2020 J115104.76+714200.9; unWISE 1755p711o0056823 |
| 16 | phineas | 1153 | halo | confirmed | Class 3 (Non-star) | 16.04 | 0.32 | PASS (Starlight-dominated) | 9.98 | 2877.9 | 0.05 | GSC2.4.2 ID=N77R002597; ALLWISE II/328/allwise; CatWISE2020 J115106.75+714220.0; unWISE 1755p711o0028408 |
| 17 | phineas | 1190 | halo | confirmed | Class 0 (Star) | 15.72 | 0.23 | PASS (Starlight-dominated) | 9.68 | 2987.7 | 0.04 | GSC2.4.2 ID=N77R002619; ALLWISE II/328/allwise; CatWISE2020 J115107.54+714235.7; unWISE 1755p711o0028499 |
| 18 | phineas | 194021777634832653 | halo | confirmed | Class 3 (Non-star) | 16.80 | 0.39 | PASS (Starlight-dominated) | 9.39 | 2901.3 | 0.05 | GSC2.4.2 ID=N77R002453; ALLWISE II/328/allwise; CatWISE2020 J115103.25+714105.2; unWISE 1755p711o0027955 |
| 19 | phineas | 194031778315722893 | halo | refuted | Class 3 (Non-star) | \nodata | \nodata | NO COLOR DATA | \nodata | \nodata | \nodata | GSC2.4.2 ID=N77R026264 |
| 20 | phineas | 194041777780157594 | halo | confirmed | Class 3 (Non-star) | 16.04 | 0.32 | PASS (Starlight-dominated) | 9.98 | 2877.9 | 0.04 | GSC2.4.2 ID=N77R002597; ALLWISE II/328/allwise; CatWISE2020 J115106.75+714220.0; unWISE 1755p711o0028408 |
| 21 | phineas | 194051777813062524 | halo | confirmed | Class 0 (Star) | 15.72 | 0.23 | PASS (Starlight-dominated) | 9.68 | 2987.7 | 0.03 | GSC2.4.2 ID=N77R002619; ALLWISE II/328/allwise; CatWISE2020 J115107.54+714235.7; unWISE 1755p711o0028499 |
| 22 | phineas | J115120.4+714435, 1254337 | cluster | confirmed | Class 3 (Non-star) | 13.76 | 0.28 | PASS (Starlight-dominated) | 10.91 | 2893.4 | 0.21 | GSC2.4.2 ID=N77R002800; ALLWISE II/328/allwise; CatWISE2020 J115120.36+714433.5; unWISE 1755p711o0029262 |
| 23 | phineas | J115128.2+713637, 1254415 | cluster | confirmed | Class 3 (Non-star) | 13.41 | 0.22 | PASS (Starlight-dominated) | 11.18 | 2902.2 | 0.36 | GSC2.4.2 ID=N77Q004575; ALLWISE II/328/allwise; CatWISE2020 J115128.25+713636.8; unWISE 1755p711o0026264 |
| 24 | phineas | J114944.0+714348, 1253496 | cluster | confirmed | Class 3 (Non-star) | 14.30 | 0.34 | PASS (Starlight-dominated) | 10.75 | 2846.7 | 0.55 | GSC2.4.2 ID=N77R002778; ALLWISE II/328/allwise; CatWISE2020 J114943.75+714347.0; unWISE 1755p711o0028857 |
| 25 | phineas | J115140.5+712732, 1254506 | cluster | confirmed | Class 0 (Star) | 13.27 | 0.23 | PASS (Starlight-dominated) | 11.11 | 2918.9 | 0.72 | GSC2.4.2 ID=N77Q003429; ALLWISE II/328/allwise; CatWISE2020 J115140.42+712732.0; unWISE 1755p711o0054519 |
| 26 | phineas | J115400.9+713320, 1255773 | cluster | confirmed | Class 3 (Non-star) | 13.80 | 0.25 | PASS (Starlight-dominated) | 10.74 | 2940.8 | 1.04 | GSC2.4.2 ID=N77Q004040; ALLWISE II/328/allwise; CatWISE2020 J115400.57+713319.4; unWISE 1800p711o0024085 |
| 27 | phineas | J115031.4+715735, 1253898 | cluster | confirmed | Class 3 (Non-star) | 14.40 | 0.21 | PASS (Starlight-dominated) | 11.15 | 2819.4 | 1.52 | GSC2.4.2 ID=N77R003886; ALLWISE II/328/allwise; CatWISE2020 J115031.00+715734.4; unWISE 1751p726o0001449 |
| 28 | phineas | J115436.9+713930, 1256077 | cluster | confirmed | Class 3 (Non-star) | 14.72 | 0.25 | PASS (Starlight-dominated) | 10.88 | 2826.6 | 1.41 | GSC2.4.2 ID=N77Q004772; ALLWISE II/328/allwise; CatWISE2020 J115437.01+713929.3; unWISE 1800p711o0026286 |
| 29 | phineas | J114928.5+712526, 1253366 | cluster | confirmed | Class 0 (Star) | 13.57 | 0.19 | PASS (Starlight-dominated) | \nodata | \nodata | \nodata | GSC2.4.2 ID=N77Q003303; ALLWISE II/328/allwise; CatWISE2020 J114928.54+712526.4; unWISE 1755p711o0022147 |
| 30 | freya | 197030881733398302 | halo | inconclusive | Class 0 (Star) | 15.36 | 0.42 | PASS (Starlight-dominated) | 10.34 | 2781.9 | 0.02 | GSC2.4.2 ID=NAE0006013; ALLWISE II/328/allwise; CatWISE2020 J055241.48+741152.1; unWISE 0900p742o0016394 |
| 31 | freya | 197040882212782495 | halo | inconclusive | Class 3 (Non-star) | 16.02 | -0.54 | PASS (Starlight-dominated) | 13.25 | 2455.8 | 0.10 | GSC2.4.2 ID=NAE0023085; ALLWISE II/328/allwise; CatWISE2020 J055253.08+741205.0; unWISE 0900p742o0016471 |
| 32 | hamilton | 192943050854547067 | halo | inconclusive | Class 3 (Non-star) | 15.90 | 0.59 | PASS (Starlight-dominated) | 9.68 | 2784.4 | 0.08 | GSC2.4.2 ID=N1IH008858; ALLWISE II/328/allwise; CatWISE2020 J202020.49+704718.9; unWISE 3060p711o0045548 |
| 33 | hamilton | 192963050359413614 | halo | inconclusive | Class 3 (Non-star) | 15.97 | 0.59 | PASS (Starlight-dominated) | 9.68 | 2778.5 | 0.05 | GSC2.4.2 ID=N1IH009163; ALLWISE II/328/allwise; CatWISE2020 J202008.70+704808.5; unWISE 3060p711o0011361 |
| 34 | chromatica | 196673126794497004 | halo | inconclusive | Class 4 (Unclassified) | 17.06 | 0.27 | PASS (Starlight-dominated) | 8.69 | 3024.0 | 0.04 | GSC2.4.2 ID=N0UO030752; ALLWISE II/328/allwise; CatWISE2020 J205043.12+735348.5; unWISE 3123p742o0012945 |
| 35 | chromatica | 196723126173351736 | halo | inconclusive | Class 0 (Star) | 16.71 | 0.01 | PASS (Starlight-dominated) | 11.30 | 2601.4 | 0.04 | GSC2.4.2 ID=N0UO004308; ALLWISE II/328/allwise; CatWISE2020 J205028.16+735604.0; unWISE 3123p742o0013997 |
| 36 | chromatica | 196733128040225775 | halo | confirmed | Class 0 (Star) | 13.35 | 0.17 | PASS (Starlight-dominated) | 10.14 | 3043.8 | 0.07 | GSC2.4.2 ID=N0UO004450; ALLWISE II/328/allwise; CatWISE2020 J205112.96+735644.9; unWISE 3123p742o0014323 |
| 37 | casey | 192821699728654764 | halo | refuted | Class 3 (Non-star) | 16.18 | 0.00 | PASS (Starlight-dominated) | 11.28 | 2707.3 | 0.08 | GSC2.4.2 ID=N77T001639; ALLWISE II/328/allwise; CatWISE2020 J111953.44+704112.4; unWISE 1710p711o0006066 |
| 38 | casey | 192821700026167542 | halo | confirmed | Class 0 (Star) | 15.03 | 0.33 | PASS (Starlight-dominated) | 10.29 | 2890.4 | 0.06 | GSC2.4.2 ID=N77T001648; ALLWISE II/328/allwise; CatWISE2020 J112000.47+704119.7; unWISE 1710p711o0006111 |
| 39 | casey | 192831699797402822 | halo | confirmed | Class 0 (Star) | 15.48 | 0.33 | PASS (Starlight-dominated) | 10.30 | 2851.1 | 0.08 | GSC2.4.2 ID=N77T001679; ALLWISE II/328/allwise; CatWISE2020 J111955.15+704136.1; unWISE 1710p711o0006206 |
| 40 | casey | 660 | halo | refuted | Class 3 (Non-star) | 16.98 | 0.52 | PASS (Starlight-dominated) | 9.64 | 2709.4 | 0.00 | GSC2.4.2 ID=N77T022725; ALLWISE II/328/allwise; CatWISE2020 J111956.49+704034.8; unWISE 1710p711o0005834 |
| 41 | casey | 795 | halo | refuted | Class 3 (Non-star) | 16.18 | 0.00 | PASS (Starlight-dominated) | 11.28 | 2707.3 | 0.08 | GSC2.4.2 ID=N77T001639; ALLWISE II/328/allwise; CatWISE2020 J111953.44+704112.4; unWISE 1710p711o0006066 |
| 42 | casey | 796 | halo | refuted | unmatched | \nodata | \nodata | NO COLOR DATA | \nodata | \nodata | \nodata | CatWISE2020 J111954.72+704110.4 |
| 43 | casey | 827 | halo | confirmed | Class 0 (Star) | 15.48 | 0.33 | PASS (Starlight-dominated) | 10.30 | 2851.1 | 0.08 | GSC2.4.2 ID=N77T001679; ALLWISE II/328/allwise; CatWISE2020 J111955.15+704136.1; unWISE 1710p711o0006206 |
| 44 | casey | 824 | halo | confirmed | Class 0 (Star) | 15.03 | 0.33 | PASS (Starlight-dominated) | 10.29 | 2890.4 | 0.06 | GSC2.4.2 ID=N77T001648; ALLWISE II/328/allwise; CatWISE2020 J112000.47+704119.7; unWISE 1710p711o0006111 |
| 45 | casey | 825 | halo | inconclusive | unmatched | \nodata | \nodata | NO COLOR DATA | \nodata | \nodata | \nodata | Catalog Matched |
| 46 | casey | J111929.5+705441, 1237905 | cluster | confirmed | Class 0 (Star) | 13.91 | 0.32 | PASS (Starlight-dominated) | 10.85 | 2876.2 | 1.09 | GSC2.4.2 ID=N77T002980; ALLWISE II/328/allwise; CatWISE2020 J111929.65+705438.1; unWISE 1710p711o0010964 |
| 47 | casey | J112235.5+705438, 1239515 | cluster | confirmed | Class 3 (Non-star) | 14.65 | 0.36 | PASS (Starlight-dominated) | 10.42 | 2876.6 | 1.49 | GSC2.4.2 ID=N77T002984; ALLWISE II/328/allwise; CatWISE2020 J112235.45+705437.6; unWISE 1710p711o0010878 |
| 48 | casey | J112350.9+704142, 1240175 | cluster | confirmed | Class 3 (Non-star) | 13.97 | 0.30 | PASS (Starlight-dominated) | 10.84 | 2879.3 | 1.48 | GSC2.4.2 ID=N77T001731; ALLWISE II/328/allwise; CatWISE2020 J112350.62+704142.0; unWISE 1710p711o0006166 |
| 49 | casey | J111930.9+702041, 1237924 | cluster | confirmed | Class 3 (Non-star) | 14.19 | 0.27 | PASS (Starlight-dominated) | 10.04 | 3007.1 | 1.27 | GSC2.4.2 ID=N7RA003713; ALLWISE II/328/allwise; CatWISE2020 J111931.04+702039.3; unWISE 1716p696o0029328 |
| 50 | isha | WISEA J044538.83+701843.3 | halo | inconclusive | Class 0 (Star) | 15.10 | 0.16 | PASS (Starlight-dominated) | 10.91 | 2839.8 | 0.01 | GSC2.4.2 ID=NAYJ000955; ALLWISE II/328/allwise; CatWISE2020 J044538.86+701843.2; unWISE 0711p696o0036881 |
| 51 | oran | WISEA J211150.32+724807.8 | halo | inconclusive | Class 3 (Non-star) | 13.06 | 0.16 | PASS (Starlight-dominated) | 11.91 | 2786.4 | 0.07 | GSC2.4.2 ID=N1G0001534; ALLWISE II/328/allwise; CatWISE2020 J211150.75+724806.8; unWISE 3162p726o0026023 |
| 52 | phineas | WHL J115048.0+714428 | cluster | confirmed | Class 0 (Star) | 13.85 | 0.35 | PASS (Starlight-dominated) | 10.65 | 2904.7 | 0.21 | GSC2.4.2 ID=N77R002803; ALLWISE II/328/allwise; CatWISE2020 J115048.40+714428.0; unWISE 1755p711o0029178 |
