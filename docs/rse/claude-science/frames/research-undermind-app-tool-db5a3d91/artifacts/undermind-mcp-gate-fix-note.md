# Correction for Claude Code — `scan_for_secrets` shipped the OLD (buggy) gate

> On branch `feat/passive-endpoint-capture`, file `src/undermind_mcp/_sanitize.py`. One function +
> one test. Do not touch anything else. Commit on the same branch.

## What's wrong

The brief (§5a) specified a **dedicated `_GATE_PATS`** list for `scan_for_secrets` — value-only
patterns. The shipped `scan_for_secrets` instead **iterates `_PATS`**, which includes the two
substring-keyed patterns (`SENSITIVE_KEY + "=..."` and `SENSITIVE_KEY + '":"..."'`). Those match the
substring `key` inside benign field names. This is the exact bug fixed two review rounds ago; it
regressed on the way into the repo.

**Runtime impact (not cosmetic).** The `/capture` route (`http_receiver.py:373–378`) does
`redact_obj` → `scan_for_secrets` → **422 + write nothing** on any hit. Verified against a realistic
`/api/v2/.../papers/` response:

```
redact_obj({"results":[{"cite_key":"Faber2026","author":"Faber, J.","project_id":"<uuid>", ...}]})
→ shipped scan_for_secrets → ['key": "Faber…']  → route returns 422, writes nothing
→ corrected scan_for_secrets → []               → capture written
```

`cite_key` is a real field on the papers endpoint (`endpoints.md`: paper batches of cite_keys) — the
**exact endpoint fix #3 needs**. So the papers fixtures would be silently rejected. Any surviving
field whose name contains a sensitive substring (`cite_key`, and similar) with a value ≥6 chars trips
it.

**Not a leak.** The buggy gate is a strict *superset* of the correct one (it has extra patterns), so
it never lets a real secret through — verified it still catches raw `sessionid`/`csrftoken`/`Bearer`/
opaque tokens. The bug is **over-rejection only**: it drops valid captures, it does not leak. Security
posture is intact; capture functionality is broken for the endpoint that matters most.

## Fix 1 — replace `scan_for_secrets` with the `_GATE_PATS` version (from the brief §5a)

Add `_GATE_PATS` above the function and make `scan_for_secrets` iterate it, not `_PATS`:

```python
# Gate patterns: value-intrinsic secrets ONLY (the match itself IS a secret). The key=value /
# "key":"value" patterns (_PATS #4,#5) are DELIBERATELY EXCLUDED — they are substring-keyed and
# false-positive on benign fields like cite_key ('key' inside it), 422-rejecting valid captures.
# A real key=value secret is already turned into "<REDACTED>" by redact_obj before the gate runs,
# so it never reaches here raw; the gate is the backstop for value-shaped secrets. UUIDs exempt.
_GATE_PATS = [
    re.compile(r"sessionid=[^;&\s\"']+", re.I),
    re.compile(r"(app-)?csrftoken=[A-Za-z0-9]{8,}", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{12,}", re.I),
    re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),  # long opaque token; UUIDs skipped below
]


def scan_for_secrets(blob: str) -> list[str]:
    """Gate: non-empty list of offending fragments if a value-shaped secret survives redaction.
    '<REDACTED>' and canonical UUIDs are never leaks. Value-only patterns — key=value secrets are
    already redacted upstream, and matching substring keys here 422-rejects benign fields."""
    leaks: list[str] = []
    for pat in _GATE_PATS:
        for m in pat.finditer(blob):
            frag = m.group(0)
            if frag == "<REDACTED>" or "<REDACTED>" in frag or UUID.match(frag):
                continue
            leaks.append(frag[:12] + "…")
    return leaks
```

Leave `redact_obj` / `redact_str` / `key_sensitive` / `_PATS` exactly as they are — those are correct
and pinned; only the gate changes.

## Fix 2 — add the missing gate test (the reason this passed CI)

`test_sanitize.py`'s `test_must_survive` asserts `keep in out` but **never runs the gate** over the
survivors, so the false-positive was invisible. Add the gate to the survive path:

```python
@pytest.mark.parametrize("value,keep", SURVIVE_CASES)
def test_survivors_do_not_trip_gate(value: object, keep: str) -> None:
    """A benign field that correctly survives redaction must NOT be flagged by the gate.
    Regression guard for the cite_key / status_code substring-key false positive."""
    out = _blob(value)
    assert keep in out
    assert scan_for_secrets(out) == [], f"gate false-positived on benign {out!r}"
```

Also add one explicit end-to-end case for the endpoint that matters:

```python
def test_gate_allows_papers_response_with_cite_key() -> None:
    papers = {"results": [{"cite_key": "Faber2026", "author": "Faber, J.",
                           "project_id": "550e8400-e29b-41d4-a716-446655440000",
                           "status": "complete"}]}
    out = json.dumps(redact_obj(papers))
    assert scan_for_secrets(out) == []
    assert "Faber2026" in out and "550e8400-e29b-41d4-a716-446655440000" in out
```

Keep `test_scan_gate_catches_unredacted_secret` — it still must pass (proves the value-only gate still
catches real leaks). If you have a `/capture` route test, add a 200 case posting a `cite_key`-bearing
record and asserting a file is written (not 422).

## Acceptance
- `test_survivors_do_not_trip_gate` and `test_gate_allows_papers_response_with_cite_key` pass;
  `test_scan_gate_catches_unredacted_secret` still passes.
- `ruff` + `pyright --strict src/` clean; full suite green.
- Commit: `"fix: gate uses value-only patterns (no cite_key false-positive 422)"`.
- Nothing else on the branch changes.
