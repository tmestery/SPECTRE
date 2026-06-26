import { useEffect, useMemo, useRef, useState } from "react";
import { AgentChatPanel } from "../crew/AgentChatPanel";
import { HandoffGraph } from "../crew/HandoffGraph";
import { FindingsTimeline } from "../findings/FindingsTimeline";
import { LiveReportPanel } from "../report/LiveReportPanel";
import { ScopeBanner } from "../target/ScopeBanner";
import { HaltButton } from "../target/HaltButton";
import { useEngagementStream } from "../hooks/useEngagementStream";

export function App() {
  const { state, startEngagement, loadSession, refreshSessions, requestHalt } =
    useEngagementStream();
  const [repo, setRepo] = useState("");
  const [branch, setBranch] = useState("main");
  const [scopePath, setScopePath] = useState("");
  const [historySession, setHistorySession] = useState("");
  const loadedFromUrl = useRef(false);

  const selectedScope = useMemo(
    () => state.scopes.find((scope) => scope.path === scopePath) ?? state.scopes[0],
    [scopePath, state.scopes],
  );

  useEffect(() => {
    if (!state.defaults) return;
    setRepo((current) => current || state.defaults?.repo || "");
    setBranch((current) => current || state.defaults?.branch || "main");
    setScopePath((current) => current || state.defaults?.scope_path || state.scopes[0]?.path || "");
  }, [state.defaults, state.scopes]);

  useEffect(() => {
    if (loadedFromUrl.current || !state.ready) return;
    const session = new URLSearchParams(window.location.search).get("session");
    if (session?.trim()) {
      loadedFromUrl.current = true;
      loadSession(session.trim());
    }
  }, [loadSession, state.ready]);

  const displayRepo = state.meta?.repo ?? (repo || "owner/repo");
  const displayBranch = state.meta?.branch ?? branch;
  const canStart =
    state.ready &&
    state.connected &&
    !state.activeSession &&
    repo.trim() &&
    branch.trim() &&
    scopePath.trim();
  const canHalt = state.connected && state.status === "running" && Boolean(state.sessionId);
  const running = state.status === "running";

  return (
    <div className="shell">
      <ScopeBanner meta={state.meta} status={state.status} />

      {!state.llmConfigured ? (
        <p className="token-warning">
          LLM is not configured. Add <code>GROQ_API_KEY</code> to <code>.env</code> for AI subagent
          analysis (tools still run without it).
        </p>
      ) : null}

      {!state.githubTokenConfigured ? (
        <p className="token-warning">
          GITHUB_TOKEN is not set. Add it to <code>.env</code> and restart Docker
          (e.g. <code>GITHUB_TOKEN=$(gh auth token)</code>).
        </p>
      ) : null}

      <div className="toolbar start-panel">
        <label className="field">
          Repository
          <input
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            placeholder="owner/repo"
            list="allowed-repos"
            disabled={running}
          />
        </label>
        <datalist id="allowed-repos">
          {(selectedScope?.allowed_repos ?? []).map((slug) => (
            <option key={slug} value={slug} />
          ))}
        </datalist>

        <label className="field">
          Branch
          <input
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="main"
            list="allowed-branches"
            disabled={running}
          />
        </label>
        <datalist id="allowed-branches">
          {(selectedScope?.allowed_branches ?? []).map((name) => (
            <option key={name} value={name} />
          ))}
        </datalist>

        <label className="field">
          Scope
          <select
            value={scopePath}
            onChange={(e) => setScopePath(e.target.value)}
            disabled={running || state.scopes.length === 0}
          >
            {state.scopes.map((scope) => (
              <option key={scope.path} value={scope.path}>
                {scope.name}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className="primary-btn"
          disabled={!canStart}
          onClick={() => startEngagement(repo.trim(), branch.trim(), scopePath)}
        >
          Start audit
        </button>

        <HaltButton disabled={!canHalt} onHalt={requestHalt} />

        {state.sessionId ? <span className="session-chip">{state.sessionId}</span> : null}
        {state.error ? <span className="error">{state.error}</span> : null}
        {!state.connected ? <span className="muted">Connecting to orchestrator…</span> : null}
      </div>

      <div className="toolbar history-panel">
        <label className="field">
          Past session
          <select
            value={historySession}
            onChange={(e) => setHistorySession(e.target.value)}
            disabled={!state.ready || running}
          >
            <option value="">Select a saved session…</option>
            {state.sessions.map((session) => (
              <option key={session.session_id} value={session.session_id}>
                {session.session_id} · {session.repo} · {session.status}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={!historySession || running}
          onClick={() => loadSession(historySession)}
        >
          Load session
        </button>
        <button type="button" disabled={!state.ready} onClick={refreshSessions}>
          Refresh
        </button>
      </div>

      <main className="dashboard">
        <div className="column">
          <AgentChatPanel messages={state.messages} />
          <HandoffGraph handoffs={state.handoffs} />
        </div>
        <div className="column">
          <FindingsTimeline findings={state.findings} repo={displayRepo} branch={displayBranch} />
          <LiveReportPanel sections={state.reportSections} />
        </div>
      </main>
    </div>
  );
}
