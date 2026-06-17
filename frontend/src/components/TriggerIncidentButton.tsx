type Props = {
  disabled?: boolean;
  onTrigger: () => void;
};

export function TriggerIncidentButton({ disabled, onTrigger }: Props) {
  return (
    <button
      disabled={disabled}
      onClick={onTrigger}
      className="button button-primary"
    >
      Trigger mock incident
    </button>
  );
}
