"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ResultColumn, ResultRow } from "@/lib/analytics";
import { formatAxisValue, formatDateTick } from "@/lib/format";

import { ChartTooltip, Legend, seriesColor, tickStyle } from "./chart-parts";

/** Change over time: one 2px line per metric, a crosshair tooltip, and dots when there are few points. */
export function LineView({ x, metrics, rows }: { x: ResultColumn; metrics: ResultColumn[]; rows: ResultRow[] }) {
  const showDots = rows.length <= 31;
  const format = metrics[0].format;

  return (
    <div>
      <Legend metrics={metrics} mark="line" />
      <div className="h-60 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--grid)" />
            <XAxis
              dataKey={x.key}
              tickFormatter={(value) => formatDateTick(x.key, String(value))}
              tick={tickStyle}
              tickLine={false}
              axisLine={{ stroke: "var(--axis)" }}
              minTickGap={20}
            />
            <YAxis
              tickFormatter={(value) => formatAxisValue(Number(value), format)}
              tick={tickStyle}
              tickLine={false}
              axisLine={false}
              width={60}
              allowDecimals={format !== "count"}
            />
            <Tooltip
              cursor={{ stroke: "var(--axis)", strokeWidth: 1 }}
              content={({ active, payload }) => <ChartTooltip active={active} payload={payload} x={x} metrics={metrics} />}
            />
            {metrics.map((metric, index) => (
              <Line
                key={metric.key}
                dataKey={metric.key}
                name={metric.label}
                type="linear"
                stroke={seriesColor(index)}
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                dot={showDots ? { r: 4, fill: seriesColor(index), stroke: "var(--surface)", strokeWidth: 2 } : false}
                activeDot={{ r: 5, fill: seriesColor(index), stroke: "var(--surface)", strokeWidth: 2 }}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
