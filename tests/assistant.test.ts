import { simulateReadableStream, type UIMessage } from "ai";
import { MockLanguageModelV4 } from "ai/test";
import { describe, expect, it } from "vitest";

import { describeDataset, resolvePeriods } from "@/lib/analytics";
import { streamMerchantAnswer } from "@/lib/assistant/answer";
import { buildInstructions } from "@/lib/assistant/instructions";
import { createMerchantTools, TOOL_DESCRIPTIONS } from "@/lib/assistant/tools";

const TODAY = "2025-10-27"; // Monday; last day of data and the date of the merchant requests
const execOptions = { toolCallId: "test", messages: [] } as never;
const periodFor = (phrase: string, today = TODAY) =>
  resolvePeriods(today, "2025-05-06").find((period) => period.phrases.includes(phrase));

describe("resolvePeriods", () => {
  it("resolves the phrases merchants use to exact dates", () => {
    expect(periodFor("last week")).toMatchObject({ startDate: "2025-10-20", endDate: "2025-10-26" });
    expect(periodFor("last wk")).toMatchObject({ startDate: "2025-10-20", endDate: "2025-10-26" });
    expect(periodFor("this week")).toMatchObject({ startDate: "2025-10-27", endDate: "2025-10-27" });
    expect(periodFor("last 14 days")).toMatchObject({ startDate: "2025-10-14", endDate: "2025-10-27" });
    expect(periodFor("last 30 days")).toMatchObject({ startDate: "2025-09-28", endDate: "2025-10-27" });
    expect(periodFor("last 8 weeks (full Monday–Sunday weeks)")).toMatchObject({ startDate: "2025-09-01", endDate: "2025-10-26" });
    expect(periodFor("this month")).toMatchObject({ startDate: "2025-10-01", endDate: "2025-10-27" });
    expect(periodFor("last month")).toMatchObject({ startDate: "2025-09-01", endDate: "2025-09-30" });
    expect(periodFor("this season")).toMatchObject({ startDate: "2025-09-01", endDate: "2025-10-27" });
    expect(periodFor("since summer")).toMatchObject({ startDate: "2025-06-01", endDate: "2025-10-27" });
    expect(periodFor("all time")).toMatchObject({ startDate: "2025-05-06", endDate: "2025-10-27" });
  });

  it("handles year boundaries", () => {
    expect(periodFor("last month", "2026-01-10")).toMatchObject({ startDate: "2025-12-01", endDate: "2025-12-31" });
    expect(periodFor("this season", "2026-01-10")).toMatchObject({ startDate: "2025-12-01" });
    expect(periodFor("since summer", "2026-03-01")).toMatchObject({ startDate: "2025-06-01" });
  });
});

describe("instructions", () => {
  it("give the model today's date, exact periods and the catalogue", () => {
    const instructions = buildInstructions(TODAY, describeDataset());
    expect(instructions).toContain("Today is Monday 2025-10-27");
    expect(instructions).toContain('"last week" / "last wk" / "through last Sunday": 2025-10-20 to 2025-10-26');
    expect(instructions).toContain("Make exactly ONE tool call");
    expect(instructions).toContain("Alpine Down Parka (Outerwear)");
  });
});

