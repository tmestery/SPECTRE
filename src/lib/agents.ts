export const AGENT_META: Record<string, { label: string; color: string }> = {
  recon: { label: "Recon", color: "#38bdf8" },
  vuln_hunter: { label: "VulnHunter", color: "#fbbf24" },
  exploiter: { label: "Exploiter", color: "#f87171" },
  reporter: { label: "Reporter", color: "#4ade80" },
  finding_judge: { label: "FindingJudge", color: "#2dd4bf" },
  handoff_judge: { label: "HandoffJudge", color: "#67e8f9" },
  report_judge: { label: "ReportJudge", color: "#a3e635" },
};

export function agentLabel(agentId: string): string {
  return AGENT_META[agentId]?.label ?? agentId;
}

export function agentColor(agentId: string): string {
  return AGENT_META[agentId]?.color ?? "#94a3b8";
}
