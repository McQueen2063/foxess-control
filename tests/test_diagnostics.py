"""Tests for the FoxESS Control diagnostics platform."""

from __future__ import annotations

import asyncio
from collections import deque
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.foxess_control.const import DOMAIN
from custom_components.foxess_control.diagnostics import (
    async_get_config_entry_diagnostics,
)


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def _make_hass_and_entry(domain_data: Any) -> tuple[Any, Any]:
    hass = MagicMock()
    hass.data = {DOMAIN: domain_data}
    entry = MagicMock()
    entry.entry_id = "e1"
    entry.data = {"api_key": "SECRET", "device_serial": "SN123"}
    entry.options = {"ws_mode": "auto"}
    return hass, entry


def test_diagnostics_includes_recent_errors() -> None:
    buf: deque[dict[str, Any]] = deque(maxlen=30)
    buf.append(
        {
            "t": "2026-06-02T00:00:00+00:00",
            "category": "ws_discovery",
            "attempted": "discover battery id",
            "exc_type": "WSServerHandshakeError",
            "exc_str": "200, message='Invalid response status'",
            "hint": "regional endpoint mismatch",
            "context": {"host": "www.foxesscloud.com"},
            "severity": "warning",
        }
    )
    dd = SimpleNamespace(
        entries={},
        smart_charge_state=None,
        smart_discharge_state=None,
        smart_error_state=None,
        realtime_ws=None,
        taper_profile=None,
        ws_mode="auto",
        recent_errors=buf,
        web_session=None,
        plant_id="p1",
        battery_compound_id=None,
    )
    hass, entry = _make_hass_and_entry(dd)
    result = _run(async_get_config_entry_diagnostics(hass, entry))
    assert "recent_errors" in result
    assert result["recent_errors"][0]["exc_type"] == "WSServerHandshakeError"


def test_diagnostics_environment_reports_host_and_ws_mode() -> None:
    dd = SimpleNamespace(
        entries={},
        smart_charge_state=None,
        smart_discharge_state=None,
        smart_error_state=None,
        realtime_ws=None,
        taper_profile=None,
        ws_mode="auto",
        recent_errors=deque(maxlen=30),
        web_session=SimpleNamespace(BASE_URL="https://www.foxesscloud.com"),
        plant_id="p1",
        battery_compound_id=None,
    )
    hass, entry = _make_hass_and_entry(dd)
    result = _run(async_get_config_entry_diagnostics(hass, entry))
    env = result["environment"]
    assert env["cloud_base_url"] == "https://www.foxesscloud.com"
    assert env["ws_mode"] == "auto"
    assert env["ws_connected"] is False
    assert env["plant_id_present"] is True
    assert env["battery_compound_id_status"] == "missing"


def test_diagnostics_redacts_secrets_everywhere() -> None:
    buf: deque[dict[str, Any]] = deque(maxlen=30)
    buf.append(
        {
            "t": "2026-06-02T00:00:00+00:00",
            "category": "login",
            "attempted": "web login",
            "exc_type": "X",
            "exc_str": "y",
            "hint": None,
            "context": {"api_key": "LEAKED", "host": "h"},
            "severity": "warning",
        }
    )
    dd = SimpleNamespace(
        entries={},
        smart_charge_state=None,
        smart_discharge_state=None,
        smart_error_state=None,
        realtime_ws=None,
        taper_profile=None,
        ws_mode="auto",
        recent_errors=buf,
        web_session=SimpleNamespace(BASE_URL="https://www.foxesscloud.com"),
        plant_id="p1",
        battery_compound_id="uuid@SN999",
    )
    hass, entry = _make_hass_and_entry(dd)
    result = _run(async_get_config_entry_diagnostics(hass, entry))
    flat = str(result)
    assert "SECRET" not in flat
    assert "SN123" not in flat
    assert "LEAKED" not in flat
    assert "SN999" not in flat


def test_paused_entry_capability_diagnostics_do_not_load_or_write() -> None:
    hass, entry = _make_hass_and_entry(None)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *a: fn(*a))
    client = MagicMock()
    client.post.return_value = {
        "deviceSN": "SN123",
        "groups": [],
        "properties": {"fdpwr": {"min": 0, "max": 12000}},
    }
    with patch(
        "custom_components.foxess_control.diagnostics.FoxESSClient",
        return_value=client,
    ):
        result = _run(async_get_config_entry_diagnostics(hass, entry))
    probe = result["environment"]["scheduler_capabilities"]
    assert probe["success"] is True
    assert probe["properties"]["fdpwr"]["max"] == 12000
    client.post.assert_called_once_with(
        "/op/v3/device/scheduler/get", {"deviceSN": "SN123"}
    )
    hass.config_entries.async_reload.assert_not_called()
    assert "SECRET" not in str(result) and "SN123" not in str(result)


def test_unsupported_capability_read_is_explicit_not_a_guessed_limit() -> None:
    hass, entry = _make_hass_and_entry(None)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *a: fn(*a))
    client = MagicMock()
    client.post.return_value = None
    with patch(
        "custom_components.foxess_control.diagnostics.FoxESSClient",
        return_value=client,
    ):
        result = _run(async_get_config_entry_diagnostics(hass, entry))
    assert result["environment"]["scheduler_capabilities"] == {
        "success": False, "error": "ValueError", "errno": None,
    }
