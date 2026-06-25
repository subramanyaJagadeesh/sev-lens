import { formatDecisionLabel } from "../lib/statusLabels";

export type DecisionType = "APPROVE" | "REJECT" | "ESCALATE";

type Props = {
  disabled?: boolean;
  currentDecision?: DecisionType | null;
  editing?: boolean;
  onDecision: (decision: DecisionType) => void;
  onBeginChange?: () => void;
};

const decisionOptions: Array<{ decision: DecisionType; label: string; className: string }> = [
  { decision: "APPROVE", label: "Approve", className: "button-success" },
  { decision: "REJECT", label: "Reject", className: "button-danger" },
  { decision: "ESCALATE", label: "Escalate", className: "button-warning" },
];

export function DecisionButtons({ disabled, currentDecision = null, editing = false, onDecision, onBeginChange }: Props) {
  const availableOptions = decisionOptions;

  return (
    <div className="space-y-4">
      {currentDecision && !editing ? (
        <div className="flex flex-wrap items-center gap-3">
          <span className="chip px-3 py-1 text-xs">Current decision: {formatDecisionLabel(currentDecision)}</span>
          {onBeginChange ? (
            <button type="button" disabled={disabled} onClick={onBeginChange} className="button theme-toggle">
              Change decision
            </button>
          ) : null}
        </div>
      ) : null}

      {editing ? (
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-sm text-muted">
            {currentDecision ? "Choose a replacement decision." : "Choose a decision."}
          </p>
        </div>
      ) : null}

      {(!currentDecision || editing) && (
        <div className="flex flex-wrap gap-3">
          {availableOptions.map((option) => (
            <button
              key={option.decision}
              disabled={disabled}
              onClick={() => onDecision(option.decision)}
              className={`button ${option.className}`}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
