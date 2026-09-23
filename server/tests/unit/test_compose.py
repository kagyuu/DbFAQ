"""compose.yaml の構成の検査(docs/P007-impl-direction/U006-deploy.md U006-T3)。"""

from pathlib import Path

import pytest
import yaml

COMPOSE = Path(__file__).resolve().parents[3] / "compose.yaml"


@pytest.fixture(scope="module")
def services():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["services"]


def test_api_has_no_ports(services):
    assert "ports" not in services["api"]


def test_only_web_publishes(services):
    assert [name for name, s in services.items() if "ports" in s] == ["web"]


def test_config_mounted_read_only(services):
    assert "./config.yaml:/config/config.yaml:ro" in services["api"]["volumes"]


def test_restart_policy(services):
    assert all(s["restart"] == "unless-stopped" for s in services.values())


def test_host_gateway(services):
    assert "host.docker.internal:host-gateway" in services["api"]["extra_hosts"]


def test_data_volume(services):
    assert "dbfaq-data:/data" in services["api"]["volumes"]
