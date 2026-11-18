# Demo deck outline

Six slides for the live demo. Q&A takes the last 4 minutes. `build_deck.py` turns this into `shopify-merchant-analytics.pptx`. It uses Shopify's admin look: deep green opening and closing slides, light grey content slides with white cards, green accents and Lucide icons.

1. **"Which jackets came back as returns last week?"** (the problem)
   A real request from `data/merchant-report-requests-2025-10-27.xlsx` as the headline. The "Report requests" card shows all 30 requests from that day, one square each, grouped by the report that answers them: 14 sales, 9 returns, 5 repeat customers, and 2 about ad spend, which isn't in the store data. So 28 of 30 fit three reports. The fix: ask the dashboard, get a chart in under 3 seconds. At the bottom, a white card: "Built by Zaid Khan", with GitHub, X and email.

2. **Type a question. Get a chart and an answer.** (the interface)
   The jacket returns screenshot in a browser window, with numbered pins for the steps, the exact dates and the short answer.

3. **How a question becomes a chart** (for Tomasz and Hana)
   A swimlane diagram with three lanes (merchant, AI model, our code) and six numbered steps, each showing its real data: the question, the date table, the report the AI picks (Returns, Oct 20–26, Outerwear), the rows our code returns, the one-sentence answer, and the chart. The AI lane holds only two steps: it chooses and it writes. Code does the dates, the maths and the chart.

4. **Vague words become exact dates** (speed and "last week")
   A timeline showing the range each phrase becomes, next to the weekly revenue chart for "recently". Along the bottom: 2.4 s median to chart, 3 reports, no made-up charts.

5. **Erik's 20 questions: every pass mark met** (results)
   19/20 right report, 0 crashes, 4.63 s slowest. A native chart of seconds to chart per question, with the 5 s pass mark as a dashed line. AQ-15 is the one miss: fixed, but not re-run yet.

6. **Ready for Black Friday** (for Priya)
   Live now at shopify-merchant-analytics.vercel.app, with the AI key. A timeline from now to Nov 28 with one step left: $10 of OpenRouter credits, which lifts the free limit from about 25 questions a day to about 500. GitHub, X and email next to "Questions?".
