# H3 scheduler: payload/API comparison

## Result

The reconstructed v1.0.23 start and cleanup groups fit the device's declared v3
numeric ranges and work-mode list. We have no evidence for an out-of-range power,
SoC or time field in those groups. That does not prove the complete historical
request was accepted: the exact merged wire body was not archived before restart.

The strongest compatibility lead is the **deprecated v0 schedule endpoint on a
device advertising max-SoC support**. Official v1 documents flat group fields and
optional `maxSoc`; other users report v0 rejection on such devices. This is a
justified candidate correction, not a proven diagnosis or live compatibility claim.

## Reconstructed requests, not captured network traffic

Executed the actual group-builder and inverter methods from tag v1.0.23 against
a recording fake transport. Known test inputs: 00:13–00:18, 2000 W, reserve 15%,
API minimum 11%, HA target 80%. The charge service sets `fdSoc=100`; its 80% target
is HA-managed and was not sent as an independent inverter cutoff.

Both requests used `POST /op/v0/device/scheduler/enable`, with device identity
omitted here. Newly constructed start group:

```json
{
  "enable": 1,
  "startHour": 0, "startMinute": 13,
  "endHour": 0, "endMinute": 18,
  "workMode": "ForceCharge",
  "minSocOnGrid": 15, "fdSoc": 100, "fdPwr": 2000
}
```

Historical charge cleanup first constructed this replacement group:

```json
{
  "enable": 1,
  "startHour": 0, "startMinute": 0,
  "endHour": 23, "endMinute": 59,
  "workMode": "SelfUse",
  "minSocOnGrid": 15, "fdSoc": 15, "fdPwr": 4000
}
```

Both failed with 40257 live. A failed start nevertheless enabled the scheduler;
the cleanup never reached its master-disable call. Later releases corrected that
cleanup/rollback dependency. Historical additional merged groups cannot be proved
from this reconstruction, and no fresh write was made to recover old evidence.

## Actual H3 declared properties

The v1.0.25 read-only flow successfully fetched `/op/v3/device/scheduler/get`:

| Property | Declared constraint | Reconstructed value(s) |
| --- | --- | --- |
| `fdpwr` | 0–60000 W | 2000 / 4000 W |
| `fdsoc` | 10–100% | 100 / 15% |
| `minsocongrid` | 10–100% | 15% |
| `maxsoc` | 10–100% | omitted in legacy groups |
| `starthour`, `endhour` | 0–23 | within range |
| `startminute`, `endminute` | 0–59 | within range |
| `workmode` | includes `ForceCharge`, `SelfUse` | both present |

These are API declarations, not a 60 kW physical inverter/battery rating. The
response does not label fields required. `maxsoc` being present does not itself
prove either that v1 is mandatory or that v0 rejection was caused by its omission.

## Documentation and independent evidence

- [Official Open API documentation](https://www.foxesscloud.com/public/i18n/en/OpenApiDocument.html):
  v0 scheduler marked deprecated. v1 examples use flat `minSocOnGrid`, `fdSoc`,
  `fdPwr`, `maxSoc`; `maxSoc` is explicitly optional. v2/v3 use `extraParam` and
  are different request contracts, not endpoint-only replacements.
- [Upstream #28](https://github.com/nicois/foxess-control/issues/28): EVO owner
  reports flat v1 with `maxSoc` succeeded, flat v0 and nested parameters failed.
  Different device: corroboration only, not proof for this H3.
- [Upstream #17](https://github.com/nicois/foxess-control/issues/17): a separate
  H3 power-ceiling explanation does not fit our 2000 W request versus the measured
  declared range. Later H3-12.0-E reports remained unresolved after clamping.
- [Community v0/max-SoC report](https://foxesscommunity.com/viewtopic.php?t=2179):
  v0 writes on max-SoC-capable devices were reported to break later writes; the
  author confirmed recovery and switching to v1. This is anecdotal. Do not copy
  its reset schedules or perform recovery writes without explicit approval.

Power semantics remain model/API dependent: v1 docs call `fdPwr` maximum discharge
power; v3 explicitly describes charge/discharge power. V1 acceptance alone will
not prove charging-cap enforcement. Keep the existing 4000 W requested ceiling;
any future approved test must observe real charging power and stop behavior.

## Small candidate patch, not an API negotiation framework

- One explicit cloud option, `scheduler_api_version`: legacy `v0` default or
  opt-in `v1`. No automatic device guessing, write retries on other versions,
  additional capability polling or new read-only operating mode.
- With v1 selected, read/write flat v1 schedules and add missing `maxSoc: 100`,
  preserving an existing explicit `maxSoc` during schedule merges. Default 100
  deliberately preserves the existing HA-managed charging-target behavior; it
  does not silently turn the HA target into a claimed hardware cutoff.
- Preserve direct master-disable cleanup and verified-idle rollback. Record the
  actual selected endpoint/payload in existing diagnostics.
- Focused existing-style mocks check exact payloads, default-v0 behavior,
  preservation of existing maxSoc, and rollback without alternate-endpoint writes.

This candidate is not installed or live-tested. Reviewed CI/release/install and
explicit approval of any subsequent bounded control test are still required.

## Current live operation

The user subsequently accepted startup recovery/cleanup risk and authorized
re-enabling installed v1.0.25 to collect telemetry. The original entry is loaded;
initial reads confirmed SelfUse, disabled scheduler and idle Smart Operations.
No new charge test was triggered. Leave this monitoring running; battery-charger
stays observe-only. Earlier documents saying the integration must remain paused
describe the earlier installation/diagnostic phase, not a request to disable it now.
