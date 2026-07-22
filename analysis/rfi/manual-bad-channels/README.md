# Manual bad-channel maps

These files are the event-specific channel-mask authority for downstream
analysis. Automated RFI diagnostics may propose channels, but they do not alter
science support. Only a map with `status: owner_approved` may be consumed.

Each approved map is bound to the exact frequency-axis file by SHA-256 and row
count. It stores sorted, non-overlapping, half-open row ranges plus their
frequency limits, reason, review evidence, reviewer, and review time. A changed
frequency axis invalidates the map rather than silently remapping it.

Workflow:

1. generate the event/instrument fine-frequency atlas;
2. create a draft map from owner-selected rows;
3. render before/after dynamic spectrum, off-pulse measures, on-pulse spectrum,
   time profile, and retained-support summary;
4. record owner approval in the map;
5. validate with `scripts/manual_bad_channels.py`;
6. represent mapped rows only as `NaN` in every downstream product.

Before an autocorrelation-function (ACF) run, materialize the effective row
mask with `scripts/manual_bad_channels.py --source-valid ... --output-mask ...
--output-provenance ...`. The artifact is exactly the union of channels already
unavailable in the source-valid array and owner-approved manual rows. The ACF
loader verifies both artifact hashes, exact frequency values, event,
instrument, approval evidence, and the union counts before applying it. A
configuration with `analysis.bad_channel_mask.required: true` fails closed when
the artifact is absent or stale. Set `authoritative: true` with `required: true`
to bypass legacy statistical channel-row promotion; pre-existing source masks
and later non-finite/bandpass-validity masks remain in force.

The index is fail-closed. `pending_manual_review`, `draft`, and `rejected` maps
are not analysis inputs. CHIME/FRB is the first review lane; the same schema is
reserved for DSA-110.

The current CHIME/FRB atlas generator is
`scripts/manual_bad_channel_atlas.py`. It shows bandpass-only measured support,
not package RFI masks, in 50-MHz review segments.

## Interactive notebook review

Generate a hash-bound review bundle on the data host with
`scripts/manual_bad_channel_atlas.py --output-bundle ...`, then copy the bundle
to the review machine. Bundles are data products and do not belong in Git.

Launch JupyterLab from the repository root:

```bash
jupyter lab analysis/rfi/notebooks/manual_bad_channel_review.ipynb
```

Controls:

- choose `Flag`, `Unflag`, or `Set view`, then click-drag vertically on any
  panel (frequency is the vertical axis);
- use `Undo` for the previous change and `Clear` for all proposed rows;
- use `Refresh` to redraw and `Save draft` to write exact full-resolution
  half-open row ranges.

Requires an interactive matplotlib backend (`ipympl`) in the kernel. In Cursor /
VS Code, restart the kernel after installing `ipympl`, then re-run all cells.
Status should read `Interactive canvas ready` before click-drag will work.

The notebook refuses to modify an approved map. Saving always clears reviewer and
review-time fields and writes `status: draft`. Approval therefore remains a
separate owner action. Review each 50-MHz interval before approval.

## Standalone desktop review

Launch the native GUI from the repository root:

```bash
/opt/anaconda3/bin/python scripts/manual_bad_channel_gui.py
```

Drag vertically on any of the three panels in `Flag` or `Unflag` mode. Use the
previous/next buttons to move through 50-MHz bands. Undo, clear, refresh, and
save-draft use the same hash-bound backend as the notebook. The GUI cannot
approve a map or apply it downstream.
