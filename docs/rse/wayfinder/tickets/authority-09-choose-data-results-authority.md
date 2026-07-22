# Choose the data and results authority policy

- Type: `wayfinder:grilling` (HITL)
- Status: resolved
- Assignee: —
- Blocked by: [Define authority roles and their required proof](authority-01-define-authority-roles-and-proof.md), [Reconcile local data and results custody](authority-04-reconcile-local-data-and-results.md), [Restore CANFAR read-only verification access](authority-05-restore-canfar-read-access.md), [Reverify remote and institutional custody](authority-06-reverify-remote-custody.md), [Trace the missing h23 quarantine](authority-14-trace-missing-h23-quarantine.md), [Complete Drive-to-iacobus parity and duplicate adjudication](authority-15-complete-drive-iacobus-parity.md)
- Map: [Project authority and custody](../map-project-authority-and-custody.md)
- Triage: `ready-for-human`

## Question

For raw observations, derived inputs, fit outputs, evidence packets, manuscript
artifacts, and archives, choose the authoritative store and permitted replicas.
Ratify or amend Google Drive's processed-data role, iacobus quarantine/staging,
h17 compute outputs, CANFAR institutional custody, local data replicas, and the
claim-level registry versus byte-level results-library split. Define parity and
repair requirements before any link or reference update.

## Answer

Owner-ratified 2026-07-20.

### Authority topology

- Faber2026 GitHub `main` is authority for the claim registry, trust state,
  manuscript artifacts, compact evidence, and catalog definitions.
- Google Drive is authority for the existing 5,437-path processed-data scope.
  It is the intended authority for accepted bulk result bytes after each exact
  destination receives its own role receipt.
- CANFAR is authority for the checksum-manifested 24 derived fit-input cubes:
  12 CHIME/FRB and 12 DSA-110. The matched Mac cubes are replicas. Overlapping
  Drive objects are historical/archive objects unless explicitly matched to
  this lineage.
- The twelve raw CHIME singlebeam HDF5 files on h17 remain unclassified and
  deletion-prohibited until a checksum-manifested institutional archive is
  verified. CANFAR is the intended authority; h17 does not gain authority from
  sole visible custody.
- The local `results-library` is an intended materialized replica and
  navigation view, never a conflict resolver. It remains unclassified until
  its broken links, conflicts, stale inventory, identifiers, and byte manifests
  are repaired.
- h17 outputs are working copies or staging areas until promoted. Iacobus is
  the verified recovery replica for Drive's 5,437 project-data paths. HPCC and
  missing h23 holdings do not settle conflicts.

### Parity standard

New or promoted artifacts require stable result IDs, exact paths, byte sizes,
SHA-256 checksums, provenance, and live readability. Legacy Drive parity may
use MD5 only with complete path/size counts and duplicate-object adjudication.
A replica must match every in-scope authority path; drift demotes it from
replica. Duplicate names require object-ID adjudication, and equal bytes do not
establish strict one-to-one object parity. Symbolic links provide navigation,
not custody. Byte parity never establishes scientific trust.

Every comparison records the authority identity, tool/version, timestamps,
full manifests, exceptions, and report checksums.

### Repair and promotion gates

The claim registry, results catalog, byte manifest, and local view must share
one stable ID per result. Repair starts with an inventory of real files, links,
conflicts, uncatalogued objects, and superseded versions.

H17 output promotion requires producing commit, pipeline pin, input identities,
output checksums, logs, and explicit trust state. Byte promotion may retain
pending or revoked science; claim promotion remains a separate scientific
gate. Accepted bulk bytes go to their receipted Drive scope before the local
results view becomes their verified replica.

The local view must be rebuilt from the canonical checkout. Repair the eight
broken links, two real-file conflicts, three relink cases, and stale inventory
entry individually. Replace expendable-worktree links with generated stable
links. Current CHIME paths change only after an exact dry run, rollback receipt,
and post-change verification; dated historical records remain unchanged.
Drive duplicate removal is optional cleanup, not a parity prerequisite.

No source deletion or reference rewrite may precede verified destination and
independent recovery-copy checks.

### Replica and retention policy

An authority without an independent verified replica is explicitly `at risk`.
Nothing may be consolidated or removed until an independent replica exists.
Drive permits the full iacobus recovery replica and selective Mac replicas;
iCloud remains retired or unclassified. CANFAR fit inputs permit the matched
Mac replica. GitHub authorities permit exact-commit clones and bundles;
Overleaf remains a working copy. Accepted Drive result bytes permit the repaired
local results view as replica, while h17 remains working or staging.

Superseded results remain immutable and marked non-current. Quarantines and
preservation packets remain until their named release gates pass. Age alone
never permits deletion. Iacobus, HPCC, h17 staging, and the Drive duplicate
require separate owner disposition. The absent h23 quarantine remains a
permanent custody-gap record.
