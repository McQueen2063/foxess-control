"""Entity-backend labels must be accepted by HA's enum state validation."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from custom_components.foxess_control.foxess_adapter import _ENTITY_MODE_MAP
from custom_components.foxess_control.sensor import FoxESSWorkModeSensor


@pytest.mark.parametrize("label", list(_ENTITY_MODE_MAP.values()))
def test_entity_mode_label_renders_without_normalizing(label: str) -> None:
    coordinator = MagicMock()
    coordinator.data = {"_work_mode": label}
    entry = SimpleNamespace(entry_id="existing", data={})
    sensor = FoxESSWorkModeSensor(coordinator, entry)
    # Isolate enum validation from platform-dependent translation lookup.
    sensor._attr_translation_key = None
    assert sensor.native_value == label
    assert sensor.state == label
    assert sensor.unique_id == "existing_work_mode"
