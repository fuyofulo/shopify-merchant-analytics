# Shopify Merchant Analytics

A chat dashboard for a Shopify store. The merchant asks a question in their own words, like "jakets returnd last wk", and gets a chart and a short answer.

![Jacket returns last week: bar chart with the tooltip on Alpine Down Parka showing 3 returned units](docs/screenshots/jacket-returns-tooltip.png)

## How it works

1. A free OpenRouter model reads the question and makes exactly one tool call: `salesReport`, `returnsReport`, `repeatCustomersReport` or `cannotAnswer`. The tool descriptions use the merchants' own words from `data/merchant-report-requests-2025-10-27.xlsx`.
2. Dates are worked out in code ("last week" is Oct 20–26) and given to the model as a table. The model copies dates; it never calculates them.
3. The tool runs a plain query over `data/orders.csv` and returns rows, totals and a chart spec. The model never sees the raw data or does arithmetic.
4. The page draws the chart, and the model writes a one-to-three-sentence answer from the result.

"Today" is Oct 27, 2025, the last day in the data. The default model is `baidu/ernie-5.5-flash-preview:free`, with two free fallbacks.

## Chart shapes

The code picks the chart from the shape of the result, not the model, so the same question always gets the same chart.

| Metric | Chart | Why |
| --- | --- | --- |
| Net sales over time | Line | Shows whether sales are going up or down. |
| Best sellers | Bar | Ranks products so the top ones stand out. |
| Sales by channel or category | Bar | Compares a few groups side by side. |
| Totals and averages (sales, orders, average order value) | Metric card | It's one number. |
| Returns by product or reason | Bar | Shows what comes back most, and why. |
| Return rate by category | Bar | Compares categories against what they sold. |
| Returned orders list | Table | Row-by-row detail to scan before a reorder. |
| Returns by size and reason | Table | Two breakdowns read better as a grid. |
| Repeat customer share by month | Line | Answers "are repeat customers growing?" |
| Repeat customers, repeat orders | Metric card | It's one count. |

## Loading state

![The steps appear in grey, fold into "Show steps (3)" when the chart lands, and the answer streams in under it](docs/screenshots/loading-steps.gif)

While the model works, the reply shows what it's doing in grey, built from the real tool call: "Choosing a report…", then "Running the returns report for Oct 20–26: returned units by product, Outerwear only…". The chart appears as soon as the result arrives, the steps fold into "Show steps (3)", and the answer streams in underneath. If the model fails, the steps stay open and a message with "Try again" takes the chart's place.

## Built with Claude Code

The chat page came from this prompt (excerpt):

> Show the loading state inside the assistant's reply, where the answer will appear. No chart skeleton or spinner. Show the steps the assistant is taking in muted grey, in plain words, built from the tool call and result that `/api/chat` already streams. When the chart is ready, fold the steps into a collapsed "Show steps (3)" toggle above it. If something goes wrong, keep the steps visible and show a friendly message instead of the chart.

I checked it in the browser with real merchant questions, timing each stage of the reply and comparing every chart against the query engine. That led to four changes:

- The tool call and its result arrived together, so the middle steps never showed. Each step now stays on screen for at least 0.45s while the merchant waits. At first the chart also waited for the steps, which made AQ-03 miss the 5-second mark (5.26s). Now the chart appears as soon as the result arrives (4.63s).
- The count axes showed fractions like 0.75. They now show whole numbers.
- A rate-limited model showed "Something went wrong" because retries hid the 429 error. It now says the model is busy, or that the daily limit is used up.
- The sales report showed "Returns 0" for a week when 4 jackets came back, because it counts returns on orders *placed* that week. It now adds a note with the number sent back.

## Live run

All 20 of Erik Vogt's acceptance questions (`data/acceptance-questions-erik-vogt.xlsx`), asked on the [Vercel preview](https://shopify-merchant-analytics-k0wfdy9i2-fuyofulo-613da217.vercel.app), each in a fresh chat. The preview needs a Vercel sign-in. "First chart" is the time from pressing Ask to the chart appearing. Every number was checked against the query engine.

