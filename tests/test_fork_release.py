"""Validate fork metadata without changing integration/storage identity."""

import json
from pathlib import Path

from awesomeversion import AwesomeVersion

ROOT = Path(__file__).resolve().parents[1]


def test_fork_manifest_and_changelog_agree() -> None:
    manifest = json.loads(
        (ROOT / "custom_components/foxess_control/manifest.json").read_text()
    )
    assert manifest["domain"] == "foxess_control"
    assert manifest["config_flow"] is True
    assert manifest["version"] == "1.0.24"
    assert AwesomeVersion(manifest["version"]) > AwesomeVersion("1.0.23")
    assert f"## {manifest['version']}\n" in (ROOT / "CHANGELOG.md").read_text()
    assert manifest["documentation"] == "https://github.com/McQueen2063/foxess-control"
    assert manifest["issue_tracker"].startswith(manifest["documentation"])
    assert manifest["codeowners"] == ["@McQueen2063"]
