"""Regression checks for the existing two-worker HA image-build lock budget.

Load only the helper source, not E2E fixture imports or any container runtime.
"""

from __future__ import annotations

import ast
import logging
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


def _build_helper():
    source = Path(__file__).parent / "e2e" / "conftest.py"
    function = next(
        node
        for node in ast.parse(source.read_text()).body
        if isinstance(node, ast.FunctionDef) and node.name == "_build_container_once"
    )
    process = MagicMock()
    process.run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
    namespace = {
        "REPO_ROOT": Path("/disposable-test"),
        "E2E_DIR": source.parent,
        "CONTAINER_IMAGE": "foxess-e2e-regression:test",
        "subprocess": process,
        "time": time,
        "_log": logging.getLogger(__name__),
    }
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"),
        namespace,
    )
    return namespace["_build_container_once"], process


@pytest.mark.parametrize("holder_build_seconds", [0, 300, 540, 600])
def test_waiter_allows_full_holder_build_budget(holder_build_seconds: int) -> None:
    """Deterministic budget simulation: no real sleeps, builds or downloads."""
    build, process = _build_helper()
    state = {"held": False, "released": False}
    observed = {}

    class Lock:
        def __init__(self, path, *, timeout):
            observed.update(path=path, lock_timeout=timeout)

        def __enter__(self):
            if observed["lock_timeout"] <= holder_build_seconds:
                raise TimeoutError("other worker still legitimately building")
            state["held"] = True

        def __exit__(self, *_):
            state["held"] = False
            state["released"] = True

    def run(*args, **kwargs):
        assert state["held"]
        observed["build_timeout"] = kwargs["timeout"]
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    process.run.side_effect = run
    with patch.dict("sys.modules", {"filelock": SimpleNamespace(FileLock=Lock)}):
        build()
    assert observed["lock_timeout"] > observed["build_timeout"] == 600
    assert state == {"held": False, "released": True}
    assert process.run.call_count == 1


@pytest.mark.parametrize("timed_out", [False, True])
def test_failed_or_timed_out_build_releases_lock_and_does_not_report_success(
    timed_out: bool,
) -> None:
    build, process = _build_helper()
    lock = MagicMock()
    module = SimpleNamespace(FileLock=MagicMock(return_value=lock))
    if timed_out:
        process.run.side_effect = subprocess.TimeoutExpired("podman build", 600)
        expected = subprocess.TimeoutExpired
    else:
        process.run.return_value = SimpleNamespace(
            returncode=1, stdout="build output", stderr="pull failed"
        )
        expected = RuntimeError
    with (
        patch.dict("sys.modules", {"filelock": module}),
        pytest.raises(expected),
    ):
        build()
    lock.__exit__.assert_called_once()
