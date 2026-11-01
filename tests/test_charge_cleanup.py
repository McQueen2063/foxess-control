"""Focused charge cleanup tests: mocked transport, no hardware simulation."""

from unittest.mock import MagicMock, call

import pytest

from custom_components.foxess_control.domain_data import build_config
from custom_components.foxess_control.foxess.client import FoxESSApiError
from custom_components.foxess_control.foxess.inverter import Inverter
from custom_components.foxess_control.foxess_adapter import _remove_mode_from_schedule
from custom_components.foxess_control.smart_battery.types import WorkMode


@pytest.mark.parametrize(
    "configured, expected", [(None, 12600), (4000, 4000), (20000, 12600)]
)
def test_charge_ceiling_is_optional_and_bounded_by_rating(
    configured: int | None, expected: int
) -> None:
    options = {} if configured is None else {"max_charge_power_w": configured}
    cfg = build_config(options, inverter_max_power_w=12600)
    assert cfg.charge_power_ceiling_w == expected
    assert cfg.max_power_w == 12600  # Discharge/rating semantics unchanged.


def _client(
    *,
    base: str = "SelfUse",
    enabled: bool = True,
    reject_schedule: bool = False,
    fail_disable: bool = False,
    ignore_disable: bool = False,
) -> tuple[MagicMock, dict[str, bool]]:
    """Mock HTTP responses, including the observed partial side effect."""
    client = MagicMock()
    state = {"enable": enabled}

    def post(path: str, payload: dict[str, object]) -> dict[str, object] | None:
        if path.endswith("/setting/get"):
            return {"value": base}
        if path.endswith("/scheduler/get/flag"):
            return {"enable": state["enable"], "support": True}
        if path.endswith("/scheduler/set/flag"):
            if fail_disable:
                raise RuntimeError("flag write failed")
            if not ignore_disable:
                state["enable"] = False
            return None
        if path.endswith("/scheduler/enable"):
            state["enable"] = True
            if reject_schedule:
                raise FoxESSApiError(40257, "Rejected after enabling master")
            return None
        raise AssertionError(f"Unexpected endpoint {path}")

    client.post.side_effect = post
    return client, state


def test_finish_charge_disables_master_without_any_schedule_write() -> None:
    client, state = _client()
    inv = Inverter(client, "TEST")
    inv.finish_charge(20, 4000)
    assert state["enable"] is False
    assert client.post.call_args_list == [
        call("/op/v0/device/setting/get", {"sn": "TEST", "key": "WorkMode"}),
        call("/op/v1/device/scheduler/get/flag", {"deviceSN": "TEST"}),
        call("/op/v1/device/scheduler/set/flag", {"deviceSN": "TEST", "enable": 0}),
        call("/op/v1/device/scheduler/get/flag", {"deviceSN": "TEST"}),
    ]


def test_already_restored_idle_does_not_send_another_write() -> None:
    client, _ = _client(enabled=False)
    Inverter(client, "TEST").finish_charge(20, 4000)
    assert all("get" in c.args[0] for c in client.post.call_args_list)


@pytest.mark.parametrize("base", ["Backup", "unexpected"])
def test_finish_charge_never_disables_over_conflicting_or_unknown_base(
    base: str,
) -> None:
    client, state = _client(base=base)
    inv = Inverter(client, "TEST")
    with pytest.raises(ValueError):
        inv.finish_charge(20, 4000)
    assert state["enable"] is True
    assert not any("set/flag" in c.args[0] for c in client.post.call_args_list)


def test_cleanup_retry_with_selfuse_baseline_still_disables_master() -> None:
    inv = MagicMock(spec=Inverter)
    inv.get_schedule.return_value = {
        "groups": [
            {
                "enable": 1,
                "workMode": "SelfUse",
                "startHour": 0,
                "startMinute": 0,
                "endHour": 23,
                "endMinute": 59,
                "minSocOnGrid": 11,
                "fdSoc": 11,
                "fdPwr": 4000,
            }
        ]
    }
    _remove_mode_from_schedule(inv, WorkMode.FORCE_CHARGE, 20, 4000)
    inv.finish_charge.assert_called_once_with(20, 4000)
    inv.set_schedule.assert_not_called()


def test_failed_master_write_is_not_reported_as_success() -> None:
    client, _ = _client(fail_disable=True)
    with pytest.raises(RuntimeError, match="flag write failed"):
        Inverter(client, "TEST").finish_charge(20, 4000)
    assert not any(
        c.args[0].endswith("/scheduler/enable") for c in client.post.call_args_list
    )


def test_successful_disable_response_requires_disabled_readback() -> None:
    client, _ = _client(ignore_disable=True)
    with pytest.raises(RuntimeError, match="could not be verified"):
        Inverter(client, "TEST").finish_charge(20, 4000)


@pytest.mark.parametrize("already_enabled", [False, True])
def test_partial_charge_write_rolls_back_only_verified_idle(
    already_enabled: bool,
) -> None:
    client, state = _client(enabled=already_enabled, reject_schedule=True)
    inv = Inverter(client, "TEST")
    with pytest.raises(FoxESSApiError) as error:
        inv.set_schedule([{"workMode": "ForceCharge", "fdPwr": 2000}])
    assert error.value.errno == 40257
    assert state["enable"] is already_enabled
    assert inv.last_schedule_attempt["errno"] == 40257
    assert inv.last_schedule_attempt["rollback"] == (
        "not_needed" if already_enabled else "disabled_verified"
    )


def test_failed_idle_rollback_surfaces_manual_recovery_requirement() -> None:
    client, state = _client(enabled=False, reject_schedule=True, fail_disable=True)
    inv = Inverter(client, "TEST")
    with pytest.raises(RuntimeError, match="manual recovery required"):
        inv.set_schedule([{"workMode": "ForceCharge", "fdPwr": 2000}])
    assert state["enable"] is True
    assert inv.last_schedule_attempt["rollback"] == "failed"
    assert inv.last_schedule_attempt["errno"] == 40257


def test_charge_preflight_refuses_conflicting_base_without_write() -> None:
    client, state = _client(base="Backup", enabled=False)
    with pytest.raises(ValueError, match="non-SelfUse"):
        Inverter(client, "TEST").set_schedule([{"workMode": "ForceCharge"}])
    assert state["enable"] is False
    assert not any(
        c.args[0].endswith("/scheduler/enable") for c in client.post.call_args_list
    )


def test_scheduler_capability_probe_is_read_only_and_omits_identity() -> None:
    client = MagicMock()
    client.post.return_value = {
        "deviceSN": "PRIVATE",
        "groups": [],
        "properties": {"fdpwr": {"min": 0, "max": 12000}},
    }
    result = Inverter(client, "TEST").get_scheduler_capabilities()
    assert result["properties"]["fdpwr"]["max"] == 12000
    assert "deviceSN" not in result and "groups" not in result
    client.post.assert_called_once_with(
        "/op/v3/device/scheduler/get", {"deviceSN": "TEST"}
    )


@pytest.mark.parametrize("response", [None, {}, {"properties": {}}, {"properties": []}])
def test_missing_capabilities_never_invent_a_device_limit(response: object) -> None:
    client = MagicMock()
    client.post.return_value = response
    with pytest.raises(ValueError):
        Inverter(client, "TEST").get_scheduler_capabilities()


def test_disabled_stored_charge_group_is_not_reported_as_running() -> None:
    inv = Inverter(MagicMock(), "TEST")
    inv.get_schedule = MagicMock(return_value={
        "enable": 0,
        "groups": [{"enable": 1, "workMode": "ForceCharge"}],
    })
    assert inv.get_current_mode() is None
