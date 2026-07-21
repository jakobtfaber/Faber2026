# Native Overleaf Git contract

Date: 2026-07-21

Question: what can the manuscript-only bridge rely on when it uses the existing Overleaf project's native Git remote?

Scope: Overleaf Cloud. Primary sources only. No live-project write test. No credential inspection or disclosure.

## Decision-grade findings

### Authentication and remote identity

Documented:

- Native Git is a premium feature. It supports clone, pull, and push against an existing Overleaf project.
- Authentication tokens are the only supported login method. Use `git` as the username and the token as the password. Old account-password authentication is unavailable.
- A token belongs to one Overleaf user, reaches every Git-enabled project that user may access, expires after one year, and must not be shared. Each user may hold at most ten tokens. Deleting a token revokes it.
- Overleaf recommends a Git credential helper. Each collaborator should use their own account and token.
- For an existing Cloud project at `https://www.overleaf.com/project/<PROJECT_ID>`, the remote is `https://git.overleaf.com/<PROJECT_ID>`. The authoritative value should be copied from **Integrations → Git** in that project. The project identifier selects the existing project; do not create or copy a project to establish this bridge.

Sources: [Git integration](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git); [Git integration authentication tokens](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration/git-integration-authentication-tokens).

Local observation, not an Overleaf guarantee:

- The separate checkout at `~/Developer/overleaf/Faber2026` currently has only its GitHub `origin`; no native Overleaf remote is configured. This was a read-only configuration inspection. The existing project's native URL therefore remains an activation input to obtain from its Git dialog.

### Branch and history semantics

Documented:

- Each project has one linear Git history. The sole remote branch is hard-coded as `master`. Branches and tags are unsupported.
- A local branch with another name may push explicitly as `<local-branch>:master`.
- Overleaf History is not Git history. The Git service translates between them.
- A fetch or pull dynamically creates a Git commit for the current Overleaf state if one does not already exist. A push creates a commit visible to later clones.
- Web-editor changes do not create Git commits continuously. Several collaborators' edits may collapse into one generated commit, attributed to the person who made the most recent edit.
- A labeled Overleaf History version can force a corresponding Git commit only when no newer Git commit exists after that history point.

Source: [Advanced Git operations](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration/advanced-git-operations).

Implication, not a guarantee:

- The bridge must map its local staging branch explicitly to remote `master`; it must not infer Overleaf support from ordinary multi-branch Git behavior.
- Git commit identity is unsuitable as a complete record of who changed prose in the web editor.

### Web-editor concurrency and Git pushes

Documented:

- Web-editor collaboration uses Overleaf's own simultaneous-editing system. Edits are sent to the server every few seconds and rebased so connected clients converge.
- Overleaf describes Git as a translation layer over that internal history, not a complete Git implementation.
- Pushing from Git can lose or displace tracked changes and comments. Moving or renaming a file is represented as delete plus create and can delete that file's tracked changes and comments. Overleaf advises against mixing active Git use with tracked changes or comments.

Sources: [Collaborating in Overleaf](https://docs.overleaf.com/collaborating/collaborating-in-overleaf); [Advanced Git operations](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration/advanced-git-operations).

Not documented:

- No first-party guarantee was found for ordinary Git non-fast-forward rejection, atomic push behavior, the exact result of a push concurrent with web edits, or a server-side compare-and-swap operation.
- No first-party mechanism was found to pause web editing during a push.

Required planning consequence:

- Treat concurrent-push behavior as unknown. Fetch immediately before export, require the expected fetched `master` tip, avoid path moves and renames, and coordinate an editor pause for first activation or destructive reconciliation. These are bridge safety rules, not Overleaf guarantees.

### Limits and unsupported repository features

Documented limits for both free and premium plans:

| Limit | Contract |
| --- | --- |
| Files per project | 2,000 maximum |
| Editable material | 7 MB total maximum |
| Individual editable text file | Keep at or below 2 MB for reliable editability; some larger files may remain editable |
| Individual upload | 50 MB maximum |
| Total project size | No enforced maximum; Overleaf recommends below 500 MB generally and below 100 MB when using Git or GitHub synchronization |

Native Git does not support Git Large File Storage, nested Git submodules, branches, or tags. Symlinks become regular files. Execute permissions are not preserved. Folder renames can leave an empty old folder; a rename combined with creating a file at the old folder path can be rejected.

Sources: [Plan limits](https://docs.overleaf.com/getting-started/free-and-premium-plans/plan-limits); [Advanced Git operations](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration/advanced-git-operations).

Planning consequence:

- The bridge preflight must enforce the hard file/editable-material limits and reject unsupported repository objects before touching Overleaf. The 100 MB figure is guidance, not an enforced service limit.

### Push rejection, transport failure, and recovery

Documented failure cases and responses:

- A push-reference failure can come from project file-size or file-count limits, symlinks, Git Large File Storage, or another unsupported file.
- Large change sets may time out; Overleaf recommends smaller commits.
- Increasing Git's HTTP `postBuffer` to 10 MB may help some push failures. This is troubleshooting advice, not a success guarantee.
- Automated polling can trigger rate limiting. Overleaf says manual operations generally do not; reduce or disable polling if rate limited.
- A wrong URL can report “repository not found.” Authentication failure should be checked against token configuration, expiry, and revocation.
- Full Project History can download an older project version, restore one file including its comments and tracked changes, recover deleted files, or restore the entire project including comments and tracked changes. A copied project starts with fresh history, so copying is not a recovery method that preserves existing history.

Sources: [Advanced Git operations](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration/advanced-git-operations); [Git integration authentication tokens](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/git-integration/git-integration-authentication-tokens); [History and versioning](https://docs.overleaf.com/writing-and-editing/history-and-versioning).

Not documented:

- Overleaf does not promise that every failed push leaves the project unchanged.
- Overleaf does not publish a native-Git rollback transaction or recovery-point objective.

Required planning consequence:

- Before first activation, create both an Overleaf History label and a downloaded source snapshot, then fetch and record the generated `master` commit. After any push, fetch again and compare the projected tree before declaring success. Recovery should use Overleaf History for comments and tracked changes; a Git tree alone cannot preserve that metadata. This is a conservative bridge protocol assembled from supported mechanisms, not an official transaction guarantee.

## Contract summary for later tickets

The bridge may rely on token-authenticated access to the existing project's single `master` branch, on pull/fetch materializing the current web state as a Git commit, on explicit project limits, and on History restoration. It must not rely on normal multi-branch Git semantics, one-commit-per-editor-change history, conflict-safe concurrent pushes, or preservation of comments and tracked changes across Git writes. Later design tickets should therefore require expected-tip checks, path stability, human coordination for destructive exports, hard preflight limits, post-push tree verification, and an Overleaf-native recovery snapshot.
