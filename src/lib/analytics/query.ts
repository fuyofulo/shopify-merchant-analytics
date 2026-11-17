import { loadOrderLineItems, type OrderLineItem } from "@/lib/store-data";

import { bucketsBetween } from "./dates";
import { DIMENSIONS, dateOf, type DateField, type DimensionKey } from "./dimensions";
import { applyFilters } from "./filters";
import { METRICS, roundMetric, type MetricFormat, type MetricKey } from "./metrics";
import { storeQuerySchema, type StoreQuery, type StoreQueryInput } from "./schema";

export type ResultValue = string | number | null;
export type ResultRow = Record<string, ResultValue>;

/** Describes one column of `rows`, so a UI can label and format it (e.g. for charts). */
export interface ResultColumn {
  key: DimensionKey | MetricKey;
  label: string;
  role: "dimension" | "metric";
  format: MetricFormat | "date" | "text";
}

export interface DateRange {
  startDate: string;
  endDate: string;
}

export interface StoreQueryResult {
  /** The validated query that was run, with defaults filled in. */
  query: StoreQuery;
  period: DateRange & {
    dateField: DateField;
    /** First and last date present in the data for `dateField`. */
    dataAvailable: DateRange | null;
  };
  columns: ResultColumn[];
  /** One row per group: dimension values keyed by dimension, metric values keyed by metric. */
  rows: ResultRow[];
  /** Metrics over everything matched, independent of grouping and `limit`. */
  totals: Partial<Record<MetricKey, number | null>>;
  /** Number of line items that matched the period and filters. */
  matchedLineItems: number;
  /** Number of rows before `limit` was applied. */
  totalRows: number;
  truncated: boolean;
  /** Human-readable notes about the result: empty periods, unknown filter values, etc. */
  warnings: string[];
}

/**
 * Answers an analytics question over the store's order history.
 *
 * Takes a period (`startDate`–`endDate`, inclusive), the metrics to compute,
 * and optionally dimensions to group by, filters, sorting and a row limit.
 * Designed to be called by an LLM as a tool: input is validated with
 * `storeQuerySchema`, and the output is plain JSON with warnings the model can
 * act on.
 *
 * @param input   The query; validated and defaulted with `storeQuerySchema`.
 * @param dataset Line items to query. Defaults to `data/orders.csv`.
 * @throws ZodError when the input is invalid.
 */
export function queryStoreData(
  input: StoreQueryInput,
  dataset: readonly OrderLineItem[] = loadOrderLineItems(),
): StoreQueryResult {
  const parsed = storeQuerySchema.parse(input);
  // De-duplicate, and always return the sort metric even if it was not asked for.
  const query: StoreQuery = {
    ...parsed,
    metrics: [...new Set([...parsed.metrics, ...(parsed.sortBy ? [parsed.sortBy] : [])])],
    groupBy: [...new Set(parsed.groupBy)],
  };
  const { startDate, endDate, dateField, groupBy, metrics } = query;

  const available = dateRangeOf(dataset, dateField);
  const warnings = periodWarnings({ startDate, endDate }, available, dateField);

  const inPeriod = dataset.filter((item) => {
    const date = dateOf(item, dateField);
    return date !== null && date >= startDate && date <= endDate;
  });
  const filtered = applyFilters(inPeriod, query.filters, dataset);
  warnings.push(...filtered.warnings);
  const items = filtered.items;
  if (items.length === 0 && inPeriod.length > 0) {
    warnings.push("No line items match the filters in this period.");
  }

  const groups = groupItems(items, query, available);
  const evaluate = (groupItems: readonly OrderLineItem[]) =>
    Object.fromEntries(
      metrics.map((key) => [key, roundMetric(METRICS[key].compute(groupItems), METRICS[key].format)]),
    ) as Record<MetricKey, number | null>;

  const allRows: ResultRow[] = groups.map(({ dimensionValues, items: groupItems }) => ({
    ...Object.fromEntries(groupBy.map((key, i) => [key, dimensionValues[i]])),
    ...evaluate(groupItems),
  }));
  allRows.sort(rowComparator(query));
  const rows = query.limit ? allRows.slice(0, query.limit) : allRows;

  return {
    query,
    period: { startDate, endDate, dateField, dataAvailable: available },
    columns: [
      ...groupBy.map((key): ResultColumn => ({
        key,
        label: DIMENSIONS[key].label,
        role: "dimension",
        format: DIMENSIONS[key].timeGrain ? "date" : "text",
      })),
      ...metrics.map((key): ResultColumn => ({
        key,
        label: METRICS[key].label,
        role: "metric",
        format: METRICS[key].format,
      })),
    ],
    rows,
    totals: evaluate(items),
    matchedLineItems: items.length,
    totalRows: allRows.length,
    truncated: rows.length < allRows.length,
    warnings,
  };
}

