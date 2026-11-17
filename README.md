# Shopify Merchant Analytics

**Zero Uni · Project 1.** A Next.js app where a Shopify merchant asks questions about their store in plain English (*"What are our top-selling products?"*, *"Why are customers returning things?"*) and gets answers and charts.

An LLM never reads the raw data or does arithmetic. It turns the question into a structured call to one function, **`queryStoreData`**: a date range, the metrics needed, and how to break them down. That function computes exact numbers from the order history and returns JSON that the LLM explains in words and the UI can draw as a chart.

```
Merchant question
   │  "How many sales did we do last month?"
   ▼
LLM (Vercel AI SDK, tool calling)
   │  queryStoreData({ startDate: "2025-09-01", endDate: "2025-09-30", metrics: ["orders", "net_sales"] })
   ▼
Query engine (this repo)  ──reads──▶  data/orders.csv
   │  { totals: { orders: 2, net_sales: 231.1 }, rows: [...], columns: [...], warnings: [] }
   ▼
LLM answer + chart  →  "You made 2 sales last month, totalling $231.10."
```

## Status

| Part | State |
| --- | --- |
| Data layer: CSV parsing, validation, typed line items | ✅ Done |
| Query engine `queryStoreData`: metrics, breakdowns, filters, sorting, warnings | ✅ Done |
| AI SDK tool definitions (`storeAnalyticsTools`) | ✅ Done |
| API routes (`/api/analytics/query`, `/api/analytics/dataset`) | ✅ Done |
| Tests (19, every number checked against values computed separately) | ✅ Done |
| Chat UI + LLM route + chart rendering | ⏭ Next step |

## Quick start

```bash
npm install
npm run dev        # http://localhost:3000
npm test           # vitest
npm run typecheck
npm run lint
```

Node 20.9+ is required (developed on Node 24).

## The function: `queryStoreData`

```ts
import { queryStoreData } from "@/lib/analytics";

const result = queryStoreData({
  startDate: "2025-05-06",         // inclusive, YYYY-MM-DD
  endDate: "2025-10-27",           // inclusive, YYYY-MM-DD
  metrics: ["net_sales", "units_sold"],
  groupBy: ["product"],            // optional, up to 2 dimensions
  filters: { customerType: "repeat" }, // optional
  limit: 5,                        // optional, "top 5"
});
```

### Input

| Field | Required | Description |
| --- | --- | --- |
| `startDate`, `endDate` | yes | The period, inclusive (`YYYY-MM-DD`). |
| `metrics` | yes | What to measure (see below). The first metric is the default sort key. |
| `groupBy` | no | Up to two dimensions to break results down by, e.g. `["product"]` or `["month", "sales_channel"]`. If empty, you get one overall row. |
| `filters` | no | `products`, `categories`, `salesChannels`, `customerType` (`new`/`repeat`), `customerIds`, `orderIds`, `sizes`, `colors`, `fulfillmentStatuses`, `returned`, `returnReasons`. Text matching ignores case. Values within one list are OR-ed, and different filters are AND-ed. `products` accepts an ID or part of a title (`"parka"`). |
| `dateField` | no | `order_date` (default) or `return_date`. Use `return_date` for "returns that *happened* in this period". |
| `sortBy`, `sortDirection` | no | Rank rows by any metric (`desc` by default). Time breakdowns default to chronological order. |
| `limit` | no | Maximum rows, e.g. `5` for "top 5". `totals` still cover everything. |

Input is validated with a Zod schema (`storeQuerySchema`). The same schema is the tool's input schema, so the LLM sees the allowed values and descriptions.

### Metrics

| Key | Meaning |
| --- | --- |
| `net_sales` | Sales after discounts, before refunds (sum of line totals). Default meaning of "sales" or "revenue". |
| `gross_sales` | Sales before discounts (quantity × unit price). |
| `discounts` | Total discounts given. |
| `refunds` | Total refunded on returned items. |
| `net_revenue` | Net sales − refunds. |
| `orders` | Distinct orders. |
| `line_items` | Order lines. |
| `units_sold` | Total quantity sold. |
| `customers` | Distinct customers. |
| `average_order_value` | Net sales ÷ orders. |
| `sales_per_customer` | Net sales ÷ customers. |
| `units_per_order` | Units ÷ orders. |
| `returns` | Returned line items. |
| `returned_units` | Returned quantity. |
| `customers_with_returns` | Distinct customers who returned something. |
| `return_rate` | Returned units as a % (0–100) of units sold. |
| `discount_rate` | Discounts as a % (0–100) of gross sales. |

