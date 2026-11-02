# Scheduler capabilities after a disabled cold start

## Observed gap in v1.0.24

After the approved v1.0.24 HACS update and HA restart, the original entry remained
`not_loaded` / `disabled_by: user`, with options preserved. HACS reported v1.0.24
and no FoxESS system-log errors were present. Download diagnostics nevertheless
returned unavailable. No scheduler capability request or control was performed.

HA registers diagnostics platforms for loaded integration domains. If the only
entry is disabled across restart, the domain is never loaded and the diagnostics
handler is not registered. The v1.0.24 function handles absent runtime data, but
its mocked tests did not exercise HA's cold-start handler registration. It can
work after unloading a previously loaded domain; that is not a cold-start guarantee.

**Do not enable the integration to expose diagnostics.** Entry setup can invoke
session recovery and writes, regardless of battery-charger's observe-only setting.

## Correction under review (not installed)

Use HA's independently accessible config flow for a read-only diagnostic action:

1. Open **Add integration → FoxESS Control**. This only opens the flow; do not
   enter credentials, select cloud setup, or create another integration entry.
2. Choose **Read scheduler capabilities for a paused inverter (no controls)**.
   This menu option exists only with an eligible saved user-disabled cloud entry.
3. Select that existing paused entry and explicitly submit the read confirmation.
4. The flow ends with a capability result and **does not create an entry**.
   `success: false` means unsupported/failed, with exception type and API errno
   only. It is not a guessed constraint and not permission to probe writes.

The flow rechecks saved entry eligibility on submission, uses its existing
credentials, calls only `/op/v3/device/scheduler/get`, redacts known identity keys,
and does not set up the integration domain/entry, enable/reload/update the entry,
start polling/web login, or restore sessions. Normal setup paths remain unchanged.
Ordinary diagnostics may still be unavailable; this is an independent read path,
not a workaround that registers domain services or silently enables controls.

## Regression coverage and gates

- Focused unit cases cover no-network menu/form display, submission revalidation,
  missing/unsupported capability replies, redaction and unchanged paused entry.
- Real-HA regression starts the existing disposable container with a user-disabled
  seeded entry, confirms ordinary diagnostics are unavailable, then traverses the
  actual config-flow API. A bounded path-only trace in the existing simulator must
  contain exactly one capability read, no login/poll/control calls. Entry identity,
  disabled state and configuration remain unchanged. Simulator properties are
  synthetic and do not represent this H3's actual constraints.
- Full CI, reviewed merge, separate release/install approval and another cold-start
  verification are required. Multi-hour soak and broader UI E2E remain unverified.
- Keep installed v1.0.24 paused and battery-charger observe-only. No live writes,
  automatic upstream merge, release, HA update or re-enable is authorized here.
