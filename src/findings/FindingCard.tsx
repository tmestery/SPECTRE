import type { Finding } from "../types/events";
import { SeverityBadge } from "./SeverityBadge";
import { VerdictBadge } from "./VerdictBadge";
import { fileFromTarget, githubPermalink } from "../lib/github";

interface Props {
  finding: Finding;
  repo: string;
  branch: string;
  judgment?: Finding | null;
}

export function FindingCard({ finding, repo, branch, judgment }: Props) {
  const evidencePath =
    (finding.evidence.file as string | undefined) ??
    (finding.evidence.path as string | undefined);
  const line = finding.evidence.line as number | undefined;
  const fromTarget = fileFromTarget(finding.target);
  const path = evidencePath ?? fromTarget.path;
  const permalink = path ? githubPermalink(repo, branch, path, line ?? fromTarget.line) : null;
  const judgmentVerdict = judgment?.evidence?.verdict
    ? String(judgment.evidence.verdict)
    : null;

  return (
    <article className="finding-card">
      <div className="finding-header">
        <SeverityBadge severity={finding.severity} />
        <span className="finding-type">{finding.type}</span>
        <span className="finding-agent">{finding.agent}</span>
        {judgmentVerdict ? <VerdictBadge verdict={judgmentVerdict} kind="judgment" /> : null}
      </div>
      <h3>{finding.title}</h3>
      {permalink ? (
        <a href={permalink} target="_blank" rel="noreferrer">
          {path}
          {line ? `:${line}` : ""}
        </a>
      ) : (
        <code>{finding.target}</code>
      )}
      {finding.evidence.snippet_redacted ? (
        <pre className="evidence">{String(finding.evidence.snippet_redacted)}</pre>
      ) : null}
    </article>
  );
}
