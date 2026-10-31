"""Nested container build errors must include the underlying runtime output."""

import subprocess
from unittest.mock import patch

import pytest

from .e2e.conftest import _build_container_once


def test_build_failure_exposes_podman_output() -> None:
    result = subprocess.CompletedProcess(
        args=["podman", "build"],
        returncode=125,
        stdout="pulling HA image",
        stderr="specific runtime failure",
    )
    with (
        patch("tests.e2e.conftest.subprocess.run", return_value=result),
        pytest.raises(RuntimeError, match="specific runtime failure"),
    ):
        _build_container_once()
