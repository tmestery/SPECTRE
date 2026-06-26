from pathlib import Path

from spectre.config import settings


def halt_signal_path(session_id: str) -> Path:
    return settings.spectre_data_dir / session_id / "halt.signal"


def request_halt(session_id: str) -> None:
    path = halt_signal_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def is_halt_requested(session_id: str) -> bool:
    return halt_signal_path(session_id).exists()


def clear_halt(session_id: str) -> None:
    halt_signal_path(session_id).unlink(missing_ok=True)
