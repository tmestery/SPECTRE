import type { EngagementDefaults, ScopeOption, SessionSummary } from "../hooks/useEngagementStream";

interface Props {
  repo: string;
  branch: string;
  scopePath: string;
  historySession: string;
  scopes: ScopeOption[];
  sessions: SessionSummary[];
  defaults: EngagementDefaults | null;
  ready: boolean;
  connected: boolean;
  canStart: boolean;
  error: string | null;
  llmConfigured: boolean;
  githubTokenConfigured: boolean;
  onRepoChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onScopeChange: (value: string) => void;
  onHistoryChange: (value: string) => void;
  onStart: () => void;
  onLoadSession: () => void;
  onRefreshSessions: () => void;
}

export function SetupView({
  repo,
  branch,
  scopePath,
  historySession,
  scopes,
  sessions,
  ready,
  connected,
  canStart,
  error,
  llmConfigured,
  githubTokenConfigured,
  onRepoChange,
  onBranchChange,
  onScopeChange,
  onHistoryChange,
  onStart,
  onLoadSession,
  onRefreshSessions,
}: Props) {
  const selectedScope = scopes.find((scope) => scope.path === scopePath) ?? scopes[0];

  return (
    <div className="setup-view">
      <header className="banner">
        <div className="brand-block">
          <p className="brand-mark">SPECTRE</p>
          <p className="brand-tag">Self-coordinating repo audit crew</p>
        </div>
        <span className="status-pill idle">ready</span>
      </header>

      {!llmConfigured ? (
        <p className="token-warning">
          LLM is not configured. Add <code>GROQ_API_KEY</code> to <code>.env</code> for AI subagent
          analysis (tools still run without it).
        </p>
      ) : null}

      {!githubTokenConfigured ? (
        <p className="token-warning">
          GITHUB_TOKEN is not set. Add it to <code>.env</code> and restart Docker (e.g.{" "}
          <code>GITHUB_TOKEN=$(gh auth token)</code>).
        </p>
      ) : null}

      <section className="control-deck setup-deck">
        <div className="toolbar start-panel">
          <label className="field">
            Repository
            <input
              value={repo}
              onChange={(e) => onRepoChange(e.target.value)}
              placeholder="owner/repo"
              list="allowed-repos"
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
              onChange={(e) => onBranchChange(e.target.value)}
              placeholder="main"
              list="allowed-branches"
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
              onChange={(e) => onScopeChange(e.target.value)}
              disabled={scopes.length === 0}
            >
              {scopes.map((scope) => (
                <option key={scope.path} value={scope.path}>
                  {scope.name}
                </option>
              ))}
            </select>
          </label>

          <button type="button" className="primary-btn" disabled={!canStart} onClick={onStart}>
            Start audit
          </button>

          {error ? <span className="error">{error}</span> : null}
          {!connected ? <span className="muted">Connecting to orchestrator…</span> : null}
        </div>

        <div className="toolbar history-panel">
          <label className="field grow">
            Past session
            <select
              value={historySession}
              onChange={(e) => onHistoryChange(e.target.value)}
              disabled={!ready}
            >
              <option value="">Select a saved session…</option>
              {sessions.map((session) => (
                <option key={session.session_id} value={session.session_id}>
                  {session.session_id} · {session.repo} · {session.status}
                </option>
              ))}
            </select>
          </label>
          <button type="button" disabled={!historySession} onClick={onLoadSession}>
            Load session
          </button>
          <button type="button" disabled={!ready} onClick={onRefreshSessions}>
            Refresh
          </button>
        </div>
      </section>
    </div>
  );
}
