import type { OrderLineItem } from "@/lib/store-data";

import { bucketOf, type TimeGrain } from "./dates";

/** Which date a query filters and buckets on. */
export type DateField = "order_date" | "return_date";

export interface DimensionDefinition {
  label: string;
  description: string;
  /** Set for time dimensions; their values sort chronologically. */
  timeGrain?: TimeGrain;
  value: (item: OrderLineItem, dateField: DateField) => string;
}

export const DIMENSION_KEYS = [
  "day",
  "week",
  "month",
  "product",
  "category",
  "variant",
  "size",
  "color",
  "sales_channel",
  "customer_type",
  "customer",
  "fulfillment_status",
  "return_reason",
  "order",
] as const;

export type DimensionKey = (typeof DIMENSION_KEYS)[number];

/** The date an item is bucketed by. Return dates are only set on returned items. */
export function dateOf(item: OrderLineItem, dateField: DateField): string | null {
  return dateField === "order_date" ? item.orderDate : item.returnDate;
}

const timeDimension = (grain: TimeGrain, label: string, description: string): DimensionDefinition => ({
  label,
  description,
  timeGrain: grain,
  value: (item, dateField) => bucketOf(dateOf(item, dateField) ?? item.orderDate, grain),
});

export const DIMENSIONS: Record<DimensionKey, DimensionDefinition> = {
  day: timeDimension("day", "Day", "Calendar day (YYYY-MM-DD)."),
  week: timeDimension("week", "Week", "Week starting Monday, labelled by the Monday's date (YYYY-MM-DD)."),
  month: timeDimension("month", "Month", "Calendar month (YYYY-MM)."),
  product: {
    label: "Product",
    description: "Product title.",
    value: (item) => item.productTitle,
  },
  category: {
    label: "Category",
    description: "Product category (e.g. Outerwear, Tops).",
    value: (item) => item.productCategory,
  },
  variant: {
    label: "Variant",
    description: "Full variant label, size / colour (e.g. 'M / Black').",
    value: (item) => item.variant,
  },
  size: {
    label: "Size",
    description: "Variant size (e.g. S, M, L, One Size).",
    value: (item) => item.size,
  },
  color: {
    label: "Colour",
    description: "Variant colour.",
    value: (item) => item.color || "Unspecified",
  },
  sales_channel: {
    label: "Sales channel",
    description: "Where the order was placed (e.g. Online Store, Shop app, Point of Sale, Instagram).",
    value: (item) => item.salesChannel,
  },
  customer_type: {
    label: "Customer type",
    description: "'new' for a customer's first order, 'repeat' for orders from returning customers.",
    value: (item) => (item.isRepeatCustomer ? "repeat" : "new"),
  },
  customer: {
    label: "Customer",
    description: "Customer ID.",
    value: (item) => item.customerId,
  },
  fulfillment_status: {
    label: "Fulfillment status",
    description: "fulfilled, partially_fulfilled or unfulfilled.",
    value: (item) => item.fulfillmentStatus,
  },
  return_reason: {
    label: "Return reason",
    description: "Why the item was returned; 'Not returned' for kept items.",
    value: (item) => (item.returned ? (item.returnReason ?? "Unspecified") : "Not returned"),
  },
  order: {
    label: "Order",
    description: "Order ID.",
    value: (item) => item.orderId,
  },
};
