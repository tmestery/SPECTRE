import type { EngagementMeta } from "../types/events";

interface Props {
  meta: EngagementMeta | null;
  status: string;
}

export function ScopeBanner({ meta, status }: Props) {
  if (!meta) {
    return (
      <header className="banner">
        <div>
          <h1>SPECTRE</h1>
          <p>GitHub repo audit crew — Phase 3</p>
        </div>
        <span className="status-pill idle">idle</span>
      </header>
    );
  }

  return (
    <header className="banner">
      <div>
        <h1>SPECTRE</h1>
        <p>
          {meta.repo} @ {meta.branch}
          {meta.scopeName ? ` · scope: ${meta.scopeName}` : ""}
        </p>
      </div>
      <span className={`status-pill ${status}`}>{status}</span>
    </header>
  );
}
