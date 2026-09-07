# Conventions

These rules are enforced by the DoD check, a required status check on
the default branch.

## Branches

`story/FDY-<issue#>-<slug>` — bugs use `bug/FDY-<issue#>-<slug>`.

## Commit trailers

Every commit on a PR branch carries four trailers:

```
Work-Item: <owner>/<repo>#<issue>
Requirement: REQ-0XX            # comma-separated list allowed
Agent-Role: <orchestrator|pm|architect|developer|qa|devops|techwriter|human>
Harness: <claude-code/x.y|codex/x.y|manual|...>
```

Pre-automation commits use `Agent-Role: human` and `Harness: manual`.
That is honest provenance, not a gap.

## Definition of Done

The policy of record lives in the control plane's `policies/dod.yaml`.
The enforced subset runs here as the `dod` required status check on the
default branch. If the policy and the check disagree, the policy wins.
