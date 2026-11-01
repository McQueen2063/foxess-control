# v1.0.23 — charge-power ceiling and idle scheduler cleanup

Draft release text; publish only after approval of the exact green release commit.

Maintained fork based on upstream v1.0.21, building on fork v1.0.22.

## Changes

- Optional **Maximum charge power (W)** integration option for smart charging.
  Excessive requests fail before writes; omitted power uses the configured
  ceiling, bounded by the integration's inverter rating.
- Charge-only cloud cleanup restores a SelfUse baseline, verifies the base mode,
  then disables the scheduler master switch. Failed cleanup is retried.
- Other non-SelfUse schedules retain existing mode-scoped behavior. Entity-mode
  cleanup and unscoped clearing are unchanged.
- Existing integration entry, domain, entity identities and session formats are
  preserved. Update the existing fork; do not recreate the integration entry.

## Validation and limitations

Implementation passed unit/lint/type checks and real-HA simulator lifecycle
tests (40 passed, 27 backend-specific skips; Forgejo run #30). Record the exact
release commit and its green CI URL before publication.

Actual H3 power-cap enforcement is not yet verified. Target SoC remains managed
by HA; the inverter charge schedule still uses `fdSoc: 100`. Clearing is scoped
by mode, not session ownership. Multi-hour soak and broader UI E2E remain
unverified. This release does not authorize unattended or live inverter control.

Before updating, confirm no active smart operation/pending cleanup and take an
HA backup. Keep battery-charger observe-only. Retain v1.0.22 for rollback.
