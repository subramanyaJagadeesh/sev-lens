import Highcharts from "highcharts";
import HighchartsReact from "highcharts-react-official";
import type { IncidentSummary } from "../contracts/incidentContracts";
import type { EventRecord } from "../contracts/eventView";

type Props = {
  incidents: IncidentSummary[];
  events: EventRecord[];
  theme: "light" | "dark";
};

function countBy<T>(items: T[], keyGetter: (item: T) => string) {
  return items.reduce<Record<string, number>>((accumulator, item) => {
    const key = keyGetter(item);
    accumulator[key] = (accumulator[key] ?? 0) + 1;
    return accumulator;
  }, {});
}

function chartColors(theme: "light" | "dark") {
  return theme === "light"
    ? ["#0f766e", "#2563eb", "#7c3aed", "#ea580c", "#be123c", "#ca8a04", "#16a34a"]
    : ["#5eead4", "#93c5fd", "#c4b5fd", "#fdba74", "#fda4af", "#fde68a", "#86efac"];
}

function heatmapColors(theme: "light" | "dark") {
  return theme === "light"
    ? ["#fef3c7", "#fde68a", "#fcd34d", "#fdba74", "#fb923c", "#f97316", "#ea580c"]
    : ["#3f2d0a", "#7c2d12", "#b45309", "#d97706", "#f59e0b", "#fbbf24", "#fde68a"];
}

function chartTextColor(theme: "light" | "dark") {
  return theme === "light" ? "#0f172a" : "#f4f4f5";
}

function chartGridColor(theme: "light" | "dark") {
  return theme === "light" ? "#d8e0ea" : "#2a2a2a";
}

function commonOptions(theme: "light" | "dark") {
  return {
    chart: {
      backgroundColor: "transparent",
      style: {
        fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      },
    },
    title: { text: undefined },
    credits: { enabled: false },
    legend: { enabled: false },
    colors: chartColors(theme),
    xAxis: {
      labels: { style: { color: chartTextColor(theme) } },
      lineColor: chartGridColor(theme),
      tickColor: chartGridColor(theme),
    },
    yAxis: {
      title: { text: undefined },
      labels: { style: { color: chartTextColor(theme) } },
      gridLineColor: chartGridColor(theme),
    },
    tooltip: {
      backgroundColor: theme === "light" ? "#ffffff" : "#111111",
      borderColor: chartGridColor(theme),
      style: { color: chartTextColor(theme) },
    },
  } as const;
}

export function DashboardCharts({ incidents, events, theme }: Props) {
  const incidentStatusCounts = countBy(incidents, (incident) => incident.status);
  const eventTypeCounts = countBy(events, (event) => event.event_type);
  const eventCountsByIncident = countBy(events, (event) => event.incident_id);

  const incidentStatusOptions = {
    ...commonOptions(theme),
    chart: { ...commonOptions(theme).chart, type: "pie" as const },
    tooltip: {
      ...commonOptions(theme).tooltip,
      pointFormat: "<b>{point.y}</b> incidents",
    },
    colors: heatmapColors(theme),
    plotOptions: {
      pie: {
        innerSize: "60%",
        borderWidth: 0,
        dataLabels: {
          enabled: true,
          style: {
            color: chartTextColor(theme),
          },
        },
      },
    },
    series: [
      {
        type: "pie" as const,
        data: Object.entries(incidentStatusCounts).map(([name, y]) => ({ name, y })),
      },
    ],
  };

  const eventTypeOptions = {
    ...commonOptions(theme),
    chart: { ...commonOptions(theme).chart, type: "column" as const },
    xAxis: {
      ...commonOptions(theme).xAxis,
      categories: Object.keys(eventTypeCounts),
    },
    tooltip: {
      ...commonOptions(theme).tooltip,
      pointFormat: "<b>{point.y}</b> events",
    },
    colors: heatmapColors(theme),
    series: [
      {
        type: "column" as const,
        data: Object.values(eventTypeCounts).map((value, index) => ({
          y: value,
          color: heatmapColors(theme)[index % heatmapColors(theme).length],
        })),
      },
    ],
  };

  const eventCountOptions = {
    ...commonOptions(theme),
    chart: { ...commonOptions(theme).chart, type: "bar" as const },
    xAxis: {
      ...commonOptions(theme).xAxis,
      categories: incidents.map((incident) => incident.service_name),
    },
    tooltip: {
      ...commonOptions(theme).tooltip,
      pointFormat: "<b>{point.y}</b> events",
    },
    colors: heatmapColors(theme),
    series: [
      {
        type: "bar" as const,
        data: incidents.map((incident, index) => ({
          y: eventCountsByIncident[incident.incident_id] ?? 0,
          color: heatmapColors(theme)[index % heatmapColors(theme).length],
        })),
      },
    ],
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="panel rounded-2xl p-5">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Incident status mix</h3>
          <p className="text-sm text-muted">Current lifecycle spread across all tracked incidents.</p>
        </div>
        <HighchartsReact highcharts={Highcharts} options={incidentStatusOptions} />
      </div>

      <div className="panel rounded-2xl p-5">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Event volume by type</h3>
          <p className="text-sm text-muted">Which audit events are happening most often.</p>
        </div>
        <HighchartsReact highcharts={Highcharts} options={eventTypeOptions} />
      </div>

      <div className="panel rounded-2xl p-5">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Events per incident</h3>
          <p className="text-sm text-muted">How much activity each incident has accumulated.</p>
        </div>
        <HighchartsReact highcharts={Highcharts} options={eventCountOptions} />
      </div>
    </div>
  );
}
