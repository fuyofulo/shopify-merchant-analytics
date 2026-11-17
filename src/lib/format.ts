/** Display formatting shared by the chat page and charts. Safe to import on the client. */

import type { ResultColumn, ResultValue } from "@/lib/analytics";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_LONG = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const parts = (isoDate: string) => {
  const [year, month, day] = isoDate.split("-").map(Number);
  return { year, month, day };
};

/** "Oct 27, 2025" · "Oct 20–26, 2025" · "Jun 1 – Oct 27, 2025" · "Nov 29, 2024 – Dec 1, 2024" */
export function formatRange(startDate: string, endDate: string): string {
  const a = parts(startDate);
  const b = parts(endDate);
  if (startDate === endDate) return `${MONTHS[a.month - 1]} ${a.day}, ${a.year}`;
  if (a.year === b.year && a.month === b.month) return `${MONTHS[a.month - 1]} ${a.day}–${b.day}, ${a.year}`;
  if (a.year === b.year) return `${MONTHS[a.month - 1]} ${a.day} – ${MONTHS[b.month - 1]} ${b.day}, ${b.year}`;
  return `${MONTHS[a.month - 1]} ${a.day}, ${a.year} – ${MONTHS[b.month - 1]} ${b.day}, ${b.year}`;
}

/** Short label for an axis tick: day/week "Oct 20", month "Oct". */
export function formatDateTick(key: string, value: string): string {
  if (key === "month") return MONTHS[parts(`${value}-01`).month - 1];
  const { month, day } = parts(value);
  return `${MONTHS[month - 1]} ${day}`;
}

/** Full label for a tooltip or table cell. */
export function formatDateLabel(key: string, value: string): string {
  if (key === "month") {
    const { year, month } = parts(`${value}-01`);
    return `${MONTHS_LONG[month - 1]} ${year}`;
  }
  const { year, month, day } = parts(value);
  const date = `${MONTHS[month - 1]} ${day}, ${year}`;
  return key === "week" ? `Week of ${date}` : date;
}

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const wholeCurrency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const compactCurrency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});
const integer = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const decimal = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

/** A value in full: "$1,234.56", "38.46%", "1,284", "1.65". Missing values are an em dash. */
export function formatValue(value: ResultValue | undefined, format: ResultColumn["format"], key = ""): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return format === "date" ? formatDateLabel(key, value) : value;
  switch (format) {
    case "currency":
      return currency.format(value);
    case "percent":
      return `${decimal.format(value)}%`;
    case "count":
      return integer.format(value);
    default:
      return decimal.format(value);
  }
}

/** A value on an axis: whole numbers, compact from 10,000 up ("$2,000", "$12.5K", "40%"). */
export function formatAxisValue(value: number, format: ResultColumn["format"]): string {
  if (format === "currency") return Math.abs(value) >= 10_000 ? compactCurrency.format(value) : wholeCurrency.format(value);
  if (format === "percent") return `${integer.format(value)}%`;
  return Math.abs(value) >= 10_000 ? compactCurrency.format(value).replace("$", "") : decimal.format(value);
}
