# Raw data provenance: h17 is the point of access

**Authority.** For every burst in this project, raw data is pulled from **h17**
(`lxd110h17`) and from nowhere else. This holds across the board — CHIME/FRB
baseband and DSA-110 filterbanks alike, for all twelve co-detected bursts.
Any analysis, revalidation, or figure regeneration that needs raw input reads it
from h17. Copies that exist elsewhere are convenience caches, not sources, and
must not be cited as the origin of a number.

The two upstream archives below are recorded because knowing where h17 got a
file matters for auditing it. They are not access paths. Do not fetch from them
directly for project work.

## Layout on h17

```
/data/Faber2026/
├── data/
│   ├── chime-frb/<burst>/singlebeam_<chime_event_id>.h5
│   └── dsa-110/<burst>/<dsa_observation_id>_dev_polcal_I.fil
├── evidence/
└── provenance/h17-source-data-migration-20260721.json
```

`/data` is a separate 13 TB volume (`/dev/sda1`), not part of h17's root
filesystem. A search rooted at `/` with `-xdev` will silently miss all of it;
this is a real trap and has already produced one wrong "the files are not on
h17" conclusion.

## Upstream origins

| Instrument | Upstream | Evidence |
|---|---|---|
| CHIME/FRB baseband | CANFAR `arc` — `arc:projects/chime_frb/data/chime/baseband/processed/<YYYY>/<MM>/<DD>/astro_<event_id>/` | Verified live 2026-07-24 with `vls` under CADC proxy certificate `CN=jfaber_1ff`; the listed size matches the h17 copy byte for byte |
| DSA-110 filterbanks | `dsa-storage` (`dsa-storage.ovro.pvt`) and `h23` | `dsastorage` is a configured host in h17's own SSH config; the `h23` leg is recorded on the project owner's statement and has not been independently re-verified in this document |

Reaching CANFAR requires a current CADC proxy certificate at `~/.ssl/cadcproxy.pem`
(`cadc-get-cert` to refresh). This is only needed to re-derive provenance, never
for normal analysis.

## Retired path form — do not reintroduce

Earlier records addressed DSA filterbanks as
`iacobus:/Users/iacobus/Library/Mobile Documents/…/Codetections_DSA_Filterbanks/…`.
**That form is retired**, though not for the reason it first appears. `iacobus`
is a real machine — `iacobus-bkp-mbp`, a macOS host on the tailnet at
100.93.229.114, offline as of 2026-07-24 with a last-seen of three days. The
paths are dead for two other reasons. First, that staging tree was drained on
2026-07-13 and moved to `~/Research/_quarantine/CHIME_DSA_Codetections-drained-20260713/`,
so nothing sits at the recorded location any more. Second, and more durably: a
single laptop that is usually asleep is not an acceptable point of access for
project raw data, whatever its uptime on a given day.

The form must not appear in new provenance records, manifests, fixtures, or
figure metadata. Where it survives in historical handoffs, journals, migration
scripts, and machine inventories it is left alone — those describe a migration
in which that host genuinely participated, and rewriting them would falsify the
record rather than correct it.

## Migration ledger

`/data/Faber2026/provenance/h17-source-data-migration-20260721.json`
(schema `faber2026-h17-source-data-migration-v1`, created 2026-07-21T09:42:20Z,
status `verified`, 0 errors) records all 24 files — twelve bursts on two
instruments — with `sha256`, size, inode, and mtime captured both before and
after the move into the curated layout, plus each file's pre-migration h17 path.
Three files were deliberately excluded: an archived singlebeam under
`arc_trash_2026-06/`, and two DSA filterbanks belonging to observations outside
this sample.

The hashes below are copied from that ledger. Verify against it, not against
this document.

## Inventory

| burst | TNS name | CHIME event | DSA observation |
|---|---|---|---|
| `casey` | FRB 20240229A | 362593221 | 240229aaad |
| `chromatica` | FRB 20240203A | 356959136 | 240203aacl |
| `freya` | FRB 20230325A | 278720455 | 230325aaag |
| `hamilton` | FRB 20230913A | 318353610 | 230913aaao |
| `isha` | FRB 20221113A | 252069198 | 221113aaao |
| `johndoeii` | FRB 20230814B | 311723353 | 230814aaas |
| `mahi` | FRB 20240122A | 354049284 | 240122aaag |
| `oran` | FRB 20220506D | 224263996 | 220506aabd |
| `phineas` | FRB 20230307A | 274819243 | 230307aaao |
| `whitney` | FRB 20220310F | 215063905 | 220310aaam |
| `wilhelm` | FRB 20221203A | 253635173 | 221203aaaa |
| `zach` | FRB 20220207C | 210456524 | 220207aabh |

### CHIME/FRB singlebeam baseband

Under `/data/Faber2026/data/chime-frb/<burst>/`.

