import type { ReactNode } from "react";
import { IncidentDataProvider } from "../contexts/IncidentDataContext";
import { LayoutProvider } from "../contexts/LayoutContext";
import { ThemeProvider } from "../contexts/ThemeContext";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <IncidentDataProvider>
        <LayoutProvider>{children}</LayoutProvider>
      </IncidentDataProvider>
    </ThemeProvider>
  );
}
