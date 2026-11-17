import { loadOrderLineItems, type OrderLineItem } from "@/lib/store-data";

import type { ChartSpec } from "./chart";
import { applyFilters } from "./filters";
import { dateRangeOf, periodWarnings, type DateRange, type ResultColumn, type ResultRow } from "./query";
import type { StoreQueryFilters } from "./schema";

export interface ReturnedItemsQuery {
  startDate: string;
  endDate: string;
  filters?: StoreQueryFilters;
  /** Maximum rows; newest returns first. Defaults to 50. */
  limit?: number;
}

/** Row-by-row list of returned items. Same shape as a report result, drawn as a table. */
export interface ReturnedItemsResult {
  view: "list";
  period: DateRange & { dateField: "return_date"; dataAvailable: DateRange | null };
  columns: ResultColumn[];
  rows: ResultRow[];
  totals: { returns: number; refunds: number };
  matchedLineItems: number;
  totalRows: number;
  truncated: boolean;
  warnings: string[];
  chart: ChartSpec;
}

const COLUMNS: ResultColumn[] = [
  { key: "day", label: "Returned", role: "dimension", format: "date" },
  { key: "order", label: "Order", role: "dimension", format: "text" },
  { key: "product", label: "Product", role: "dimension", format: "text" },
  { key: "variant", label: "Size / colour", role: "dimension", format: "text" },
  { key: "return_reason", label: "Reason", role: "dimension", format: "text" },
  { key: "refunds", label: "Refund", role: "metric", format: "currency" },
];

/** Every item that came back between the two dates (by return date), newest first. */
export function listReturnedItems(
  query: ReturnedItemsQuery,
  dataset: readonly OrderLineItem[] = loadOrderLineItems(),
): ReturnedItemsResult {
  const { startDate, endDate } = query;
  const available = dateRangeOf(dataset, "return_date");
  const warnings = periodWarnings({ startDate, endDate }, available, "return_date");

  const inPeriod = dataset.filter(
    (item) => item.returnDate !== null && item.returnDate >= startDate && item.returnDate <= endDate,
  );
  const filtered = applyFilters(inPeriod, query.filters ?? {}, dataset);
  warnings.push(...filtered.warnings);

  const items = [...filtered.items].sort(
    (a, b) => b.returnDate!.localeCompare(a.returnDate!) || a.lineItemId.localeCompare(b.lineItemId),
  );
  const limit = query.limit ?? 50;
  const refundCents = items.reduce((total, item) => total + Math.round(item.refundAmount * 100), 0);

  return {
    view: "list",
    period: { startDate, endDate, dateField: "return_date", dataAvailable: available },
    columns: COLUMNS,
    rows: items.slice(0, limit).map((item) => ({
      day: item.returnDate,
      order: item.orderId,
      product: item.productTitle,
      variant: item.variant,
      return_reason: item.returnReason ?? "Unspecified",
      refunds: item.refundAmount,
    })),
    totals: { returns: items.length, refunds: refundCents / 100 },
    matchedLineItems: items.length,
    totalRows: items.length,
    truncated: items.length > limit,
    warnings,
    chart: { type: "table", title: "Returned items", x: null, metrics: COLUMNS.filter((column) => column.role === "metric") },
  };
}
