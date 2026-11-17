import type { InferUITools, UIDataTypes, UIMessage } from "ai";

import type { ChartSpec, ResultColumn, ResultRow } from "@/lib/analytics";

import type { MerchantTools } from "./tools";

/** Chat messages as the client sees them, with typed tool parts (`tool-salesReport`, …). */
export type MerchantUIMessage = UIMessage<unknown, UIDataTypes, InferUITools<MerchantTools>>;

/** The part of a report tool's output the chat page needs to draw it. */
export interface ReportOutput {
  /** Set for row-by-row lists (returned items). */
  view?: "list";
  period: { startDate: string; endDate: string; dateField: "order_date" | "return_date" };
  columns: ResultColumn[];
  rows: ResultRow[];
  totals: Partial<Record<string, number | null>>;
  matchedLineItems: number;
  totalRows: number;
  truncated: boolean;
  warnings: string[];
  chart: ChartSpec;
}

export function isReportOutput(output: unknown): output is ReportOutput {
  return typeof output === "object" && output !== null && "chart" in output && "rows" in output;
}
