# FoxESS Control v1.0.24

Draft for review; publish only after release gates and explicit approval.

## Changes

- Charge-only cleanup directly disables the scheduler master over verified
  SelfUse and independently verifies the result, without writing a replacement
  schedule. Already-idle cleanup is read-only; stored groups remain disabled.
- Failed charge-only writes from verified disabled/SelfUse idle attempt bounded
  master-disable rollback. Existing enabled/mixed-mode schedules are not disabled
  by this guard. Failed rollback explicitly requires manual recovery.
- Disabled stored groups are no longer reported as an active legacy mode.
- Explicit diagnostics downloads can read declared v3 scheduler capabilities
  while the integration is paused, without loading it or invoking recovery/writes.
  Loaded entries also expose the in-memory last schedule attempt/rollback outcome.
- Deferred-start WebSocket lifecycle test uses existing simulator telemetry to
  trigger the transition rather than guessing its future start deadline.

## Important limitations

This contains the observed H3 partial-write failure; it does **not** fix or prove
H3 schedule payload compatibility. Start and cleanup on v1.0.23 returned 40257;
failed start nevertheless enabled scheduling. No alternate write payload/endpoint
is introduced. Actual charging-power cap enforcement remains unverified.

The inverter retains stored groups when master-disabled. Do not manually enable
the master over unreviewed groups. Preserve existing exclusive-authority checks.
Diagnostics may report unsupported capability properties; no limits are guessed.

Keep the affected installation paused and battery-charger observe-only. Updating
does not authorize re-enabling the integration or further live writes. Back up HA
before any separately approved installation; retain the existing config entry,
credentials, session storage and entity identities.

## Validation

PR runtime validation passed (run #35); deterministic-transition PR run #37 retry
passed all jobs, including 40 HA cases and 27 intentional skips. Its first attempt
had three container startup failures; unchanged code passed on a different runner.
Merged-main run #38 and exact-release metadata checks must pass before publication.
Multi-hour soak and broader UI E2E have not been validated for this release.

Forgejo is authoritative; GitHub is the one-way HACS distribution mirror.
