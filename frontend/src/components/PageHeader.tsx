import type { ReactNode } from "react";
import { useLayout } from "../contexts/LayoutContext";
import { useTheme } from "../contexts/ThemeContext";

type Props = {
  title: string;
  description: string;
  showBackButton?: boolean;
  onBack?: () => void;
  actions?: ReactNode;
};

function SidebarIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5">
      <rect x="4" y="4" width="16" height="16" rx="3" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <line x1="9" y1="4" x2="9" y2="20" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5">
      <path d="M14 6l-6 6 6 6" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
    </svg>
  );
}

export function PageHeader({ title, description, showBackButton, onBack, actions }: Props) {
  const { isSidebarCollapsed, toggleSidebar } = useLayout();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="flex items-center justify-between gap-4">
      <div className="flex min-w-0 items-start gap-3">
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            className="icon-button"
            onClick={toggleSidebar}
            aria-label={isSidebarCollapsed ? "Open sidebar" : "Collapse sidebar"}
            title={isSidebarCollapsed ? "Open sidebar" : "Collapse sidebar"}
          >
            <SidebarIcon />
          </button>
          {showBackButton ? (
            <button
              type="button"
              className="icon-button"
              onClick={onBack}
              aria-label="Back"
              title="Back"
            >
              <BackIcon />
            </button>
          ) : null}
        </div>
        <div className="min-w-0">
          <p className="heading-eyebrow text-xs">SevLens</p>
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p className="text-sm text-muted">{description}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {actions}
        <button type="button" className="icon-button" onClick={toggleTheme} aria-label="Toggle theme">
          <span aria-hidden="true">{theme === "light" ? "☾" : "☀"}</span>
        </button>
      </div>
    </header>
  );
}
