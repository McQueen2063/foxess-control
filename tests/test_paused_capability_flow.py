"""Read-only config-flow access must not set up or mutate a paused entry."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryDisabler, ConfigEntryState

from custom_components.foxess_control.config_flow import FoxessControlConfigFlow


def _flow(
    *, disabled_by: object = ConfigEntryDisabler.USER
) -> tuple[FoxessControlConfigFlow, Any]:
    entry = SimpleNamespace(
        entry_id="paused",
        title="Paused inverter",
        disabled_by=disabled_by,
        state=ConfigEntryState.NOT_LOADED,
        data={"api_key": "SECRET", "device_serial": "PRIVATE"},
        options={},
    )
    flow = FoxessControlConfigFlow()
    flow.hass = MagicMock()
    flow.hass.config_entries.async_entries.side_effect = (
        lambda domain: [entry] if domain == "foxess_control" else []
    )
    flow.hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *a: fn(*a))
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_abort = MagicMock(side_effect=lambda **kw: {"type": "abort", **kw})
    flow.async_create_entry = MagicMock()
    return flow, entry


@pytest.mark.asyncio
async def test_paused_menu_and_confirmation_make_no_network_calls() -> None:
    flow, _ = _flow()
    with patch("custom_components.foxess_control.diagnostics.FoxESSClient") as client:
        await flow.async_step_user()
        assert flow.async_show_menu.call_args.kwargs["menu_options"] == [
            "cloud",
            "scheduler_diagnostics",
        ]
        await flow.async_step_scheduler_diagnostics()
        assert (
            flow.async_show_form.call_args.kwargs["step_id"] == "scheduler_diagnostics"
        )
        client.assert_not_called()
    flow.async_create_entry.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("unsupported", [False, True])
async def test_confirmed_probe_calls_only_read_endpoint_and_finishes(
    unsupported: bool,
) -> None:
    flow, entry = _flow()
    client = MagicMock()
    client.post.return_value = (
        None
        if unsupported
        else {
            "deviceSN": "PRIVATE",
            "groups": [{"workMode": "ForceCharge"}],
            "properties": {"fdpwr": {"max": 12000}, "sn": "PRIVATE"},
        }
    )
    with patch(
        "custom_components.foxess_control.diagnostics.FoxESSClient", return_value=client
    ):
        result = await flow.async_step_scheduler_diagnostics({"entry_id": "paused"})
    assert result["reason"] == "scheduler_capabilities_read"
    payload = json.loads(result["description_placeholders"]["capabilities"])
    assert payload["success"] is not unsupported
    if unsupported:
        assert payload == {"success": False, "error": "ValueError", "errno": None}
    else:
        assert payload["properties"]["fdpwr"]["max"] == 12000
    assert "SECRET" not in str(result) and "PRIVATE" not in str(result)
    client.post.assert_called_once_with(
        "/op/v3/device/scheduler/get", {"deviceSN": "PRIVATE"}
    )
    assert entry.disabled_by == ConfigEntryDisabler.USER
    assert entry.options == {}
    flow.async_create_entry.assert_not_called()
    flow.hass.config_entries.async_reload.assert_not_called()
    flow.hass.config_entries.async_setup.assert_not_called()
    flow.hass.config_entries.async_update_entry.assert_not_called()
    flow.hass.config_entries.async_set_disabled_by.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change", ["enabled", "removed", "entity", "credentials", "failed_unload"]
)
async def test_submission_rechecks_eligibility_without_read_or_mutation(
    change: str,
) -> None:
    flow, entry = _flow()
    await flow.async_step_scheduler_diagnostics()
    if change == "enabled":
        entry.disabled_by = None
    elif change == "removed":
        flow.hass.config_entries.async_entries.side_effect = lambda domain: []
    elif change == "entity":
        entry.options = {"work_mode_entity": "select.inverter"}
    elif change == "failed_unload":
        entry.state = ConfigEntryState.FAILED_UNLOAD
    else:
        entry.data = {}
    with patch("custom_components.foxess_control.diagnostics.FoxESSClient") as client:
        result = await flow.async_step_scheduler_diagnostics({"entry_id": "paused"})
        client.assert_not_called()
    assert result["reason"] == "no_paused_cloud_entry"
    flow.async_create_entry.assert_not_called()


@pytest.mark.asyncio
async def test_unknown_entry_id_is_rejected_without_network() -> None:
    flow, _ = _flow()
    with patch("custom_components.foxess_control.diagnostics.FoxESSClient") as client:
        await flow.async_step_scheduler_diagnostics({"entry_id": "other"})
        client.assert_not_called()
    assert flow.async_show_form.call_args.kwargs["errors"] == {
        "base": "invalid_paused_entry"
    }


@pytest.mark.asyncio
async def test_failed_read_does_not_expose_exception_message_or_enable_entry() -> None:
    flow, entry = _flow()
    client = MagicMock()
    client.post.side_effect = RuntimeError("SECRET PRIVATE")
    with patch(
        "custom_components.foxess_control.diagnostics.FoxESSClient", return_value=client
    ):
        result = await flow.async_step_scheduler_diagnostics({"entry_id": "paused"})
    payload = json.loads(result["description_placeholders"]["capabilities"])
    assert payload == {"success": False, "error": "RuntimeError", "errno": None}
    assert "SECRET" not in str(result) and "PRIVATE" not in str(result)
    assert entry.disabled_by == ConfigEntryDisabler.USER
    client.post.assert_called_once()
    flow.async_create_entry.assert_not_called()
