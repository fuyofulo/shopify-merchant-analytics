import type { OrderLineItem } from "@/lib/store-data";

/** How a metric's value should be read and displayed. Percentages are 0–100. */
export type MetricFormat = "count" | "currency" | "percent" | "decimal";

export interface MetricDefinition {
  label: string;
  description: string;
  format: MetricFormat;
  /** Computes the metric over a set of line items; `null` when undefined (e.g. divide by zero). */
  compute: (items: readonly OrderLineItem[]) => number | null;
}

export const METRIC_KEYS = [
  "net_sales",
  "gross_sales",
  "discounts",
  "refunds",
  "net_revenue",
  "orders",
  "line_items",
  "units_sold",
  "customers",
  "average_order_value",
  "sales_per_customer",
  "units_per_order",
  "returns",
  "returned_units",
  "customers_with_returns",
  "return_rate",
  "discount_rate",
  "repeat_orders",
  "repeat_customers",
  "repeat_order_share",
] as const;

export type MetricKey = (typeof METRIC_KEYS)[number];

// Money is summed in integer cents so totals are exact.
const cents = (amount: number) => Math.round(amount * 100);
const sumMoney = (items: readonly OrderLineItem[], amount: (item: OrderLineItem) => number) =>
  items.reduce((total, item) => total + amount(item), 0) / 100;
const sum = (items: readonly OrderLineItem[], value: (item: OrderLineItem) => number) =>
  items.reduce((total, item) => total + value(item), 0);
const countDistinct = (items: readonly OrderLineItem[], key: (item: OrderLineItem) => string) =>
  new Set(items.map(key)).size;
const ratio = (numerator: number, denominator: number) => (denominator === 0 ? null : numerator / denominator);

const grossSales = (items: readonly OrderLineItem[]) =>
  sumMoney(items, (item) => item.quantity * cents(item.unitPrice));
const discounts = (items: readonly OrderLineItem[]) => sumMoney(items, (item) => cents(item.discountAmount));
const netSales = (items: readonly OrderLineItem[]) => sumMoney(items, (item) => cents(item.lineTotal));
const refunds = (items: readonly OrderLineItem[]) => sumMoney(items, (item) => cents(item.refundAmount));
const orders = (items: readonly OrderLineItem[]) => countDistinct(items, (item) => item.orderId);
const customers = (items: readonly OrderLineItem[]) => countDistinct(items, (item) => item.customerId);
const unitsSold = (items: readonly OrderLineItem[]) => sum(items, (item) => item.quantity);
const returnedItems = (items: readonly OrderLineItem[]) => items.filter((item) => item.returned);
const repeatItems = (items: readonly OrderLineItem[]) => items.filter((item) => item.isRepeatCustomer);

export const METRICS: Record<MetricKey, MetricDefinition> = {
  net_sales: {
    label: "Net sales",
    description: "Sales after discounts, before refunds (sum of line totals). The default meaning of 'sales' or 'revenue'.",
    format: "currency",
    compute: netSales,
  },
  gross_sales: {
    label: "Gross sales",
    description: "Sales before discounts (quantity × unit price).",
    format: "currency",
    compute: grossSales,
  },
  discounts: {
    label: "Discounts",
    description: "Total discount amount given.",
    format: "currency",
    compute: discounts,
  },
  refunds: {
    label: "Refunds",
    description: "Total amount refunded on returned items.",
    format: "currency",
    compute: refunds,
  },
  net_revenue: {
    label: "Net revenue",
    description: "Net sales minus refunds: what the store kept.",
    format: "currency",
    compute: (items) => (Math.round(netSales(items) * 100) - Math.round(refunds(items) * 100)) / 100,
  },
  orders: {
    label: "Orders",
    description: "Number of distinct orders. When grouped by product/category, the orders that contain it.",
    format: "count",
    compute: orders,
  },
  line_items: {
    label: "Line items",
    description: "Number of order line items (one per product/variant per order).",
    format: "count",
    compute: (items) => items.length,
  },
  units_sold: {
    label: "Units sold",
    description: "Total quantity of items sold.",
    format: "count",
    compute: unitsSold,
  },
  customers: {
    label: "Customers",
    description: "Number of distinct customers who ordered.",
    format: "count",
    compute: customers,
  },
  average_order_value: {
    label: "Average order value",
    description: "Net sales divided by number of orders.",
    format: "currency",
    compute: (items) => ratio(netSales(items), orders(items)),
  },
  sales_per_customer: {
    label: "Sales per customer",
    description: "Net sales divided by number of distinct customers (average spend per customer).",
    format: "currency",
    compute: (items) => ratio(netSales(items), customers(items)),
  },
  units_per_order: {
    label: "Units per order",
    description: "Units sold divided by number of orders (average basket size).",
    format: "decimal",
    compute: (items) => ratio(unitsSold(items), orders(items)),
  },
  returns: {
    label: "Returns",
    description: "Number of returned line items.",
    format: "count",
    compute: (items) => returnedItems(items).length,
  },
  returned_units: {
    label: "Returned units",
    description: "Total quantity of items returned.",
    format: "count",
    compute: (items) => unitsSold(returnedItems(items)),
  },
  customers_with_returns: {
    label: "Customers with returns",
    description: "Number of distinct customers who returned at least one item.",
    format: "count",
    compute: (items) => customers(returnedItems(items)),
  },
  return_rate: {
    label: "Return rate",
    description: "Returned units as a percentage (0–100) of units sold.",
    format: "percent",
    compute: (items) => {
      const rate = ratio(unitsSold(returnedItems(items)), unitsSold(items));
      return rate === null ? null : rate * 100;
    },
  },
  discount_rate: {
    label: "Discount rate",
    description: "Discounts as a percentage (0–100) of gross sales.",
    format: "percent",
    compute: (items) => {
      const rate = ratio(discounts(items), grossSales(items));
      return rate === null ? null : rate * 100;
    },
  },
  repeat_orders: {
    label: "Repeat orders",
    description: "Orders placed by customers who had ordered before (2nd order or later).",
    format: "count",
    compute: (items) => orders(repeatItems(items)),
  },
  repeat_customers: {
    label: "Repeat customers",
    description: "Distinct customers who came back and placed a repeat order.",
    format: "count",
    compute: (items) => customers(repeatItems(items)),
  },
  repeat_order_share: {
    label: "Repeat order share",
    description: "Repeat orders as a percentage (0–100) of all orders.",
    format: "percent",
    compute: (items) => {
      const share = ratio(orders(repeatItems(items)), orders(items));
      return share === null ? null : share * 100;
    },
  },
};

/** Rounds a computed value for output: counts to integers, everything else to 2 decimals. */
export function roundMetric(value: number | null, format: MetricFormat): number | null {
  if (value === null) return null;
  if (format === "count") return Math.round(value);
  return Math.round((value + Number.EPSILON) * 100) / 100;
}
