interface Props {
  disabled: boolean;
  onHalt: () => void;
}

export function HaltButton({ disabled, onHalt }: Props) {
  return (
    <button type="button" className="halt-btn" disabled={disabled} onClick={onHalt}>
      HALT
    </button>
  );
}
