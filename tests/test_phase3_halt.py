
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


def test_halt_cli_rejects_missing_session(tmp_path, monkeypatch, capsys):
    import sys
    from unittest.mock import patch

    from spectre import config
    from spectre.cli import main

    monkeypatch.setattr(config.settings, "spectre_data_dir", tmp_path / "sessions")

    with patch.object(sys, "argv", ["spectre", "halt", "--session", "eng_none"]):
        with pytest.raises(SystemExit) as exit_info:
            main()
    assert exit_info.value.code == 1
    captured = capsys.readouterr()
    assert "session not found" in captured.err
