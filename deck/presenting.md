# Presenting the demo

Ten minutes: six of talking, with one question typed live, then four for Erik's questions. The full script is in each slide's speaker notes, with a time cue at the start.

## Run of show

| Time | Slide | What happens |
| --- | --- | --- |
| 0:00 | 1 | Who I am. The jacket question. 28 of 30 requests fit three reports. |
| 0:50 | 2, then the browser | Type Erik's question 1 at the live URL. |
| 2:20 | 3 | What just happened, in six steps. |
| 3:15 | 4 | Vague words become exact dates. |
| 4:00 | 5 | Erik's 20 questions: every pass mark met. |
| 4:50 | 6 | Ready for Black Friday, and the Nov 7 decision. |
| 5:45 | | 15 seconds spare. |

## Before you start

- The free plan allows about 25 questions a day for the whole account, rehearsals included. It resets at midnight UTC. Don't use it up rehearsing on the day. $10 of OpenRouter credits removes the worry (1,000 requests a day).
- The day before, type Erik's four questions at the public URL once (8 of the 50 requests).
- Before you share your screen, open https://shopify-merchant-analytics.vercel.app in a tab, zoom to 125%, and reload for an empty chat.
- If the model is slow or busy, press Try again once, then go back to slide 2. It shows the same question, answered earlier.

## Erik's four typed questions

What should come back. The reports were run in code to get these numbers. The model's choices for these exact wordings still need the live test.

| Question | Report and dates | Chart | Answer |
| --- | --- | --- | --- |
| Which winter jackets came back as returns last week? | Returns, Oct 20–26, Outerwear only | Bar | 4 units, $792.15 refunded. Alpine Down Parka 3, Northridge Insulated Jacket 1. |
| How are sales doing recently? | Sales, Sep 27 – Oct 26 | Weekly line, or one number | $2,079.05 from 12 orders. Best week: Oct 13, $635.40. |
| Show repeat customers by month since summer | Repeat customers, Jun 1 – Oct 26, by month | Line | 7 repeat customers, 4 of them in October. October's repeat share: 41.67%. |
| What's my profit margin on hoodies? | Can't answer | None | Costs aren't in the data, so there's no margin. Suggests a question it can answer. |

In the live test, check that question 1 filters to Outerwear rather than searching for a product called "winter jackets".

## Erik's questions afterwards

Answer in about 20 seconds, then point to the proof. He wants "a repo path, a README row or a live run".

**1. How did "last week" and "recently" become exact dates?**
Code works out the dates, not the model. `src/lib/analytics/periods.ts` turns each phrase into exact dates. `src/lib/assistant/instructions.ts` puts them in the prompt as a table, and the model copies from it. "Today" is the last day in the data, Oct 27, 2025 (`storeToday` in `src/lib/assistant/answer.ts`; `STORE_TODAY` overrides it). So last week is Mon–Sun, Oct 20–26, and recently is the last 30 full days, Sep 27 – Oct 26. Every chart shows its range.
If he types it on Oct 30, it still counts from Oct 27, because that's where the data ends. With live store data, "today" would be the store's own date. Say this before he finds it.

**2. What happens with no date at all?**
It uses all the data, May 6 – Oct 27. The prompt says so in `instructions.ts`, and slide 4's last row shows it. README rows AQ-08, AQ-11, AQ-17 and AQ-18.

**3. Why a line, bar or table?**
Code picks the chart from the shape of the result, never the model: `chartFor` in `src/lib/analytics/chart.ts`.
- One number: a card.
- Over time: a line.
- Comparing things: a bar.
- Two breakdowns, or a list: a table.

Same question, same chart. The README has a "Chart shapes" table, and the test is "chart shapes" in `tests/chat-page.test.ts`.

**4. How did you measure time to first chart, and on what network?**
In Chrome on the Vercel preview. A timer started when Ask was pressed and stopped when the chart appeared on the page. One run per question, each in a fresh chat. It ran from my laptop on my home internet (say where, and Wi-Fi or wired). The app runs in Vercel's iad1 region (Washington, D.C.) and calls a free OpenRouter model. Median 2.4 s, slowest 4.63 s (AQ-03). See the README "Live run" table.
The limit: one run each, on a free model whose speed varies.

**5. Which questions missed, and why?**
AQ-15, "which sweaters sell best". It picked the right report but no Knitwear filter, so it charted every product. The answer still named the right two. The cause: the prompt didn't say sweaters are Knitwear. It does now ("Sweaters, cardigans and knits are in Knitwear" in `instructions.ts`). It hasn't been re-run yet. See the README AQ-15 row.
Also, AQ-20's tool call was right, but its written answer hit the free daily limit.

**6. Where are the OpenRouter key and the model id configured in Vercel?**
- **The key:** `OPENROUTER_API_KEY`, under the project's Environment Variables, for Production and Preview, stored as Sensitive. It's never in git; `.env.local` is ignored.
- **The model:** the `OPENROUTER_MODEL` variable is optional and takes a comma-separated list for fallbacks. It isn't set, so the default in `src/lib/assistant/model.ts` runs: `baidu/ernie-5.5-flash-preview:free`, then two free fallbacks.

**7. What if two tools could both answer?**
It can make only one call, and three things enforce that:
- The first step requires exactly one tool call (`toolChoice: "required"` in `answer.ts`).
- Parallel calls are off (`model.ts`).
- A guard in `tools.ts` runs only the first call.

The tool descriptions draw the line between returns and sales:
- Items sent back go to the returns report, counted by return date.
- A return rate, or returns next to sales, goes to the sales report.

Example: AQ-05, "sales and returns on jackets last week", goes to the sales report, with a note that 4 items came back that week. The test is "sales report returns" in `tests/chat-page.test.ts`.

## The Nov 7 decision

Erik wants one decision by Nov 7: which metrics go to Priya to ship. Propose:
- **Sales:** net sales over time, best sellers by revenue or units, sales by channel and category, and average order value.
- **Returns:** returned units and refunds by product, category, size and reason.
- **Repeat customers:** repeat share by month, and the number of repeat customers.

Not in the data, so it can't ship: ad spend, ROAS, stock, and costs or profit.
