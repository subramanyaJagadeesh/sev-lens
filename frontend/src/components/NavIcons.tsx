import type { ReactNode } from "react";

type IconProps = {
  className?: string;
  children?: ReactNode;
};

function BaseIcon({ className = "h-4 w-4", children }: IconProps) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className={className}>
      {children}
    </svg>
  );
}

export function DashboardIcon({ className }: IconProps) {
  return (
    <BaseIcon className={className ?? "h-4 w-4"}>
      <path
        d="M4 11.5 12 4l8 7.5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
      <path d="M6.5 10.5V20h11V10.5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
      <path d="M10 20v-5h4v5" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
    </BaseIcon>
  );
}

export function IncidentsIcon({ className }: IconProps) {
  return (
    <BaseIcon className={className ?? "h-4 w-4"}>
      <rect x="5" y="4.5" width="14" height="15" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8 8h8M8 12h8M8 16h5" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </BaseIcon>
  );
}

export function KnowledgeIcon({ className }: IconProps) {
  return (
    <BaseIcon className={className ?? "h-4 w-4"}>
      <path
        d="M4.5 6.5c2-1.4 4.2-2.1 6.5-2.1s4.5.7 6.5 2.1V18c-2-1.4-4.2-2.1-6.5-2.1S6.5 16.6 4.5 18V6.5Z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
      <path d="M11 5v11.2" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </BaseIcon>
  );
}

export function RcaIcon({ className }: IconProps) {
  return (
    <BaseIcon className={className ?? "h-4 w-4"}>
      <circle cx="12" cy="12" r="7.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M12 7.5V12l3 2" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
    </BaseIcon>
  );
}
