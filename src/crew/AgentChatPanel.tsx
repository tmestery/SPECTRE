import type { AgentMessage } from "../types/events";
import { agentLabel } from "../lib/agents";
import { AgentAvatar } from "./AgentAvatar";
import { sortEventsByTimestamp } from "../lib/sort";

interface Props {
  messages: AgentMessage[];
}

export function AgentChatPanel({ messages }: Props) {
  const sorted = sortEventsByTimestamp(messages);

  return (
    <div className="panel chat-panel">
      <h2>Agent Chat</h2>
      <div className="chat-scroll">
        {sorted.length === 0 ? (
          <p className="placeholder">Waiting for agent messages…</p>
        ) : (
          sorted.map((msg, index) => (
            <div key={`${msg.timestamp}-${index}`} className="chat-row">
              <AgentAvatar agentId={msg.agent} />
              <div>
                <div className="chat-meta">
                  <strong>{agentLabel(msg.agent)}</strong>
                  {msg.subagent ? <span className="subagent-chip">{msg.subagent}</span> : null}
                  <time>{new Date(msg.timestamp).toLocaleTimeString()}</time>
                </div>
                <p>{msg.message}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
