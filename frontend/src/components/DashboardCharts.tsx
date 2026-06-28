import Highcharts from "highcharts";
import HighchartsReact from "highcharts-react-official";
import type { IncidentAnalysisRun, IncidentSummary } from "../contracts/incidentContracts";
import type { EventRecord } from "../contracts/eventView";

type Props = {
  incidents: IncidentSummary[];
  events: EventRecord[];
  analysisRuns: IncidentAnalysisRun[];
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
    ? ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#6366f1", "#a855f7"]
    : ["#fca5a5", "#fdba74", "#fde047", "#86efac", "#93c5fd", "#c4b5fd", "#d8b4fe"];
}

function gradientColor(theme: "light" | "dark", color: string) {
  const paletteColor = Highcharts.color(color);
  const start = theme === "light" ? paletteColor?.brighten(0.28).get("rgba") ?? color : paletteColor?.brighten(0.08).get("rgba") ?? color;
  const end = theme === "light" ? color : paletteColor?.brighten(-0.04).get("rgba") ?? color;

  return {
    linearGradient: { x1: 0, y1: 0, x2: 1, y2: 1 },
    stops: [
      [0, start],
      [1, end],
    ],
  };
}

function chartGradients(theme: "light" | "dark") {
  return chartColors(theme).map((color) => gradientColor(theme, color));
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

export function DashboardCharts({ incidents, events, analysisRuns, theme }: Props) {
  const incidentStatusCounts = countBy(incidents, (incident) => incident.status);
  const eventTypeCounts = countBy(events, (event) => event.event_type);
  const eventCountsByIncident = countBy(events, (event) => event.incident_id);
  const palette = chartGradients(theme);

  const incidentStatusOptions = {
    ...commonOptions(theme),
    chart: { ...commonOptions(theme).chart, type: "pie" as const, height: 300 },
    tooltip: {
      ...commonOptions(theme).tooltip,
      pointFormat: "<b>{point.y}</b> incidents",
    },
    colors: palette,
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
    chart: { ...commonOptions(theme).chart, type: "column" as const, height: 300 },
    xAxis: {
      ...commonOptions(theme).xAxis,
      categories: Object.keys(eventTypeCounts),
    },
    tooltip: {
      ...commonOptions(theme).tooltip,
      pointFormat: "<b>{point.y}</b> events",
    },
    colors: palette,
    series: [
      {
        type: "column" as const,
        data: Object.values(eventTypeCounts).map((value, index) => ({
          y: value,
          color: palette[index % palette.length],
        })),
      },
    ],
  };

  const eventCountOptions = {
    ...commonOptions(theme),
    chart: { ...commonOptions(theme).chart, type: "bar" as const, height: 300 },
    xAxis: {
      ...commonOptions(theme).xAxis,
      categories: incidents.map((incident) => incident.service_name),
    },
    tooltip: {
      ...commonOptions(theme).tooltip,
      pointFormat: "<b>{point.y}</b> events",
    },
    colors: palette,
    series: [
      {
        type: "bar" as const,
        data: incidents.map((incident, index) => ({
          y: eventCountsByIncident[incident.incident_id] ?? 0,
          color: palette[index % palette.length],
        })),
      },
    ],
  };

  const evaluationLatencyOptions = {
    ...commonOptions(theme),
    chart: { ...commonOptions(theme).chart, type: "bar" as const, height: 300 },
    xAxis: {
      ...commonOptions(theme).xAxis,
      categories: analysisRuns.map((run) => run.scenario_type),
    },
    tooltip: {
      ...commonOptions(theme).tooltip,
      pointFormat: "<b>{point.y}</b> ms",
    },
    colors: palette,
    series: [
      {
        type: "bar" as const,
        data: analysisRuns.map((run, index) => ({
          y: run.analysis_latency_ms ?? 0,
          color: palette[index % palette.length],
        })),
      },
    ],
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="panel rounded-2xl p-5 h-full">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Incident status mix</h3>
          <p className="text-sm text-muted">Current lifecycle spread across all tracked incidents.</p>
        </div>
        <HighchartsReact highcharts={Highcharts} options={incidentStatusOptions} />
      </div>

      <div className="panel rounded-2xl p-5 h-full">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Event volume by type</h3>
          <p className="text-sm text-muted">Which audit events are happening most often.</p>
        </div>
        <HighchartsReact highcharts={Highcharts} options={eventTypeOptions} />
      </div>

      <div className="panel rounded-2xl p-5 h-full">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Events per incident</h3>
          <p className="text-sm text-muted">How much activity each incident has accumulated.</p>
        </div>
        <HighchartsReact highcharts={Highcharts} options={eventCountOptions} />
      </div>

      <div className="panel rounded-2xl p-5 h-full">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Analysis latency</h3>
          <p className="text-sm text-muted">Completed run timing across scenario types.</p>
        </div>
        <HighchartsReact highcharts={Highcharts} options={evaluationLatencyOptions} />
      </div>
    </div>
  );
}
