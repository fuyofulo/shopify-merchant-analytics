import type { StoreQueryInput } from "./schema";

/**
 * Merchant questions and the `queryStoreData` call that answers each one.
 * Useful as few-shot examples in the LLM prompt, and run as tests.
 *
 * Relative periods are resolved against 2025-10-27 (a Monday), the latest
 * date in the dataset: "last week" = 2025-10-20 to 2025-10-26, "last month" =
 * September 2025. "All time" = the full order history, 2025-05-06 to 2025-10-27.
 */
export const EXAMPLE_QUERIES: { question: string; query: StoreQueryInput }[] = [
  {
    question: "How many customers have returned their products, and why?",
    query: {
      startDate: "2025-05-06",
      endDate: "2025-10-27",
      metrics: ["customers_with_returns", "returns", "refunds"],
      groupBy: ["return_reason"],
      filters: { returned: true },
    },
  },
  {
    question: "What are our top-selling products?",
    query: {
      startDate: "2025-05-06",
      endDate: "2025-10-27",
      metrics: ["net_sales", "units_sold", "orders"],
      groupBy: ["product"],
      limit: 5,
    },
  },
  {
    question: "What are repeat customers buying on their repeat purchases?",
    query: {
      startDate: "2025-05-06",
      endDate: "2025-10-27",
      metrics: ["units_sold", "net_sales", "customers"],
      groupBy: ["product"],
      filters: { customerType: "repeat" },
    },
  },
  {
    question: "What is the average sale we are doing per customer?",
    query: {
      startDate: "2025-05-06",
      endDate: "2025-10-27",
      metrics: ["sales_per_customer", "average_order_value", "customers", "orders"],
    },
  },
  {
    question: "Which sales channel is being used the most?",
    query: {
      startDate: "2025-05-06",
      endDate: "2025-10-27",
      metrics: ["orders", "net_sales", "customers"],
      groupBy: ["sales_channel"],
    },
  },
  {
    question: "How many sales did we do last week?",
    query: {
      startDate: "2025-10-20",
      endDate: "2025-10-26",
      metrics: ["orders", "net_sales", "units_sold"],
    },
  },
  {
    question: "How many sales did we do last month?",
    query: {
      startDate: "2025-09-01",
      endDate: "2025-09-30",
      metrics: ["orders", "net_sales", "units_sold"],
    },
  },
  {
    question: "How have sales trended month over month?",
    query: {
      startDate: "2025-05-06",
      endDate: "2025-10-27",
      metrics: ["net_sales", "orders"],
      groupBy: ["month"],
    },
  },
];