/** First and last date in the dataset for the given date field. */
export function dateRangeOf(dataset: readonly OrderLineItem[], dateField: DateField): DateRange | null {
  const dates = dataset.map((item) => dateOf(item, dateField)).filter((date): date is string => date !== null);
  if (dates.length === 0) return null;
  dates.sort();
  return { startDate: dates[0], endDate: dates[dates.length - 1] };
}

/** Warnings when the requested period is outside, or partly outside, the data. */
export function periodWarnings(requested: DateRange, available: DateRange | null, dateField: DateField): string[] {
  const noun = dateField === "return_date" ? "Return" : "Order";
  if (!available) return [`The dataset contains no ${noun.toLowerCase()} dates.`];

  const range = `${available.startDate} to ${available.endDate}`;
  if (requested.endDate < available.startDate || requested.startDate > available.endDate) {
    return [`No data in the requested period. ${noun} data is only available from ${range}.`];
  }
  if (requested.startDate < available.startDate || requested.endDate > available.endDate) {
    return [`The requested period extends beyond the available ${noun.toLowerCase()} data (${range}); results cover only the overlap.`];
  }
  return [];
}

interface Group {
  dimensionValues: string[];
  items: OrderLineItem[];
}

function groupItems(items: readonly OrderLineItem[], query: StoreQuery, available: DateRange | null): Group[] {
  const { groupBy, dateField } = query;
  if (groupBy.length === 0) return [{ dimensionValues: [], items: [...items] }];

  const groups = new Map<string, Group>();

  // A single time breakdown gets a row for every bucket in the period, including
  // empty ones, so charts show gaps as zero. Buckets outside the data are not added.
  const grain = groupBy.length === 1 ? DIMENSIONS[groupBy[0]].timeGrain : undefined;
  if (grain && available) {
    const from = query.startDate > available.startDate ? query.startDate : available.startDate;
    const to = query.endDate < available.endDate ? query.endDate : available.endDate;
    if (from <= to) {
      for (const bucket of bucketsBetween(from, to, grain)) {
        groups.set(JSON.stringify([bucket]), { dimensionValues: [bucket], items: [] });
      }
    }
  }

  for (const item of items) {
    const dimensionValues = groupBy.map((key) => DIMENSIONS[key].value(item, dateField));
    const key = JSON.stringify(dimensionValues);
    let group = groups.get(key);
    if (!group) {
      group = { dimensionValues, items: [] };
      groups.set(key, group);
    }
    group.items.push(item);
  }

  return [...groups.values()];
}

/**
 * Explicit `sortBy` sorts by that metric. Otherwise time breakdowns are
 * chronological and everything else is sorted by the first metric, descending.
 * Ties fall back to dimension order so results are deterministic.
 */
function rowComparator(query: StoreQuery): (a: ResultRow, b: ResultRow) => number {
  const { groupBy, metrics, sortDirection } = query;
  const byDimensions = (a: ResultRow, b: ResultRow) => {
    for (const key of groupBy) {
      const order = String(a[key]).localeCompare(String(b[key]), "en", { numeric: true });
      if (order !== 0) return order;
    }
    return 0;
  };

  const chronological = groupBy.length > 0 && DIMENSIONS[groupBy[0]].timeGrain !== undefined;
  const sortMetric = query.sortBy ?? (chronological ? undefined : metrics[0]);
  if (!sortMetric) return byDimensions;

  return (a, b) => {
    const x = a[sortMetric] as number | null;
    const y = b[sortMetric] as number | null;
    if (x !== y) {
      if (x === null) return 1; // nulls last
      if (y === null) return -1;
      return sortDirection === "asc" ? x - y : y - x;
    }
    return byDimensions(a, b);
  };
}
