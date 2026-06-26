import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../layouts/AppLayout";
import { DashboardPage } from "../pages/DashboardPage";
import { IncidentDetailsPage } from "../pages/IncidentDetailsPage";
import { IncidentsPage } from "../pages/IncidentsPage";
import { KnowledgeBasePage } from "../pages/KnowledgeBasePage";
import { KnowledgeDetailPage } from "../pages/KnowledgeDetailPage";
import { RcaMemoryPage } from "../pages/RcaMemoryPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/incidents/:incidentId" element={<IncidentDetailsPage />} />
        <Route path="/knowledge" element={<KnowledgeBasePage />} />
        <Route path="/knowledge/detail" element={<KnowledgeDetailPage />} />
        <Route path="/rca-memory" element={<RcaMemoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
