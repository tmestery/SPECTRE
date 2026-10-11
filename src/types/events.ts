export type EventType =
  | "engagement_started"
  | "agent_activated"
  | "agent_message"
  | "finding"
  | "handoff_decision"
  | "handoff_verdict"
  | "tool_invocation"
  | "llm_invocation"
  | "subagent_activated"
  | "report_section"
  | "report_verdict"
  | "engagement_halted"
  | "engagement_complete";

export interface BusEvent {
  id: string;
  type: EventType;
  session_id: string;
  sequence_num: number;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface Finding {
  id: string;
  type: string;
  agent: string;
  target: string;
  severity: string;
  confidence: number;
  title: string;
  description?: string | null;
  evidence: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface HandoffDecision {
  rule: string;
  from_agent: string;
  to_agent: string | null;
  rationale: string;
}

export interface ReportSection {
  section_id: string;
  title: string;
  markdown: string;
}

export interface AgentMessage {
  agent: string;
  message: string;
  timestamp: string;
  subagent?: string;
}

export interface EngagementMeta {
  repo: string;
  branch: string;
  scopeName: string;
}
