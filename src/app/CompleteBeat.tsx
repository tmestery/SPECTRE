import { useEffect } from "react";

interface Props {
  status: "complete" | "halted";
  durationMs?: number;
  onDone: () => void;
}

export function CompleteBeat({ status, durationMs = 1200, onDone }: Props) {
  useEffect(() => {
    const timer = window.setTimeout(onDone, durationMs);
    return () => window.clearTimeout(timer);
  }, [durationMs, onDone]);

  return (
    <div className="complete-beat" role="status" aria-live="polite">
      <div className="shell-atmosphere" aria-hidden="true" />
      <div className="complete-beat-inner">
        <p className="boot-mark">{status === "halted" ? "Halted" : "Audit complete"}</p>
        <p className="boot-status">Opening results…</p>
      </div>
    </div>
  );
}
