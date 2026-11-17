import type { ResultColumn, StoreQueryResult } from "./query";

/**
 * How to draw a result. Derived from the result's shape, never chosen by the
 * LLM, so the same question always gets the same chart:
 *
 * - `stat`  (metrics card): no breakdown — single numbers.
 * - `line`: one time breakdown (day / week / month) — change over time.
 * - `bar`:  one category breakdown (product, channel, reason, …) — comparison.
 * - `table`: two breakdowns at once, or a row-by-row list — detail.
 */
export interface ChartSpec {
  type: "stat" | "line" | "bar" | "table";
  title: string;
  /** The dimension on the x axis (line) or category axis (bar); null otherwise. */
  x: ResultColumn | null;
  metrics: ResultColumn[];
}

type ChartableResult = Pick<StoreQueryResult, "columns">;

export function chartFor(result: ChartableResult): ChartSpec {
  const dimensions = result.columns.filter((column) => column.role === "dimension");
  const metrics = result.columns.filter((column) => column.role === "metric");

  const metricTitle = metrics.map((metric) => metric.label).join(", ");
  const byTitle = dimensions.map((dimension) => dimension.label.toLowerCase()).join(" and ");
  const title = byTitle ? `${metricTitle} by ${byTitle}` : metricTitle;

  if (dimensions.length === 0) return { type: "stat", title, x: null, metrics };
  if (dimensions.length > 1) return { type: "table", title, x: null, metrics };
  const [x] = dimensions;
  return { type: x.format === "date" ? "line" : "bar", title, x, metrics };
}
