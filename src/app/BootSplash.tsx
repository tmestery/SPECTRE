interface Props {
  status: "connecting" | "error";
  errorMessage?: string | null;
  onRetry?: () => void;
}

export function BootSplash({ status, errorMessage, onRetry }: Props) {
  return (
    <div className="boot-splash" role="status" aria-live="polite">
      <div className="shell-atmosphere" aria-hidden="true" />
      <div className="boot-splash-inner">
        <p className="boot-mark">SPECTRE</p>
        <div className="boot-scan" aria-hidden="true">
          <span className="boot-scan-bar" />
        </div>
        {status === "error" ? (
          <>
            <p className="boot-status boot-status-error">
              {errorMessage || "Could not reach the orchestrator."}
            </p>
            {onRetry ? (
              <button type="button" className="primary-btn" onClick={onRetry}>
                Retry
              </button>
            ) : null}
          </>
        ) : (
          <p className="boot-status">Connecting to orchestrator…</p>
        )}
      </div>
    </div>
  );
}
