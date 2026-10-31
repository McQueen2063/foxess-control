# Fork release review: 1.0.22

**Status: prepared, not approved for publication or installation.**

Upstream base: v1.0.21 (`bd83aef`). Development lives in Forgejo
`utt/foxess-control`; the public GitHub distribution is
`McQueen2063/foxess-control`. The domain stays `foxess_control`.

## Release gates

- [x] Read-only client/coordinator/sensor unit regression tests.
- [x] Unit/browser suite and isolated HA 2026.2.3 load/status smoke passed in
  CI before this release-review change. Exact release commit must pass again.
- [x] Buildx migration reviewed and merged separately.
- [ ] CI green on the exact release commit, including manifest/version checks.
- [ ] Full existing HA-container control-lifecycle E2E suite and soak checks,
  or an explicitly reviewed change to this release gate. The one-test status
  smoke is not a substitute; no successful live-device test is claimed.
- [ ] Review sequential cloud-read assumptions, freshness contract, and API
  compatibility on the target device. Live read verification is still pending.
- [ ] Explicit approval of release commit, tag, and GitHub Release text.

The lifecycle CI change selects the complete `tests/e2e/test_e2e.py` module
(66 cloud/entity parameterized cases collected locally), plus the status smoke
test, with two workers and a 120-minute job timeout. Some cloud-only/entity-only
cases intentionally skip the other mode. The broader UI E2E and multi-hour soak
suite are not included. Collection is not execution; record actual CI results
before checking off any gate.

The known H3 scheduler write/power-limit compatibility concern is **not fixed**
here. It must be inspected before any later live control testing. Publishing
this fork does not authorize battery writes or enabling battery-charger control.

## Publication (only after approval)

1. Record the reviewed merge commit and green CI URLs. Ensure manifest version
   is `1.0.22`; intended tag is `v1.0.22`.
2. Tag only that approved commit in Forgejo. Confirm the one-way GitHub push
   mirror has the same commit/tag. Do not edit or use GitHub's Sync Fork button.
3. Create a GitHub Release separately for that tag, with the changelog and known
   limitations. Git mirroring does not copy Release objects. Imported upstream
   publishing jobs are intentionally disabled for this fork.
4. Verify HACS can discover the exact version before scheduling migration.
   HACS/version selection has not yet been validated for this fork tag;
   resolve any compatibility problem before installing, not by silently changing
   versioning on an already-published release.

## HA migration (one user-confirmed step at a time)

1. Record installed integration/HACS versions, config-entry ID and existing
   device/entity IDs. Download integration diagnostics privately. Never paste
   credentials, tokens, `.storage` contents or a full backup into chat.
2. Confirm no active smart charge/discharge or pending recovery/cleanup. Do not
   assume observe-only in battery-charger disables the integration's own session
   recovery writes. Resolve any active operation before restarting or replacing
   code, with separate authorization for any inverter writes.
3. Take a full HA backup and verify its availability. Retain upstream v1.0.21
   as the rollback code version and record how to restore the backup.
4. Inspect the installed HACS version's replacement procedure. Switch the
   downloaded code provider to the public fork as a custom integration repository
   and select the exact approved release. Only one HACS repository may manage
   `custom_components/foxess_control`; do not delete the FoxESS integration entry
   under Settings / Devices & Services or create a second entry.
5. Restart HA once, then verify the same entry, credentials, entity IDs and
   existing services. Check logs for setup/recovery errors without invoking
   charging services. Validate Base Work Mode, Scheduler Status, Mode Status Read,
   and independent UTC timestamps against a read-only vendor-app view.
6. Keep parents' battery-charger `observe_only: true`, `exclusive_control: false`.
   Its current adapter still consumes the legacy mode sensor and needs a separate
   reviewed update; installing this fork does not unblock live charging by itself.

## Rollback

With no active smart operation, replace only the integration code with the
recorded upstream v1.0.21 and restart HA. Do not delete/recreate the config entry
or purge the entity registry. The fork introduces no config-entry or session
storage migration; the additive sensors will no longer be provided by upstream.
Verify existing entries/entities and service availability again. If code-only
rollback is insufficient, restore the verified pre-change HA backup using HA's
supported restore process; that is a separate user-approved operation.

## Maintaining the fork

Upstream notifications trigger review, never automatic merges or HA upgrades.
Fetch upstream changes deliberately and compare the minimal fork patch set and
storage/control compatibility before integrating them or returning to upstream.
Keep Forgejo authoritative and GitHub a one-way release distribution mirror.

Fork versions are independent of upstream releases. The initial proposal
`1.0.21.post1` was rejected before publication because the locally tested HA
AwesomeVersion library did not order it above SemVer `1.0.21`. Use SemVer
`1.0.22` and retain the upstream-base record rather than mix version schemes.
If upstream later uses the same version number, compare code and choose a new
fork version deliberately; a matching version number does not mean matching code.
