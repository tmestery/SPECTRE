import type { HandoffDecision } from "../types/events";
import { agentLabel } from "../lib/agents";

interface Props {
  handoffs: HandoffDecision[];
}

export function HandoffGraph({ handoffs }: Props) {
  if (handoffs.length === 0) {
    return (
      <div className="panel handoff-panel">
        <h2>Handoff Graph</h2>
        <p className="placeholder">No handoffs yet.</p>
      </div>
    );
  }

  return (
    <div className="panel handoff-panel">
      <h2>Handoff Graph</h2>
      <ul className="handoff-list">
        {handoffs.map((handoff, index) => (
          <li key={`${handoff.rule}-${index}`} className="handoff-item">
            <div className="handoff-edge">
              <span>{agentLabel(handoff.from_agent)}</span>
              <span className="arrow">→</span>
              <span>{handoff.to_agent ? agentLabel(handoff.to_agent) : "End"}</span>
            </div>
            <div className="handoff-rule">{handoff.rule}</div>
            <p>{handoff.rationale}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
