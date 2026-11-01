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
also select full tests. Both full jobs remain parallel and can use either runner.

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
