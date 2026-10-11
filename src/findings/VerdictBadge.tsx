type VerdictKind = "judgment" | "handoff" | "report";

interface Props {
  verdict?: string | null;
  kind?: VerdictKind;
}

const LABELS: Record<string, string> = {
  uphold: "Uphold",
  downgrade: "Downgrade",
  dismiss: "Dismiss",
  approve: "Approve",
  defer: "Defer",
  reject: "Reject",
  accept: "Accept",
  revise: "Revise",
};

export function VerdictBadge({ verdict, kind = "judgment" }: Props) {
  if (!verdict) {
    return <span className="verdict-badge verdict-unknown">No verdict</span>;
  }

  const normalized = verdict.toLowerCase();
  const label = LABELS[normalized] ?? verdict;
  return (
    <span className={`verdict-badge verdict-${kind} verdict-${normalized}`} data-verdict={normalized}>
      {label}
    </span>
  );
}
