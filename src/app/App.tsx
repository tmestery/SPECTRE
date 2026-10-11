import { useCallback, useEffect, useRef, useState } from "react";
import { useEngagementStream } from "../hooks/useEngagementStream";
import { resolveActiveCrewAgent } from "../lib/crewStages";
import { LiveCinemaView } from "../crew/LiveCinemaView";
import { AnalyticsPage } from "../report/AnalyticsPage";
import { BootSplash } from "./BootSplash";
import { CompleteBeat } from "./CompleteBeat";
import { SetupView } from "./SetupView";

export type AppView = "boot" | "setup" | "live" | "complete_beat" | "analytics";

const BOOT_MIN_DWELL_MS = 1000;
const BOOT_ERROR_AFTER_MS = 8000;
const COMPLETE_BEAT_MS = 1200;
const HALT_BEAT_MS = 800;

export function App() {
  const { state, startEngagement, loadSession, refreshSessions, requestHalt, reconnect } =
    useEngagementStream();
  const [view, setView] = useState<AppView>("boot");
  const [bootReady, setBootReady] = useState(false);
  const [bootTimedOut, setBootTimedOut] = useState(false);
  const [repo, setRepo] = useState("");
  const [branch, setBranch] = useState("main");
  const [scopePath, setScopePath] = useState("");
  const [historySession, setHistorySession] = useState("");
  const [liveReadOnly, setLiveReadOnly] = useState(false);
  const loadedFromUrl = useRef(false);
  const bootStartedAt = useRef(Date.now());
  const prevStatus = useRef(state.status);

  useEffect(() => {
    if (!state.defaults) return;
    setRepo((current) => current || state.defaults?.repo || "");
    setBranch((current) => current || state.defaults?.branch || "main");
    setScopePath((current) => current || state.defaults?.scope_path || state.scopes[0]?.path || "");
  }, [state.defaults, state.scopes]);

  // Boot: min dwell + stream ready
  useEffect(() => {
    if (view !== "boot") return;
    const elapsed = Date.now() - bootStartedAt.current;
    const remaining = Math.max(0, BOOT_MIN_DWELL_MS - elapsed);
    const timer = window.setTimeout(() => setBootReady(true), remaining);
    return () => window.clearTimeout(timer);
  }, [view]);

  useEffect(() => {
    if (view !== "boot") return;
    const timer = window.setTimeout(() => setBootTimedOut(true), BOOT_ERROR_AFTER_MS);
    return () => window.clearTimeout(timer);
  }, [view]);

  useEffect(() => {
    if (view !== "boot") return;
    if (bootReady && state.connected && state.ready) {
      setView("setup");
    }
  }, [bootReady, state.connected, state.ready, view]);

  // Start → live
  useEffect(() => {
    if (state.status === "running" && state.activeSession && view === "setup") {
      setLiveReadOnly(false);
      setView("live");
    }
  }, [state.status, state.activeSession, view]);

  // Complete / halt → beat → analytics
  useEffect(() => {
    const prev = prevStatus.current;
    prevStatus.current = state.status;
    if (view !== "live" && view !== "complete_beat") return;
    if (state.status === "complete" && prev !== "complete") {
      setView("complete_beat");
    }
    if (state.status === "halted" && prev !== "halted") {
      setView("complete_beat");
    }
  }, [state.status, view]);

  // Failed engagement while trying to start
  useEffect(() => {
    if (state.status === "idle" && state.error && view === "live") {
      setView("setup");
    }
  }, [state.status, state.error, view]);

  useEffect(() => {
    if (loadedFromUrl.current || !state.ready || view === "boot") return;
    const session = new URLSearchParams(window.location.search).get("session");
    if (session?.trim()) {
      loadedFromUrl.current = true;
      loadSession(session.trim());
      setView("analytics");
    }
  }, [loadSession, state.ready, view]);

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

  const handleCompleteDone = useCallback(() => {
    setView("analytics");
  }, []);

  const handleRunAnother = useCallback(() => {
    setLiveReadOnly(false);
    setView("setup");
  }, []);

  const handleWatchTimeline = useCallback(() => {
    setLiveReadOnly(true);
    setView("live");
  }, []);

  const handleLoadSession = useCallback(() => {
    if (!historySession) return;
    loadSession(historySession);
    setLiveReadOnly(false);
    setView("analytics");
  }, [historySession, loadSession]);

  const handleRetryBoot = useCallback(() => {
    setBootTimedOut(false);
    bootStartedAt.current = Date.now();
    setBootReady(false);
    reconnect();
  }, [reconnect]);

  if (view === "boot") {
    const showError = bootTimedOut && !(state.connected && state.ready);
    return (
      <BootSplash
        status={showError ? "error" : "connecting"}
        errorMessage={state.error}
        onRetry={showError ? handleRetryBoot : undefined}
      />
    );
  }

  if (view === "complete_beat") {
    return (
      <CompleteBeat
        status={state.status === "halted" ? "halted" : "complete"}
        durationMs={state.status === "halted" ? HALT_BEAT_MS : COMPLETE_BEAT_MS}
        onDone={handleCompleteDone}
      />
    );
  }

  if (view === "live") {
    return (
      <div className="shell shell-live">
        <div className="shell-atmosphere" aria-hidden="true" />
        <LiveCinemaView
          meta={state.meta}
          sessionId={state.sessionId}
          status={state.status}
          activeAgent={resolveActiveCrewAgent({
            activeAgent: state.activeAgent,
            messages: state.messages,
            handoffs: state.handoffs,
          })}
          messages={state.messages}
          findings={state.findings}
          judgments={state.judgments}
          handoffs={state.handoffs}
          repo={displayRepo}
          branch={displayBranch}
          canHalt={canHalt && !liveReadOnly}
          readOnly={liveReadOnly}
          onHalt={requestHalt}
        />
        {liveReadOnly ? (
          <div className="live-replay-bar">
            <button type="button" className="primary-btn" onClick={() => setView("analytics")}>
              Back to results
            </button>
          </div>
        ) : null}
      </div>
    );
  }

  if (view === "analytics") {
    return (
      <div className="shell shell-analytics">
        <div className="shell-atmosphere" aria-hidden="true" />
        <AnalyticsPage
          meta={state.meta}
          status={state.status}
          sessionId={state.sessionId}
          findings={state.findings}
          judgments={state.judgments}
          handoffs={state.handoffs}
          reportSections={state.reportSections}
          reportVerdict={state.reportVerdict}
          messages={state.messages}
          repo={displayRepo}
          branch={displayBranch}
          onRunAnother={handleRunAnother}
          onWatchTimeline={handleWatchTimeline}
        />
      </div>
    );
  }

  return (
    <div className="shell">
      <div className="shell-atmosphere" aria-hidden="true" />
      <SetupView
        repo={repo}
        branch={branch}
        scopePath={scopePath}
        historySession={historySession}
        scopes={state.scopes}
        sessions={state.sessions}
        defaults={state.defaults}
        ready={state.ready}
        connected={state.connected}
        canStart={Boolean(canStart)}
        error={state.error}
        llmConfigured={state.llmConfigured}
        githubTokenConfigured={state.githubTokenConfigured}
        onRepoChange={setRepo}
        onBranchChange={setBranch}
        onScopeChange={setScopePath}
        onHistoryChange={setHistorySession}
        onStart={() => startEngagement(repo.trim(), branch.trim(), scopePath)}
        onLoadSession={handleLoadSession}
        onRefreshSessions={refreshSessions}
      />
    </div>
  );
}
