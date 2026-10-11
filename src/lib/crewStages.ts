import { isJudgeAgent } from "./agents";

/** Ordered crew stages for the cinematic progress rail. */
export const CREW_STAGES = ["recon", "vuln_hunter", "exploiter", "reporter"] as const;

export type CrewStageId = (typeof CREW_STAGES)[number];

export const STAGE_CUES: Record<CrewStageId, string> = {
  recon: "Mapping repository surface…",
  vuln_hunter: "Hunting secrets, CVEs, and misconfigs…",
  exploiter: "Validating candidate findings…",
  reporter: "Synthesizing the audit report…",
};

export function isCrewStage(agentId: string): agentId is CrewStageId {
  return (CREW_STAGES as readonly string[]).includes(agentId);
}

export function stageIndex(agentId: string | null | undefined): number {
  if (!agentId || !isCrewStage(agentId)) return -1;
  return CREW_STAGES.indexOf(agentId);
}

/** Prefer explicit activation; fall back to last crew message or handoff target. */
export function resolveActiveCrewAgent(input: {
  activeAgent: string | null;
  messages: { agent: string }[];
  handoffs: { to_agent: string | null }[];
}): string | null {
  if (input.activeAgent && isCrewStage(input.activeAgent)) {
    return input.activeAgent;
  }
  for (let i = input.messages.length - 1; i >= 0; i -= 1) {
    const agent = input.messages[i].agent;
    if (isCrewStage(agent) && !isJudgeAgent(agent)) return agent;
  }
  for (let i = input.handoffs.length - 1; i >= 0; i -= 1) {
    const to = input.handoffs[i].to_agent;
    if (to && isCrewStage(to)) return to;
  }
  return null;
}

export function recentCrewMessages<T extends { agent: string }>(messages: T[], limit = 4): T[] {
  const crew = messages.filter((m) => !isJudgeAgent(m.agent));
  return crew.slice(-limit);
}
