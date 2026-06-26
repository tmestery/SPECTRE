import { agentColor, agentLabel } from "../lib/agents";

interface Props {
  agentId: string;
}

export function AgentAvatar({ agentId }: Props) {
  return (
    <span className="avatar" style={{ borderColor: agentColor(agentId) }}>
      {agentLabel(agentId).slice(0, 1)}
    </span>
  );
}
