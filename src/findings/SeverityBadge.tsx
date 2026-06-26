interface Props {
  severity: string;
}

const COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  info: "#64748b",
};

export function SeverityBadge({ severity }: Props) {
  const color = COLORS[severity] ?? COLORS.info;
  return (
    <span className="severity-badge" style={{ backgroundColor: color }}>
      {severity}
    </span>
  );
}
