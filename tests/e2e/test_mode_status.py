"""Load the fork into real, disposable HA; read only from a local simulator."""

from __future__ import annotations

import datetime
import json
from typing import TYPE_CHECKING

import pytest
import requests

if TYPE_CHECKING:
    from .conftest import SimulatorHandle
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


@pytest.mark.parametrize("ha_e2e", ["paused_cloud"], indirect=True)
def test_cold_paused_capability_flow_without_domain_setup(
    ha_e2e: HAClient, foxess_sim: SimulatorHandle
) -> None:
    """Exercise real HA flow routing after a never-loaded, disabled cold boot."""
    assert foxess_sim is not None
    session = ha_e2e._session
    base = ha_e2e.base_url

    def entries():
        response = session.get(f"{base}/api/config/config_entries/entry", timeout=10)
        response.raise_for_status()
        # Flow handler import can change discovered supports_* flags without
        # changing saved configuration. Compare identity/state/storage metadata.
        keys = (
            "entry_id",
            "created_at",
            "modified_at",
            "domain",
            "title",
            "source",
            "disabled_by",
            "state",
            "pref_disable_new_entities",
            "pref_disable_polling",
        )
        return [
            {key: e[key] for key in keys}
            for e in response.json()
            if e["domain"] == "foxess_control"
        ]

    def domain_loaded():
        response = session.get(f"{base}/api/config", timeout=10)
        response.raise_for_status()
        return "foxess_control" in response.json()["components"]

    before = entries()
    assert len(before) == 1
    entry_id = before[0]["entry_id"]
    assert before[0]["disabled_by"] == "user"
    assert before[0]["state"] == "not_loaded"
    assert not domain_loaded()
    diagnostics_url = f"{base}/api/diagnostics/config_entry/{entry_id}"
    assert session.get(diagnostics_url, timeout=10).status_code == 404

    def trace():
        response = requests.get(f"{foxess_sim.url}/sim/requests", timeout=5)
        response.raise_for_status()
        return response.json()

    assert trace() == []  # No setup, recovery, polling or login at cold boot.
    response = session.post(
        f"{base}/api/config/config_entries/flow",
        json={"handler": "foxess_control", "show_advanced_options": False},
        timeout=30,
    )
    response.raise_for_status()
    flow = response.json()
    assert flow["type"] == "menu"
    assert "scheduler_diagnostics" in flow["menu_options"]
    url = f"{base}/api/config/config_entries/flow/{flow['flow_id']}"
    response = session.post(
        url, json={"next_step_id": "scheduler_diagnostics"}, timeout=30
    )
    response.raise_for_status()
    assert response.json()["step_id"] == "scheduler_diagnostics"
    assert trace() == []  # Opening the confirmation form performs no read.

    response = session.post(url, json={"entry_id": entry_id}, timeout=30)
    response.raise_for_status()
    result = response.json()
    assert result["type"] == "abort"  # No config entry is created.
    assert result["reason"] == "scheduler_capabilities_read"
    payload = json.loads(result["description_placeholders"]["capabilities"])
    assert payload["success"] is True
    assert payload["properties"]["fdpwr"]["max"] > 0
    assert trace() == [["POST", "/op/v3/device/scheduler/get"]]
    assert entries() == before  # Same disabled entry; no setup/options mutation.
    assert not domain_loaded()
    # The domain is still never-loaded: ordinary diagnostics remain unavailable.
    assert session.get(diagnostics_url, timeout=10).status_code == 404
