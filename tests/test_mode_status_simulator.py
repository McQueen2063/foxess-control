"""Exercise the status endpoints over HTTP before relying on them in HA E2E."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.foxess_control.foxess.client import FoxESSClient
from custom_components.foxess_control.foxess.inverter import Inverter

if TYPE_CHECKING:
    from .conftest import SimulatorHandle


def test_status_endpoints_match_client_contract(foxess_sim: SimulatorHandle) -> None:
    client = FoxESSClient("test-api-key", base_url=foxess_sim.url)
    inv = Inverter(client, "SIM0001")
    assert inv.get_base_work_mode() == "SelfUse"
    assert inv.get_scheduler_flag() == {"enable": False, "support": True}
    assert inv.get_current_mode() is None
