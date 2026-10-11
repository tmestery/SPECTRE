"""Docker Compose and container networking configuration."""

from pathlib import Path

import yaml


def test_docker_compose_defines_spectre_service():
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))
    assert "spectre" in compose["services"]
    assert compose["services"]["spectre"]["ports"]


def test_ws_host_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("WS_HOST", raising=False)
    from spectre.config import Settings

    assert Settings().ws_host == "127.0.0.1"


def test_ws_host_reads_from_environment(monkeypatch):
    monkeypatch.setenv("WS_HOST", "0.0.0.0")
    from spectre.config import Settings

    assert Settings().ws_host == "0.0.0.0"


def test_dockerfile_declares_runtime_tools():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert "gitleaks" in dockerfile
    assert "osv-scanner" in dockerfile
    assert "AS cli" in dockerfile


def test_dockerfile_copies_handoff_profiles():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert "COPY handoff_profiles ./handoff_profiles" in dockerfile
    assert "HANDOFF_PROFILES_DIR=/app/handoff_profiles" in dockerfile


def test_compose_mounts_handoff_profiles():
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))
    volumes = compose["services"]["spectre"]["volumes"]
    assert "./handoff_profiles:/app/handoff_profiles:ro" in volumes
    assert compose["services"]["spectre"]["environment"]["HANDOFF_PROFILES_DIR"] == (
        "/app/handoff_profiles"
    )


def test_default_handoff_profile_file_exists():
    path = Path("handoff_profiles/default.yaml")
    assert path.is_file()
    assert "secret_confidence_min" in path.read_text(encoding="utf-8")


def test_docker_entrypoint_is_executable():
    entrypoint = Path("docker/entrypoint.sh")
    assert entrypoint.is_file()
    assert (entrypoint.stat().st_mode & 0o111) != 0
