import type { OrderLineItem } from "@/lib/store-data";

import type { StoreQueryFilters } from "./schema";

const normalize = (value: string) => value.trim().toLowerCase();

type ListFilter = Exclude<keyof StoreQueryFilters, "products" | "customerType" | "returned">;

/** List filters that match one field exactly (case-insensitive). */
const EXACT_MATCH_FILTERS: Record<ListFilter, { label: string; field: (item: OrderLineItem) => string | null }> = {
  categories: { label: "category", field: (item) => item.productCategory },
  salesChannels: { label: "sales channel", field: (item) => item.salesChannel },
  customerIds: { label: "customer ID", field: (item) => item.customerId },
  orderIds: { label: "order ID", field: (item) => item.orderId },
  sizes: { label: "size", field: (item) => item.size },
  colors: { label: "colour", field: (item) => item.color },
  fulfillmentStatuses: { label: "fulfillment status", field: (item) => item.fulfillmentStatus },
  returnReasons: { label: "return reason", field: (item) => item.returnReason },
};

const matchesProduct = (item: OrderLineItem, term: string) =>
  normalize(item.productId) === normalize(term) || normalize(item.productTitle).includes(normalize(term));

/**
 * Applies the query filters. Also returns a warning for every filter value that
 * matches nothing in the whole dataset, so the caller (or LLM) can correct it.
 */
export function applyFilters(
  items: readonly OrderLineItem[],
  filters: StoreQueryFilters,
  dataset: readonly OrderLineItem[],
): { items: OrderLineItem[]; warnings: string[] } {
  const warnings: string[] = [];
  const predicates: ((item: OrderLineItem) => boolean)[] = [];

  if (filters.products?.length) {
    const terms = filters.products;
    for (const term of terms) {
      if (!dataset.some((item) => matchesProduct(item, term))) {
        const known = [...new Set(dataset.map((item) => item.productTitle))].sort();
        warnings.push(`No product matches "${term}". Known products: ${known.join(", ")}.`);
      }
    }
    predicates.push((item) => terms.some((term) => matchesProduct(item, term)));
  }

  for (const [key, { label, field }] of Object.entries(EXACT_MATCH_FILTERS) as [
    ListFilter,
    (typeof EXACT_MATCH_FILTERS)[ListFilter],
  ][]) {
    const wanted = filters[key];
    if (!wanted?.length) continue;

    const known = new Set(dataset.map(field).filter((value): value is string => value !== null && value !== ""));
    const knownNormalized = new Set([...known].map(normalize));
    const unknown = wanted.filter((value) => !knownNormalized.has(normalize(value)));
    if (unknown.length > 0) {
      warnings.push(`Unknown ${label} value(s): ${unknown.join(", ")}. Known values: ${[...known].sort().join(", ")}.`);
    }

    const wantedNormalized = new Set(wanted.map(normalize));
    predicates.push((item) => {
      const value = field(item);
      return value !== null && wantedNormalized.has(normalize(value));
    });
  }

  if (filters.customerType) {
    const repeat = filters.customerType === "repeat";
    predicates.push((item) => item.isRepeatCustomer === repeat);
  }

  if (filters.returned !== undefined) {
    const returned = filters.returned;
    predicates.push((item) => item.returned === returned);
  }

  return { items: items.filter((item) => predicates.every((matches) => matches(item))), warnings };
}
