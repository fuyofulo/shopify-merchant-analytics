# Demo deck outline

Six slides for the live demo. Q&A takes the last 4 minutes. `build_deck.py` turns this into `shopify-merchant-analytics.pptx`.

1. **Merchants ask in their own words. Now they get a chart back.**
   Four real requests from `data/merchant-report-requests-2025-10-27.xlsx`. 30 requests were logged on Oct 27, many needed before the Black Friday reorder. The fix: type the question, get a chart and a short answer.

2. **Type a question. Get a chart and a short answer.** (the interface)
   Screenshot: jacket returns last week. Four callouts: own words, grey steps, exact dates under the title, short answer.

3. **How a question becomes a chart.** (for Tomasz and Hana)
   You type → the AI picks one report and fills in the details → our code runs the numbers → the page draws the chart and the AI writes one sentence. The AI never does maths or dates.

4. **Vague questions get exact dates, in seconds.** (speed and "last week")
   What it answers: sales and best sellers, returns and why, repeat customers. Vague words become exact dates. Ad spend and stock get a clear "not in the data". Screenshot: weekly revenue for "recently". Most charts land in under 3 seconds.

5. **Erik's 20 questions: all three pass marks met.** (results)
   19 of 20 right report (needs 18), 0 crashes, slowest chart 4.63s (needs under 5s). Native chart: seconds to first chart per question. The one miss, AQ-15, has been fixed but not re-run yet.

6. **Ready for Black Friday, November 28.** (for Priya)
   It's live on Vercel and tested. Three small steps before Nov 28: put the key on the public URL, add OpenRouter credits for more than ~25 questions a day, and re-run the sweaters question.
