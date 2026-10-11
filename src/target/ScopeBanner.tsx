import type { EngagementMeta } from "../types/events";

interface Props {
  meta: EngagementMeta | null;
  status: string;
}

export function ScopeBanner({ meta, status }: Props) {
  return (
    <header className="banner">
      <div className="brand-block">
        <p className="brand-mark">SPECTRE</p>
        <p className="brand-tag">
          {meta
            ? `${meta.repo} @ ${meta.branch}${meta.scopeName ? ` · ${meta.scopeName}` : ""}`
            : "Self-coordinating repo audit crew"}
        </p>
      </div>
      <span className={`status-pill ${status}`}>{status}</span>
    </header>
  );
}
