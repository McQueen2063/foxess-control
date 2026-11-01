# Charge-control correction (unreleased)

This change does not authorize live controls or change installed deployments.
Keep battery-charger observe-only until a separate live test is approved.

- `smart_charge.power` must not exceed the integration's optional **Maximum
  charge power** (`max_charge_power_w`) ceiling, capped at the inverter rating.
  This option is available in integration options for cloud and entity mode.
  Requests above it fail before schedule writes
  or cancellation of an existing session. An omitted power uses that ceiling.
  The automatically derived capacity × 1050 fallback is not an H3-specific
  hardware guarantee; configure an explicit conservative ceiling for testing.
- Scoped `clear_overrides(mode: ForceCharge)` and automatic charge cleanup now
  return charge-only schedules to a disabled scheduler with a verified SelfUse
  base. Cleanup writes a bounded SelfUse baseline first, preserving the configured
  grid reserve. Only then does it read the base and disable the master flag.
  A failed base read, conflicting base, or failed flag write raises an error;
  automatic/manual cleanup uses the existing pending-cleanup retry mechanism.
- If another non-SelfUse schedule remains, existing scoped-clear behavior is
  retained: other modes are kept and the scheduler is not disabled. Clearing
  remains mode-scoped, not owner/session-scoped; exclusive authority is required.
- Entity-mode control and unscoped clearing are unchanged. Existing SelfUse
  groups are treated as baseline, as they already are during schedule merge.
- Target SoC remains HA-managed (`fdSoc: 100` on the charge schedule). Neither
  hardware enforcement of the requested power nor an independent hardware target
  cutoff is claimed. A later live test must verify actual power and stop behavior.

Tests reuse existing mocks and the HTTP simulator. The only simulator addition
is the scheduler master-flag write endpoint; no new inverter physics is modeled.
