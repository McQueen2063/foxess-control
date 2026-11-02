"""Explicit flat-V1 opt-in; legacy defaults and idle rollback stay intact."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import voluptuous as vol

from custom_components.foxess_control.config_flow import FoxessControlOptionsFlow
from custom_components.foxess_control.foxess.client import FoxESSApiError
from custom_components.foxess_control.foxess.inverter import Inverter
from custom_components.foxess_control.foxess_adapter import _sanitize_group
from custom_components.foxess_control.smart_battery.types import WorkMode


def _group():
    return {
        "enable": 1,
        "startHour": 0,
        "startMinute": 13,
        "endHour": 0,
        "endMinute": 18,
        "workMode": "ForceCharge",
        "minSocOnGrid": 15,
        "fdSoc": 100,
        "fdPwr": 2000,
    }


def _client(*, fail_write=False):
    client = MagicMock()
    state = {"enable": False}

    def post(path, payload):
        if path.endswith("/scheduler/get/flag"):
            return {"support": True, "enable": state["enable"]}
        if path.endswith("/setting/get"):
            return {"value": "SelfUse"}
        if path.endswith("/scheduler/get"):
            return {"enable": 0, "groups": []}
        if path.endswith("/scheduler/set/flag"):
            state["enable"] = False
            return None
        if path.endswith("/scheduler/enable"):
            state["enable"] = True
            if fail_write:
                raise FoxESSApiError(40257, "rejected after master enabled")
            return None
        raise AssertionError(path)

    client.post.side_effect = post
    return client, state


@pytest.mark.parametrize("version", ["v0", "v1"])
def test_selected_read_and_write_api_have_exact_flat_payload(version: str) -> None:
    client, _ = _client()
    inv = Inverter(client, "TEST", scheduler_api_version=version)
    assert inv.get_schedule() == {"enable": 0, "groups": []}
    client.post.assert_called_with(
        f"/op/{version}/device/scheduler/get", {"deviceSN": "TEST"}
    )
    group = _group()
    before = deepcopy(group)
    inv.set_schedule([group])
    expected = dict(group)
    if version == "v1":
        expected["maxSoc"] = 100
    writes = [c for c in client.post.call_args_list if c.args[0].endswith("/enable")]
    assert len(writes) == 1
    assert writes[0].args == (
        f"/op/{version}/device/scheduler/enable",
        {"deviceSN": "TEST", "groups": [expected]},
    )
    assert group == before
    assert inv.last_schedule_attempt["groups"] == [expected]
    assert inv.last_schedule_attempt["endpoint"] == writes[0].args[0]


def test_unconfigured_inverter_keeps_legacy_v0_without_maxsoc() -> None:
    client, _ = _client()
    inv = Inverter(client, "TEST")
    inv.set_schedule([_group()])
    client.post.assert_called_with(
        "/op/v0/device/scheduler/enable", {"deviceSN": "TEST", "groups": [_group()]}
    )


@pytest.mark.parametrize("mode", ["SelfUse", "ForceCharge", "ForceDischarge"])
def test_direct_mode_write_uses_the_same_selected_v1_serializer(mode: str) -> None:
    client, _ = _client()
    inv = Inverter(client, "TEST", scheduler_api_version="v1")
    inv.set_work_mode(WorkMode(mode), min_soc_on_grid=15, fd_soc=100, fd_pwr=2000)
    assert client.post.call_args.args[0] == "/op/v1/device/scheduler/enable"
    group = client.post.call_args.args[1]["groups"][0]
    assert group["maxSoc"] == 100
    assert group["workMode"] == mode
    assert group["fdPwr"] == 2000
    assert "extraParam" not in group


def test_v1_preserves_existing_flat_maxsoc_through_schedule_sanitization() -> None:
    client, _ = _client()
    group = _sanitize_group({**_group(), "maxSoc": 80, "irrelevant": "drop"})
    Inverter(client, "TEST", scheduler_api_version="v1").set_schedule([group])
    assert client.post.call_args.args[1]["groups"][0]["maxSoc"] == 80
    assert "irrelevant" not in client.post.call_args.args[1]["groups"][0]


@pytest.mark.parametrize("version", ["v0", "v1"])
def test_rejected_write_rolls_back_idle_without_trying_another_api(
    version: str,
) -> None:
    client, state = _client(fail_write=True)
    inv = Inverter(client, "TEST", scheduler_api_version=version)
    with pytest.raises(FoxESSApiError):
        inv.set_schedule([_group()])
    writes = [c for c in client.post.call_args_list if c.args[0].endswith("/enable")]
    assert len(writes) == 1
    assert writes[0].args[0] == f"/op/{version}/device/scheduler/enable"
    assert state["enable"] is False
    assert inv.last_schedule_attempt["rollback"] == "disabled_verified"


@pytest.mark.parametrize("version", ["v2", "v3", "", None])
def test_unimplemented_versions_are_rejected_without_network(version) -> None:
    client = MagicMock()
    with pytest.raises(ValueError, match="v0 or v1"):
        Inverter(client, "TEST", scheduler_api_version=version)
    client.post.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stored, expected", [({}, "v0"), ({"scheduler_api_version": "v1"}, "v1")]
)
async def test_options_expose_legacy_default_and_persisted_optin(
    stored, expected
) -> None:
    entry = SimpleNamespace(options=stored, data={})
    flow = FoxessControlOptionsFlow(entry)
    flow.hass = MagicMock()
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    await flow.async_step_init()
    schema = flow.async_show_form.call_args.kwargs["data_schema"]
    field = next(k for k in schema.schema if str(k) == "scheduler_api_version")
    assert field.default() == expected
    assert schema.schema[field]("v1") == "v1"
    with pytest.raises(vol.Invalid):
        schema.schema[field]("v3")
