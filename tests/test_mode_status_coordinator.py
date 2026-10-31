"""Mode status is independent of legacy schedule-derived mode and telemetry."""

import datetime
from copy import deepcopy
from unittest.mock import MagicMock

import pytest

from custom_components.foxess_control.foxess.inverter import Inverter

from .test_coordinator import _make_coordinator


def _inverter() -> MagicMock:
    inv = MagicMock(spec=Inverter)
    inv.get_real_time.return_value = {"SoC": 50}
    inv.get_current_mode.return_value = None
    inv.get_base_work_mode.return_value = "SelfUse"
    inv.get_scheduler_flag.return_value = {"enable": False, "support": True}
    return inv


def test_disabled_scheduler_is_success_not_unknown() -> None:
    coord = _make_coordinator(_inverter())
    data = coord._fetch_all()
    assert data["_work_mode"] is None
    status = data["_mode_status"]
    assert status["base"]["value"] == "SelfUse"
    assert status["scheduler"]["value"] == {"enable": False, "support": True}
    for read in status.values():
        assert read["success"] is True
        assert datetime.datetime.fromisoformat(read["last_success"]).tzinfo


@pytest.mark.parametrize("failed", ["base", "scheduler"])
def test_failed_read_clears_value_but_retains_last_success(failed: str) -> None:
    inv = _inverter()
    coord = _make_coordinator(inv)
    coord.data = coord._fetch_all()
    previous = coord.data["_mode_status"][failed]["last_success"]
    method = inv.get_base_work_mode if failed == "base" else inv.get_scheduler_flag
    method.side_effect = TimeoutError("no reply")

    data = coord._fetch_all()
    read = data["_mode_status"][failed]
    assert read["success"] is False
    assert read["value"] is None
    assert read["last_success"] == previous
    assert read["error"] == "TimeoutError"
    other = "scheduler" if failed == "base" else "base"
    assert data["_mode_status"][other]["success"] is True

    method.side_effect = None
    assert coord._fetch_all()["_mode_status"][failed]["success"] is True


@pytest.mark.asyncio
async def test_telemetry_failure_invalidates_status_without_losing_timestamp() -> None:
    inv = _inverter()
    coord = _make_coordinator(inv)
    coord.data = coord._fetch_all()
    previous = coord.data["_mode_status"]["base"]["last_success"]
    inv.get_real_time.side_effect = TimeoutError()
    data = await coord._async_update_data()
    assert data["_mode_status"]["base"]["success"] is False
    assert data["_mode_status"]["base"]["last_success"] == previous
    assert coord.data["_mode_status"]["base"]["success"] is True


def test_websocket_does_not_refresh_mode_status() -> None:
    coord = _make_coordinator(_inverter())
    coord.data = coord._fetch_all()
    previous = deepcopy(coord.data["_mode_status"])
    coord.inject_realtime_data({"SoC": 51, "batChargePower": 1.0})
    assert coord.data["_mode_status"] == previous