describe("merchant tools", () => {
  it("are described in merchants' words", () => {
    expect(TOOL_DESCRIPTIONS.returnsReport).toMatch(/^See how your returns are doing/);
    expect(TOOL_DESCRIPTIONS.salesReport).toMatch(/^See your sales and revenue/);
    expect(TOOL_DESCRIPTIONS.repeatCustomersReport).toMatch(/^See how many customers came back/);
  });

  it("salesReport returns rows and a chart spec", async () => {
    const tools = createMerchantTools();
    const result = await tools.salesReport.execute!(
      { startDate: "2025-10-20", endDate: "2025-10-26", metrics: ["net_sales", "orders"], groupBy: ["day"] },
      execOptions,
    );
    expect(result).toMatchObject({
      totals: { net_sales: 543.5, orders: 4 },
      chart: { type: "line", title: "Net sales, Orders by day", x: { key: "day" } },
    });
  });

  it("returnsReport counts returns by return date unless compared with sales", async () => {
    const byReturnDate = await createMerchantTools().returnsReport.execute!(
      { startDate: "2025-10-20", endDate: "2025-10-26", metrics: ["returns"], groupBy: ["product"], filters: { categories: ["Outerwear"] } },
      execOptions,
    );
    expect(byReturnDate).toMatchObject({
      period: { dateField: "return_date" },
      rows: [
        { product: "Alpine Down Parka", returns: 3 },
        { product: "Northridge Insulated Jacket", returns: 1 },
      ],
    });

    const withRate = await createMerchantTools().returnsReport.execute!(
      { startDate: "2025-05-06", endDate: "2025-10-27", metrics: ["return_rate"], groupBy: ["category"], limit: 1 },
      execOptions,
    );
    expect(withRate).toMatchObject({ period: { dateField: "order_date" }, rows: [{ category: "Outerwear", return_rate: 60 }] });
  });

  it("returnsReport by reason only includes returned items", async () => {
    const result = await createMerchantTools().returnsReport.execute!(
      { startDate: "2025-05-06", endDate: "2025-10-27", metrics: ["returns"], groupBy: ["return_reason"] },
      execOptions,
    );
    expect("rows" in result && result.rows.map((row) => row.return_reason)).not.toContain("Not returned");
  });

  it("repeatCustomersReport gives the monthly repeat order share", async () => {
    const result = await createMerchantTools().repeatCustomersReport.execute!(
      { startDate: "2025-05-06", endDate: "2025-10-27", metrics: ["repeat_order_share", "repeat_customers"], groupBy: ["month"] },
      execOptions,
    );
    expect(result).toMatchObject({
      totals: { repeat_order_share: 40, repeat_customers: 7 },
      rows: [
        { month: "2025-05", repeat_order_share: 0 },
        { month: "2025-06", repeat_order_share: 100 },
        { month: "2025-07", repeat_order_share: 0 },
        { month: "2025-08", repeat_order_share: 100 },
        { month: "2025-09", repeat_order_share: 50 },
        { month: "2025-10", repeat_order_share: 38.46, repeat_customers: 4 },
      ],
    });
  });

  it("only allow each tool's own metrics", async () => {
    const tools = createMerchantTools();
    const schema = tools.salesReport.inputSchema as unknown as { safeParse: (value: unknown) => { success: boolean } };
    expect(schema.safeParse({ startDate: TODAY, endDate: TODAY, metrics: ["repeat_order_share"] }).success).toBe(false);
    expect(schema.safeParse({ startDate: TODAY, endDate: TODAY, metrics: ["net_sales"] }).success).toBe(true);
  });

  it("run only the first tool call per question", async () => {
    const tools = createMerchantTools();
    const input = { startDate: TODAY, endDate: TODAY, metrics: ["orders"] as ["orders"] };
    await tools.salesReport.execute!(input, execOptions);
    expect(await tools.salesReport.execute!(input, execOptions)).toMatchObject({ error: expect.stringMatching(/Only one tool call/) });
  });
});

describe("streamMerchantAnswer", () => {
  const usage = {
    inputTokens: { total: 10, noCache: 10, cacheRead: undefined, cacheWrite: undefined },
    outputTokens: { total: 5, text: 5, reasoning: undefined },
  };
  const question: UIMessage[] = [{ id: "1", role: "user", parts: [{ type: "text", text: "jakets returnd last wk" }] }];

  it("makes one tool call with exact dates, then answers from the result", async () => {
    const model = new MockLanguageModelV4({
      doStream: [
        {
          stream: simulateReadableStream({
            chunks: [
              {
                type: "tool-call",
                toolCallId: "call-1",
                toolName: "returnsReport",
                input: JSON.stringify({
                  startDate: "2025-10-20",
                  endDate: "2025-10-26",
                  metrics: ["returns", "refunds"],
                  groupBy: ["product"],
                  filters: { categories: ["Outerwear"] },
                }),
              },
              { type: "finish", finishReason: { unified: "tool-calls", raw: "tool_calls" }, usage },
            ],
          }),
        },
        {
          stream: simulateReadableStream({
            chunks: [
              { type: "text-start", id: "t1" },
              { type: "text-delta", id: "t1", delta: "4 jackets came back last week, mostly the Alpine Down Parka." },
              { type: "text-end", id: "t1" },
              { type: "finish", finishReason: { unified: "stop", raw: "stop" }, usage },
            ],
          }),
        },
      ],
    });

    const result = await streamMerchantAnswer({ model, messages: question, today: TODAY });
    await result.consumeStream();
    const steps = await result.steps;

    expect(steps).toHaveLength(2);
    expect(steps.flatMap((step) => step.toolCalls)).toHaveLength(1);
    expect(steps[0].toolResults[0].output).toMatchObject({
      totals: { returns: 4, refunds: 792.15 },
      chart: { type: "bar", title: "Returns, Refunds by product" },
    });
    expect(await result.text).toBe("4 jackets came back last week, mostly the Alpine Down Parka.");

    // Step 1 forces a tool call; step 2 forbids more tool calls.
    expect(model.doStreamCalls[0].toolChoice).toEqual({ type: "required" });
    expect(model.doStreamCalls[1].toolChoice).toEqual({ type: "none" });
    expect(JSON.stringify(model.doStreamCalls[0].prompt[0])).toContain("Today is Monday 2025-10-27");
  });
});
