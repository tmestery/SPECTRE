import pytest

from spectre.safety.halt import clear_halt, is_halt_requested, request_halt


def test_halt_signal_created_and_cleared(tmp_path, monkeypatch):
    from spectre import config

    monkeypatch.setattr(config.settings, "spectre_data_dir", tmp_path / "sessions")
    request_halt("eng_halt")
    assert is_halt_requested("eng_halt")
    clear_halt("eng_halt")
    assert not is_halt_requested("eng_halt")


def test_halt_signal_missing_session_returns_false(tmp_path, monkeypatch):
    from spectre import config

    monkeypatch.setattr(config.settings, "spectre_data_dir", tmp_path / "sessions")
    assert not is_halt_requested("eng_none")
