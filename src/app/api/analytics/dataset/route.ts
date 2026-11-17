import { describeDataset } from "@/lib/analytics";

/** GET /api/analytics/dataset — what the dataset contains and which metrics/dimensions can be queried. */
export async function GET() {
  return Response.json(describeDataset());
}
