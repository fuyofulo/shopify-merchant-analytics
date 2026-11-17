import { Chat } from "@/components/chat/chat";
import { describeDataset } from "@/lib/analytics";
import { formatRange } from "@/lib/format";

/** Real questions from data/merchant-report-requests-2025-10-27.xlsx, plus one that shows the returns list. */
const SUGGESTIONS = [
  "jakets returnd last wk",
  "best seller since summer?",
  "sales by week last 8 weeks",
  "repeat customer share by month",
  "which coats got returned most over the last couple weeks?",
  "show me the returned orders from the last 30 days",
];

export default function Home() {
  const { orderDates } = describeDataset();
  const dataNote = orderDates ? `Store data covers ${formatRange(orderDates.startDate, orderDates.endDate)}.` : "";
  return <Chat suggestions={SUGGESTIONS} dataNote={dataNote} />;
}
