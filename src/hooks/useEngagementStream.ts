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

export interface ScopeOption {
  path: string;
  name: string;
  allowed_repos: string[];
  allowed_branches: string[];
}

export interface SessionSummary {
  session_id: string;
  repo: string;
  branch: string;
  scope_name: string;
  status: string;
  updated_at: string;
}

export interface EngagementDefaults {
  repo: string;
  branch: string;
  scope_path: string;
}

export interface EngagementState {
  connected: boolean;
  ready: boolean;
  sessionId: string | null;
  meta: EngagementMeta | null;
  messages: AgentMessage[];
  findings: Finding[];
  handoffs: HandoffDecision[];
  reportSections: ReportSection[];
  status: "idle" | "running" | "complete" | "halted";
  error: string | null;
  defaults: EngagementDefaults | null;
  scopes: ScopeOption[];
  sessions: SessionSummary[];
  activeSession: string | null;
}

const INITIAL: EngagementState = {
  connected: false,
  ready: false,
  sessionId: null,
  meta: null,
  messages: [],
  findings: [],
  handoffs: [],
  reportSections: [],
  status: "idle",
  error: null,
  defaults: null,
  scopes: [],
  sessions: [],
  activeSession: null,
};

function applyEvent(state: EngagementState, event: BusEvent): EngagementState {
  const next = { ...state };

  switch (event.type) {
    case "engagement_started":
      next.status = "running";
      next.sessionId = event.session_id;
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
      next.activeSession = null;
      break;
    case "engagement_halted":
      next.status = "halted";
      next.activeSession = null;
      break;
    default:
      break;
  }

  return next;
}

function isBusEvent(data: Record<string, unknown>): boolean {
  return typeof data.sequence_num === "number";
}

export function useEngagementStream() {
  const [state, setState] = useState<EngagementState>(INITIAL);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef(true);

  const send = useCallback((payload: Record<string, unknown>) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify(payload));
  }, []);

  const handleControlMessage = useCallback((data: Record<string, unknown>) => {
    switch (data.type) {
      case "server_hello":
        setState((s) => ({
          ...s,
          ready: true,
          error: null,
          defaults: (data.defaults as EngagementDefaults | undefined) ?? s.defaults,
          scopes: (data.scopes as ScopeOption[] | undefined) ?? s.scopes,
          sessions: (data.sessions as SessionSummary[] | undefined) ?? s.sessions,
          activeSession: (data.active_session as string | null | undefined) ?? null,
        }));
        break;
      case "engagement_launched":
        setState((s) => ({
          ...INITIAL,
          connected: true,
          ready: true,
          sessionId: String(data.session_id ?? ""),
          status: "running",
          activeSession: String(data.session_id ?? ""),
          defaults: s.defaults,
          scopes: s.scopes,
          sessions: s.sessions,
        }));
        break;
      case "subscribed":
        setState((s) => ({
          ...s,
          sessionId: String(data.session_id ?? s.sessionId ?? ""),
          error: null,
        }));
        break;
      case "sessions_list":
        setState((s) => ({
          ...s,
          sessions: (data.sessions as SessionSummary[] | undefined) ?? s.sessions,
        }));
        break;
      case "halt_ack":
        break;
      case "error":
        setState((s) => ({ ...s, error: String(data.message ?? "Unknown server error") }));
        break;
      default:
        break;
    }
  }, []);

  const connectSocket = useCallback(() => {
    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onopen = () => {
      setState((s) => ({ ...s, connected: true, error: null }));
    };

    socket.onmessage = (message) => {
      try {
        const data = JSON.parse(String(message.data)) as Record<string, unknown>;
        if (isBusEvent(data)) {
          setState((s) => applyEvent(s, data as unknown as BusEvent));
          return;
        }
        handleControlMessage(data);
      } catch {
        setState((s) => ({ ...s, error: "Failed to parse WebSocket event" }));
      }
    };

    socket.onerror = () => {
      setState((s) => ({ ...s, error: "WebSocket connection error" }));
    };

    socket.onclose = () => {
      setState((s) => ({ ...s, connected: false, ready: false }));
      if (reconnectRef.current) {
        window.setTimeout(() => {
          if (reconnectRef.current) connectSocket();
        }, 1500);
      }
    };
  }, [handleControlMessage]);

  useEffect(() => {
    reconnectRef.current = true;
    connectSocket();
    return () => {
      reconnectRef.current = false;
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [connectSocket]);

  const startEngagement = useCallback(
    (repo: string, branch: string, scopePath: string) => {
      setState((s) => ({ ...s, error: null }));
      send({
        type: "start_engagement",
        repo,
        branch,
        scope_path: scopePath,
      });
    },
    [send],
  );

  const loadSession = useCallback(
    (sessionId: string) => {
      setState({
        ...INITIAL,
        connected: true,
        ready: true,
        sessionId,
        defaults: state.defaults,
        scopes: state.scopes,
        sessions: state.sessions,
      });
      send({ type: "subscribe", session_id: sessionId });
    },
    [send, state.defaults, state.scopes, state.sessions],
  );

  const refreshSessions = useCallback(() => {
    send({ type: "list_sessions" });
  }, [send]);

  const requestHalt = useCallback(() => {
    if (!state.sessionId) return;
    send({ type: "halt", session_id: state.sessionId });
  }, [send, state.sessionId]);

  return {
    state,
    startEngagement,
    loadSession,
    refreshSessions,
    requestHalt,
  };
}
