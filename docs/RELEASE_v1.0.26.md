# FoxESS Control v1.0.26

Draft for review; publish only after release gates and explicit approval.

## Changes

- Add one explicit cloud option: `scheduler_api_version`, legacy `v0` by default
  or opt-in `v1`. Existing installations are not automatically migrated.
- V1 reads/writes flat scheduler groups and supplies missing `maxSoc: 100`, while
  preserving an existing explicit maxSoc during schedule merges. HA-managed
  charging-target behavior is unchanged; no new independent target cutoff is claimed.
- Retain direct master-disable charge cleanup and verified-idle failed-write
  rollback. No automatic retry against another scheduler API version.
- Diagnostics show the selected API version and actual attempted endpoint/payload.

## Why this candidate exists

Reconstructed v1.0.23 test groups fit the H3's declared ranges. The strongest
remaining lead is deprecated v0 scheduling on a device advertising max-SoC support.
Official v1 documentation uses flat fields and optional maxSoc; independent
reports corroborate v0 rejection on other max-SoC-capable devices. The old full
wire request was not archived, so its reconstructed groups are not a captured
request and cannot prove the exact cause of 40257.

This is a compatibility candidate, **not a proven H3 fix**. In particular, accepting
a schedule does not prove that fdPwr enforces a charging-power limit. The declared
60000 W API range is not a physical safe-power rating. Keep the configured 4000 W
requested ceiling and independently observe power during any later approved test.

## Validation and upgrade

PR #18 full CI #49 passed. Merged-main #50 and exact-release metadata checks must
pass before publication. Existing real-HA simulator lifecycle tests cover default
v0; v1 is covered by focused mocked payload/rollback and options-flow tests, not
a real-HA v1 lifecycle or live H3 write. Multi-hour soak and broader UI E2E remain
unverified.

Back up HA before a separately approved update. Preserve the original integration
entry, credentials/session storage and entity identities. Monitoring can continue;
there is no new read-only operating mode. With separate approval, select **Cloud
scheduler API → v1** in integration options and verify reload/readings. That does
not approve a charging test. Battery-charger remains observe-only.

Forgejo is authoritative; GitHub is the one-way HACS distribution mirror.