| ID | Question | Tool | Dates | First chart | Result |
| --- | --- | --- | --- | --- | --- |
| AQ-01 | sales last 30 days online store only | `salesReport` | Sep 27 – Oct 26 | 2.04s | $1,230.90 from the Online Store. |
| AQ-02 | best sellers this season | `salesReport` | Sep 1 – Oct 27 | 2.99s* | Alpine Down Parka first, at $854.10. |
| AQ-03 | which jackets came back the most last week | `returnsReport` | Oct 20–26 | 4.63s | Alpine Down Parka 3, Northridge 1. |
| AQ-04 | are repeat customers growing since summer | `repeatCustomersReport` | Jun 1 – Oct 26 | 2.31s | Repeat orders rose to 5 in October, but repeat share fell to 41.67%. |
| AQ-05 | sales and returns on jackets last week | `salesReport` | Oct 20–26 | 2.92s | $356.10 in sales, with a note that 4 items came back that week. |
| AQ-06 | top 5 hoodies in august | `salesReport` | Aug 1–31 | 2.33s | The store sells no hoodies. It says so and shows August's top products. |
| AQ-07 | what's my ad spend on Meta this month | `cannotAnswer` | none | no chart | Says ad spend isn't in the data. |
| AQ-08 | how are returns doing | `returnsReport` | May 6 – Oct 27 | 2.69s* | 8 returns, $1,116.94 refunded. |
| AQ-09 | how much did i make since labor day | `salesReport` | Sep 1 – Oct 26 | 1.67s | $2,310.15. |
| AQ-10 | how many ppl bought twice in october | `repeatCustomersReport` | Oct 1–27 | 2.73s | 4 repeat customers, 5 repeat orders. |
| AQ-11 | what's selling rn | `salesReport` | May 6 – Oct 27 | 2.31s | Best sellers. "rn" was read as all data. |
| AQ-12 | return rate on boots lately? | `salesReport` | Sep 27 – Oct 26 | 2.15s | The store sells no boots. Empty cards and a note saying so. |
| AQ-13 | revenue by wk recently | `salesReport` | Sep 28 – Oct 27* | 2.64s* | Weekly line, peaking at $635.40 in the week of Oct 13. |
| AQ-14 | repeat buyers lately on beanies and scarves | `repeatCustomersReport` | Sep 27 – Oct 26 | 2.84s | Wool Beanie: 2 orders, 1 from a repeat customer. No scarves in the store. |
| AQ-15 | which sweaters sell best | `salesReport` | May 6 – Oct 27 | 1.65s | Miss: no Knitwear filter, so it charted every product. The answer still named the right two. |
| AQ-16 | top return reasons for jakets in september | `returnsReport` | Sep 1–30 | 2.18s | No jackets came back in September. It says so. |
| AQ-17 | whats my pos vs online split | `salesReport` | May 6 – Oct 27 | 1.75s | Online $2,690.35, Point of Sale $408.00. |
| AQ-18 | repeat customer share | `repeatCustomersReport` | May 6 – Oct 27 | 2.63s | 40% (8 of 20 orders). |
| AQ-19 | refunds been bad lately? | `returnsReport` | Sep 27 – Oct 26 | 2.46s | $920.94 across 5 returns. |
| AQ-20 | how many fleece vests do i have left in stock | `cannotAnswer` | none | no chart | The steps say stock isn't in the data. The written answer hit the daily free limit. |

\* AQ-02, AQ-08 and AQ-13 were run on the first preview, before two changes. One was the chart fix, so their times include the old half-second wait. The other was the date change below, so "recently" (AQ-13) now resolves to Sep 27 – Oct 26.

Against Erik's pass marks:

- **Right call:** 19 of 20 (pass mark 18). AQ-15 missed the Knitwear filter. The prompt now says where sweaters and other everyday product types live. That fix is deployed but not re-run yet, because the run used up the day's free requests.
- **Rendered without a crash:** 20 of 20.
- **First chart under 5 seconds:** yes, for every question that draws a chart. The slowest was AQ-03 at 4.63s.

Two changes came out of this run. First, "last 30 days" and "since Labor Day" now end yesterday, which matches the ranges in Erik's sheet (AQ-01, AQ-09). "This week / month / season" still run to today. Second, the chart no longer waits for the loading steps.

## Known limits

- The free model allows about 25 questions a day: 50 requests, and each question uses two.
- With 20 orders over six months, monthly percentages swing a lot. Repeat share jumps between 0% and 100%.
- Sales and returns can't share one chart. Money and counts would need two axes, and every chart here has one.

## Run it

```bash
npm install
cp .env.example .env.local    # add your free OpenRouter key
npm run dev                   # http://localhost:3000
npm test                      # 42 tests, no key needed
```

To deploy, run `vercel link`, then `vercel env add OPENROUTER_API_KEY preview --sensitive`, then `vercel deploy`. The key lives only in Vercel's encrypted settings and in `.env.local`, which git ignores.

## Code

```
src/lib/analytics/        query engine: metrics, breakdowns, dates, chart spec
src/lib/assistant/        tools, system prompt, model, the two-step stream
src/app/api/chat/         streaming chat route
src/components/           chat page and charts
tests/                    engine, tools and chat-page tests
```
