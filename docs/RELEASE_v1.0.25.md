# FoxESS Control v1.0.25

Draft for review; publish only after release gates and explicit approval.

## Changes

- Add an explicit read-only scheduler-capability action in the config flow for
  an existing user-disabled, not-loaded cloud entry. It works after a disabled
  cold start, when HA has not registered the ordinary diagnostics handler.
- Opening the action performs no network call. Submitting rechecks eligibility,
  uses saved credentials for `/op/v3/device/scheduler/get`, redacts known identity
  keys and finishes without creating, enabling or modifying an entry. No domain
  setup, session recovery, polling, web login or inverter-control writes run.
- Add a real-HA cold-start regression with exactly one simulator capability read
  and unchanged paused entry/domain state.
- Correct the CI image-build lock wait to cover the existing bounded build budget;
  add build-duration logging and failure/timeout lock-release regressions.

## Important limitations

v1.0.24's diagnostics function could handle a paused entry, but HA did not register
its handler when the domain stayed disabled across restart. This release adds an
independent read path; do not enable the integration to expose ordinary diagnostics.

This does **not** establish H3 schedule payload compatibility or charging-power-cap
enforcement. Unknown/unsupported capability responses are errors, not guessed
limits. No alternate scheduler write payload or endpoint is introduced.

Keep the affected installation disabled and battery-charger observe-only. Back up
HA before any separately approved update. Preserve the existing entry, credentials,
session storage and entity identities. After update/restart, use **Add integration
→ FoxESS Control → Read scheduler capabilities for a paused inverter (no controls)**,
select the existing paused entry and confirm the read. The flow ends without
creating an entry. Do not choose cloud setup or add a duplicate entry.

## Validation

Full PR CI passed in #43 and #45. Run #45 included 41 HA passes and 27 intentional
skips, including the actual cold-start capability-flow test. Main #44 failed shared
build-lock setup; it did not report control assertion failures. Main #46 and exact
release metadata checks must pass before publication. Multi-hour soak and broader
UI E2E remain unverified. Simulator properties are not real H3 constraints.

Forgejo is authoritative; GitHub is the one-way HACS distribution mirror.
