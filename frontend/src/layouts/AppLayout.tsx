import { Outlet } from "react-router-dom";
import { Sidebar } from "../components/Sidebar";
import { useLayout } from "../contexts/LayoutContext";

export function AppLayout() {
  const { isSidebarCollapsed } = useLayout();
  const sidebarWidth = isSidebarCollapsed ? "0px" : "clamp(16rem, 15vw, 20rem)";

  return (
    <div className="min-h-screen w-full">
      <div
        className="fixed inset-y-0 left-0 z-20 overflow-hidden border-r border-[color:var(--border)] bg-[color:var(--surface)] transition-[width,opacity,transform] duration-300 ease-in-out"
        style={{
          width: sidebarWidth,
          opacity: isSidebarCollapsed ? 0 : 1,
          transform: isSidebarCollapsed ? "translateX(-1rem)" : "translateX(0)",
          pointerEvents: isSidebarCollapsed ? "none" : "auto",
        }}
      >
        <Sidebar />
      </div>
      <main className="min-h-screen w-full transition-[padding-left] duration-300 ease-in-out" style={{ paddingLeft: sidebarWidth }}>
        <div className="mx-auto max-w-[1680px] p-6 space-y-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
