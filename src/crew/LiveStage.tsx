import type { AgentMessage } from "../types/events";
import { agentLabel, agentColor, isJudgeAgent } from "../lib/agents";
import { recentCrewMessages, STAGE_CUES, isCrewStage } from "../lib/crewStages";
import { AgentAvatar } from "./AgentAvatar";

interface Props {
  activeAgent: string | null;
  messages: AgentMessage[];
  readOnly?: boolean;
}

export function LiveStage({ activeAgent, messages, readOnly = false }: Props) {
  const visible = recentCrewMessages(messages, 4);
  const cue =
    activeAgent && isCrewStage(activeAgent)
      ? STAGE_CUES[activeAgent]
      : "Waiting for the crew to activate…";

  return (
    <section className="live-stage" aria-label="Live agent stage">
      <header className="live-stage-hero">
        <p className="live-stage-kicker">{readOnly ? "Timeline replay" : "Live stage"}</p>
        <h2
          className="live-stage-title"
          style={activeAgent ? { color: agentColor(activeAgent) } : undefined}
        >
          {activeAgent ? agentLabel(activeAgent) : "Standing by"}
        </h2>
        <p className="live-stage-cue">{cue}</p>
      </header>

      <div className="live-stage-feed">
        {visible.length === 0 ? (
          <p className="placeholder">Agent messages will appear here as the crew works.</p>
        ) : (
          visible.map((msg, index) => (
            <div
              key={`${msg.timestamp}-${index}`}
              className={`chat-row${isJudgeAgent(msg.agent) ? " chat-row-judge" : ""}`}
              style={{ animationDelay: `${index * 40}ms` }}
            >
              <AgentAvatar agentId={msg.agent} />
              <div>
                <div className="chat-meta">
                  <strong>{agentLabel(msg.agent)}</strong>
                  <time>{new Date(msg.timestamp).toLocaleTimeString()}</time>
                </div>
                <p>{msg.message}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
