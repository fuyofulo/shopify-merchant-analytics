"use client";

import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ResultColumn, ResultRow } from "@/lib/analytics";
import { formatAxisValue, formatValue } from "@/lib/format";

import { ChartTooltip, Legend, seriesColor, tickStyle } from "./chart-parts";

const BAR_THICKNESS = 16; // ≤ 24px, never fills the slot

/**
 * Comparison across categories: horizontal bars so long product names stay
 * readable, 4px rounded data-ends, value at the tip when there is one series.
 */
export function BarView({ x, metrics, rows }: { x: ResultColumn; metrics: ResultColumn[]; rows: ResultRow[] }) {
  const single = metrics.length === 1;
  const longestLabel = Math.max(...rows.map((row) => String(row[x.key] ?? "").length), 4);
  const labelWidth = Math.min(190, Math.max(64, longestLabel * 7));
  const rowHeight = metrics.length * (BAR_THICKNESS + 2) + 14;
  const height = rows.length * rowHeight + (single ? 8 : 32);
  const format = metrics[0].format;

  return (
    <div>
      <Legend metrics={metrics} mark="bar" />
      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={rows} margin={{ top: 0, right: single ? 72 : 16, bottom: 0, left: 0 }} barGap={2}>
            {!single && <CartesianGrid horizontal={false} stroke="var(--grid)" />}
            <XAxis
              type="number"
              hide={single}
              tickFormatter={(value) => formatAxisValue(Number(value), format)}
              tick={tickStyle}
              tickLine={false}
              axisLine={false}
              allowDecimals={format !== "count"}
            />
            <YAxis
              type="category"
              dataKey={x.key}
              width={labelWidth}
              tick={{ ...tickStyle, fill: "var(--ink-2)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--axis)" }}
              interval={0}
            />
            <Tooltip
              cursor={{ fill: "var(--wash)" }}
              content={({ active, payload }) => <ChartTooltip active={active} payload={payload} x={x} metrics={metrics} />}
            />
            {metrics.map((metric, index) => (
              <Bar
                key={metric.key}
                dataKey={metric.key}
                name={metric.label}
                fill={seriesColor(index)}
                radius={[0, 4, 4, 0]}
                barSize={BAR_THICKNESS}
                isAnimationActive={false}
              >
                {single && (
                  <LabelList
                    dataKey={metric.key}
                    position="right"
                    formatter={(value) => formatValue(typeof value === "number" ? value : null, metric.format)}
                    style={{ fill: "var(--ink-2)", fontSize: 12, fontVariantNumeric: "tabular-nums" }}
                  />
                )}
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
