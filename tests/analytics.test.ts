import { describe, expect, it } from "vitest";

import {
  describeDataset,
  EXAMPLE_QUERIES,
  queryStoreData,
  storeQuerySchema,
  type StoreQueryInput,
} from "@/lib/analytics";
import { bucketsBetween, startOfWeek } from "@/lib/analytics/dates";
import { loadOrderLineItems, parseCsv } from "@/lib/store-data";

// Expected values below were computed independently from data/orders.csv.
const ALL_TIME = { startDate: "2025-05-06", endDate: "2025-10-27" } as const;
const run = (query: Omit<StoreQueryInput, "startDate" | "endDate"> & Partial<StoreQueryInput>) =>
  queryStoreData({ ...ALL_TIME, ...query });

describe("store data", () => {
  it("parses every line item in the export", () => {
    const items = loadOrderLineItems();
    expect(items).toHaveLength(28);
    expect(items[0]).toMatchObject({
      orderId: "#1047",
      orderDate: "2025-05-06",
      size: "M",
      color: "Black",
      quantity: 2,
      lineTotal: 56,
      returned: false,
      returnDate: null,
      refundAmount: 0,
    });
  });

  it("handles quoted CSV fields", () => {
    expect(parseCsv('a,b\r\n"x, y","say ""hi"""\n')).toEqual([
      ["a", "b"],
      ["x, y", 'say "hi"'],
    ]);
  });
});

