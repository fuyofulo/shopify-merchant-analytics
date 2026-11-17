/**
 * Turns the streamed tool call into the plain-English steps the merchant sees
 * while waiting ("Choosing a report…", "Running the returns report for Oct
 * 20–26, 2025: returned units by product, Outerwear only", "Got results for 2
 * products"). Pure functions, safe on the client.
 */

import { DIMENSIONS, type DimensionKey } from "@/lib/analytics/dimensions";
import { METRICS, type MetricKey } from "@/lib/analytics/metrics";
import { formatRange } from "@/lib/format";

import { isReportOutput } from "./ui-types";

export type StepStatus = "active" | "done" | "error";

export interface Step {
  id: "choose" | "run" | "result";
  label: string;
  status: StepStatus;
  /** The in-progress wording ("Running …") shown while this step is the newest one on screen. */
  activeLabel?: string;
}

/** The fields of a streamed tool part the steps depend on. */
export interface ToolPartLike {
  type: string;
  state: string;
  input?: unknown;
  output?: unknown;
  errorText?: string;
}

const REPORT_NAMES: Record<string, string> = {
  salesReport: "sales report",
  returnsReport: "returns report",
  repeatCustomersReport: "repeat customers report",
};

/** [singular, plural] for "Got results for 1 product" / "… 2 products". */
const NOUNS: Partial<Record<DimensionKey, [string, string]>> = {
  day: ["day", "days"],
  week: ["week", "weeks"],
  month: ["month", "months"],
  product: ["product", "products"],
  category: ["category", "categories"],
  variant: ["variant", "variants"],
  size: ["size", "sizes"],
  color: ["colour", "colours"],
  sales_channel: ["sales channel", "sales channels"],
  customer_type: ["customer type", "customer types"],
  customer: ["customer", "customers"],
  fulfillment_status: ["fulfillment status", "fulfillment statuses"],
  return_reason: ["return reason", "return reasons"],
  order: ["order", "orders"],
};

interface ReportInputLike {
  startDate?: string;
  endDate?: string;
  metrics?: string[];
  groupBy?: string[];
  filters?: Record<string, unknown>;
  limit?: number;
  view?: string;
  missingData?: string;
}

const toolNameOf = (part: ToolPartLike) => part.type.replace(/^tool-/, "");

const joinWords = (words: string[]) =>
  words.length <= 1 ? (words[0] ?? "") : `${words.slice(0, -1).join(", ")} and ${words[words.length - 1]}`;

const metricLabel = (key: string) => (key in METRICS ? METRICS[key as MetricKey].label.toLowerCase() : key);
const dimensionLabel = (key: string) => (key in DIMENSIONS ? DIMENSIONS[key as DimensionKey].label.toLowerCase() : key);

/** "returned units and refunds by product, Outerwear only, top 5" */
export function describeQuery(input: ReportInputLike): string {
  const what =
    input.view === "list"
      ? "a list of returned items"
      : `${joinWords((input.metrics ?? []).map(metricLabel))}${
          input.groupBy?.length ? ` by ${joinWords(input.groupBy.map(dimensionLabel))}` : ""
        }`;

  const filters = input.filters ?? {};
  const only: string[] = [];
  for (const key of ["categories", "products", "salesChannels", "sizes", "colors", "returnReasons", "fulfillmentStatuses"]) {
    const values = filters[key];
    if (Array.isArray(values) && values.length > 0) only.push(values.join(" or "));
  }
  if (filters.customerType === "repeat") only.push("repeat customers");
  if (filters.customerType === "new") only.push("new customers");
  if (filters.returned === true) only.push("returned items");

  const isTimeSeries = input.groupBy?.[0] !== undefined && ["day", "week", "month"].includes(input.groupBy[0]);
  return [what, only.length ? `${only.join(", ")} only` : "", input.limit && !isTimeSeries ? `top ${input.limit}` : ""]
    .filter(Boolean)
    .join(", ");
}

function describeResult(input: ReportInputLike, output: unknown): string {
  if (!isReportOutput(output)) return "Got the result";
  if (input.view === "list") {
    const count = output.totalRows;
    return count === 0 ? "No returned items in these dates" : `Found ${count} returned item${count === 1 ? "" : "s"}`;
  }
  if (output.matchedLineItems === 0) return "No matching data for these dates";
  const [dimension] = (output.columns ?? []).filter((column) => column.role === "dimension");
  if (!dimension) return "Got the totals";
  if (output.chart.type === "table") return `Got ${output.totalRows} rows`;
  const [singular, plural] = NOUNS[dimension.key as DimensionKey] ?? ["row", "rows"];
  const noun = output.totalRows === 1 ? singular : plural;
  return ["day", "week", "month"].includes(dimension.key)
    ? `Got ${output.totalRows} ${noun} of results`
    : `Got results for ${output.totalRows} ${noun}`;
}

/**
 * The steps for one answer, from the streamed tool part (or none yet).
 * `failed` marks the current step as failed when the request itself errored.
 */
export function stepsFor(part: ToolPartLike | undefined, failed = false): Step[] {
  if (!part) {
    return [{ id: "choose", label: failed ? "Couldn't reach the AI model" : "Choosing a report…", status: failed ? "error" : "active" }];
  }

  const toolName = toolNameOf(part);
  const input = (part.input ?? {}) as ReportInputLike;

  if (toolName === "cannotAnswer") {
    const steps: Step[] = [{ id: "choose", label: "Checked what the store data covers", status: "done" }];
    if (part.state === "output-available") {
      steps.push({ id: "result", label: `Not in the store data: ${input.missingData ?? "this question"}`, status: "done" });
    }
    return steps;
  }

  const report = REPORT_NAMES[toolName] ?? "report";
  const choose: Step = { id: "choose", label: `Chose the ${report}`, status: "done", activeLabel: "Choosing a report…" };

  if (part.state === "input-streaming") {
    return [choose, { id: "run", label: `Setting up the ${report}…`, status: failed ? "error" : "active" }];
  }

  const range = input.startDate && input.endDate ? ` for ${formatRange(input.startDate, input.endDate)}` : "";
  const query = describeQuery(input);
  const target = `the ${report}${range}${query ? `: ${query}` : ""}`;

  const toolError =
    part.state === "output-error"
      ? part.errorText
      : typeof part.output === "object" && part.output !== null && "error" in part.output
        ? String((part.output as { error: unknown }).error)
        : undefined;
  if (toolError !== undefined) {
    return [choose, { id: "run", label: `Couldn't run ${target}`, status: "error" }];
  }

  if (part.state === "output-available") {
    return [
      choose,
      { id: "run", label: `Ran ${target}`, status: "done", activeLabel: `Running ${target}…` },
      { id: "result", label: describeResult(input, part.output), status: "done" },
    ];
  }

  return [choose, { id: "run", label: `Running ${target}…`, status: failed ? "error" : "active" }];
}
