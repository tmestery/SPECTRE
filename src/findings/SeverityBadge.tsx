interface Props {
  severity: string;
}

const COLORS: Record<string, string> = {
  critical: "#c45c4a",
  high: "#d4844a",
  medium: "#d4a574",
  low: "#7aa889",
  info: "#6f6a61",
};

export function SeverityBadge({ severity }: Props) {
  const color = COLORS[severity] ?? COLORS.info;
  return (
    <span className="severity-badge" style={{ backgroundColor: color }}>
      {severity}
    </span>
  );
}
