import type { HandoffDecision } from "../types/events";
import { agentLabel } from "../lib/agents";
import { VerdictBadge } from "../findings/VerdictBadge";

interface Props {
  handoffs: HandoffDecision[];
}

export function HandoffGraph({ handoffs }: Props) {
  if (handoffs.length === 0) {
    return (
      <div className="panel handoff-panel">
        <h2>Handoffs</h2>
        <p className="placeholder">No handoffs yet.</p>
      </div>
    );
  }

  return (
    <div className="panel handoff-panel">
      <h2>Handoffs</h2>
      <ul className="handoff-list">
        {handoffs.map((handoff, index) => (
          <li
            key={handoff.id || `${handoff.rule}-${index}`}
            className="handoff-item"
            style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
          >
            <div className="handoff-edge">
              <span>{agentLabel(handoff.from_agent)}</span>
              <span className="arrow">→</span>
              <span>{handoff.to_agent ? agentLabel(handoff.to_agent) : "End"}</span>
              <VerdictBadge verdict={handoff.verdict?.verdict} kind="handoff" />
            </div>
            <div className="handoff-rule">{handoff.rule}</div>
            <p>{handoff.rationale}</p>
            {handoff.verdict?.rationale ? (
              <p className="verdict-rationale">{handoff.verdict.rationale}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
