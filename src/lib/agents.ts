export const AGENT_META: Record<
  string,
  { label: string; color: string; role: "crew" | "judge" }
> = {
  recon: { label: "Recon", color: "#5b9fd4", role: "crew" },
  vuln_hunter: { label: "VulnHunter", color: "#d4a574", role: "crew" },
  exploiter: { label: "Exploiter", color: "#c45c4a", role: "crew" },
  reporter: { label: "Reporter", color: "#6a9f7a", role: "crew" },
  finding_judge: { label: "Finding Judge", color: "#8f7a5e", role: "judge" },
  handoff_judge: { label: "Handoff Judge", color: "#7a6e5c", role: "judge" },
  report_judge: { label: "Report Judge", color: "#6e6558", role: "judge" },
};

export function agentLabel(agentId: string): string {
  return AGENT_META[agentId]?.label ?? agentId;
}

export function agentColor(agentId: string): string {
  return AGENT_META[agentId]?.color ?? "#8a8478";
}

export function isJudgeAgent(agentId: string): boolean {
  return AGENT_META[agentId]?.role === "judge" || agentId.endsWith("_judge");
}

export function isCrewAgent(agentId: string): boolean {
  return AGENT_META[agentId]?.role === "crew";
}
