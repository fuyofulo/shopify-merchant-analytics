import { APICallError, RetryError } from "ai";
import { describe, expect, it } from "vitest";

import { chartFor, listReturnedItems, queryStoreData } from "@/lib/analytics";
import { merchantErrorMessage } from "@/lib/assistant/errors";
import { stepsFor } from "@/lib/assistant/steps";
import { createMerchantTools } from "@/lib/assistant/tools";
import { formatAxisValue, formatDateLabel, formatRange, formatValue } from "@/lib/format";

const execOptions = { toolCallId: "test", messages: [] } as never;
const returnsInput = {
  startDate: "2025-10-20",
  endDate: "2025-10-26",
  metrics: ["returned_units", "refunds"],
  groupBy: ["product"],
  filters: { categories: ["Outerwear"] },
};

describe("chart shapes", () => {
  const shape = (groupBy: Parameters<typeof queryStoreData>[0]["groupBy"]) =>
    chartFor(queryStoreData({ startDate: "2025-05-06", endDate: "2025-10-27", metrics: ["net_sales"], groupBy })).type;

  it("follow the rule: number → card, time → line, comparison → bar, two breakdowns → table", () => {
    expect(shape([])).toBe("stat");
    expect(shape(["week"])).toBe("line");
    expect(shape(["product"])).toBe("bar");
    expect(shape(["product", "size"])).toBe("table");
  });
});

describe("returned items list", () => {
  it("lists each returned line, newest first, as a table", () => {
    const list = listReturnedItems({ startDate: "2025-10-20", endDate: "2025-10-26", filters: { categories: ["Outerwear"] } });
    expect(list.view).toBe("list");
    expect(list.chart.type).toBe("table");
    expect(list.totals).toEqual({ returns: 4, refunds: 792.15 });
    expect(list.rows[0]).toEqual({
      day: "2025-10-26",
      order: "#2706",
      product: "Alpine Down Parka",
      variant: "S / Black",
      return_reason: "Defective",
      refunds: 219,
    });
    expect(list.rows.map((row) => row.day)).toEqual(["2025-10-26", "2025-10-24", "2025-10-23", "2025-10-21"]);
  });

  it("is what returnsReport returns for view: list", async () => {
    const result = await createMerchantTools().returnsReport.execute!(
      { startDate: "2025-09-28", endDate: "2025-10-27", metrics: ["returns"], view: "list" },
      execOptions,
    );
    expect(result).toMatchObject({ view: "list", totals: { returns: 6, refunds: 994.94 }, chart: { type: "table" } });
  });
});

describe("waiting steps", () => {
  it("start with choosing a report", () => {
    expect(stepsFor(undefined)).toEqual([{ id: "choose", label: "Choosing a report…", status: "active" }]);
  });

  it("describe the running query in plain words", () => {
    const steps = stepsFor({ type: "tool-returnsReport", state: "input-available", input: returnsInput });
    expect(steps).toMatchObject([
      { id: "choose", label: "Chose the returns report", status: "done" },
      {
        id: "run",
        label: "Running the returns report for Oct 20–26, 2025: returned units and refunds by product, Outerwear only…",
        status: "active",
      },
    ]);
  });

  it("end with what came back, ready to fold into 'Show steps (3)'", async () => {
    const output = await createMerchantTools().returnsReport.execute!(returnsInput as never, execOptions);
    const steps = stepsFor({ type: "tool-returnsReport", state: "output-available", input: returnsInput, output });
    expect(steps.map((step) => step.label)).toEqual([
      "Chose the returns report",
      "Ran the returns report for Oct 20–26, 2025: returned units and refunds by product, Outerwear only",
      "Got results for 2 products",
    ]);
    expect(steps.every((step) => step.status === "done")).toBe(true);
    // While the steps are revealed one by one, the newest uses its in-progress wording.
    expect(steps[1].activeLabel).toBe(
      "Running the returns report for Oct 20–26, 2025: returned units and refunds by product, Outerwear only…",
    );
  });

  it("mark failures", () => {
    expect(stepsFor(undefined, true)[0]).toMatchObject({ status: "error" });
    expect(stepsFor({ type: "tool-salesReport", state: "output-error", input: returnsInput, errorText: "bad" })[1]).toMatchObject({
      status: "error",
    });
  });

  it("explain questions the data can't answer", () => {
    const steps = stepsFor({
      type: "tool-cannotAnswer",
      state: "output-available",
      input: { missingData: "ad spend for the fall jacket campaign" },
      output: { answerable: false },
    });
    expect(steps.map((step) => step.label)).toEqual([
      "Checked what the store data covers",
      "Not in the store data: ad spend for the fall jacket campaign",
    ]);
  });
});

describe("formatting", () => {
  it("formats ranges, dates and values for merchants", () => {
    expect(formatRange("2025-10-20", "2025-10-26")).toBe("Oct 20–26, 2025");
    expect(formatRange("2025-06-01", "2025-10-27")).toBe("Jun 1 – Oct 27, 2025");
    expect(formatRange("2024-11-29", "2024-12-01")).toBe("Nov 29 – Dec 1, 2024");
    expect(formatRange("2024-12-20", "2025-01-05")).toBe("Dec 20, 2024 – Jan 5, 2025");
    expect(formatDateLabel("week", "2025-10-13")).toBe("Week of Oct 13, 2025");
    expect(formatDateLabel("month", "2025-10")).toBe("October 2025");
    expect(formatValue(1234.5, "currency")).toBe("$1,234.50");
    expect(formatValue(38.46, "percent")).toBe("38.46%");
    expect(formatValue(null, "currency")).toBe("—");
    expect(formatAxisValue(2000, "currency")).toBe("$2,000");
    expect(formatAxisValue(12_500, "currency")).toBe("$12.5K");
  });
});

describe("sales report returns", () => {
  it("say how many items came back by return date, so 0 returns isn't misread", async () => {
    const result = await createMerchantTools().salesReport.execute!(
      {
        startDate: "2025-10-20",
        endDate: "2025-10-26",
        metrics: ["net_sales", "returns", "return_rate"],
        groupBy: ["product"],
        filters: { categories: ["Outerwear"] },
      } as never,
      execOptions,
    );
    expect(result).toMatchObject({ totals: { returns: 0 } });
    expect((result as { warnings: string[] }).warnings).toContain(
      "Returns here are from orders placed in these dates. Counted by return date, 4 items were sent back during these dates.",
    );
  });
});

describe("error messages", () => {
  const rateLimited = (body: string) =>
    new APICallError({ message: "Rate limit exceeded", url: "https://openrouter.ai", requestBodyValues: {}, statusCode: 429, responseBody: body });

  it("see through retries and tell a busy model from the daily cap", () => {
    const retried = new RetryError({ message: "Failed after 3 attempts", reason: "maxRetriesExceeded", errors: [rateLimited("{}")] });
    expect(merchantErrorMessage(retried)).toBe("The free AI model is busy right now. Please try again in a minute.");
    expect(merchantErrorMessage(rateLimited('{"error":{"message":"Rate limit exceeded: free-models-per-day"}}'))).toMatch(
      /used up today's free requests/,
    );
    expect(merchantErrorMessage(new Error("boom"))).toBe("Something went wrong while answering. Please try again.");
  });
});
