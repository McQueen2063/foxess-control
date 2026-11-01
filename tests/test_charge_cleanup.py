"""Focused charge cleanup tests: mocked transport, no hardware simulation."""

from unittest.mock import MagicMock, call

import pytest

from custom_components.foxess_control.domain_data import build_config
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


def test_finish_charge_writes_safe_baseline_then_disables_master() -> None:
    client = MagicMock()
    client.post.return_value = {"value": "SelfUse"}
    inv = Inverter(client, "TEST")
    inv.finish_charge(20, 4000)
    calls = client.post.call_args_list
    assert calls[0].args[0] == "/op/v0/device/scheduler/enable"
    group = calls[0].args[1]["groups"][0]
    assert group["workMode"] == "SelfUse"
    assert group["fdPwr"] == 4000
    assert group["minSocOnGrid"] == 20
    assert calls[1] == call(
        "/op/v0/device/setting/get", {"sn": "TEST", "key": "WorkMode"}
    )
    assert calls[2] == call(
        "/op/v1/device/scheduler/set/flag", {"deviceSN": "TEST", "enable": 0}
    )


@pytest.mark.parametrize("base", ["Backup", "unexpected"])
def test_finish_charge_never_disables_over_conflicting_or_unknown_base(base: str) -> None:
    client = MagicMock()
    client.post.return_value = {"value": base}
    inv = Inverter(client, "TEST")
    with pytest.raises(ValueError):
        inv.finish_charge(20, 4000)
    assert client.post.call_args_list[0].args[0] == "/op/v0/device/scheduler/enable"
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
    client = MagicMock()

    def post(path: str, payload: dict[str, object]) -> dict[str, str]:
        if path.endswith("/set/flag"):
            raise RuntimeError("flag write failed")
        return {"value": "SelfUse"}

    client.post.side_effect = post
    with pytest.raises(RuntimeError, match="flag write failed"):
        Inverter(client, "TEST").finish_charge(20, 4000)
    assert client.post.call_args_list[0].args[0] == "/op/v0/device/scheduler/enable"
