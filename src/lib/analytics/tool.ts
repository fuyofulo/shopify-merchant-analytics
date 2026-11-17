import { tool } from "ai";
import { z } from "zod";

import { describeDataset } from "./describe";
import { queryStoreData } from "./query";
import { storeQuerySchema } from "./schema";

export const QUERY_STORE_DATA_DESCRIPTION = `Query the store's order history (one row per order line item) and compute metrics for a date range.
Use it for any question about sales, orders, products, customers, sales channels, discounts or returns.

- Always set startDate and endDate (inclusive, YYYY-MM-DD). Resolve relative periods ("last week", "last month") against the current date the app gives you; for this historical dataset that is latestDataDate from describeStoreData. Weeks run Monday to Sunday. For "all time", use the full range of order dates.
- "Sales" or "revenue" means net_sales unless the merchant says otherwise. "Average sale per customer" is sales_per_customer; "average order" is average_order_value.
- Returns: to explain why items were returned, filter { returned: true } and group by return_reason. Use dateField "return_date" for returns that happened during a period, rather than returns of orders placed in it.
- Repeat purchases: filter { customerType: "repeat" } to see what returning customers buy.
- Group by day/week/month for trends, by product/category/sales_channel/etc. for breakdowns. Use limit for "top N" questions and sortBy/sortDirection to rank.
- Read "warnings" in the result: they flag unknown filter values and periods outside the data. Fix the query and retry when needed.`;

/** Lets the LLM look up date coverage, products, channels, return reasons, metrics and dimensions. */
export const describeStoreDataTool = tool({
  description:
    "Describe the store dataset: date coverage (latestDataDate), counts, products, categories, sales channels, return reasons, sizes, colours, and the metrics and dimensions queryStoreData accepts. Call this first if you are unsure which values exist.",
  inputSchema: z.object({}),
  execute: async () => describeDataset(),
});

/** Runs `queryStoreData` with the LLM's arguments. */
export const queryStoreDataTool = tool({
  description: QUERY_STORE_DATA_DESCRIPTION,
  inputSchema: storeQuerySchema,
  execute: async (query) => queryStoreData(query),
});

/** Tool set to pass to the AI SDK, e.g. `streamText({ model, tools: storeAnalyticsTools, ... })`. */
export const storeAnalyticsTools = {
  describeStoreData: describeStoreDataTool,
  queryStoreData: queryStoreDataTool,
};
