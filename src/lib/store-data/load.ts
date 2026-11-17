import { readFileSync } from "node:fs";
import path from "node:path";

import { parseOrderLineItems } from "./parse";
import type { OrderLineItem } from "./types";

/** Location of the order export, relative to the project root. */
export const ORDERS_CSV_PATH = path.join(process.cwd(), "data", "orders.csv");

let cache: readonly OrderLineItem[] | undefined;

/**
 * Loads and parses `data/orders.csv` once per server process.
 * Server-only: it reads from the filesystem.
 */
export function loadOrderLineItems(): readonly OrderLineItem[] {
  cache ??= Object.freeze(parseOrderLineItems(readFileSync(ORDERS_CSV_PATH, "utf8")));
  return cache;
}
