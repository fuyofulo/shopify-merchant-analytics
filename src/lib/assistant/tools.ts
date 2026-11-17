import { tool } from "ai";
import { z } from "zod";

import {
  chartFor,
  DIMENSIONS,
  queryStoreData,
  storeQueryFiltersSchema,
  type DateField,
  type DimensionKey,
  type MetricKey,
} from "@/lib/analytics";

/**
 * Tool descriptions, written in the words merchants used in
 * data/merchant-report-requests-2025-10-27.xlsx. The first sentence is the
 * plain-English description, and the quoted phrases are real questions from
 * the Merchant Question column. The model matches a question to a tool by
 * this wording, so keep it in the merchants' language.
 */
export const TOOL_DESCRIPTIONS = {
  salesReport: `See your sales and revenue for any stretch of time (per day, by week, last month or since summer) and which products are your best sellers by revenue or by units sold, so you know what sold best before BFCM.
Merchants ask: "best seller since summer?", "top 10 products by revenue Oct 1 to Oct 15", "sales by week last 8 weeks", "weekly revenue by product since august", "what sold best this season?", "sales per day last 14 days", "revenue last month", "top sellers by units since July 1", "sales been weird lately", "total sales for each week from May through October".
"Sales" and "revenue" mean net_sales. For best sellers, group by product and rank by net_sales, or by units_sold when they say "by units". For trends, group by day, week or month.
Counts orders placed in the period. To compare returns with sales ("Returns too if it's easy", "are returns eating the sales bump", return rate), add returns, refunds or return_rate here.`,

  returnsReport: `See how your returns are doing: which products or categories got returned the most, how much you refunded, and why they came back, so you can tell if it's a sizing thing before you reorder.
Merchants ask: "which jackets came back as returns last week", "jakets returnd last wk", "how are returns doing", "returns by category this month", "returns by product last 30 days", "most returned category", "which styles are coming back the most? Is it a sizing thing?", "which coats got returned most over the last couple weeks".
Counts items that came back during the period (by return date). For "why" and sizing questions, group by return_reason or size. For a return rate or returns compared with sales, use salesReport instead.`,

  repeatCustomersReport: `See how many customers came back to order a 2nd time and what share of your orders come from repeat customers each month, so you know whether repeat customers are growing or not.
Merchants ask: "are repeat customers growing or not", "what % of orders are from returning customers lately", "repeat customer share by month", "how many customers came back twice", "are more ppl ordering a 2nd time now".
"Returning customers" here means people who ordered again, not product returns. For growth, group by month and use repeat_order_share. To see what repeat customers buy, filter customerType "repeat" and group by product.`,

  cannotAnswer: `The store's order data can't answer this question. Use only when it needs data the store doesn't have: ad spend, ROAS, campaigns or other marketing, website traffic, inventory or stock levels, product costs or profit, or forecasts. Also use it when the question isn't about the store.
Merchants ask: "what was my ROAS on the fall jacket campaign?", "how much did we spend on instagram ads".
Questions about dates outside the data still go to a report tool, because its warnings explain what is missing.`,
} as const;

const SALES_METRICS = [
  "net_sales", "units_sold", "orders", "customers", "average_order_value", "sales_per_customer",
  "gross_sales", "discounts", "discount_rate", "net_revenue", "units_per_order", "returns", "refunds", "return_rate",
] as const satisfies readonly MetricKey[];

const SALES_DIMENSIONS = [
  "day", "week", "month", "product", "category", "variant", "size", "color", "sales_channel", "customer_type",
  "fulfillment_status",
] as const satisfies readonly DimensionKey[];

const RETURNS_METRICS = ["returns", "returned_units", "refunds", "customers_with_returns"] as const satisfies readonly MetricKey[];

const RETURNS_DIMENSIONS = [
  "day", "week", "month", "product", "category", "variant", "size", "color", "return_reason", "sales_channel",
  "customer_type",
] as const satisfies readonly DimensionKey[];

const REPEAT_METRICS = [
  "repeat_order_share", "repeat_orders", "repeat_customers", "orders", "customers", "net_sales", "units_sold",
  "sales_per_customer", "average_order_value",
] as const satisfies readonly MetricKey[];

const REPEAT_DIMENSIONS = [
  "day", "week", "month", "customer_type", "product", "category", "sales_channel",
] as const satisfies readonly DimensionKey[];

/** Input schema shared by the report tools, limited to the metrics and dimensions each one allows. */
function reportInputSchema<
  const M extends readonly [MetricKey, ...MetricKey[]],
  const D extends readonly [DimensionKey, ...DimensionKey[]],
