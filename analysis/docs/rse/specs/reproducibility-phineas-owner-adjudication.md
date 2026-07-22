# Independent validation: Phineas owner adjudication

Date: 2026-07-22

Pipeline commit tested: `4e951c8acd6f0e221058d86ed97bb52b9d8c8597`

Analysis record: `6c2c41f`

## Verdict

The owner-approved implementation is understood and its deterministic arithmetic
is valid under its adopted point inputs. A clean-room implementation reproduces
the rounded intervening dispersion measure: `243.2445 -> 243 pc cm^-3`.

The scientific point verdict is **not independently valid as a frozen result**.
The raw photometry required to reproduce the adopted stellar masses is absent;
the calculation uses the redshift-zero rather than redshift-dependent Moster et
al. (2013) relation; and the hard virial-crossing decisions omit mass-relation,
stellar-mass, and photometric-redshift uncertainty. Keep the Wayfinder ticket
open. Use a probabilistic crossing model before freezing the Phineas foreground
or host-dispersion headline.

## How the approved result was obtained

1. Select eight confirmed, budget-eligible Phineas halo catalog rows.
2. Remove three sub-0.02-arcsecond cross-catalog duplicate pairs, leaving five
   physical halos.
3. Keep the catalog-resolvable identifier from each pair.
4. Replace heterogeneous listed impact parameters with separations calculated
   from the frozen burst, object coordinates, and adopted redshift.
5. Read the adjudicated stellar masses from `halo_rvir_ADJUDICATED.csv`.
6. Invert the redshift-zero Moster stellar-to-halo relation and calculate
   `R200c` from the Planck 2018 cosmology.
7. Set the halo column to zero outside the modified-NFW truncation radius.
8. Add one cluster using `M200 = 1.3 M500` and the same modified-NFW gas model.

The calculation did not use the heterogeneous `122/159 kpc` listed values in
the original ticket. Uniform geometry gives `115.731 kpc` for object 983 and
`144.437 kpc` for the canonical object paired with 832.

## Independent result

The validator uses only the Python standard library. It imports no pipeline,
Astropy, SciPy, NumPy, or Pandas code.

| Physical halo | b (kpc) | log10 M200 | R200c (kpc) | b/R200c | Crosses | Hot + cool DM |
|---|---:|---:|---:|---:|---|---:|
| 953 | 194.259 | 11.555 | 140.170 | 1.386 | no | 0.000 |
| 983 | 115.731 | 10.973 | 90.733 | 1.276 | no | 0.000 |
| 832 / `194021777634832653` | 144.437 | 11.647 | 150.751 | 0.958 | yes | 8.261 |
| 1153 / `194041777780157594` | 129.623 | 12.246 | 236.803 | 0.547 | yes | 38.463 |
| 1190 / `194051777813062524` | 105.160 | 11.492 | 137.808 | 0.763 | yes | 12.847 |

Cluster `J115120.4+714435, 1254337`: `M500=1.48e14 Msun`, adopted
`M200=1.924e14 Msun`, `b=603.6 kpc`, hot dispersion measure `183.674 pc cm^-3`.

Total: hot `241.428` + cool `1.816` = `243.245 pc cm^-3`. The maximum fractional
difference between independently calculated and stored `R200c` is `2.6e-6`.

## Failed independent gates

### Stellar-mass provenance

The method says it queried live Pan-STARRS g/i and WISE W1 photometry. The
committed table stores only the derived stellar masses. It names
`halo_rvir_MEASURED_diagnostic.csv` as the raw measured artifact, but that file
is absent from commit `4e951c8`. The Phineas rows are not among the eight rows in
`suspect_vetting_adjudicated.csv`. Therefore the five adopted stellar masses
cannot be recomputed from committed measurements. The Taylor et al. (2011)
calibration itself is independently identifiable, but its inputs are missing.

### Redshift dependence

The approved calculation uses the four Moster et al. (2013) redshift-zero
parameters for objects at `z=0.1096-0.2146`. The paper defines parameter
evolution with `z/(1+z)`, and the repository's newer `vo/halos.py` implements
that Table 1 form. Recomputing with the published redshift dependence changes
the five halo masses by `-0.014` to `+0.097 dex`. Central crossing labels happen
to remain unchanged; that agreement does not cure the uncertainty omission.

### Borderline classifications

The canonical 832 object sits only `0.056 dex` in halo mass above the hard
crossing threshold. Mapping the Moster paper's `0.15 dex` intrinsic stellar-mass
scatter through the local relation gives an illustrative crossing probability
of `0.68` before measurement and redshift uncertainties. This is a sensitivity
calculation, not a final posterior.

Object 983 is also not robust. Holding its observed Taylor-calibration
photometry fixed while moving its catalog photometric redshift through the
reported one-standard-deviation interval changes the redshift-dependent result:

- `z=0.1064`: `b/R200c=0.952`, crossing;
- `z=0.1649`: `b/R200c=1.200`, not crossing;
- `z=0.2234`: `b/R200c=1.378`, not crossing.

Thus a catalog central value cannot support a binary zero-versus-nonzero
foreground column for this object.

## Reproduction

```bash
snapshot=$(mktemp -d /tmp/phineas-owner-4e951c8.XXXXXX)
git -C pipeline archive 4e951c8 | tar -x -C "$snapshot"
/usr/bin/python3 analysis/scripts/validate_phineas_owner_adjudication.py \
  --pipeline-root "$snapshot" \
  --expect-rounded-dm 243
```

Focused tests:

```bash
env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  /opt/anaconda3/bin/conda run -n flits \
  python -m pytest analysis/tests/test_validate_phineas_owner_adjudication.py -q
```

Observed: `5 passed`. A deliberately wrong expected total (`242`) exits `2`;
the committed expected total (`243`) exits `0`.

## Input hashes

| Input | SHA-256 |
|---|---|
| frozen bursts | `204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644` |
| census registry | `b45d698cde155427b272d0ead4c1a248303ef8c839ddcb84a0393adcdd1ae222` |
| adjudicated masses | `3cea6b099d8238bea971e6289dfe5c729ac0da20470ae0678c9de558783d12a9` |
| duplicate ledger | `336e4023dbf046762477c724e57365c29a3ecabb982f6978e635fb0d05d47e45` |
| mass overrides | `108a9ed842ec10c76ed281e87b58aca2c32bb2785fdcf2d2ef5082c809c76748` |
| method note | `3df502e9244f8603f06336262e15d0f23aa6d52c858d4c4934fc1bbe741567bc` |
| committed budget | `e8ca970d48c06709ddc141182f5c61729f99ed1fa1f33cfbb00fdcd95111a90b` |

## Primary references

- Moster et al. (2013), redshift-dependent stellar-to-halo mass relation:
  <https://arxiv.org/abs/1205.5807>
- Taylor et al. (2011), optical-color stellar masses:
  <https://arxiv.org/abs/1108.0635>
- Planck Collaboration (2020), Planck 2018 cosmological parameters:
  <https://arxiv.org/abs/1807.06209>
