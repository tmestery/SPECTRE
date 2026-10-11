import type { Finding } from "../types/events";
import { FindingCard } from "../findings/FindingCard";
import { sortByCreatedAt } from "../lib/sort";

const SECURITY_TYPES = new Set(["secret", "vulnerability", "misconfiguration", "validation_attempt"]);

interface Props {
  findings: Finding[];
  judgments?: Finding[];
  repo: string;
  branch: string;
}

export function LatestDiscovery({ findings, judgments = [], repo, branch }: Props) {
  const security = sortByCreatedAt(
    findings.filter((f) => SECURITY_TYPES.has(f.type) && f.severity !== "info"),
  );
  const latest = security.length > 0 ? security[security.length - 1] : null;
  const judgment = latest
    ? judgments.find((j) => String(j.evidence.reviewed_finding_id ?? "") === latest.id)
    : null;

  return (
    <aside className="latest-discovery" aria-label="Latest discovery">
      <div className="panel-heading">
        <h2>Latest discovery</h2>
        <span className="discovery-count">{security.length}</span>
      </div>
      {latest ? (
        <FindingCard finding={latest} judgment={judgment} repo={repo} branch={branch} />
      ) : (
        <p className="placeholder">Scanning… discoveries will surface here one at a time.</p>
      )}
    </aside>
  );
}
