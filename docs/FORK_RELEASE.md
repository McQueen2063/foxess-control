# Fork release review: 1.0.26

**Status: prepared for review; no tag, publication, installation or v1 opt-in approved yet.**

Installed baseline v1.0.25 is enabled for telemetry with the user's accepted
startup recovery/cleanup risk. Leave it running; battery-charger remains
`observe_only: true`, `exclusive_control: false`. No new control test is approved.

## v1.0.26 gates

- [x] PR #18 reviewed/merged; full PR run #49 passed.
- [ ] Merged runtime commit `8edb6c05105acf34a070b2c302d4ffc3525df5da` passes
  [run #50](https://git.kernel32.de/utt/foxess-control/actions/runs/50).
- [ ] Version/docs-only release PR reviewed/merged; exact merge passes fast
  metadata checks. Heavy jobs should skip; no duplicate manual simulation needed.
- [ ] User approves exact release commit, new `v1.0.26` tag and
  [draft GitHub Release notes](RELEASE_v1.0.26.md).
- [ ] Tag in Forgejo, verify identical GitHub mirror commit/tag, then publish
  the GitHub Release separately and verify HACS availability.

## Installation and explicit v1 selection

After separate installation approval and a fresh verified HA backup, update the
existing HACS fork and restart. Preserve the original entry, credentials/session
storage and entities. Do not disable an otherwise healthy monitoring entry merely
to install this release. Verify no active smart session before restart and obtain
separate approval to resolve one if found. Retain v1.0.25 for code rollback.

Default scheduling remains v0. With separate configuration approval, change only
**Cloud scheduler API** to `v1` and verify reload, unchanged options and fresh
telemetry. Reload may run normal session recovery; selecting v1 is not permission
to start a new control session. No automatic endpoint retry is introduced.

Read [the payload comparison](H3_SCHEDULER_COMPARISON.md) before any bounded live
test. V1 is a compatibility candidate, not proven H3 support. Existing full HA
simulator lifecycle tests use default v0; v1 has exact mocked transport/payload/
rollback and options-flow coverage. Neither proves charging-power enforcement.
Keep battery-charger observe-only; request new explicit control-test approval.

---

# Historical v1.0.25 release-review record

**Subsequent result:** published/installed v1.0.25 passed the live read-only
capability check. The user then accepted startup recovery/cleanup risk and approved
re-enabling the existing entry for monitoring; it loaded normally with SelfUse,
disabled scheduler and idle Smart Operations. Battery-charger remains observe-only.
No new live charge test was performed. See [comparison/current plan](H3_SCHEDULER_COMPARISON.md).
The checklist below is the historical release-preparation record.

**Status: prepared for review; no tag, publication or installation approval yet.**

Installed baseline is v1.0.24, user-disabled across restart. Keep battery-charger
`observe_only: true`, `exclusive_control: false`. Do not enable the entry merely
to obtain diagnostics. H3 schedule payload compatibility remains unresolved.

## v1.0.25 release gates

- [x] PR #15 (cold-paused capability flow) and #16 (build-lock budget) merged.
- [x] Full PR run #45 green: 41 HA passed / 27 intentional skips, including actual
  cold-start config-flow routing with the original entry disabled. PR #43 also
  passed. Main #44 failed shared image-build lock setup, not runtime assertions.
- [ ] Merged runtime commit `aa59e4b3c3f9f1693ffa9d95ece04dd970774ac2` passes
  [run #46](https://git.kernel32.de/utt/foxess-control/actions/runs/46).
- [ ] Version/docs-only release PR reviewed/merged; exact release merge passes
  fast metadata checks. Heavy jobs should skip, not run a duplicate simulation.
- [ ] User approves exact release commit, new `v1.0.25` tag and
  [draft GitHub Release text](RELEASE_v1.0.25.md).
- [ ] Tag only the approved commit in Forgejo, verify identical GitHub mirror
  tag/commit, then publish the GitHub Release separately and verify HACS availability.

## v1.0.25 installation and read verification

Installation needs separate approval and a fresh verified HA backup. Update only
the existing HACS fork; preserve the original disabled entry, credentials/session
storage and entity identities. Retain v1.0.24 code for rollback while disabled.
Restart HA, verify installed version and `disabled_by: user` / `not_loaded`.

Then explicitly approve the [read-only config-flow action](PAUSED_CAPABILITY_ACCESS.md):
open FoxESS Control's Add integration flow, select the paused-entry scheduler
diagnostics action and the existing entry, then confirm the read. Do not create a
second entry or choose cloud setup. It must finish without entry creation/enabling
or setup/recovery, using only the v3 capability read. Ordinary diagnostics may
remain unavailable; this action is deliberately independent of domain setup.

Unsupported/failed results are not guessed constraints. Inspect declared properties
before proposing any payload correction. No re-enable, live control test, automatic
HA update or upstream merge is authorized by release preparation/publication.
Multi-hour soak and broader UI E2E remain unverified.

---

# Historical v1.0.24 release-review record

**Subsequent installation evidence:** v1.0.24 was published, installed through
HACS and restarted while the original entry stayed user-disabled. Ordinary
diagnostics were unavailable after that cold start: HA had not registered the
never-loaded domain's handler. The paused-read instruction below was incomplete;
see [observed gap and reviewed correction path](PAUSED_CAPABILITY_ACCESS.md).
Do not enable the integration to work around it. The original review follows.

**Status: prepared for review; not approved for tagging, publication or installation.**

Published/installed baseline is v1.0.23. The installed FoxESS Control entry remains
user-disabled. Battery-charger remains `observe_only: true`, `exclusive_control: false`.

## v1.0.24 gates

- [x] Containment/diagnostics PR #11 and deterministic WS test PR #12 merged.
- [x] PR validation: run #35 passed; unchanged run #37 retry passed all jobs,
  including HA 40 passed / 27 intentional skips, on a different runner from the
  failed attempt. The first attempt had HA startup crashes, not assertion failures.
- [ ] Merged runtime commit `823b21e2ef76d9a4c376738e73dc1ce6a5774fe6` passes
  [run #38](https://git.kernel32.de/utt/foxess-control/actions/runs/38).
- [ ] Version/docs-only release PR reviewed and merged; exact release commit
  passes metadata/version checks. Skipped heavy jobs add no simulation evidence.
- [ ] User approves exact release commit, new `v1.0.24` tag and
  [draft Release text](RELEASE_v1.0.24.md). Do not move v1.0.23.
- [ ] Tag in Forgejo, verify identical GitHub mirror tag/commit, then publish
  GitHub Release separately and verify HACS availability. No automatic HA update.

## v1.0.24 installation and diagnostic-only scope

After separate installation approval, take/verify an HA backup, retain v1.0.23 as
code rollback, and update the existing HACS fork without recreating the entry or
changing entity identities. Keep the entry disabled across update/restart and
verify installed version and disabled state. Do not enable it to obtain diagnostics:
setup/recovery could write to the inverter even with battery-charger observe-only.

With approval, request only the paused-entry capability diagnostics. They read
`/op/v3/device/scheduler/get` without setup/recovery or scheduler writes. Inspect
declared constraints before proposing H3 payload changes; absent properties are
an explicit unsupported result, not permission to guess or probe writes.

See [containment semantics and remaining limitations](CHARGE_WRITE_FAILURE.md).
This release does not establish H3 payload compatibility or power-cap enforcement.
Any re-enable or live-control test needs new explicit approval. Multi-hour soak
and broader UI E2E remain unverified. If rolling back code, preserve the disabled
entry: v1.0.23 retains the known failed-write/cleanup problem.

---

# Historical v1.0.23 release-review record

v1.0.23 was published and installed; live start/cleanup subsequently failed with
40257 and required vendor-app recovery. The checklist below is historical, not
current installation guidance.

**Status: prepared for review; publication and installation not yet approved.**

Published baseline: fork v1.0.22 (`b51348a`), based on upstream v1.0.21.
Implementation merge: `b9943da44caf233e469229312556a547929c9997`.
Forgejo is authoritative; GitHub is a one-way HACS distribution mirror.

## Current release gates

- [x] Implementation reviewed and merged (PR #8).
- [x] Post-merge [run #30](https://git.kernel32.de/utt/foxess-control/actions/runs/30)
  passed unit/lint/type checks and HA simulator lifecycle tests: 40 passed,
  27 intentional backend-specific skips. HA tests took about 40 minutes.
- [ ] Release PR reviewed/merged; exact release merge commit passes CI including
  the manifest/changelog/version-order test. Record its SHA and run URL.
- [ ] User approves the exact release commit, `v1.0.23` tag and
  [draft GitHub Release text](RELEASE_v1.0.23.md).
- [ ] Tag only the approved commit in Forgejo, verify the GitHub mirror matches,
  then publish the GitHub Release separately. No automatic deployment.
- [ ] Verify HACS offers v1.0.23 before scheduling the HA update.

Version/docs-only releases use the [fast CI gate](CI_TEST_GATES.md). A skipped HA
job does not add simulation evidence; the unchanged runtime was validated in
run #30. Manual dispatch can repeat the full suites if needed.

## Current scope and HA update

See [control changes and limitations](CHARGE_CONTROL_REVIEW.md). The release
adds an optional charge-only ceiling and fixes charge-only cloud cleanup; it
does not establish H3 hardware enforcement or an independent target-SoC cutoff.
Mode-scoped clearing still requires exclusive charging authority. Multi-hour
soak and broader UI E2E remain unverified; the v1.0.22 read-only soak deferral
must not be treated as approval for production controls in this release.

After separate installation approval, proceed one user-confirmed step at a time:

1. Confirm no active smart operation or pending recovery/cleanup. The integration
   can write during recovery even while battery-charger is observe-only.
2. Take and verify an HA backup. Retain fork v1.0.22 as the code rollback version.
3. Update the existing fork through HACS to the exact approved v1.0.23 release.
   Do not remove/recreate the integration entry or change entity identities.
4. Restart HA, verify the installed version, original entry/entities, read-only
   status timestamps and absence of setup/recovery errors.
5. Set **Maximum charge power (W)** to the separately agreed conservative ceiling
   (currently planned: 4000 W). Confirm the option survives reload and status
   polling resumes. This does not authorize a charging service call.
6. Keep battery-charger `observe_only: true`, `exclusive_control: false`.
   A bounded live power/stop test requires separate explicit approval.

Rollback with no active operation: restore fork v1.0.22 code and restart HA
without deleting the entry. The older code ignores the new optional ceiling;
do not rely on that ceiling after downgrade. If code-only rollback is insufficient,
restore the verified backup through HA's supported process. No database or
session-storage migration is introduced by v1.0.23.

---

## Historical v1.0.22 release-review record

The following is the original checklist, not the current release status.
v1.0.22 was subsequently published at `b51348a` after green run #26 and installed
with preserved entry/entity identities. Its read-only sensors were verified live,
including independently advancing successful base/scheduler timestamps.

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
- [x] Existing HA-container control-lifecycle module and status smoke:
  [run #22](https://git.kernel32.de/utt/foxess-control/actions/runs/22), commit
  `4c11156`, 40 passed and 27 intentional backend-specific skips.
- [x] User approved deferring the multi-hour soak suite for this read-only status
  release on 2026-10-31. Soak tests have NOT passed or run as part of this gate.
- [ ] Review sequential cloud-read assumptions, freshness contract, and API
  compatibility on the target device. Live read verification is still pending.
- [ ] Explicit approval of release commit, tag, and GitHub Release text.

The lifecycle CI change selects the complete `tests/e2e/test_e2e.py` module
(66 cloud/entity parameterized cases collected locally), plus the status smoke
test, with two workers and a 120-minute job timeout. Some cloud-only/entity-only
cases intentionally skip the other mode. The broader UI E2E and multi-hour soak
suite are not included. Collection is not execution; record actual CI results
before checking off any gate.

The first lifecycle run (#21) reported 28 passed, 27 skipped and 12 failures,
all in entity mode. HA rejected existing select labels such as `Self Use`
because the inherited Work Mode sensor declared only cloud enum values. The
follow-up expands accepted options from the existing adapter label map, without
normalizing returned states, changing entity IDs or altering control writes.
Regression tests reproduce HA's enum validation failure for all five labels.
The correction passed run #22 in both cloud and entity modes. This is simulator
validation, not validation on a physical inverter. The merge commit `b6271c0`
has its own post-merge run #23; record its result separately.

The known H3 scheduler write/power-limit compatibility concern is **not fixed**
here. It must be inspected before any later live control testing. Publishing
this fork does not authorize battery writes or enabling battery-charger control.

## Approved scope: read-only status release

This release is intended to install and verify the new read-only status sensors,
not to commission charging/discharging. Deferring soak tests does not remove
their value or imply successful long-duration validation. Broader UI E2E and
multi-hour soak coverage remain unverified; existing controls are still present
in the integration, not technically disabled by this release.

Parents must remain `observe_only: true`, `exclusive_control: false`. Do not
invoke control services, run live control tests, or enable automations that can
write to the inverter as part of migration. Before any later live-control work,
separately review the H3 power-limit concern, active-session/recovery behavior,
adapter changes, and required additional test coverage, then obtain explicit
approval. Target-device read-only API compatibility will be checked during the
controlled installation/verification; no pre-install live compatibility success
is claimed. Release publication and HA installation still require separate
explicit approval and a verified backup before installation.

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
