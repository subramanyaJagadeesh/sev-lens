type SelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

type Props = {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  maxLabelLength?: number;
  disabled?: boolean;
  className?: string;
  ariaLabel?: string;
  id?: string;
  name?: string;
};

function ChevronDownIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4">
      <path d="M7 10l5 5 5-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
    </svg>
  );
}

export function Select({
  value,
  options,
  onChange,
  placeholder,
  maxLabelLength,
  disabled = false,
  className = "",
  ariaLabel,
  id,
  name,
}: Props) {
  return (
    <div className={`relative min-w-0 ${className}`}>
      <select
        id={id}
        name={name}
        value={value}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={(event) => onChange(event.target.value)}
        className="input appearance-none pr-10"
      >
        {placeholder ? (
          <option value="">
            {truncateLabel(placeholder, maxLabelLength)}
          </option>
        ) : null}
        {options.map((option) => (
          <option key={option.value} value={option.value} disabled={option.disabled}>
            {truncateLabel(option.label, maxLabelLength)}
          </option>
        ))}
      </select>
      <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-subtle">
        <ChevronDownIcon />
      </span>
    </div>
  );
}

function truncateLabel(value: string, maxLength?: number) {
  if (!maxLength || value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, Math.max(0, maxLength - 1)).trimEnd()}…`;
}
