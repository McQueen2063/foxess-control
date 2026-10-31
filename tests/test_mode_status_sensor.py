"""Status sensors must not turn fresh telemetry into fresh mode evidence."""

import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.foxess_control.mode_status_sensor import FoxESSModeStatusSensor

from .test_coordinator import _make_coordinator
from .test_mode_status_coordinator import _inverter


def _sensors():
    coord = _make_coordinator(_inverter())
    coord.data = coord._fetch_all()
    sensors = [
        FoxESSModeStatusSensor(coord, SimpleNamespace(entry_id="existing"), key, {})
        for key in ("base_work_mode", "scheduler_status", "mode_status_read")
    ]
    return coord, sensors


def test_successful_disabled_status_and_stable_ids() -> None:
    _, sensors = _sensors()
    assert [s.native_value for s in sensors] == ["SelfUse", "disabled", "success"]
    assert [s.unique_id for s in sensors] == [
        "existing_base_work_mode",
        "existing_scheduler_status",
        "existing_mode_status_read",
    ]
    assert sensors[0].extra_state_attributes["reads"]["base"]["success"] is True


@pytest.mark.parametrize("failed", ["base", "scheduler"])
def test_partial_failure_does_not_hide_other_read(failed: str) -> None:
    coord, sensors = _sensors()
    coord.data["_mode_status"][failed].update(success=False, value=None)
    assert sensors[2].native_value == "failed"
    assert sensors[0 if failed == "base" else 1].native_value is None
    assert sensors[1 if failed == "base" else 0].native_value is not None


def test_stale_status_is_not_refreshed_by_telemetry() -> None:
    coord, sensors = _sensors()
    now = datetime.datetime.now(datetime.UTC)
    for read in coord.data["_mode_status"].values():
        read["last_success"] = (now - datetime.timedelta(hours=1)).isoformat()
    coord.data["_data_last_update"] = now.isoformat()
    with patch(
        "custom_components.foxess_control.mode_status_sensor.dt_util.utcnow",
        return_value=now,
    ):
        assert [s.native_value for s in sensors] == [None, None, "stale"]


@pytest.mark.parametrize(
    "value,expected",
    [
        ({"enable": True, "support": True}, "enabled"),
        ({"enable": False, "support": False}, "unsupported"),
    ],
)
def test_scheduler_states(value, expected) -> None:
    coord, sensors = _sensors()
    coord.data["_mode_status"]["scheduler"]["value"] = value
    assert sensors[1].native_value == expected


def test_initial_state_is_unknown() -> None:
    coord, sensors = _sensors()
    coord.data = {}
    assert all(s.native_value is None for s in sensors)


@pytest.mark.parametrize(
    "value", [{}, {"support": True}, {"enable": "0", "support": True}]
)
def test_malformed_scheduler_value_never_reports_disabled(value) -> None:
    coord, sensors = _sensors()
    coord.data["_mode_status"]["scheduler"]["value"] = value
    assert sensors[1].native_value is None
