import { describeDataset, EXAMPLE_QUERIES } from "@/lib/analytics";

export default function Home() {
  const dataset = describeDataset();

  const stats = [
    { label: "Orders", value: dataset.counts.orders },
    { label: "Line items", value: dataset.counts.lineItems },
    { label: "Customers", value: dataset.counts.customers },
    { label: "Products", value: dataset.counts.products },
  ];

  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-12 sm:px-6">
      <p className="text-sm font-medium text-neutral-500">Zero Uni · Project 1</p>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight">Shopify Merchant Analytics</h1>
      <p className="mt-3 max-w-2xl text-neutral-600 dark:text-neutral-400">
        Ask questions about your store in plain English. An LLM turns each question into a call to{" "}
        <code className="font-mono text-sm">queryStoreData</code> — a date range, the metrics needed, and how to break
        them down — and answers from the result. The query engine is in place; the chat interface comes next.
      </p>

      <section className="mt-10">
        <h2 className="text-lg font-semibold">Dataset</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Orders from {dataset.orderDates?.startDate} to {dataset.orderDates?.endDate}. {dataset.grain}
        </p>
        <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
              <dt className="text-sm text-neutral-500">{stat.label}</dt>
              <dd className="mt-1 text-2xl font-semibold tabular-nums">{stat.value}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-sm text-neutral-600 dark:text-neutral-400">
          Channels: {dataset.salesChannels.join(", ")} · Return reasons: {dataset.returnReasons.join(", ")}
        </p>
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-semibold">Example questions → queries</h2>
        <ul className="mt-4 space-y-4">
          {EXAMPLE_QUERIES.map(({ question, query }) => (
            <li key={question} className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800">
              <p className="font-medium">“{question}”</p>
              <pre className="mt-2 overflow-x-auto rounded bg-neutral-100 p-3 font-mono text-xs dark:bg-neutral-900">
                {JSON.stringify(query, null, 2)}
              </pre>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-semibold">API</h2>
        <ul className="mt-2 list-inside list-disc text-sm text-neutral-600 dark:text-neutral-400">
          <li>
            <code className="font-mono">POST /api/analytics/query</code> — run a query (JSON body)
          </li>
          <li>
            <code className="font-mono">GET /api/analytics/dataset</code> — dataset summary, metrics and dimensions
          </li>
        </ul>
      </section>
    </main>
  );
}
