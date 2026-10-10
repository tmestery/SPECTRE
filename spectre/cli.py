import argparse
import asyncio
import json
import sys
from pathlib import Path

from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.orchestrator.loop import Orchestrator, create_engagement
from spectre.orchestrator.runner import launch_engagement, watch_halt_signal
from spectre.report.generator import ReportGenerator
from spectre.safety.halt import request_halt
from spectre.schemas.events import EventType
from spectre.schemas.scope import RepoScope
from spectre.server.control import SpectreControlServer
from spectre.sessions import list_sessions, session_exists


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spectre", description="SPECTRE repo audit crew")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run a repo audit engagement")
    run.add_argument("--repo", required=True, help="owner/repo slug")
    run.add_argument("--scope", required=True, type=Path, help="Path to scope yaml")
    run.add_argument("--branch", default="main", help="Branch to audit")
    run.add_argument("--ws", action="store_true", help="Start WebSocket event stream")

    serve = sub.add_parser("serve", help="Start WebSocket control server for the demo UI")
    serve.add_argument(
        "--scope-dir",
        type=Path,
        default=Path("scopes"),
        help="Directory containing authorized scope yaml files",
    )

    sub.add_parser("sessions", help="List saved engagement sessions")

    halt = sub.add_parser("halt", help="Halt a running engagement")
    halt.add_argument("--session", required=True, help="Engagement session id")

    report = sub.add_parser("report", help="Export report for a completed session")
    report.add_argument("--session", required=True, help="Engagement session id")
    report.add_argument(
        "--format",
        choices=["markdown", "html", "md"],
        default="markdown",
        help="Report output format",
    )
    report.add_argument(
        "--output",
        type=Path,
        help="Write report to this path (default: reports/<session>.<ext>)",
    )

    metrics = sub.add_parser("metrics", help="Export coordination metrics for a session")
    metrics.add_argument("--session", required=True, help="Engagement session id")
    metrics.add_argument(
        "--output",
        type=Path,
        help="Directory for handoffs.jsonl and metrics.json (default: session data dir)",
    )

    replay = sub.add_parser("replay", help="Replay a completed engagement from its event log")
    replay.add_argument("--session", required=True, help="Engagement session id")
    replay.add_argument(
        "--speed",
        type=float,
        default=0.0,
        help="Playback speed (0=immediate, 1=real-time, 2=2x faster)",
    )
    replay.add_argument(
        "--ws",
        action="store_true",
        help="Stream replayed events to WebSocket clients",
    )

    return parser


async def _stream_events(bus: FindingsBus) -> None:
    async for event in bus.subscribe():
        print(json.dumps(event.model_dump(mode="json")), flush=True)
        if event.type in {EventType.ENGAGEMENT_COMPLETE, EventType.ENGAGEMENT_HALTED}:
            break


async def _run_engagement(args: argparse.Namespace) -> int:
    scope = RepoScope.load(args.scope)
    if not scope.allows_repo(args.repo):
        print(f"error: repo not in scope: {args.repo}", file=sys.stderr)
        return 1

    engagement = create_engagement(args.repo, args.branch, scope)
    session_dir = settings.spectre_data_dir / engagement.id
    bus = FindingsBus(session_dir / "events.db")
    await bus.connect()

    orchestrator = Orchestrator(bus)
    ws_server = None
    server = None
    halt_task = None

    if args.ws:
        from spectre.server.websocket import EngagementWebSocketServer

        ws_server = EngagementWebSocketServer(bus, engagement.id)
        server = await ws_server.start()
        halt_task = asyncio.create_task(watch_halt_signal(engagement.id, orchestrator))

    try:
        print(json.dumps({"session_id": engagement.id, "ws_port": settings.ws_port}), flush=True)
        stream_task = asyncio.create_task(_stream_events(bus))
        handle = launch_engagement(engagement, bus, orchestrator)
        _, result = await asyncio.gather(stream_task, handle.task)
        print(json.dumps({"result": result.model_dump(mode="json")}), flush=True)
        return 0 if result.status.value in {"complete", "halted"} else 1
    finally:
        if halt_task:
            halt_task.cancel()
        if ws_server and server:
            await ws_server.stop(server)
        await bus.close()


async def _serve(args: argparse.Namespace) -> int:
    server = SpectreControlServer(scope_dir=args.scope_dir)
    print(
        json.dumps(
            {
                "status": "serving",
                "ws_host": settings.ws_host,
                "ws_port": settings.ws_port,
                "scope_dir": str(args.scope_dir),
            }
        ),
        flush=True,
    )
    await server.run_forever()
    return 0


