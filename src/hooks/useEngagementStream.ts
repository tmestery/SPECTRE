import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentMessage,
  BusEvent,
  EngagementMeta,
  Finding,
  HandoffDecision,
  ReportSection,
} from "../types/events";

const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8765";

export interface EngagementState {
  connected: boolean;
  sessionId: string | null;
  meta: EngagementMeta | null;
  messages: AgentMessage[];
  findings: Finding[];
  handoffs: HandoffDecision[];
  reportSections: ReportSection[];
  status: "idle" | "running" | "complete" | "halted";
  error: string | null;
}

const INITIAL: EngagementState = {
  connected: false,
  sessionId: null,
  meta: null,
  messages: [],
  findings: [],
  handoffs: [],
  reportSections: [],
  status: "idle",
  error: null,
};

function applyEvent(state: EngagementState, event: BusEvent): EngagementState {
  const next = { ...state };

  switch (event.type) {
    case "engagement_started":
      next.status = "running";
      next.meta = {
        repo: String(event.payload.repo ?? ""),
        branch: String(event.payload.branch ?? "main"),
        scopeName: String((event.payload.scope as { name?: string })?.name ?? ""),
      };
      break;
    case "agent_message":
      next.messages = [
        ...next.messages,
        {
          agent: String(event.payload.agent ?? ""),
          message: String(event.payload.message ?? ""),
          timestamp: event.timestamp,
        },
      ];
      break;
    case "finding": {
      const finding = event.payload.finding as Finding;
      if (finding) next.findings = [...next.findings, finding];
      break;
    }
    case "handoff_decision":
      next.handoffs = [
        ...next.handoffs,
        {
          rule: String(event.payload.rule ?? ""),
          from_agent: String(event.payload.from_agent ?? ""),
          to_agent: (event.payload.to_agent as string | null) ?? null,
          rationale: String(event.payload.rationale ?? ""),
        },
      ];
      break;
    case "report_section":
      next.reportSections = [
        ...next.reportSections,
        {
          section_id: String(event.payload.section_id ?? ""),
          title: String(event.payload.title ?? ""),
          markdown: String(event.payload.markdown ?? ""),
        },
      ];
      break;
    case "engagement_complete":
      next.status = "complete";
      break;
    case "engagement_halted":
      next.status = "halted";
      break;
    default:
      break;
  }

  return next;
}

export function useEngagementStream() {
  const [state, setState] = useState<EngagementState>(INITIAL);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef(false);

  const disconnect = useCallback(() => {
    reconnectRef.current = false;
    socketRef.current?.close();
    socketRef.current = null;
    setState((s) => ({ ...s, connected: false }));
  }, []);

  const connect = useCallback((sessionId: string) => {
    disconnect();
    reconnectRef.current = true;
    setState({ ...INITIAL, sessionId, status: "running" });

    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onopen = () => {
      setState((s) => ({ ...s, connected: true, error: null }));
    };

    socket.onmessage = (message) => {
      try {
        const data = JSON.parse(String(message.data)) as BusEvent | { type: string };
        if (!("sequence_num" in data)) return;
        setState((s) => applyEvent(s, data as BusEvent));
      } catch {
        setState((s) => ({ ...s, error: "Failed to parse WebSocket event" }));
      }
    };

    socket.onerror = () => {
      setState((s) => ({ ...s, error: "WebSocket connection error" }));
    };

    socket.onclose = () => {
      setState((s) => ({ ...s, connected: false }));
      if (reconnectRef.current && sessionId) {
        window.setTimeout(() => {
          if (reconnectRef.current) connect(sessionId);
        }, 1500);
      }
    };
  }, [disconnect]);

  const requestHalt = useCallback(() => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: "halt", session_id: state.sessionId }));
  }, [state.sessionId]);

  useEffect(() => () => disconnect(), [disconnect]);

  return { state, connect, disconnect, requestHalt };
}
