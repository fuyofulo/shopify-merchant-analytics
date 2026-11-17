import { z } from "zod";

import { DIMENSION_KEYS } from "./dimensions";
import { METRIC_KEYS } from "./metrics";

const stringList = (description: string) => z.array(z.string().min(1)).optional().describe(description);

export const storeQueryFiltersSchema = z
  .object({
    products: stringList("Product IDs (exact, e.g. 'P-1001') or product titles (case-insensitive, partial match, e.g. 'parka')."),
    categories: stringList("Product categories, e.g. ['Outerwear']."),
    salesChannels: stringList("Sales channels, e.g. ['Online Store', 'Point of Sale']."),
    customerType: z
      .enum(["new", "repeat"])
      .optional()
      .describe("'repeat' keeps only orders placed by returning customers (their repeat purchases); 'new' only first orders."),
    customerIds: stringList("Customer IDs, e.g. ['C-10233']."),
    orderIds: stringList("Order IDs, e.g. ['#1047']."),
    sizes: stringList("Variant sizes, e.g. ['S', 'M']."),
    colors: stringList("Variant colours, e.g. ['Black']."),
    fulfillmentStatuses: stringList("Fulfillment statuses: fulfilled, partially_fulfilled, unfulfilled."),
    returned: z.boolean().optional().describe("true = only returned items, false = only items that were kept."),
    returnReasons: stringList("Return reasons, e.g. ['Too small']. Implies returned items only."),
  })
  .describe("Optional filters. Text matching is case-insensitive; multiple values in one list are OR-ed, different filters are AND-ed.");

export const storeQuerySchema = z
  .object({
    startDate: z.iso.date().describe("First day of the period, inclusive (YYYY-MM-DD)."),
    endDate: z.iso.date().describe("Last day of the period, inclusive (YYYY-MM-DD)."),
    metrics: z
      .array(z.enum(METRIC_KEYS))
      .min(1)
      .max(METRIC_KEYS.length)
      .describe("What to measure. The first metric is the default sort key."),
    groupBy: z
      .array(z.enum(DIMENSION_KEYS))
      .max(2)
      .default([])
      .describe("Break results down by up to two dimensions, e.g. ['product'] or ['month', 'sales_channel']. Empty = one overall row."),
    filters: storeQueryFiltersSchema.default({}),
    dateField: z
      .enum(["order_date", "return_date"])
      .default("order_date")
      .describe("Date the period applies to. Use 'return_date' for 'returns that happened in <period>'; it limits results to returned items."),
    sortBy: z
      .enum(METRIC_KEYS)
      .optional()
      .describe("Metric to sort rows by. Defaults to chronological order for time breakdowns, otherwise the first metric."),
    sortDirection: z.enum(["asc", "desc"]).default("desc").describe("Sort direction when sorting by a metric."),
    limit: z.number().int().min(1).max(500).optional().describe("Maximum rows to return, e.g. 5 for 'top 5'."),
  })
  .refine((query) => query.startDate <= query.endDate, {
    message: "startDate must be on or before endDate.",
    path: ["endDate"],
  });

/** Query as accepted from callers / the LLM (defaults optional). */
export type StoreQueryInput = z.input<typeof storeQuerySchema>;
/** Query after validation, with defaults applied. */
export type StoreQuery = z.output<typeof storeQuerySchema>;
export type StoreQueryFilters = z.output<typeof storeQueryFiltersSchema>;
