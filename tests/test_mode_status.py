"""Strict, read-only status reads must not confuse unknown with disabled."""

from unittest.mock import Mock

import pytest
import requests

from custom_components.foxess_control.foxess.inverter import Inverter


@pytest.mark.parametrize("mode", ["SelfUse", "Feedin", "Backup", "PeakShaving"])
def test_base_mode_reads_device_setting(mode: str) -> None:
    client = Mock()
    client.post.return_value = {"value": mode}
    inverter = Inverter(client, "TEST-SN")

    assert inverter.get_base_work_mode() == mode
    client.post.assert_called_once_with(
        "/op/v0/device/setting/get", {"sn": "TEST-SN", "key": "WorkMode"}
    )
    client.get.assert_not_called()


@pytest.mark.parametrize(
    "result",
    [
        None,
        [],
        {},
        {"value": None},
        {"value": 0},
        {"value": ""},
        {"value": "ForceCharge"},
        {"value": "unrecognised"},
    ],
)
def test_invalid_base_mode_is_not_self_use(result: object) -> None:
    client = Mock()
    client.post.return_value = result

    with pytest.raises(ValueError, match="base work mode"):
        Inverter(client, "TEST-SN").get_base_work_mode()


@pytest.mark.parametrize("enabled", [0, 1, False, True])
@pytest.mark.parametrize("supported", [0, 1, False, True])
def test_scheduler_master_flag_is_explicit(
    enabled: int | bool,
    supported: int | bool,
) -> None:
    client = Mock()
    client.post.return_value = {"enable": enabled, "support": supported}

    assert Inverter(client, "TEST-SN").get_scheduler_flag() == {
        "enable": bool(enabled),
        "support": bool(supported),
    }
    client.post.assert_called_once_with(
        "/op/v1/device/scheduler/get/flag", {"deviceSN": "TEST-SN"}
    )


@pytest.mark.parametrize(
    "result",
    [
        None,
        [],
        {},
        {"enable": 0},
        {"support": 1},
        {"enable": "false", "support": 1},
        {"enable": "0", "support": 1},
        {"enable": None, "support": 1},
        {"enable": 2, "support": 1},
        {"enable": 0.0, "support": 1},
        {"enable": 0, "support": "true"},
    ],
)
def test_invalid_scheduler_flag_is_not_disabled(result: object) -> None:
    client = Mock()
    client.post.return_value = result

    with pytest.raises(ValueError, match="scheduler flag"):
        Inverter(client, "TEST-SN").get_scheduler_flag()


@pytest.mark.parametrize("method", ["get_base_work_mode", "get_scheduler_flag"])
def test_status_timeout_remains_a_failure(method: str) -> None:
    client = Mock()
    client.post.side_effect = requests.Timeout("test timeout")

    with pytest.raises(requests.Timeout):
        getattr(Inverter(client, "TEST-SN"), method)()
    assert client.post.call_count == 1
