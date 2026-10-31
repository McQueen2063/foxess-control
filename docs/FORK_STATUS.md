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
The release-review change prepares manifest version `1.0.22`; no release
tag is created automatically. See [release gates and migration](FORK_RELEASE.md).

## HA status smoke gate

The `ha-status-smoke` Forgejo job builds `Dockerfile.e2e-ci` and runs one real-HA
smoke test with the existing seeded config entry and local FoxESS simulator.
Both the HA image and Python test dependency are pinned to 2026.2.3. It verifies
the new sensors, successful timestamped reads, and unchanged legacy Work Mode
and battery SoC entities. This is a focused load/status gate, not the full E2E
or soak suite and not a live-device test.

Nested Podman runs in a disposable **privileged** Docker container with its own
VFS storage. This requires a trusted Docker-capable runner: privileged mode is
not a security boundary against malicious code. Do not run untrusted external
PRs on this runner. No host Docker socket, host network, production credentials,
or production HA configuration is mounted. Existing fixtures stop the nested
HA container, and `docker run --rm` removes the outer container after exit.
Local OpenCode needs no container runtime or additional privileges.

The nested CI image sets `FOXESS_E2E_DISABLE_CGROUPS=1`: inner HA containers
use `podman run --cgroups=disabled` because Docker has not delegated cgroup
controllers. The outer Docker container still owns resource accounting/limits.
Normal E2E runs outside that image retain Podman's default cgroup management.

### Explicit Buildx builds

Following the successful HA status smoke run #14, the workflow uses explicit
Buildx builds with `--builder default --load --progress=plain`. The runner job
image must provide the Docker Buildx CLI plugin. A preflight check requires the
default builder to use the `docker` driver: the E2E Dockerfile depends on the
test image in the same daemon's local image store. A separate `docker-container`
builder does not automatically resolve that local base image. No images are
pushed, no builder is created, and no runner configuration is modified.
