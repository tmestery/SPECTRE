import type { Finding } from "../types/events";
import { FindingCard } from "./FindingCard";
import { sortByCreatedAt } from "../lib/sort";

interface Props {
  findings: Finding[];
  repo: string;
  branch: string;
}

const SECURITY_TYPES = new Set(["secret", "vulnerability", "misconfiguration", "validation_attempt"]);

export function FindingsTimeline({ findings, repo, branch }: Props) {
  const security = sortByCreatedAt(
    findings.filter((f) => SECURITY_TYPES.has(f.type) && f.severity !== "info"),
  );

  return (
    <div className="panel timeline-panel">
      <h2>Findings Timeline</h2>
      <div className="timeline-scroll">
        {security.length === 0 ? (
          <p className="placeholder">No security findings yet.</p>
        ) : (
          security.map((finding) => (
            <FindingCard key={finding.id} finding={finding} repo={repo} branch={branch} />
          ))
        )}
      </div>
    </div>
  );
}
