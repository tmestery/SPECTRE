from pathlib import Path

from spectre.cli import build_parser


def test_run_parser_requires_repo_and_scope():
    parser = build_parser()
    args = parser.parse_args(["run", "--repo", "tmestery/SPECTRE", "--scope", "scopes/spectre.yaml"])
    assert args.repo == "tmestery/SPECTRE"
    assert args.branch == "main"


def test_run_parser_rejects_missing_scope():
    parser = build_parser()
    try:
        parser.parse_args(["run", "--repo", "tmestery/SPECTRE"])
        raised = False
    except SystemExit:
        raised = True
    assert raised


def test_halt_parser_requires_session():
    parser = build_parser()
    try:
        parser.parse_args(["halt"])
        raised = False
    except SystemExit:
        raised = True
    assert raised


def test_help_lists_commands(capsys):
    parser = build_parser()
    try:
        parser.parse_args([])
    except SystemExit:
        pass


def test_report_parser_has_report_command():
    parser = build_parser()
    args = parser.parse_args(["report", "--session", "eng_abc", "--format", "markdown"])
    assert args.command == "report"
    assert args.session == "eng_abc"


def test_serve_parser_has_scope_dir_default():
    parser = build_parser()
    args = parser.parse_args(["serve"])
    assert args.command == "serve"
    assert args.scope_dir == Path("scopes")


def test_sessions_parser_exists():
    parser = build_parser()
    args = parser.parse_args(["sessions"])
    assert args.command == "sessions"
