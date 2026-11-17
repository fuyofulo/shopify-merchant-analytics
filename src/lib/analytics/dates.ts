/** Date helpers. All dates are calendar dates (`YYYY-MM-DD`) handled in UTC. */

export type TimeGrain = "day" | "week" | "month";

const toUtc = (isoDate: string) => new Date(`${isoDate}T00:00:00Z`);
const toIso = (date: Date) => date.toISOString().slice(0, 10);

export function addDays(isoDate: string, days: number): string {
  const date = toUtc(isoDate);
  date.setUTCDate(date.getUTCDate() + days);
  return toIso(date);
}

/** Monday of the ISO week that contains `isoDate`. */
export function startOfWeek(isoDate: string): string {
  const daysSinceMonday = (toUtc(isoDate).getUTCDay() + 6) % 7;
  return addDays(isoDate, -daysSinceMonday);
}

/**
 * The bucket a date falls into. Bucket labels sort chronologically as strings:
 * day → `2025-10-06`, week → Monday's date `2025-10-06`, month → `2025-10`.
 */
export function bucketOf(isoDate: string, grain: TimeGrain): string {
  if (grain === "day") return isoDate;
  if (grain === "week") return startOfWeek(isoDate);
  return isoDate.slice(0, 7);
}

/** Every bucket label between two dates (inclusive), in chronological order. */
export function bucketsBetween(startDate: string, endDate: string, grain: TimeGrain): string[] {
  const buckets: string[] = [];
  const last = bucketOf(endDate, grain);

  if (grain === "month") {
    let [year, month] = startDate.split("-").map(Number);
    for (;;) {
      const label = `${year}-${String(month).padStart(2, "0")}`;
      buckets.push(label);
      if (label >= last) break;
      month = month === 12 ? 1 : month + 1;
      if (month === 1) year++;
    }
    return buckets;
  }

  const step = grain === "week" ? 7 : 1;
  for (let date = bucketOf(startDate, grain); date <= last; date = addDays(date, step)) {
    buckets.push(date);
  }
  return buckets;
}
