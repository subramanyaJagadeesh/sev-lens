import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type LayoutContextValue = {
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
};

const LayoutContext = createContext<LayoutContextValue | null>(null);

export function LayoutProvider({ children }: { children: ReactNode }) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const value = useMemo<LayoutContextValue>(
    () => ({
      isSidebarCollapsed,
      toggleSidebar: () => setIsSidebarCollapsed((current) => !current),
    }),
    [isSidebarCollapsed],
  );

  return <LayoutContext.Provider value={value}>{children}</LayoutContext.Provider>;
}

export function useLayout() {
  const value = useContext(LayoutContext);
  if (!value) {
    throw new Error("useLayout must be used within LayoutProvider");
  }
  return value;
}
