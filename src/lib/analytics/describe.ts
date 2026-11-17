import { loadOrderLineItems, type OrderLineItem } from "@/lib/store-data";

import { DIMENSION_KEYS, DIMENSIONS, type DimensionKey } from "./dimensions";
import { METRIC_KEYS, METRICS, type MetricFormat, type MetricKey } from "./metrics";
import { dateRangeOf, type DateRange } from "./query";

export interface DatasetDescription {
  grain: string;
  /** Latest date with any order or return. Use it as "today" for relative dates on historical data. */
  latestDataDate: string | null;
  orderDates: DateRange | null;
  returnDates: DateRange | null;
  counts: { orders: number; lineItems: number; customers: number; products: number };
  products: { id: string; title: string; category: string; unitPrice: number }[];
  categories: string[];
  salesChannels: string[];
  fulfillmentStatuses: string[];
  returnReasons: string[];
  sizes: string[];
  colors: string[];
  metrics: { key: MetricKey; label: string; description: string; format: MetricFormat }[];
  dimensions: { key: DimensionKey; label: string; description: string }[];
}

const distinctSorted = (values: (string | null)[]) =>
  [...new Set(values.filter((value): value is string => Boolean(value)))].sort();

/**
 * Summarises what the dataset contains — date coverage, products, channels,
 * return reasons — plus the metrics and dimensions `queryStoreData` supports.
 * Give this to the LLM (as a tool or in the system prompt) so it can map a
 * merchant's words to valid query values.
 */
export function describeDataset(dataset: readonly OrderLineItem[] = loadOrderLineItems()): DatasetDescription {
  const orderDates = dateRangeOf(dataset, "order_date");
  const returnDates = dateRangeOf(dataset, "return_date");
  const latestDataDate = [orderDates?.endDate, returnDates?.endDate].filter(Boolean).sort().at(-1) ?? null;

  const products = new Map<string, DatasetDescription["products"][number]>();
  for (const item of dataset) {
    if (!products.has(item.productId)) {
      products.set(item.productId, {
        id: item.productId,
        title: item.productTitle,
        category: item.productCategory,
        unitPrice: item.unitPrice,
      });
    }
  }

  return {
    grain: "One row per order line item (an order with two products has two rows).",
    latestDataDate,
    orderDates,
    returnDates,
    counts: {
      orders: new Set(dataset.map((item) => item.orderId)).size,
      lineItems: dataset.length,
      customers: new Set(dataset.map((item) => item.customerId)).size,
      products: products.size,
    },
    products: [...products.values()].sort((a, b) => a.id.localeCompare(b.id)),
    categories: distinctSorted(dataset.map((item) => item.productCategory)),
    salesChannels: distinctSorted(dataset.map((item) => item.salesChannel)),
    fulfillmentStatuses: distinctSorted(dataset.map((item) => item.fulfillmentStatus)),
    returnReasons: distinctSorted(dataset.map((item) => item.returnReason)),
    sizes: distinctSorted(dataset.map((item) => item.size)),
    colors: distinctSorted(dataset.map((item) => item.color)),
    metrics: METRIC_KEYS.map((key) => ({
      key,
      label: METRICS[key].label,
      description: METRICS[key].description,
      format: METRICS[key].format,
    })),
    dimensions: DIMENSION_KEYS.map((key) => ({
      key,
      label: DIMENSIONS[key].label,
      description: DIMENSIONS[key].description,
    })),
  };
}