describe("queryStoreData", () => {
  it("computes overall totals", () => {
    const result = run({
      metrics: ["orders", "line_items", "units_sold", "customers", "gross_sales", "discounts", "net_sales", "refunds", "net_revenue"],
    });
    expect(result.rows).toHaveLength(1);
    expect(result.totals).toEqual({
      orders: 20,
      line_items: 28,
      units_sold: 33,
      customers: 18,
      gross_sales: 3216,
      discounts: 117.65,
      net_sales: 3098.35,
      refunds: 1116.94,
      net_revenue: 1981.41,
    });
    expect(result.warnings).toEqual([]);
  });

  it("answers: how many customers returned products, and why", () => {
    const result = run({
      metrics: ["customers_with_returns", "returns", "refunds"],
      groupBy: ["return_reason"],
      filters: { returned: true },
    });
    expect(result.totals.customers_with_returns).toBe(8);
    expect(result.rows).toEqual([
      { return_reason: "Changed mind", customers_with_returns: 2, returns: 2, refunds: 202.79 },
      { return_reason: "Too large", customers_with_returns: 2, returns: 2, refunds: 247 },
      { return_reason: "Too small", customers_with_returns: 2, returns: 2, refunds: 354.15 },
      { return_reason: "Defective", customers_with_returns: 1, returns: 1, refunds: 219 },
      { return_reason: "Not as pictured", customers_with_returns: 1, returns: 1, refunds: 94 },
    ]);
  });

  it("answers: top-selling products (with limit)", () => {
    const result = run({ metrics: ["net_sales", "units_sold"], groupBy: ["product"], limit: 3 });
    expect(result.rows).toEqual([
      { product: "Alpine Down Parka", net_sales: 854.1, units_sold: 4 },
      { product: "Northridge Insulated Jacket", net_sales: 596.25, units_sold: 4 },
      { product: "Selvedge Slim Jeans", net_sales: 436.6, units_sold: 4 },
    ]);
    expect(result.totalRows).toBe(11);
    expect(result.truncated).toBe(true);
    expect(result.totals.net_sales).toBe(3098.35); // totals ignore the limit
  });

  it("answers: what repeat customers buy on repeat purchases", () => {
    const result = run({
      metrics: ["net_sales"],
      groupBy: ["product"],
      filters: { customerType: "repeat" },
      sortBy: "units_sold",
      limit: 3,
    });
    expect(result.query.metrics).toEqual(["net_sales", "units_sold"]); // sort metric is added
    expect(result.rows).toEqual([
      { product: "Northridge Insulated Jacket", net_sales: 437.25, units_sold: 3 },
      { product: "Selvedge Slim Jeans", net_sales: 318.6, units_sold: 3 },
      { product: "Wool Beanie", net_sales: 72, units_sold: 3 },
    ]);
  });

  it("answers: average sale per customer and per order", () => {
    const result = run({ metrics: ["sales_per_customer", "average_order_value"] });
    expect(result.totals).toEqual({ sales_per_customer: 172.13, average_order_value: 154.92 });
  });

  it("answers: which sales channel is used the most", () => {
    const result = run({ metrics: ["orders", "net_sales"], groupBy: ["sales_channel"] });
    expect(result.rows).toEqual([
      { sales_channel: "Online Store", orders: 11, net_sales: 1882.2 },
      { sales_channel: "Point of Sale", orders: 4, net_sales: 408 },
      { sales_channel: "Shop app", orders: 3, net_sales: 501.15 },
      { sales_channel: "Instagram", orders: 2, net_sales: 307 },
    ]);
  });

  it("answers: sales last week and last month", () => {
    const lastWeek = queryStoreData({ startDate: "2025-10-20", endDate: "2025-10-26", metrics: ["orders", "net_sales", "units_sold"] });
    expect(lastWeek.totals).toEqual({ orders: 4, net_sales: 543.5, units_sold: 7 });

    const lastMonth = queryStoreData({ startDate: "2025-09-01", endDate: "2025-09-30", metrics: ["orders", "net_sales"] });
    expect(lastMonth.totals).toEqual({ orders: 2, net_sales: 231.1 });
  });

  it("returns time series in chronological order", () => {
    const result = run({ metrics: ["net_sales", "orders"], groupBy: ["month"] });
    expect(result.rows).toEqual([
      { month: "2025-05", net_sales: 224, orders: 2 },
      { month: "2025-06", net_sales: 162, orders: 1 },
      { month: "2025-07", net_sales: 118, orders: 1 },
      { month: "2025-08", net_sales: 102, orders: 1 },
      { month: "2025-09", net_sales: 231.1, orders: 2 },
      { month: "2025-10", net_sales: 2261.25, orders: 13 },
    ]);
    expect(result.columns.map((column) => [column.key, column.role, column.format])).toEqual([
      ["month", "dimension", "date"],
      ["net_sales", "metric", "currency"],
      ["orders", "metric", "count"],
    ]);
  });

  it("fills empty time buckets with zeros and undefined ratios with null", () => {
    const result = queryStoreData({
      startDate: "2025-10-20",
      endDate: "2025-10-26",
      metrics: ["orders", "average_order_value"],
      groupBy: ["day"],
    });
    expect(result.rows.map((row) => row.day)).toEqual([
      "2025-10-20", "2025-10-21", "2025-10-22", "2025-10-23", "2025-10-24", "2025-10-25", "2025-10-26",
    ]);
    expect(result.rows[0]).toEqual({ day: "2025-10-20", orders: 0, average_order_value: null });
    expect(result.rows[1]).toEqual({ day: "2025-10-21", orders: 1, average_order_value: 159 });
  });

  it("filters and buckets by return date", () => {
    const result = run({ metrics: ["returns", "refunds"], groupBy: ["month"], dateField: "return_date" });
    expect(result.period.dataAvailable).toEqual({ startDate: "2025-07-08", endDate: "2025-10-27" });
    expect(result.rows).toEqual([
      { month: "2025-07", returns: 1, refunds: 94 },
      { month: "2025-08", returns: 0, refunds: 0 },
      { month: "2025-09", returns: 1, refunds: 28 },
      { month: "2025-10", returns: 6, refunds: 994.94 },
    ]);
  });

  it("computes return rate as a percentage", () => {
    const result = run({ metrics: ["return_rate"], groupBy: ["category"], sortBy: "return_rate", limit: 1 });
    // Outerwear: 6 of 10 units returned.
    expect(result.rows).toEqual([{ category: "Outerwear", return_rate: 60 }]);
  });

  it("matches products by partial title, case-insensitively", () => {
    const result = run({ metrics: ["units_sold"], filters: { products: ["parka"] } });
    expect(result.totals.units_sold).toBe(4);
  });

  it("warns about unknown filter values and periods outside the data", () => {
    const unknown = run({ metrics: ["orders"], filters: { salesChannels: ["TikTok"] } });
    expect(unknown.totals.orders).toBe(0);
    expect(unknown.warnings.join(" ")).toMatch(/Unknown sales channel value\(s\): TikTok/);

    const future = queryStoreData({ startDate: "2026-11-01", endDate: "2026-11-30", metrics: ["orders"] });
    expect(future.totals.orders).toBe(0);
    expect(future.warnings[0]).toMatch(/only available from 2025-05-06 to 2025-10-27/);
  });

  it("rejects invalid queries", () => {
    expect(() => queryStoreData({ startDate: "2025-10-31", endDate: "2025-10-01", metrics: ["orders"] })).toThrow(/startDate/);
    expect(() => queryStoreData({ startDate: "2025-02-30", endDate: "2025-10-01", metrics: ["orders"] })).toThrow();
    expect(() => queryStoreData({ ...ALL_TIME, metrics: [] })).toThrow();
  });

  it("runs every example query cleanly", () => {
    for (const { question, query } of EXAMPLE_QUERIES) {
      expect(storeQuerySchema.safeParse(query).success, question).toBe(true);
      const result = queryStoreData(query);
      expect(result.rows.length, question).toBeGreaterThan(0);
      expect(result.warnings, question).toEqual([]);
    }
  });
});

describe("describeDataset", () => {
  it("summarises coverage and valid values", () => {
    const dataset = describeDataset();
    expect(dataset.latestDataDate).toBe("2025-10-27");
    expect(dataset.orderDates).toEqual({ startDate: "2025-05-06", endDate: "2025-10-27" });
    expect(dataset.counts).toEqual({ orders: 20, lineItems: 28, customers: 18, products: 11 });
    expect(dataset.salesChannels).toEqual(["Instagram", "Online Store", "Point of Sale", "Shop app"]);
    expect(dataset.returnReasons).toEqual(["Changed mind", "Defective", "Not as pictured", "Too large", "Too small"]);
  });
});

describe("date helpers", () => {
  it("buckets weeks from Monday and spans months", () => {
    expect(startOfWeek("2025-10-26")).toBe("2025-10-20"); // Sunday → Monday
    expect(startOfWeek("2025-10-27")).toBe("2025-10-27"); // Monday
    expect(bucketsBetween("2025-11-15", "2026-02-01", "month")).toEqual(["2025-11", "2025-12", "2026-01", "2026-02"]);
  });
});
