"""Read-only device mode status, independent of telemetry freshness."""

from __future__ import annotations

import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .coordinator import FoxESSDataCoordinator


class FoxESSModeStatusSensor(CoordinatorEntity[FoxESSDataCoordinator], SensorEntity):
    """Expose validated reads without claiming an effective inverter mode."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:state-machine"

    def __init__(
        self,
        coordinator: FoxESSDataCoordinator,
        entry: Any,
        key: str,
        device_info: Any,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = device_info
        self._attr_name, self._attr_options = {
            "base_work_mode": (
                "Base Work Mode",
                ["SelfUse", "Feedin", "Backup", "PeakShaving"],
            ),
            "scheduler_status": (
                "Scheduler Status",
                ["enabled", "disabled", "unsupported"],
            ),
            "mode_status_read": ("Mode Status Read", ["success", "failed", "stale"]),
        }[key]

    def _reads(self) -> dict[str, Any]:
        reads: dict[str, Any] = (self.coordinator.data or {}).get("_mode_status", {})
        return reads

    def _fresh(self, read: dict[str, Any]) -> bool:
        if read.get("success") is not True:
            return False
        try:
            timestamp = datetime.datetime.fromisoformat(read["last_success"])
            age = (dt_util.utcnow() - timestamp).total_seconds()
        except (KeyError, TypeError, ValueError):
            return False
        interval = self.coordinator.update_interval
        limit = max(60.0, interval.total_seconds() * 2 if interval else 60.0)
        return 0 <= age <= limit

    @property
    def native_value(self) -> str | None:
        reads = self._reads()
        if self._key == "mode_status_read":
            if not reads:
                return None
            if any(
                reads.get(k, {}).get("success") is not True
                for k in ("base", "scheduler")
            ):
                return "failed"
            return "success" if all(self._fresh(reads[k]) for k in reads) else "stale"
        read = reads.get("base" if self._key == "base_work_mode" else "scheduler", {})
        if not self._fresh(read):
            return None
        value = read.get("value")
        if self._key == "base_work_mode":
            return value if isinstance(value, str) else None
        if not isinstance(value, dict) or any(
            type(value.get(key)) is not bool for key in ("enable", "support")
        ):
            return None
        if value.get("support") is False:
            return "unsupported"
        return "enabled" if value.get("enable") is True else "disabled"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        # These timestamps are deliberately not tied to power/SoC or WS updates.
        return {"reads": self._reads()}
