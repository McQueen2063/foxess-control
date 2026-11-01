"""Unit coverage for the E2E options client; no HA instance required."""

from unittest.mock import MagicMock, patch

import pytest

from tests.e2e.ha_client import HAClient


@pytest.mark.parametrize("configured", [None, 4000])
def test_set_options_omits_missing_defaults_and_preserves_configured_ceiling(
    configured: int | None,
) -> None:
    client = HAClient("http://ha.test", "test-token")
    session = MagicMock()
    client._session = session
    session.get.return_value.json.return_value = [
        {"domain": "foxess_control", "entry_id": "entry"}
    ]
    ceiling_field: dict[str, str | int] = {"name": "max_charge_power_w"}
    if configured is not None:
        ceiling_field["default"] = configured
    flow = MagicMock()
    flow.json.return_value = {
        "flow_id": "flow",
        "data_schema": [
            {"name": "ws_mode", "default": "auto"},
            {"name": "battery_capacity_kwh", "default": 0},
            ceiling_field,
        ],
    }
    session.post.side_effect = [flow, MagicMock(ok=True), MagicMock(ok=True)]

    with patch.object(client, "_wait_for_integration_ready"):
        client.set_options(ws_mode="smart_sessions")

    submitted = session.post.call_args_list[1].kwargs["json"]
    assert submitted["ws_mode"] == "smart_sessions"
    assert submitted["battery_capacity_kwh"] == 0
    if configured is None:
        assert "max_charge_power_w" not in submitted
    else:
        assert submitted["max_charge_power_w"] == configured
