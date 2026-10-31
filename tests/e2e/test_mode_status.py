"""Load the fork into real, disposable HA; read only from a local simulator."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from .ha_client import HAClient

pytestmark = pytest.mark.slow


@pytest.fixture(scope="session")
def connection_mode() -> str:
    """The new status endpoints are cloud-only, not entity-mode sensors."""
    return "cloud"


def test_mode_status_loads_without_reconfiguring_entry(ha_e2e: HAClient) -> None:
    """The existing seeded config entry gets additive status entities."""
    ha_e2e.wait_for_state("sensor.foxess_mode_status_read", "success", timeout_s=90)
    assert ha_e2e.get_state("sensor.foxess_base_work_mode") == "SelfUse"
    assert ha_e2e.get_state("sensor.foxess_scheduler_status") == "disabled"
    # Preserve the legacy schedule-derived sensor rather than pretending that
    # an absent schedule proves an effective mode.
    assert ha_e2e.get_state("sensor.foxess_work_mode") == "unknown"
    assert float(ha_e2e.get_state("sensor.foxess_battery_soc")) >= 0
    reads = ha_e2e.get_attributes("sensor.foxess_mode_status_read")["reads"]
    for key in ("base", "scheduler"):
        read = reads[key]
        assert read["success"] is True
        assert read["error"] is None
        timestamp = datetime.datetime.fromisoformat(read["last_success"])
        assert timestamp.tzinfo is not None
        age = (datetime.datetime.now(datetime.UTC) - timestamp).total_seconds()
        assert 0 <= age < 120
    assert reads["scheduler"]["value"] == {"enable": False, "support": True}
