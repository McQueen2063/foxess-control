# Charge-write failure: containment and correction

## Live evidence (2026-11-02, Europe/Berlin)

Fork v1.0.23 on an H3-12.0-Smart was tested with separate user approval:
2000 W maximum, five-minute window 00:13–00:18, target 80%, SoC about 65%.
The start service returned FoxESS errno 40257. A subsequent successful independent
flag read reported the scheduler enabled, while Smart Operations remained idle.
The user later found no groups configured in the vendor app. A rejected write
therefore cannot be treated as proof that no inverter state changed.

Scoped ForceCharge cleanup also returned 40257. Its SelfUse schedule write ran
before the master-disable call, so the latter was never reached. Polling was
restored to 300 seconds and the integration paused to prevent cleanup retries.
The user selected and saved Self-Use in FoxESS Cloud 2.0 and confirmed it on the
dashboard. No success for charging, power enforcement or automatic stop is claimed.

Related upstream reports: [H3 #17](https://github.com/nicois/foxess-control/issues/17)
and [EVO #28](https://github.com/nicois/foxess-control/issues/28). They identify
possible range/payload-version differences, not the rejected field on this device.
No upstream code was automatically merged and no alternative payload was live-probed.

## Correction under review (not installed)

- Charge-only cleanup verifies the SelfUse base, directly disables the master
  using `/op/v1/device/scheduler/set/flag`, and independently reads back the flag.
  No replacement schedule, reserve, power or base-mode write is needed.
- Stored groups remain in the inverter but disabled. A later charge merge
  replaces same-mode groups. Do not manually enable the master over stored
  groups without reviewing them. Other-mode scoped cleanup is unchanged.
- A charge-only write from a verified disabled master and SelfUse base gets a
  bounded idle rollback on failure, including timeout/ambiguous failures.
  Rollback uses only the direct master disable plus verification. Failure still
  raises the original start error; failed rollback raises an explicit manual
  recovery error. Pre-existing enabled/mixed-mode schedules are not disabled by
  this guard. Exclusive authority and independent status checks remain required.
- A disabled schedule's stored groups are no longer reported as an active legacy
  mode. The result is unknown/None, not an inferred SelfUse state; battery-charger's
  existing independent base/master guard handles this idle case.
- Explicit diagnostics downloads read `/op/v3/device/scheduler/get` for declared
  properties, even while the entry is paused, without loading it or running
  recovery. Unsupported/empty replies are errors, never guessed constraints.
  The last attempted schedule and rollback outcome are included when available;
  this record is in-memory and does not survive reload/restart.

This is a containment/diagnostic fix, not an H3 payload compatibility claim.
Write payloads and endpoint version remain unchanged until device capabilities
have been inspected. Keep the installed integration paused and battery-charger
observe-only. Review, full runtime CI, release/install approval and a new explicit
live-test approval are required before further inverter writes.