### Dimensions (`groupBy`)

`day`, `week` (Monday start, labelled by the Monday's date), `month`, `product`, `category`, `variant`, `size`, `color`, `sales_channel`, `customer_type` (`new` / `repeat`), `customer`, `fulfillment_status`, `return_reason`, `order`.

### Output

```jsonc
{
  "query":   { /* the validated query, defaults filled in */ },
  "period":  { "startDate": "...", "endDate": "...", "dateField": "order_date",
               "dataAvailable": { "startDate": "2025-05-06", "endDate": "2025-10-27" } },
  "columns": [ { "key": "product", "label": "Product", "role": "dimension", "format": "text" },
               { "key": "net_sales", "label": "Net sales", "role": "metric", "format": "currency" } ],
  "rows":    [ { "product": "Alpine Down Parka", "net_sales": 854.1 }, ... ],
  "totals":  { "net_sales": 3098.35 },   // over everything matched, ignoring limit
  "matchedLineItems": 28,
  "totalRows": 11,
  "truncated": true,
  "warnings": []                          // e.g. unknown filter values, period outside the data
}
```

- `columns` describes each field in `rows`, so a chart component can choose its axes and number formats without guessing.
- A single time breakdown (`day`/`week`/`month`) includes empty buckets as zeros, so trend charts don't skip periods. Ratios that can't be computed (such as average order value in a week with no orders) are `null`, not `0`.
- `warnings` let the LLM correct itself. If it filters on a channel that doesn't exist, the warning lists the channels that do. If it asks about a period with no data, the warning gives the range that has data.

### `describeDataset()`

Returns what the data contains: date coverage (`latestDataDate`), counts, products, categories, channels, return reasons, sizes and colours, plus every metric and dimension with its description. Put it in the system prompt or expose it as a tool so the LLM uses real values.

## Example questions

These are in [`src/lib/analytics/examples.ts`](src/lib/analytics/examples.ts) and run as tests. The dataset ends on Monday **2025-10-27**, so relative periods are resolved from that date.

| Question | Query | Answer from the data |
| --- | --- | --- |
| How many customers have returned products, and why? | `metrics: [customers_with_returns, returns, refunds]`, `groupBy: [return_reason]`, `filters: { returned: true }` | 8 customers returned 8 items, with $1,116.94 refunded. Reasons: Too small (2, $354.15), Too large (2, $247.00), Changed mind (2, $202.79), Defective (1), Not as pictured (1). |
| What are our top-selling products? | `metrics: [net_sales, units_sold, orders]`, `groupBy: [product]`, `limit: 5` | Alpine Down Parka $854.10, Northridge Insulated Jacket $596.25, Selvedge Slim Jeans $436.60, … |
| What are repeat customers buying on repeat purchases? | `metrics: [units_sold, net_sales, customers]`, `groupBy: [product]`, `filters: { customerType: repeat }` | Northridge Insulated Jacket (3 units), Selvedge Slim Jeans (3), Wool Beanie (3), … |
| What is the average sale per customer? | `metrics: [sales_per_customer, average_order_value, customers, orders]` | $172.13 per customer across 18 customers. Average order value is $154.92 across 20 orders. |
| Which sales channel is used the most? | `metrics: [orders, net_sales, customers]`, `groupBy: [sales_channel]` | Online Store: 11 of 20 orders, $1,882.20 |
| How many sales did we do last week? | `2025-10-20 → 2025-10-26`, `metrics: [orders, net_sales, units_sold]` | 4 orders, $543.50, 7 units |
| How many sales did we do last month? | `2025-09-01 → 2025-09-30`, same metrics | 2 orders, $231.10 |
| How have sales trended month over month? | `metrics: [net_sales, orders]`, `groupBy: [month]` | May $224 → … → October $2,261.25 (13 orders) |

## Using it with the Vercel AI SDK

The tools are ready to pass to `streamText` / `generateText`:

```ts
import { stepCountIs, streamText } from "ai";
import { describeDataset, storeAnalyticsTools } from "@/lib/analytics";

const result = streamText({
  model, // any AI SDK model, e.g. through the Vercel AI Gateway
  system: `You are an analytics assistant for a Shopify merchant.
Today's date is ${describeDataset().latestDataDate}. Answer only from tool results.`,
  messages,
  tools: storeAnalyticsTools, // { describeStoreData, queryStoreData }
  stopWhen: stepCountIs(5),
});
```

The tool description in [`tool.ts`](src/lib/analytics/tool.ts) tells the model how to map common wording to queries: "sales" means `net_sales`, "why returned" means filtering on returns and grouping by `return_reason`, how to resolve relative dates, and so on.

## HTTP API

```bash
# Run a query
curl -X POST http://localhost:3000/api/analytics/query \
  -H 'content-type: application/json' \
  -d '{"startDate":"2025-05-06","endDate":"2025-10-27","metrics":["orders","net_sales"],"groupBy":["sales_channel"]}'

