"use client";

import type { TooltipContentProps } from "recharts";

import type { ResultColumn } from "@/lib/analytics";
import { formatDateLabel, formatValue } from "@/lib/format";

/** Series colours in fixed order (never by rank), from the validated palette in globals.css. */
export const seriesColor = (index: number) => `var(--series-${(index % 3) + 1})`;

/** Axis ticks: muted ink, 12px, tabular figures so values line up. */
export const tickStyle = { fill: "var(--muted)", fontSize: 12, fontVariantNumeric: "tabular-nums" } as const;

/** Legend for two or more series; one series needs none (the title names it). */
export function Legend({ metrics, mark }: { metrics: ResultColumn[]; mark: "line" | "bar" }) {
  if (metrics.length < 2) return null;
  return (
    <ul className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
      {metrics.map((metric, index) => (
        <li key={metric.key} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className={mark === "line" ? "h-0.5 w-3 rounded-full" : "h-2.5 w-2.5 rounded-sm"}
            style={{ background: seriesColor(index) }}
          />
          {metric.label}
        </li>
      ))}
    </ul>
  );
}

/** One tooltip listing every series at the hovered point: value first, then the series name. */
export function ChartTooltip({
  active,
  payload,
  x,
  metrics,
}: Pick<TooltipContentProps<number, string>, "active" | "payload"> & { x: ResultColumn; metrics: ResultColumn[] }) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload as Record<string, string | number | null> | undefined;
  const xValue = String(row?.[x.key] ?? "");
  const heading = x.format === "date" ? formatDateLabel(x.key, xValue) : xValue;

  return (
    <div className="rounded-md border border-hairline bg-surface px-3 py-2 text-xs shadow-sm">
      <p className="mb-1 text-ink-2">{heading}</p>
      {metrics.map((metric, index) => (
        <p key={metric.key} className="flex items-center gap-2">
          <span aria-hidden className="h-0.5 w-3 rounded-full" style={{ background: seriesColor(index) }} />
          <span className="font-semibold tabular-nums text-ink">{formatValue(row?.[metric.key] ?? null, metric.format)}</span>
          <span className="text-ink-2">{metric.label}</span>
        </p>
      ))}
    </div>
  );
}
