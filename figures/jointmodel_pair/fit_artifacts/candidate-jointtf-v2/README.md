# Candidate JointTF v2 model dumps

Deterministic model reconstructions from the saved posterior medians for the
mode-continuous `s2=100` candidates. These are fit-audit artifacts, not adopted
production models.

| Burst | Job | Candidate | Model dump SHA-256 | Fit JSON SHA-256 |
|---|---:|---|---|---|
| oran | 171 | C1D1 | `b550ddf48d8d922751735fda8fdff0aa5dfd1287d67c8d4ac19ee7b76382ffa6` | `bdfbb3a49b2427db7fbdff20c67fe14c4d94396da503c06d5dda220a6e4cd609` |
| johndoeII | 175 | C1D2 | `2095a1891531c14714d83334abee134c3ad54293c3385994296ff4c4c282dea6` | `c95a126664fc017a607f38dad13d32ca6961f859c3bed97e649119429941bf36` |
| zach | 178 | C2D3 fine | `eda4e8f5d4d67f6dd96d307719bb292de9215e0fc0352ff7f5e94c7dc99eb408` | `a0a1adaa1918e6b58cd9e14ff832794e71f069cd5812dfb03389f646bab561dc` |
| zach | 180 | C2D4 fine, active display | `8efa4f8dc6572cdd448dfcedebaf6c4e17a30da6f3bc8a37aba1cd5944836051` | `55bc7397ae1d100718bdb7b9cb9b2a7dd9c0ca70908c60ed684e8795e0e05590` |

## Reconstruction provenance

- Host: `lxd110h17`.
- Environment: `flits-a1-312`; Python 3.12.13; NumPy 2.4.6.
- Worktree commit: `d292f4b91ef02dfd120a816c015fbb67cb15261f`.
- `dump_jointmodel.py`: SHA-256 `7ca21f0a4ed1667befcabe1e5d3301b0d37192922ecf0458e3cf6e8a88c6ac45`.
- `joint_tf_prep.py`: SHA-256 `86019f2ed07cfe215a18811450403cbdb9bce627773b2e9eea0c1ef8a82e3395`.
- `run_joint_fit_zachfine.py`: SHA-256 `88c61aa8d61dabf68dd5ab7192938f9459a47ed0a07d2a9fdf97cd78b0395194`.
- `burstfit_joint.py`: SHA-256 `347d07a0d11e323952b5f3acfe1e45b8050c6548787263143b79b79bb11aaf90`.

The first two dumps use `dump_jointmodel.py <burst> <suffix>`. The zach dump
imports the exact fine-window hook from `run_joint_fit_zachfine.py` and calls
`joint_tf_prep.prepare_pair(..., common_window=False)`, matching jobs 178 and 180.
No sampler was rerun; model arrays were evaluated at saved posterior medians.

The active zach display uses C2D3 job 178. Owner full-size review rejected C2D4
job 180 as the active display: its fourth DSA component is a broad, low-fluence
pedestal and C2D3 is favored by 10.1 in log evidence. The job-180 dump and
triptych remain preserved as non-latest diagnostic evidence. This display
choice does not by itself record component-count adoption.

The source fit generation remains not exactly reproducible because it had no
sampler seed and used modified/untracked code. The deterministic model
reconstruction is content-hashed and structurally checked, but this does not
repair the original fit-generation provenance gap.

## Local rendering

```bash
SOURCE_DATE_EPOCH=1784505600 \
env -i HOME="$HOME" PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  /opt/anaconda3/bin/conda run -n flits python \
  scripts/plot_codetection_triptych.py \
  --burst oran --burst johndoeii --burst zach
```

The fixed epoch and renderer SVG hash salt make all nine PNG/PDF/SVG outputs
byte-identical across repeated local renders in the same pinned environment.