# What the dataset contains, and which metrics/dimensions exist
curl http://localhost:3000/api/analytics/dataset
```

An invalid query returns `400` with the Zod field errors.

## Project structure

```
.
├── data/
│   └── orders.csv                 # Store order history, May–Oct 2025 (one row per line item)
├── src/
│   ├── app/
│   │   ├── page.tsx               # Overview: dataset summary + example queries
│   │   ├── layout.tsx
│   │   └── api/analytics/
│   │       ├── query/route.ts     # POST: run queryStoreData
│   │       └── dataset/route.ts   # GET: describeDataset
│   └── lib/
│       ├── store-data/            # Loading the raw data
│       │   ├── csv.ts             # RFC 4180 CSV parser
│       │   ├── parse.ts           # CSV rows → validated OrderLineItem[]
│       │   ├── load.ts            # Reads data/orders.csv (cached per process)
│       │   └── types.ts           # OrderLineItem
│       └── analytics/             # The query engine
│           ├── query.ts           # queryStoreData(): filter → group → compute → sort → limit
│           ├── schema.ts          # Zod input schema (shared by the API and the LLM tool)
│           ├── metrics.ts         # Metric definitions
│           ├── dimensions.ts      # groupBy dimensions
│           ├── filters.ts         # Filters + "unknown value" warnings
│           ├── dates.ts           # Day/week/month bucketing
│           ├── describe.ts        # describeDataset()
│           ├── examples.ts        # Merchant questions → queries
│           ├── tool.ts            # AI SDK tool definitions
│           └── index.ts           # Public exports
└── tests/
    └── analytics.test.ts
```

To add a metric, add an entry to `METRICS` in `metrics.ts`. To add a dimension, add one to `DIMENSIONS` in `dimensions.ts`. The schema, the tool, the API and `describeDataset()` all pick it up from those registries.

## The data

`data/orders.csv` is the store's order export for May–October 2025: 28 line items across 20 orders, 18 customers and 11 products. Columns:

`order_id, line_item_id, order_date, customer_id, is_repeat_customer, product_id, product_title, product_category, variant, quantity, unit_price, discount_amount, line_total, sales_channel, fulfillment_status, returned, return_date, return_reason, refund_amount`

How the columns are interpreted:

- **Grain:** one row per order line item. Orders and customers are counted as distinct IDs, never as rows.
- **`is_repeat_customer`** describes the order: `true` means the customer had ordered before, so this order is a repeat purchase.
- **`line_total`** = `quantity × unit_price − discount_amount`, and that is what "net sales" sums.
- **Refunds can be partial**: e.g. one $143.10 line was refunded $128.79.
- **`variant`** (`"M / Black"`) is split into `size` and `color`.
- Money is summed in integer cents, so totals are exact.

## Tech

Next.js 16 (App Router, TypeScript), Zod 4, Vercel AI SDK 7, Tailwind CSS 4, Vitest.
