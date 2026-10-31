# Read-only mode status (fork development)

This fork starts from upstream v1.0.21. Existing controls, the legacy Work Mode
sensor, config-entry schemas, credentials and session storage remain unchanged.
The following additive sensors do not write inverter settings or schedules:

- **Base Work Mode** reads `/op/v0/device/setting/get`, key `WorkMode`. It is
  the base device setting, not necessarily the effective mode while the
  scheduler is enabled. Accepted values: SelfUse, Feedin, Backup, PeakShaving.
- **Scheduler Status** reads `/op/v1/device/scheduler/get/flag`. Values are
  enabled, disabled and unsupported. Empty legacy schedule groups are not
  evidence that the scheduler master switch is disabled.
- **Mode Status Read** is success only when both independent reads succeeded
  and are fresh. Otherwise it reports failed or stale; before any read it is
  unknown.

Each sensor exposes a `reads` attribute containing independent `base` and
`scheduler` records: `success`, `value`, `last_attempt`, `last_success`, and
`error`. Times are UTC ISO-8601. Errors contain exception class names only.
Failure clears the current value but preserves the last successful timestamp.
A failed telemetry poll invalidates both reads without changing their timestamps.
WebSocket telemetry never refreshes these timestamps. Status is considered stale
after twice the configured REST poll interval (minimum 60 seconds), evaluated
when entities update. Consumers must independently check `last_success` against
their own freshness requirement rather than rely on HA's `last_updated`.

These cloud reads are sequential, not an atomic inverter snapshot or a guarantee
of instantaneous physical state. In particular, enabled scheduler status does
not identify the active schedule group. No new effective-mode inference is made.
Unknown/malformed API replies must not be interpreted as SelfUse or disabled.

This work is not released yet. Do not switch HACS until release/CI review and an
HA backup are complete. Keep the existing FoxESS config entry when replacing
code; do not remove/recreate it. Migration and rollback must happen without an
active smart operation because existing startup recovery can perform writes.

## Fork CI and publishing

Forgejo runs `.forgejo/workflows/test.yml` using the existing Docker-capable
`ubuntu-latest` runner pattern. `Dockerfile.ci` installs Python 3.13, the locally
validated Home Assistant 2026.2.3, and Chromium plus its runtime dependencies.
It checks changed Python modules and runs the complete non-container test suite,
including browser unit tests. Container-based HA E2E and soak tests remain a
separate release prerequisite; this workflow must not be described as full E2E.

The imported GitHub release, add-on publishing, and tag-triggered flaky-test
workflows are restricted to the original upstream repository. Mirroring fork
tags must not publish anything automatically. A fork GitHub Release will be
created separately, only after explicit approval of the tested commit/version.
No fork release tag or manifest version is assigned by this change.
