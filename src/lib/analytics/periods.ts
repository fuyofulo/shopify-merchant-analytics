import { addDays, startOfWeek } from "./dates";

/** A time phrase a merchant might use, resolved to exact inclusive dates. */
export interface NamedPeriod {
  phrases: string[];
  startDate: string;
  endDate: string;
}

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export function weekdayOf(isoDate: string): string {
  return WEEKDAYS[new Date(`${isoDate}T00:00:00Z`).getUTCDay()];
}

const firstOfMonth = (isoDate: string) => `${isoDate.slice(0, 7)}-01`;

/** First day of the meteorological season (Mar/Jun/Sep/Dec) that contains `isoDate`. */
function seasonStart(isoDate: string): string {
  const year = Number(isoDate.slice(0, 4));
  const month = Number(isoDate.slice(5, 7));
  const startMonth = [12, 12, 3, 3, 3, 6, 6, 6, 9, 9, 9, 12][month - 1];
  const startYear = startMonth === 12 && month !== 12 ? year - 1 : year;
  return `${startYear}-${String(startMonth).padStart(2, "0")}-01`;
}

/** The most recent Labor Day (first Monday of September) on or before `isoDate`. */
function laborDay(isoDate: string): string {
  const firstMonday = (year: number) => {
    const sept1 = `${year}-09-01`;
    const weekday = new Date(`${sept1}T00:00:00Z`).getUTCDay(); // 0 = Sunday
    return addDays(sept1, (8 - weekday) % 7);
  };
  const year = Number(isoDate.slice(0, 4));
  return isoDate >= firstMonday(year) ? firstMonday(year) : firstMonday(year - 1);
}

/** The most recent June 1st on or before `isoDate`. */
function summerStart(isoDate: string): string {
  const year = Number(isoDate.slice(0, 4));
  const thisYear = `${year}-06-01`;
  return isoDate >= thisYear ? thisYear : `${year - 1}-06-01`;
}

/**
 * Resolves the time phrases merchants actually type (taken from the merchant
 * report requests) to exact dates, relative to `today`. Weeks run Monday to
 * Sunday. Rolling periods ("last 30 days", "since Labor Day") are full days
 * ending yesterday; "this week / month / season / year" run to today. This
 * matches the date ranges in the acceptance questions.
 *
 * These go into the system prompt so the model copies dates instead of
 * calculating them.
 */
export function resolvePeriods(today: string, firstDataDate: string): NamedPeriod[] {
  const thisWeekStart = startOfWeek(today);
  const lastSunday = addDays(thisWeekStart, -1);
  const thisMonthStart = firstOfMonth(today);
  const lastMonthEnd = addDays(thisMonthStart, -1);
  const yesterday = addDays(today, -1);

  return [
    { phrases: ["today"], startDate: today, endDate: today },
    { phrases: ["yesterday"], startDate: yesterday, endDate: yesterday },
    { phrases: ["this week"], startDate: thisWeekStart, endDate: today },
    { phrases: ["last week", "last wk", "through last Sunday"], startDate: addDays(thisWeekStart, -7), endDate: lastSunday },
    { phrases: ["last 7 days", "past week"], startDate: addDays(today, -7), endDate: yesterday },
    { phrases: ["last 14 days", "last 2 weeks", "last couple of weeks"], startDate: addDays(today, -14), endDate: yesterday },
    { phrases: ["last 30 days", "lately", "recently"], startDate: addDays(today, -30), endDate: yesterday },
    { phrases: ["last 8 weeks (full Monday–Sunday weeks)"], startDate: addDays(thisWeekStart, -56), endDate: lastSunday },
    { phrases: ["this month", "month to date"], startDate: thisMonthStart, endDate: today },
    { phrases: ["last month"], startDate: firstOfMonth(lastMonthEnd), endDate: lastMonthEnd },
    { phrases: ["this season"], startDate: seasonStart(today), endDate: today },
    { phrases: ["since summer"], startDate: summerStart(today), endDate: yesterday },
    { phrases: ["since Labor Day"], startDate: laborDay(today), endDate: yesterday },
    { phrases: ["this year", "year to date"], startDate: `${today.slice(0, 4)}-01-01`, endDate: today },
    { phrases: ["all time", "no period mentioned"], startDate: firstDataDate, endDate: today },
  ];
}
