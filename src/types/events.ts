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

export type JudgmentVerdict = "uphold" | "downgrade" | "dismiss";
export type HandoffVerdictValue = "approve" | "defer" | "reject";
export type ReportVerdictValue = "accept" | "revise";

export interface HandoffVerdict {
  decision_id: string;
  verdict: HandoffVerdictValue | string;
  rationale: string;
  advisory?: boolean;
}

export interface ReportVerdict {
  report_section_ids: string[];
  verdict: ReportVerdictValue | string;
  issues: string[];
  rationale: string;
  advisory?: boolean;
}

export interface HandoffDecision {
  id: string;
  rule: string;
  from_agent: string;
  to_agent: string | null;
  rationale: string;
  verdict?: HandoffVerdict | null;
}

export interface ReportSection {
  section_id: string;
  title: string;
  markdown: string;
  verdict?: ReportVerdict | null;
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