async def _list_sessions() -> int:
    summaries = await list_sessions(settings.spectre_data_dir)
    print(json.dumps([summary.__dict__ for summary in summaries], indent=2), flush=True)
    return 0


async def _export_report(args: argparse.Namespace) -> int:
    session_dir = settings.spectre_data_dir / args.session
    db_path = session_dir / "events.db"
    if not db_path.exists():
        print(f"error: session not found: {args.session}", file=sys.stderr)
        return 1

    bus = FindingsBus(db_path)
    await bus.connect()
    try:
        events = await bus.all_events()
        started = next((e for e in events if e.type == EventType.ENGAGEMENT_STARTED), None)
        if not started:
            print(f"error: no engagement data for session: {args.session}", file=sys.stderr)
            return 1

        repo = started.payload["repo"]
        branch = started.payload.get("branch", "main")
        scope = RepoScope.model_validate(started.payload["scope"])
        findings = await bus.all_findings()
        generator = ReportGenerator(repo, branch, scope)
        markdown = generator.render_markdown(findings, events)

        fmt = "markdown" if args.format == "md" else args.format
        if args.output:
            out_path = args.output
        elif fmt == "html":
            out_path = Path("reports") / f"{args.session}.html"
        else:
            out_path = Path("reports") / f"{args.session}.md"

        out_path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "html":
            out_path.write_text(generator.render_html(markdown), encoding="utf-8")
        else:
            out_path.write_text(markdown, encoding="utf-8")

        print(json.dumps({"session_id": args.session, "path": str(out_path)}), flush=True)
        return 0
    finally:
        await bus.close()


async def _replay_session(args: argparse.Namespace) -> int:
    from spectre.research.replay import ReplayWebSocketServer, replay_session

    if args.speed < 0:
        print("error: --speed must be >= 0", file=sys.stderr)
        return 1

    ws_server: ReplayWebSocketServer | None = None
    server = None

    async def on_event(event) -> None:
        print(json.dumps(event.model_dump(mode="json")), flush=True)
        if ws_server is not None:
            await ws_server.broadcast(event)

    try:
        if args.ws:
            ws_server = ReplayWebSocketServer(args.session)
            server = await ws_server.start()
            print(
                json.dumps(
                    {
                        "status": "replaying",
                        "session_id": args.session,
                        "speed": args.speed,
                        "ws_host": settings.ws_host,
                        "ws_port": settings.ws_port,
                    }
                ),
                flush=True,
            )
            await asyncio.sleep(0.25)

        events = await replay_session(
            settings.spectre_data_dir,
            args.session,
            speed=args.speed,
            on_event=on_event,
        )
        print(
            json.dumps({"status": "replay_complete", "session_id": args.session, "events": len(events)}),
            flush=True,
        )
        return 0
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if ws_server is not None and server is not None:
            await ws_server.stop(server)


async def _export_metrics(args: argparse.Namespace) -> int:
    from spectre.research.metrics import export_session_metrics

    session_dir = settings.spectre_data_dir / args.session
    db_path = session_dir / "events.db"
    if not db_path.exists():
        print(f"error: session not found: {args.session}", file=sys.stderr)
        return 1

    out_dir = args.output or session_dir
    bus = FindingsBus(db_path)
    await bus.connect()
    try:
        metrics = await export_session_metrics(bus, args.session, out_dir)
        print(
            json.dumps(
                {
                    "session_id": args.session,
                    "handoffs": str(out_dir / "handoffs.jsonl"),
                    "metrics": str(out_dir / "metrics.json"),
                    "summary": metrics.to_dict(),
                },
                indent=2,
                default=str,
            ),
            flush=True,
        )
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        await bus.close()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        raise SystemExit(asyncio.run(_run_engagement(args)))

    if args.command == "serve":
        raise SystemExit(asyncio.run(_serve(args)))

    if args.command == "sessions":
        raise SystemExit(asyncio.run(_list_sessions()))

    if args.command == "halt":
        if not session_exists(settings.spectre_data_dir, args.session):
            print(f"error: session not found: {args.session}", file=sys.stderr)
            raise SystemExit(1)
        request_halt(args.session)
        print(json.dumps({"session_id": args.session, "halt": "requested"}), flush=True)
        raise SystemExit(0)

    if args.command == "report":
        raise SystemExit(asyncio.run(_export_report(args)))

    if args.command == "metrics":
        raise SystemExit(asyncio.run(_export_metrics(args)))

    if args.command == "replay":
        raise SystemExit(asyncio.run(_replay_session(args)))

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
