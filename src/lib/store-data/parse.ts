import { parseCsv } from "./csv";
import type { OrderLineItem } from "./types";

/** Columns the order export must contain (extra columns are ignored). */
export const REQUIRED_COLUMNS = [
  "order_id",
  "line_item_id",
  "order_date",
  "customer_id",
  "is_repeat_customer",
  "product_id",
  "product_title",
  "product_category",
  "variant",
  "quantity",
  "unit_price",
  "discount_amount",
  "line_total",
  "sales_channel",
  "fulfillment_status",
  "returned",
  "return_date",
  "return_reason",
  "refund_amount",
] as const;

type Column = (typeof REQUIRED_COLUMNS)[number];

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

/** Parses the raw order-export CSV into typed, validated line items. */
export function parseOrderLineItems(csvText: string): OrderLineItem[] {
  const [header, ...records] = parseCsv(csvText.replace(/^﻿/, ""));
  if (!header) throw new Error("Order export is empty.");

  const index = new Map(header.map((name, i) => [name.trim(), i]));
  const missing = REQUIRED_COLUMNS.filter((column) => !index.has(column));
  if (missing.length > 0) {
    throw new Error(`Order export is missing columns: ${missing.join(", ")}`);
  }

  return records.map((record, i) => {
    const line = i + 2; // 1-based, after the header row
    const get = (column: Column) => (record[index.get(column)!] ?? "").trim();
    const fail = (column: Column, problem: string): never => {
      throw new Error(`Order export line ${line}, column "${column}": ${problem} (got "${get(column)}").`);
    };

    const text = (column: Column) => get(column) || fail(column, "value is required");
    const date = (column: Column) => (ISO_DATE.test(get(column)) ? get(column) : fail(column, "expected YYYY-MM-DD"));
    const optionalDate = (column: Column) => (get(column) === "" ? null : date(column));
    const number = (column: Column) => {
      const raw = get(column);
      const value = raw === "" ? 0 : Number(raw);
      return Number.isFinite(value) ? value : fail(column, "expected a number");
    };
    const boolean = (column: Column) => {
      const raw = get(column).toLowerCase();
      if (raw === "true") return true;
      if (raw === "false" || raw === "") return false;
      return fail(column, "expected true or false");
    };

    const variant = text("variant");
    const [size = variant, color = ""] = variant.split("/").map((part) => part.trim());
    const returned = boolean("returned");

    return {
      orderId: text("order_id"),
      lineItemId: text("line_item_id"),
      orderDate: date("order_date"),
      customerId: text("customer_id"),
      isRepeatCustomer: boolean("is_repeat_customer"),
      productId: text("product_id"),
      productTitle: text("product_title"),
      productCategory: text("product_category"),
      variant,
      size,
      color,
      quantity: number("quantity"),
      unitPrice: number("unit_price"),
      discountAmount: number("discount_amount"),
      lineTotal: number("line_total"),
      salesChannel: text("sales_channel"),
      fulfillmentStatus: text("fulfillment_status"),
      returned,
      returnDate: returned ? optionalDate("return_date") : null,
      returnReason: returned ? get("return_reason") || null : null,
      refundAmount: returned ? number("refund_amount") : 0,
    };
  });
}
