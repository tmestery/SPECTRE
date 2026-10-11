import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path

import aiosqlite

from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding


class FindingsBus:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._sequence = 0
        self._subscribers: list[asyncio.Queue[BusEvent]] = []
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                session_id TEXT NOT NULL,
                sequence_num INTEGER NOT NULL,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                type TEXT NOT NULL,
                agent TEXT NOT NULL,
                target TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        await self._conn.commit()
        row = await self._fetchone("SELECT MAX(sequence_num) FROM events")
        self._sequence = int((row[0] if row else None) or 0)

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def publish(self, event: BusEvent) -> BusEvent:
        if not self._conn:
            raise RuntimeError("bus not connected")

        self._sequence += 1
        event.sequence_num = self._sequence

        await self._conn.execute(
            """
            INSERT INTO events (id, type, session_id, sequence_num, payload, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.type.value,
                event.session_id,
                event.sequence_num,
                json.dumps(event.payload),
                event.timestamp.isoformat(),
            ),
        )

        if event.type == EventType.FINDING:
            finding = Finding.model_validate(event.payload["finding"])
            await self._conn.execute(
                """
                INSERT OR REPLACE INTO findings
                (id, session_id, type, agent, target, severity, status, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    finding.id,
                    event.session_id,
                    finding.type.value,
                    finding.agent,
                    finding.target,
                    finding.severity.value,
                    finding.status.value,
                    json.dumps(finding.model_dump(mode="json")),
                ),
            )

        await self._conn.commit()

        for queue in list(self._subscribers):
            await queue.put(event)

        return event

    async def get_finding(self, finding_id: str) -> Finding | None:
        row = await self._fetchone(
            "SELECT payload FROM findings WHERE id = ?",
            (finding_id,),
        )
        if not row:
            return None
        return Finding.model_validate(json.loads(row[0]))

    async def query_findings(
        self,
        *,
        finding_type: str | None = None,
        agent: str | None = None,
        status: str | None = None,
        target: str | None = None,
    ) -> list[Finding]:
        clauses = ["session_id = ?"]
        params: list[str] = [self._session_id_from_path()]

        if finding_type:
            clauses.append("type = ?")
            params.append(finding_type)
        if agent:
            clauses.append("agent = ?")
            params.append(agent)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if target:
            clauses.append("target = ?")
            params.append(target)

        sql = f"SELECT payload FROM findings WHERE {' AND '.join(clauses)} ORDER BY id"
        rows = await self._fetchall(sql, tuple(params))
        return [Finding.model_validate(json.loads(row[0])) for row in rows]

    async def all_findings(self) -> list[Finding]:
        rows = await self._fetchall(
            "SELECT payload FROM findings WHERE session_id = ? ORDER BY id",
            (self._session_id_from_path(),),
        )
        return [Finding.model_validate(json.loads(row[0])) for row in rows]

    async def all_events(self, types: list[EventType] | None = None) -> list[BusEvent]:
        session_id = self._session_id_from_path()
        rows = await self._fetchall(
            "SELECT id, type, session_id, sequence_num, payload, timestamp FROM events "
            "WHERE session_id = ? ORDER BY sequence_num",
            (session_id,),
        )
        allowed = {t.value for t in types} if types else None
        events: list[BusEvent] = []
        for row in rows:
            event_type = row[1]
            if allowed is not None and event_type not in allowed:
                continue
            events.append(
                BusEvent(
                    id=row[0],
                    type=EventType(event_type),
                    session_id=row[2],
                    sequence_num=row[3],
                    payload=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                )
            )
        return events

    async def subscribe(self, types: list[EventType] | None = None) -> AsyncIterator[BusEvent]:
        queue: asyncio.Queue[BusEvent] = asyncio.Queue()
        self._subscribers.append(queue)
        allowed = {t.value for t in types} if types else None
        try:
            while True:
                event = await queue.get()
                if allowed is None or event.type.value in allowed:
                    yield event
        finally:
            self._subscribers.remove(queue)

    def _session_id_from_path(self) -> str:
        return self.db_path.parent.name

    async def _fetchone(self, sql: str, params: tuple = ()) -> aiosqlite.Row | None:
        assert self._conn
        async with self._conn.execute(sql, params) as cursor:
            return await cursor.fetchone()

    async def _fetchall(self, sql: str, params: tuple = ()) -> list[aiosqlite.Row]:
        assert self._conn
        async with self._conn.execute(sql, params) as cursor:
            return list(await cursor.fetchall())
