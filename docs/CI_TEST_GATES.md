# CI test gates

The fast `checks` job runs on the runner's existing Node installation. It tests
the gate logic and validates manifest identity, stable SemVer, changelog heading,
release-test version agreement, and non-decreasing versions. It does not build
Docker images or start Home Assistant.

For PRs it compares the merge base with the checked-out head; for main pushes it
compares the pre-push SHA with the checked-out head. Full history is fetched.

Full unit/browser and HA status/lifecycle jobs run for runtime code, dependencies,
Dockerfiles, simulator changes, general tests, translations, unknown paths, or any
manifest change other than `version`. Missing/unresolvable bases and empty diffs
also select full tests. Both full jobs remain parallel. Unit/browser tests use
`ubuntu-latest`; nested-Podman HA tests require `ubuntu-latest-hardware`.

Metadata-only diffs skip both heavy jobs. The exact allowlist is Markdown,
`tests/test_fork_release.py`, version-only manifest edits, and this workflow's
gate script/tests/workflow. CI-policy changes require review; the fast tests
validate the gate, not changes to the runner/HA environment. If a workflow edit
changes test execution or its environment, request a manual full validation too.

**Run workflow** / `workflow_dispatch` on main always selects the complete
existing unit and HA lifecycle suites, regardless of changed paths. No soak or
broader UI E2E coverage is added by this optimization. A skipped HA job is not a
new simulation success: for v1.0.23, the unchanged runtime code's evidence remains
implementation run #30, while the release commit must pass fast metadata checks.

Imported upstream publication jobs, tag policy and deployment approvals are
unchanged. Cancelling a CI run is not stopping an installed integration/session.

## HA image-build setup budget

Main run #44 on flux passed checks/unit tests but had 60 HA setup errors:
`filelock.Timeout` waiting for `/src/.e2e-build.lock`. Eight cases passed on the
other worker. These were shared fixture errors, not 60 control assertion failures.
The same runtime passed PR run #43: 41 passed / 27 intentional skips, including
the disabled-cold-start capability flow.

The two xdist workers serialize their image builds with a lock. Previously a
waiter was allowed only 300 seconds while the build holding that lock was allowed
600 seconds. A valid slow build could therefore fail the waiting worker's session
fixture and cache that setup failure across its tests. This budget mismatch is
confirmed; the log does not establish why the particular lock holder was slow.

The lock wait now derives from the unchanged 600-second build timeout plus a
60-second release margin. Build-start/completion timing is logged for diagnosis.
Unit checks model a holder needing up to its full allowed budget and verify both
failed and timed-out builds release the lock. Builds and waits remain bounded;
test assertions, worker count and production runtime code are unchanged. A lock
timeout does not establish a VM/hardware fault and is not fixed by deleting a live
lock file. Full CI must validate the fixture correction before release preparation.
