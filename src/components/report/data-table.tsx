import type { ResultColumn, ResultRow } from "@/lib/analytics";
import { formatValue } from "@/lib/format";

/** Row-by-row detail. Numbers right-aligned with tabular figures. */
export function DataTable({ columns, rows }: { columns: ResultColumn[]; rows: ResultRow[] }) {
  return (
    <div className="max-h-80 overflow-auto rounded-lg border border-hairline">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="sticky top-0 bg-surface">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={`border-b border-hairline px-3 py-2 text-xs font-medium text-ink-2 ${
                  column.role === "metric" ? "text-right" : ""
                }`}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-hairline last:border-b-0">
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={`px-3 py-1.5 ${column.role === "metric" ? "text-right tabular-nums" : "text-ink"} whitespace-nowrap`}
                >
                  {formatValue(row[column.key] ?? null, column.format, column.key)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
