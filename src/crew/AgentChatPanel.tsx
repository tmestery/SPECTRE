import type { AgentMessage } from "../types/events";
import { agentLabel, isJudgeAgent } from "../lib/agents";
import { AgentAvatar } from "./AgentAvatar";
import { sortEventsByTimestamp } from "../lib/sort";

interface Props {
  messages: AgentMessage[];
}

export function AgentChatPanel({ messages }: Props) {
  const sorted = sortEventsByTimestamp(messages);

  return (
    <div className="panel chat-panel">
      <h2>Crew channel</h2>
      <div className="chat-scroll">
        {sorted.length === 0 ? (
          <p className="placeholder">Waiting for agent messages…</p>
        ) : (
          sorted.map((msg, index) => {
            const judge = isJudgeAgent(msg.agent);
            return (
              <div
                key={`${msg.timestamp}-${index}`}
                className={`chat-row${judge ? " chat-row-judge" : ""}`}
                style={{ animationDelay: `${Math.min(index, 12) * 30}ms` }}
              >
                <AgentAvatar agentId={msg.agent} />
                <div>
                  <div className="chat-meta">
                    <strong>{agentLabel(msg.agent)}</strong>
                    {judge ? <span className="judge-chip">judge</span> : null}
                    {msg.subagent ? <span className="subagent-chip">{msg.subagent}</span> : null}
                    <time>{new Date(msg.timestamp).toLocaleTimeString()}</time>
                  </div>
                  <p>{msg.message}</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
