# Demo deck outline

Six slides for the live demo. Q&A takes the last 4 minutes. `build_deck.py` turns this into `shopify-merchant-analytics.pptx`. The opening and closing slides are dark and the rest are light, in the app's own colours.

1. **"jakets returnd last wk"** (the problem)
   One real typo-filled request as the headline, with four more from `data/merchant-report-requests-2025-10-27.xlsx` as chat bubbles. The fix: ask the dashboard, get a chart in under 3 seconds.

2. **Type a question. Get a chart and an answer.** (the interface)
   The jacket returns screenshot in a browser window, with numbered pins for the steps, the exact dates and the short answer.

3. **How a question becomes a chart** (for Tomasz and Hana)
   The real objects at each step: the typed question → the report the AI asks for (Returns, Oct 20–26, Outerwear) → the rows our code returns → the bar chart and the one-sentence answer. The AI only chooses and fills in. Code does the dates, the maths and the chart.

4. **Vague words become exact dates** (speed and "last week")
   A timeline showing the range each phrase becomes, next to the weekly revenue chart for "recently". Along the bottom: 2.4 s median to chart, 3 reports, no made-up charts.

5. **Erik's 20 questions: every pass mark met** (results)
   19/20 right report, 0 crashes, 4.63 s slowest. A native chart of seconds to chart per question, with the 5 s pass mark as a dashed line. AQ-15 is the one miss: fixed, but not re-run yet.

6. **Ready for Black Friday** (for Priya)
   A timeline from now to Nov 28 with three small steps: put the key on the public URL, add OpenRouter credits, and re-run the sweaters question.
