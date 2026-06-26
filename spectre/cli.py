import argparse
import asyncio
import json
import sys
from pathlib import Path

from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.orchestrator.loop import Orchestrator, create_engagement
from spectre.schemas.events import EventType
from spectre.schemas.scope import RepoScope


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spectre", description="SPECTRE repo audit crew")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run a repo audit engagement")
    run.add_argument("--repo", required=True, help="owner/repo slug")
    run.add_argument("--scope", required=True, type=Path, help="Path to scope yaml")
    run.add_argument("--branch", default="main", help="Branch to audit")
    run.add_argument("--ws", action="store_true", help="Start WebSocket event stream")

    halt = sub.add_parser("halt", help="Halt a running engagement")
    halt.add_argument("--session", required=True, help="Engagement session id")

    return parser


async def _stream_events(bus: FindingsBus) -> None:
    async for event in bus.subscribe():
        print(json.dumps(event.model_dump(mode="json")), flush=True)
        if event.type == EventType.ENGAGEMENT_COMPLETE:
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

        async def watch_halt() -> None:
            while not ws_server.halt_requested():
                await asyncio.sleep(0.2)
            orchestrator.request_halt(engagement.id)

        halt_task = asyncio.create_task(watch_halt())

    try:
        stream_task = asyncio.create_task(_stream_events(bus))
        run_task = asyncio.create_task(orchestrator.run(engagement))
        _, result = await asyncio.gather(stream_task, run_task)
        print(json.dumps({"result": result.model_dump(mode="json")}), flush=True)
        return 0 if result.status.value in {"complete", "halted"} else 1
    finally:
        if halt_task:
            halt_task.cancel()
        if ws_server and server:
            await ws_server.stop(server)
        await bus.close()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        raise SystemExit(asyncio.run(_run_engagement(args)))

    if args.command == "halt":
        print(f"halt requested for session {args.session} (signal file not yet implemented)")
        raise SystemExit(0)

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
