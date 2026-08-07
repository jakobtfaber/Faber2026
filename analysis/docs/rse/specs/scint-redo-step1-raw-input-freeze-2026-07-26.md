# Scint re-do, step 1 — frozen raw-input set (owner-accepted 2026-07-26)

**Lane:** [scint-redo-01](../wayfinder/tickets/scint-redo-01-interactive-recampaign-from-raw-data.md)
**Phase:** capture/verification checkpoint. Owner accepted this set in session
on 2026-07-26 ("Yes, freeze the raw-input set").

## The frozen set

Authority: `h17:/data/Faber2026/data/` (the 2026-07-21 raw-data migration).
Exactly 24 files — per burst one CHIME/FRB singlebeam baseband product (`.h5`)
and one DSA-110 total-intensity filterbank (`_dev_polcal_I.fil`). Every
downstream product of the re-do must trace to these hashes.

Verification at freeze time (2026-07-26): all 24 files stat-match the
migration ledger
(`h17:/data/Faber2026/provenance/h17-source-data-migration-20260721.json`,
0 errors) on size and nanosecond mtime; one full SHA-256 recomputation
(zach DSA filterbank) reproduced the ledger hash exactly. The ledger's three
exclusions are outside the sample or checksum-identical duplicates.

| Burst | Instrument | File | SHA-256 | Size (bytes) |
|---|---|---|---|---|
| casey | chime-frb | singlebeam_362593221.h5 | ea15c60b2bc770b30ab24d2d21e8e3fac8f5f3fe02238019ef258679770ebc0c | 1037114494 |
| casey | dsa-110 | 240229aaad_dev_polcal_I.fil | 8eb60706543875363f20f21ab1473d439f356120b8f8852cedaa9e567b938bd1 | 503316768 |
| chromatica | chime-frb | singlebeam_356959136.h5 | 2b97829b5a9636f4f502b388abff2a57cb660a8ed59ebb881176c26cd6765211 | 1031538710 |
| chromatica | dsa-110 | 240203aacl_dev_polcal_I.fil | 0e8959debce82776250ed7dcbf01b9d90e0bd85a7ce63f300cda89e55aae420f | 503316768 |
| freya | chime-frb | singlebeam_278720455.h5 | 676a9033c10926c213603939bee78c44d6d1a011c01e4279b41bccc97127df52 | 1198412798 |
| freya | dsa-110 | 230325aaag_dev_polcal_I.fil | c813f6aa741eb37c46574f0a8b665f3b0d797d77d8ff4166b52f27cddae2ca8f | 503316768 |
| hamilton | chime-frb | singlebeam_318353610.h5 | d90ae601c450e3585333831ee0511a509e3aa9fce073f7dc3ca6df56e4f487a7 | 1074883734 |
| hamilton | dsa-110 | 230913aaao_dev_polcal_I.fil | 88a7b71f595f93f3c55ce299f9bdd46f0af49bfc798d0c73818133ab4e502ba8 | 503316768 |
| isha | chime-frb | singlebeam_252069198.h5 | 0dc5ec9802d2b700988f1b6cf1a0b21a6fce4a9f1f8565ae27ffae57e70e392e | 1107114294 |
| isha | dsa-110 | 221113aaao_dev_polcal_I.fil | 6b70d1cf3341c1002df4b8d9f89065f30b03b11ff179b48ad303bd3a3d5b589d | 503316768 |
| johndoeii | chime-frb | singlebeam_311723353.h5 | 6e254dc1d024999a2ae60956dcb5433780da702b9346432ede6837833488bb2a | 1342789614 |
| johndoeii | dsa-110 | 230814aaas_dev_polcal_I.fil | 8246bbc96d5348b63db6e6df67ee82677a769e48a6d2191c53c6884b1fd9bdcc | 503316768 |
| mahi | chime-frb | singlebeam_354049284.h5 | bcf3b157436c3282f38b1f4a479694839fc0933507e88b66b5c0ddb98d9b88bc | 1016991810 |
| mahi | dsa-110 | 240122aaag_dev_polcal_I.fil | 316718f6de89d55750a3fbed5de5ecf6c69aa2f056b8b79811547757f32ea36f | 503316768 |
| oran | chime-frb | singlebeam_224263996.h5 | 89ab4a255783b1a8cf26488032f3f8aad4e58779514d9c01c2ad16df5a470af3 | 1490075166 |
| oran | dsa-110 | 220506aabd_dev_polcal_I.fil | c22a72dd96b639d0732385a57acd35d6942adadeb3a3aee0283da82dcbc983b9 | 503316768 |
| phineas | chime-frb | singlebeam_274819243.h5 | 3ce7ab34cd00fa2eb2cf68189dc40618371dbd8a0f6387cb443bd3970e88eff6 | 1588145054 |
| phineas | dsa-110 | 230307aaao_dev_polcal_I.fil | 8724d346f89722e24c4517d754af18dc569fab554ad9c318e4afcc2fb8285859 | 503316768 |
| whitney | chime-frb | singlebeam_215063905.h5 | e76950cc2e825169cb7c912f05fe996f8918bb3eb12f730d313eed779e6b559f | 1160748918 |
| whitney | dsa-110 | 220310aaam_dev_polcal_I.fil | e72aef49b31aa463f307eeacf67863396761db4215952a1184a219b357c133c2 | 503316768 |
| wilhelm | chime-frb | singlebeam_253635173.h5 | 7f86a38d823e2a86dc2033f82e7e23fb0e476870a6032e560dd71863b3dccc42 | 1090998918 |
| wilhelm | dsa-110 | 221203aaaa_dev_polcal_I.fil | 7120d95d4acc8ebced390d938a52af60344d6c2a284bfe32812ed9589a7cdd58 | 503316768 |
| zach | chime-frb | singlebeam_210456524.h5 | 215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9 | 1171470638 |
| zach | dsa-110 | 220207aabh_dev_polcal_I.fil | 074cf21a9b8c712056f274d96dd77d4d40f1ead75d1e5240fe093fc99edbac79 | 503316768 |

## Scope notes

- CHIME raw = singlebeam baseband-derived products; the beamformed intensity
  archive is not part of this basis.
- DSA raw = total intensity only; Stokes Q/U/V were never staged to h17 and
  are out of scope for the scintillation re-do.
- Any later mutation of these files (size, mtime, or hash) makes this freeze
  STALE; re-verify before use.

**Next step:** step 2 — one recorded dispersion-measure convention per burst.