| burst | file | bytes | sha256 |
|---|---|---:|---|
| `casey` | `singlebeam_362593221.h5` | 1,037,114,494 | `ea15c60b2bc770b30ab24d2d21e8e3fac8f5f3fe02238019ef258679770ebc0c` |
| `chromatica` | `singlebeam_356959136.h5` | 1,031,538,710 | `2b97829b5a9636f4f502b388abff2a57cb660a8ed59ebb881176c26cd6765211` |
| `freya` | `singlebeam_278720455.h5` | 1,198,412,798 | `676a9033c10926c213603939bee78c44d6d1a011c01e4279b41bccc97127df52` |
| `hamilton` | `singlebeam_318353610.h5` | 1,074,883,734 | `d90ae601c450e3585333831ee0511a509e3aa9fce073f7dc3ca6df56e4f487a7` |
| `isha` | `singlebeam_252069198.h5` | 1,107,114,294 | `0dc5ec9802d2b700988f1b6cf1a0b21a6fce4a9f1f8565ae27ffae57e70e392e` |
| `johndoeii` | `singlebeam_311723353.h5` | 1,342,789,614 | `6e254dc1d024999a2ae60956dcb5433780da702b9346432ede6837833488bb2a` |
| `mahi` | `singlebeam_354049284.h5` | 1,016,991,810 | `bcf3b157436c3282f38b1f4a479694839fc0933507e88b66b5c0ddb98d9b88bc` |
| `oran` | `singlebeam_224263996.h5` | 1,490,075,166 | `89ab4a255783b1a8cf26488032f3f8aad4e58779514d9c01c2ad16df5a470af3` |
| `phineas` | `singlebeam_274819243.h5` | 1,588,145,054 | `3ce7ab34cd00fa2eb2cf68189dc40618371dbd8a0f6387cb443bd3970e88eff6` |
| `whitney` | `singlebeam_215063905.h5` | 1,160,748,918 | `e76950cc2e825169cb7c912f05fe996f8918bb3eb12f730d313eed779e6b559f` |
| `wilhelm` | `singlebeam_253635173.h5` | 1,090,998,918 | `7f86a38d823e2a86dc2033f82e7e23fb0e476870a6032e560dd71863b3dccc42` |
| `zach` | `singlebeam_210456524.h5` | 1,171,470,638 | `215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9` |

### DSA-110 filterbank, Stokes I

Under `/data/Faber2026/data/dsa-110/<burst>/`.

| burst | file | bytes | sha256 |
|---|---|---:|---|
| `casey` | `240229aaad_dev_polcal_I.fil` | 503,316,768 | `8eb60706543875363f20f21ab1473d439f356120b8f8852cedaa9e567b938bd1` |
| `chromatica` | `240203aacl_dev_polcal_I.fil` | 503,316,768 | `0e8959debce82776250ed7dcbf01b9d90e0bd85a7ce63f300cda89e55aae420f` |
| `freya` | `230325aaag_dev_polcal_I.fil` | 503,316,768 | `c813f6aa741eb37c46574f0a8b665f3b0d797d77d8ff4166b52f27cddae2ca8f` |
| `hamilton` | `230913aaao_dev_polcal_I.fil` | 503,316,768 | `88a7b71f595f93f3c55ce299f9bdd46f0af49bfc798d0c73818133ab4e502ba8` |
| `isha` | `221113aaao_dev_polcal_I.fil` | 503,316,768 | `6b70d1cf3341c1002df4b8d9f89065f30b03b11ff179b48ad303bd3a3d5b589d` |
| `johndoeii` | `230814aaas_dev_polcal_I.fil` | 503,316,768 | `8246bbc96d5348b63db6e6df67ee82677a769e48a6d2191c53c6884b1fd9bdcc` |
| `mahi` | `240122aaag_dev_polcal_I.fil` | 503,316,768 | `316718f6de89d55750a3fbed5de5ecf6c69aa2f056b8b79811547757f32ea36f` |
| `oran` | `220506aabd_dev_polcal_I.fil` | 503,316,768 | `c22a72dd96b639d0732385a57acd35d6942adadeb3a3aee0283da82dcbc983b9` |
| `phineas` | `230307aaao_dev_polcal_I.fil` | 503,316,768 | `8724d346f89722e24c4517d754af18dc569fab554ad9c318e4afcc2fb8285859` |
| `whitney` | `220310aaam_dev_polcal_I.fil` | 503,316,768 | `e72aef49b31aa463f307eeacf67863396761db4215952a1184a219b357c133c2` |
| `wilhelm` | `221203aaaa_dev_polcal_I.fil` | 503,316,768 | `7120d95d4acc8ebced390d938a52af60344d6c2a284bfe32812ed9589a7cdd58` |
| `zach` | `220207aabh_dev_polcal_I.fil` | 503,316,768 | `074cf21a9b8c712056f274d96dd77d4d40f1ead75d1e5240fe093fc99edbac79` |

## Known gaps

- **Stokes Q, U and V are not on h17.** Only `_dev_polcal_I.fil` was migrated.
  The full four-Stokes sets exist on jakob-mbp in iCloud Drive. Any polarisation
  work needs them staged to h17 first; until then h17 is authoritative for total
  intensity only.
- **The DSA filterbanks are all exactly 503,316,768 bytes.** That is the
  instrument's fixed dump size, not a copying artefact — the sha256 values are
  all distinct.
- **`zach` shares a sha256 with an excluded file.** The ledger's exclusion list
  contains `220207aabh/Level3/220207aabh_dev_polcal_I.fil` with the same hash as
  the migrated `zach` filterbank. Same content, duplicate staging path; nothing
  was lost.

## Derived products are not raw data

`/home/ubuntu/flits-runs/data/` on h17 holds dedispersed, bandpass-corrected
`.npy` waterfalls with the dispersion measure baked into both the filename and
the array. They are inputs to fitting, not raw data, and cannot be used to
revalidate a dispersion measure — the value under test has already been applied.
Go to `/data/Faber2026/data/` for that.