>(metrics: M, dimensions: D) {
  return z
    .object({
      startDate: z.iso.date().describe("Exact first day, inclusive, YYYY-MM-DD. Copy it from the date table in your instructions."),
      endDate: z.iso.date().describe("Exact last day, inclusive, YYYY-MM-DD."),
      metrics: z.array(z.enum(metrics)).min(1).describe("What to measure. The first one ranks the rows."),
      groupBy: z
        .array(z.enum(dimensions))
        .max(2)
        .optional()
        .describe("Break down by up to two of these, e.g. [\"week\"] or [\"product\"]. Leave out for a single total."),
      filters: storeQueryFiltersSchema.optional(),
      sortBy: z
        .enum(metrics)
        .optional()
        .describe("Rank rows by this metric instead of the first one. Ignored for day/week/month breakdowns, which stay in date order."),
      sortDirection: z.enum(["asc", "desc"]).optional().describe("\"desc\" (default) for most/top, \"asc\" for least/worst."),
      limit: z.number().int().min(1).max(50).optional().describe("Maximum rows, e.g. 10 for \"top 10\"."),
    })
    .refine((input) => input.startDate <= input.endDate, {
      message: "startDate must be on or before endDate.",
      path: ["endDate"],
    });
}

const salesInput = reportInputSchema(SALES_METRICS, SALES_DIMENSIONS);
const returnsInput = reportInputSchema(RETURNS_METRICS, RETURNS_DIMENSIONS);
const repeatInput = reportInputSchema(REPEAT_METRICS, REPEAT_DIMENSIONS);

type ReportInput = z.output<typeof salesInput> | z.output<typeof returnsInput> | z.output<typeof repeatInput>;

/** Runs a report and attaches a chart spec, so the UI can draw it straight from the tool result. */
function runReport(input: ReportInput, dateField: DateField = "order_date") {
  const groupBy = input.groupBy ?? [];
  // Day/week/month breakdowns always come back complete and in date order, so they draw as a line.
  const timeSeries = groupBy.length > 0 && DIMENSIONS[groupBy[0]].timeGrain !== undefined;
  const query = timeSeries
    ? {
        ...input,
        metrics: [...new Set([...input.metrics, ...(input.sortBy ? [input.sortBy] : [])])],
        sortBy: undefined,
        sortDirection: undefined,
        limit: undefined,
      }
    : input;
  const result = queryStoreData({ ...query, groupBy, filters: input.filters ?? {}, dateField });
  return { ...result, chart: chartFor(result) };
}

/**
 * Returns always use the return date: "jackets returned last week" means
 * items that came back last week, whenever they were ordered. (Return rates
 * compare returns with sales of the same orders, so they live in salesReport.)
 */
function runReturnsReport(input: z.output<typeof returnsInput>) {
  return runReport(input, "return_date");
}

/**
 * Creates the tools for one chat request. They share a guard so only the
 * first tool call runs: one question, one query, with exact dates.
 */
export function createMerchantTools() {
  let used = false;
  const once =
    <I, O>(run: (input: I) => O) =>
    async (input: I) => {
      if (used) return { error: "Only one tool call is allowed per question. Answer from the first result." };
      used = true;
      return run(input);
    };

  return {
    salesReport: tool({
      description: TOOL_DESCRIPTIONS.salesReport,
      inputSchema: salesInput,
      execute: once((input: z.output<typeof salesInput>) => runReport(input)),
    }),
    returnsReport: tool({
      description: TOOL_DESCRIPTIONS.returnsReport,
      inputSchema: returnsInput,
      execute: once(runReturnsReport),
    }),
    repeatCustomersReport: tool({
      description: TOOL_DESCRIPTIONS.repeatCustomersReport,
      inputSchema: repeatInput,
      execute: once((input: z.output<typeof repeatInput>) => runReport(input)),
    }),
    cannotAnswer: tool({
      description: TOOL_DESCRIPTIONS.cannotAnswer,
      inputSchema: z.object({
        missingData: z.string().describe("The data that would be needed, in plain words, e.g. \"ad spend for the fall jacket campaign\"."),
      }),
      execute: once(({ missingData }: { missingData: string }) => ({
        answerable: false,
        missingData,
        availableData:
          "Orders, products, categories, sizes and colours, sales channels, discounts, returns and refunds, and new vs repeat customers.",
      })),
    }),
  };
}

export type MerchantTools = ReturnType<typeof createMerchantTools>;
