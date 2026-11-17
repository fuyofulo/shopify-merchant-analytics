import type { ResultColumn, StoreQueryResult } from "./query";

/**
 * How to draw a query result. Derived from the result's shape, not chosen by
 * the LLM, so the same question always gets the same chart.
 *
 * - `stat`: no breakdown, show the numbers as tiles.
 * - `line`: a time breakdown (day/week/month) on the x axis.
 * - `bar`: a category breakdown (product, channel, return reason, …) on the x axis.
 *
 * With two dimensions, `seriesBy` splits each metric into one series per value
 * (e.g. one line per sales channel).
 */
export interface ChartSpec {
  type: "stat" | "line" | "bar";
  title: string;
  x: ResultColumn | null;
  seriesBy: ResultColumn | null;
  metrics: ResultColumn[];
}

export function chartFor(result: StoreQueryResult): ChartSpec {
  const dimensions = result.columns.filter((column) => column.role === "dimension");
  const metrics = result.columns.filter((column) => column.role === "metric");
  const [x = null, seriesBy = null] = dimensions;

  const metricTitle = metrics.map((metric) => metric.label).join(", ");
  const byTitle = dimensions.map((dimension) => dimension.label.toLowerCase()).join(" and ");

  return {
    type: x === null ? "stat" : x.format === "date" ? "line" : "bar",
    title: byTitle ? `${metricTitle} by ${byTitle}` : metricTitle,
    x,
    seriesBy,
    metrics,
  };
}
