import { useState } from "react";
import { AgentChatPanel } from "../crew/AgentChatPanel";
import { HandoffGraph } from "../crew/HandoffGraph";
import { FindingsTimeline } from "../findings/FindingsTimeline";
import { LiveReportPanel } from "../report/LiveReportPanel";
import { ScopeBanner } from "../target/ScopeBanner";
import { HaltButton } from "../target/HaltButton";
import { useEngagementStream } from "../hooks/useEngagementStream";

export function App() {
  const { state, connect, disconnect, requestHalt } = useEngagementStream();
  const [sessionInput, setSessionInput] = useState("");

  const repo = state.meta?.repo ?? "owner/repo";
  const branch = state.meta?.branch ?? "main";
  const canHalt = state.connected && state.status === "running";

  return (
    <div className="shell">
      <ScopeBanner meta={state.meta} status={state.status} />

      <div className="toolbar">
        <label className="session-input">
          Session ID
          <input
            value={sessionInput}
            onChange={(e) => setSessionInput(e.target.value)}
            placeholder="eng_…"
          />
        </label>
        <button
          type="button"
          disabled={!sessionInput.trim()}
          onClick={() => connect(sessionInput.trim())}
        >
          Connect
        </button>
        <button type="button" disabled={!state.connected} onClick={disconnect}>
          Disconnect
        </button>
        <HaltButton disabled={!canHalt} onHalt={requestHalt} />
        {state.error ? <span className="error">{state.error}</span> : null}
      </div>

      <main className="dashboard">
        <div className="column">
          <AgentChatPanel messages={state.messages} />
          <HandoffGraph handoffs={state.handoffs} />
        </div>
        <div className="column">
          <FindingsTimeline findings={state.findings} repo={repo} branch={branch} />
          <LiveReportPanel sections={state.reportSections} />
        </div>
      </main>
    </div>
  );
}
