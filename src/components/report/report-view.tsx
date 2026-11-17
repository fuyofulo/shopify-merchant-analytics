"use client";

import type { ResultColumn } from "@/lib/analytics";
import { METRICS, type MetricKey } from "@/lib/analytics/metrics";
import type { ReportOutput } from "@/lib/assistant/ui-types";
import { formatRange, formatValue } from "@/lib/format";

import { BarView } from "./bar-view";
import { DataTable } from "./data-table";
import { LineView } from "./line-view";

/** "Returned units, Refunds by product" → "Returned units, refunds by product" */
const sentenceCase = (title: string) => title.charAt(0) + title.slice(1).toLowerCase();

/** Totals as metrics cards, labelled and formatted from the metric definitions. */
function MetricCards({ totals, large }: { totals: ReportOutput["totals"]; large: boolean }) {
  const cards = Object.entries(totals).map(([key, value]) => {
    const metric = METRICS[key as MetricKey];
    return { key, label: metric?.label ?? key, value: formatValue(value ?? null, metric?.format ?? "decimal") };
  });

  return (
    <dl className={`grid gap-2 ${large ? "grid-cols-2 sm:grid-cols-3" : "grid-cols-2 sm:grid-cols-4"}`}>
      {cards.map((card) => (
        <div key={card.key} className="rounded-lg border border-hairline px-3 py-2">
          <dt className="text-xs text-ink-2">{card.label}</dt>
          <dd className={`mt-0.5 font-semibold text-ink ${large ? "text-2xl" : "text-base"}`}>{card.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function Warnings({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) return null;
  return (
    <ul className="mt-3 space-y-1">
      {warnings.map((warning) => (
        <li key={warning} className="flex gap-2 text-xs text-ink-2">
          <span aria-hidden className="text-warning">⚠</span>
          <span>
            <span className="sr-only">Note: </span>
            {warning}
          </span>
        </li>
      ))}
    </ul>
  );
}

/**
 * Draws a report tool result. The shape comes from `report.chart.type`, which
 * the server derives from the result, never from the model:
 * stat → metrics cards, line → trend, bar → comparison, table → row-by-row detail.
 */
export function ReportView({ report }: { report: ReportOutput }) {
  const { chart, rows, columns, period, warnings, totals } = report;
  // One y-axis only: plot the metrics that share the first metric's unit; the rest stay in the cards and table.
  const plotted: ResultColumn[] = chart.metrics.filter((metric) => metric.format === chart.metrics[0]?.format);
  const isList = report.view === "list";
  const empty = rows.length === 0 || (report.matchedLineItems === 0 && chart.type !== "stat");

  return (
    <section className="pop-in rounded-xl border border-hairline bg-surface p-4" aria-label={chart.title}>
      <header className="mb-3">
        <h3 className="text-sm font-semibold text-ink">{sentenceCase(chart.title)}</h3>
        <p className="text-xs text-muted">
          {formatRange(period.startDate, period.endDate)}
          {period.dateField === "return_date" ? " · by return date" : ""}
        </p>
      </header>

      {chart.type === "stat" ? (
        <MetricCards totals={totals} large />
      ) : empty ? (
        <p className="rounded-lg border border-hairline px-3 py-6 text-center text-sm text-ink-2">
          No data for these dates.
        </p>
      ) : (
        <div className="space-y-3">
          {(chart.type !== "table" || isList) && <MetricCards totals={totals} large={false} />}
          {chart.type === "line" && chart.x && <LineView x={chart.x} metrics={plotted} rows={rows} />}
          {chart.type === "bar" && chart.x && <BarView x={chart.x} metrics={plotted} rows={rows} />}
          {chart.type === "table" && <DataTable columns={columns} rows={rows} />}
          {report.truncated && (
            <p className="text-xs text-muted">
              Showing {rows.length} of {report.totalRows}.
            </p>
          )}
          {chart.type !== "table" && (
            <details className="text-sm">
              <summary className="cursor-pointer select-none text-xs text-ink-2 hover:text-ink">View as table</summary>
              <div className="mt-2">
                <DataTable columns={columns} rows={rows} />
              </div>
            </details>
          )}
        </div>
      )}

      <Warnings warnings={warnings} />
    </section>
  );
}
